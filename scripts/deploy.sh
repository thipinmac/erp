#!/bin/bash
# =============================================================================
# MóveisERP — Deploy inicial no Ubuntu Server 22.04 / 24.04
# Executa como root ou com sudo
#
# Uso:
#   chmod +x deploy.sh
#   sudo bash deploy.sh
# =============================================================================
set -e  # Para em caso de erro

# ── Configurações ──────────────────────────────────────────────────────────────
APP_NAME="moveis_erp"
APP_DIR="/var/www/$APP_NAME"
APP_USER="erp"
PYTHON="python3"
PG_DB="moveis_erp"
PG_USER="erp_user"
PG_PASS="ErpMoveis@2026"   # ← Altere antes de rodar em produção real

# Detecta IP local da máquina
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "=============================================="
echo " MóveisERP — Setup Ubuntu Server"
echo " IP detectado: $SERVER_IP"
echo "=============================================="

# ── 1. Pacotes do sistema ──────────────────────────────────────────────────────
echo ""
echo "[1/10] Atualizando pacotes..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib libpq-dev \
    redis-server \
    nginx \
    git curl wget \
    build-essential \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    supervisor

echo "  ✓ Pacotes instalados"

# ── 2. Usuário da aplicação ────────────────────────────────────────────────────
echo ""
echo "[2/10] Criando usuário '$APP_USER'..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/bash "$APP_USER"
fi
echo "  ✓ Usuário '$APP_USER' pronto"

# ── 3. PostgreSQL ──────────────────────────────────────────────────────────────
echo ""
echo "[3/10] Configurando PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename='$PG_USER'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER $PG_USER WITH PASSWORD '$PG_PASS';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$PG_DB'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $PG_DB OWNER $PG_USER;"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $PG_DB TO $PG_USER;"
echo "  ✓ Banco '$PG_DB' pronto"

# Garante que www-data acessa o socket do Gunicorn
usermod -aG "$APP_USER" www-data 2>/dev/null || true

# ── 4. Redis ──────────────────────────────────────────────────────────────────
echo ""
echo "[4/10] Iniciando Redis..."
systemctl start redis-server
systemctl enable redis-server
echo "  ✓ Redis rodando"

# ── 5. Diretório da aplicação ─────────────────────────────────────────────────
echo ""
echo "[5/10] Preparando diretório da aplicação..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/media"
mkdir -p "$APP_DIR/staticfiles"
mkdir -p "$APP_DIR/logs"

# Se o código ainda não foi copiado, avisa
if [ ! -f "$APP_DIR/manage.py" ]; then
    echo ""
    echo "  ⚠  Código não encontrado em $APP_DIR"
    echo "  Cole o projeto e re-execute este script, ou use:"
    echo "    scp -r ./moveis_erp usuario@$SERVER_IP:$APP_DIR"
    echo ""
    echo "  Após copiar o código, execute novamente: sudo bash $APP_DIR/scripts/deploy.sh"
    exit 0
fi

chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
echo "  ✓ Diretório pronto em $APP_DIR"

# ── 6. Virtualenv e dependências Python ───────────────────────────────────────
echo ""
echo "[6/10] Instalando dependências Python..."
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u "$APP_USER" $PYTHON -m venv "$APP_DIR/venv"
fi

sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip -q --no-cache-dir
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements/production.txt" -q --no-cache-dir
echo "  ✓ Pacotes Python instalados"

# ── 7. Arquivo .env de produção ────────────────────────────────────────────────
echo ""
echo "[7/10] Configurando variáveis de ambiente..."
ENV_FILE="$APP_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    SECRET_KEY=$(sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" -c \
        "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

    cat > "$ENV_FILE" <<EOF
# Gerado automaticamente em $(date)
SECRET_KEY='$SECRET_KEY'
DEBUG=False
ALLOWED_HOSTS=$SERVER_IP,localhost,127.0.0.1

# Banco de dados
DATABASE_URL=postgres://$PG_USER:$PG_PASS@localhost/$PG_DB

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Email (console para testes, substitua por SMTP em prod real)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=erp@localserver

# Sentry (deixe vazio para desativar)
SENTRY_DSN=

# Integrações fiscais (preencha quando tiver)
FISCAL_PROVEDOR=nfse
FISCAL_API_URL=
FISCAL_API_TOKEN=
WHATSAPP_API_URL=
WHATSAPP_API_TOKEN=
EOF

    chown "$APP_USER":"$APP_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  ✓ .env criado com SECRET_KEY aleatória"
else
    echo "  ✓ .env já existe (mantido)"
fi

export DJANGO_SETTINGS_MODULE=config.settings.production

# ── 8. Django: migrate + collectstatic ───────────────────────────────────────
echo ""
echo "[8/10] Rodando migrate e collectstatic..."
cd "$APP_DIR"

sudo -u "$APP_USER" bash -c "
    set -a
    source $ENV_FILE
    set +a
    $APP_DIR/venv/bin/python manage.py migrate --noinput
    $APP_DIR/venv/bin/python manage.py collectstatic --noinput --clear
"
echo "  ✓ Banco migrado e static coletados"

# ── 9. Serviços systemd ────────────────────────────────────────────────────────
echo ""
echo "[9/10] Instalando serviços systemd..."

# Gunicorn
cat > /etc/systemd/system/gunicorn_erp.service <<EOF
[Unit]
Description=MóveisERP — Gunicorn
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=$APP_DIR/venv/bin/gunicorn config.wsgi:application \\
    --workers 3 \\
    --worker-class sync \\
    --bind unix:/run/gunicorn_erp/gunicorn.sock \\
    --timeout 120 \\
    --access-logfile $APP_DIR/logs/gunicorn_access.log \\
    --error-logfile $APP_DIR/logs/gunicorn_error.log
ExecReload=/bin/kill -s HUP \$MAINPID
RuntimeDirectory=gunicorn_erp
RuntimeDirectoryMode=0755
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker
cat > /etc/systemd/system/celery_erp.service <<EOF
[Unit]
Description=MóveisERP — Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=$APP_DIR/venv/bin/celery -A config worker \\
    --loglevel=warning \\
    --logfile=$APP_DIR/logs/celery_worker.log \\
    --pidfile=/run/celery_erp_worker.pid
PIDFile=/run/celery_erp_worker.pid
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat (scheduler)
cat > /etc/systemd/system/celerybeat_erp.service <<EOF
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
ExecStart=$APP_DIR/venv/bin/celery -A config beat \\
    --loglevel=warning \\
    --logfile=$APP_DIR/logs/celery_beat.log \\
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable gunicorn_erp celery_erp celerybeat_erp
systemctl start gunicorn_erp celery_erp celerybeat_erp
echo "  ✓ Serviços systemd instalados e iniciados"

# ── 10. Nginx ─────────────────────────────────────────────────────────────────
echo ""
echo "[10/10] Configurando Nginx..."

cat > /etc/nginx/sites-available/moveis_erp <<EOF
server {
    listen 80;
    server_name $SERVER_IP localhost;

    client_max_body_size 50M;

    # Static files — servidos pelo Nginx diretamente
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        access_log off;
    }

    # Media files (uploads)
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
        access_log off;
    }

    # Aplicação Django via Gunicorn
    location / {
        proxy_pass http://unix:/run/gunicorn_erp/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
EOF

# Ativa o site
ln -sf /etc/nginx/sites-available/moveis_erp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
systemctl enable nginx
echo "  ✓ Nginx configurado"

# ── Resumo final ──────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo " ✅  Deploy concluído!"
echo "=============================================="
echo ""
echo " Acesse: http://$SERVER_IP/"
echo ""
echo " Criar superusuário:"
echo "   sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/manage.py createsuperuser"
echo ""
echo " Logs:"
echo "   journalctl -u gunicorn_erp -f"
echo "   tail -f $APP_DIR/logs/gunicorn_error.log"
echo ""
echo " Para atualizar o sistema depois:"
echo "   sudo bash $APP_DIR/scripts/update.sh"
echo "=============================================="
