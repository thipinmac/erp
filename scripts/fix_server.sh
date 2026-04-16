#!/bin/bash
# =============================================================================
# MóveisERP — Corrige e finaliza o servidor após deploy parcial
# Uso: sudo bash /var/www/moveis_erp/scripts/fix_server.sh
# =============================================================================
set -e

APP_DIR="/var/www/moveis_erp"
APP_USER="erp"
ENV_FILE="$APP_DIR/.env"
VENV="$APP_DIR/venv/bin"
SERVER_IP=$(hostname -I | awk '{print $1}')

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()  { echo -e "  ${GREEN}✓${NC} $1"; }
err() { echo -e "  ${RED}✗${NC} $1"; }
inf() { echo -e "  ${CYAN}→${NC} $1"; }

echo ""
echo "=============================================="
echo " MóveisERP — Fix & Finalização do Servidor"
echo " IP: $SERVER_IP"
echo "=============================================="

# ── 1. Para todos os serviços ──────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[1/9] Parando serviços...${NC}"
systemctl stop gunicorn_erp celery_erp celerybeat_erp 2>/dev/null || true
ok "Serviços parados"

# ── 2. Corrige o .env (SECRET_KEY precisa de aspas simples) ───────────────────
echo ""
echo -e "${YELLOW}[2/9] Verificando .env...${NC}"
python3 - << 'PYEOF'
import re, sys

path = '/var/www/moveis_erp/.env'
try:
    with open(path, 'r') as f:
        content = f.read()

    def quote_val(m):
        val = m.group(1).strip()
        if val.startswith("'") or val.startswith('"'):
            return m.group(0)
        return f"SECRET_KEY='{val}'"

    fixed = re.sub(r'^SECRET_KEY=(.+)$', quote_val, content, flags=re.MULTILINE)

    if fixed != content:
        with open(path, 'w') as f:
            f.write(fixed)
        print("  SECRET_KEY: aspas adicionadas")
    else:
        print("  SECRET_KEY: já estava OK")
except Exception as e:
    print(f"  AVISO: {e}")
PYEOF
ok ".env verificado"

# ── 3. Garante permissões corretas ─────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/9] Corrigindo permissões...${NC}"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chmod 600 "$ENV_FILE"
mkdir -p "$APP_DIR/logs" "$APP_DIR/media" "$APP_DIR/staticfiles"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR/logs" "$APP_DIR/media" "$APP_DIR/staticfiles"

# www-data (Nginx) precisa acessar o socket do Gunicorn
usermod -aG "$APP_USER" www-data 2>/dev/null && ok "www-data adicionado ao grupo $APP_USER" || true
ok "Permissões OK"

# ── 4. Reescreve o serviço Gunicorn do zero ───────────────────────────────────
echo ""
echo -e "${YELLOW}[4/9] Recriando serviços systemd...${NC}"

cat > /etc/systemd/system/gunicorn_erp.service << EOF
[Unit]
Description=MóveisERP — Gunicorn
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=$VENV/gunicorn config.wsgi:application \\
    --workers 3 \\
    --worker-class sync \\
    --bind unix:/run/gunicorn_erp/gunicorn.sock \\
    --umask 007 \\
    --timeout 120 \\
    --access-logfile $APP_DIR/logs/gunicorn_access.log \\
    --error-logfile $APP_DIR/logs/gunicorn_error.log
ExecReload=/bin/kill -s HUP \$MAINPID
RuntimeDirectory=gunicorn_erp
RuntimeDirectoryMode=0770
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/celery_erp.service << EOF
[Unit]
Description=MóveisERP — Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=$VENV/celery -A config worker \\
    --loglevel=warning \\
    --logfile=$APP_DIR/logs/celery_worker.log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/celerybeat_erp.service << EOF
[Unit]
Description=MóveisERP — Celery Beat
After=network.target redis.service celery_erp.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=$VENV/celery -A config beat \\
    --loglevel=warning \\
    --logfile=$APP_DIR/logs/celery_beat.log \\
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable gunicorn_erp celery_erp celerybeat_erp
ok "Serviços systemd recriados"

# ── 5. Recria o config do Nginx ────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/9] Recriando config do Nginx...${NC}"

cat > /etc/nginx/sites-available/moveis_erp << EOF
server {
    listen 80;
    server_name $SERVER_IP localhost;

    client_max_body_size 50M;

    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        access_log off;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
        access_log off;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn_erp/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/moveis_erp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
ok "Nginx configurado"

# ── 6. Migrate + collectstatic ────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[6/9] Rodando migrate...${NC}"
sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $VENV/python manage.py migrate --noinput 2>&1
"
ok "Migrate concluído"

echo ""
echo -e "${YELLOW}[7/9] Coletando static files...${NC}"
sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $VENV/python manage.py collectstatic --noinput --clear 2>&1
" | tail -3
ok "Static files coletados"

# ── 7. Inicia todos os serviços ────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[8/9] Iniciando serviços...${NC}"

systemctl start gunicorn_erp
sleep 2

if systemctl is-active --quiet gunicorn_erp; then
    ok "Gunicorn rodando"
else
    err "Gunicorn falhou — log abaixo:"
    journalctl -u gunicorn_erp -n 20 --no-pager
    exit 1
fi

systemctl start celery_erp
sleep 1
systemctl is-active --quiet celery_erp && ok "Celery Worker rodando" || err "Celery Worker falhou"

systemctl start celerybeat_erp
sleep 1
systemctl is-active --quiet celerybeat_erp && ok "Celery Beat rodando" || err "Celery Beat falhou"

systemctl reload nginx
ok "Nginx recarregado"

# ── 8. Testes rápidos ──────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[9/9] Testando...${NC}"
sleep 1

HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/entrar/ 2>/dev/null)
if [ "$HTTP" = "200" ]; then
    ok "HTTP /entrar/ → 200 ✅"
else
    err "HTTP /entrar/ → $HTTP"
fi

HTTP_STATIC=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/static/ 2>/dev/null)
inf "HTTP /static/ → $HTTP_STATIC"

# ── Resumo ─────────────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
if systemctl is-active --quiet gunicorn_erp; then
    echo -e " ${GREEN}✅  Servidor operacional!${NC}"
    echo ""
    echo " Acesse no navegador:"
    echo "   http://$SERVER_IP/"
    echo "   http://$SERVER_IP/entrar/"
    echo "   http://$SERVER_IP/admin/"
    echo ""
    echo " Criar superusuário:"
    echo "   sudo -u erp $VENV/python $APP_DIR/manage.py createsuperuser"
else
    echo -e " ${RED}❌  Gunicorn ainda com problemas — rode:${NC}"
    echo "   journalctl -u gunicorn_erp -n 30 --no-pager"
fi
echo "=============================================="
echo ""
