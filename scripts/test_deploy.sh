#!/bin/bash
# =============================================================================
# MóveisERP — Testa se o servidor está funcionando corretamente
# Uso: sudo bash /var/www/moveis_erp/scripts/test_deploy.sh
# =============================================================================

APP_DIR="/var/www/moveis_erp"
APP_USER="erp"
ENV_FILE="$APP_DIR/.env"
VENV="$APP_DIR/venv/bin"
SERVER_IP=$(hostname -I | awk '{print $1}')

OK=0; FAIL=0; WARN=0
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; OK=$((OK+1)); }
fail() { echo -e "  ${RED}✗${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; WARN=$((WARN+1)); }

echo ""
echo "=============================================="
echo " MóveisERP — Verificação pós-deploy"
echo " $(date '+%d/%m/%Y %H:%M:%S') | IP: $SERVER_IP"
echo "=============================================="

# ── Serviços ───────────────────────────────────────────────────────────────────
echo ""
echo "[ Serviços ]"
for svc in gunicorn_erp celery_erp celerybeat_erp nginx postgresql redis-server; do
    if systemctl is-active --quiet "$svc"; then
        ok "$svc"
    else
        fail "$svc PARADO → sudo systemctl start $svc"
    fi
done

# ── Arquivos ───────────────────────────────────────────────────────────────────
echo ""
echo "[ Arquivos ]"
for f in manage.py .env config/wsgi.py requirements/production.txt; do
    [ -f "$APP_DIR/$f" ] && ok "$f" || fail "$f não encontrado"
done
[ -d "$APP_DIR/venv" ] && ok "venv" || fail "venv não existe"

COUNT=$(find "$APP_DIR/staticfiles" -type f 2>/dev/null | wc -l)
[ "$COUNT" -gt 10 ] && ok "staticfiles ($COUNT arquivos)" || fail "staticfiles vazio → sudo bash $APP_DIR/scripts/fix_server.sh"

# ── Socket Gunicorn ────────────────────────────────────────────────────────────
echo ""
echo "[ Gunicorn ]"
SOCK="/run/gunicorn_erp/gunicorn.sock"
if [ -S "$SOCK" ]; then
    ok "socket existe: $SOCK"
    # Testa permissão do www-data no socket
    if sudo -u www-data test -r "$SOCK" 2>/dev/null; then
        ok "Nginx (www-data) pode ler o socket"
    else
        warn "Nginx pode não ter permissão no socket → sudo usermod -aG erp www-data"
    fi
else
    fail "socket não existe → sudo systemctl restart gunicorn_erp"
fi

# ── HTTP ───────────────────────────────────────────────────────────────────────
echo ""
echo "[ HTTP ]"
check_http() {
    local url="$1" label="$2" expected="$3"
    local code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$url" 2>/dev/null)
    if echo "$code" | grep -qE "$expected"; then
        ok "$label → $code"
    else
        fail "$label → $code (esperado: $expected)"
    fi
}

check_http "http://localhost/"        "GET /"           "200|301|302"
check_http "http://localhost/entrar/" "GET /entrar/"    "200"
check_http "http://localhost/admin/"  "GET /admin/"     "200|301|302"

STATIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
    "http://localhost/static/" 2>/dev/null)
[ "$STATIC_CODE" = "403" ] || [ "$STATIC_CODE" = "200" ] && \
    ok "Static files servidos pelo Nginx ($STATIC_CODE)" || \
    warn "Static files → $STATIC_CODE"

# ── PostgreSQL ─────────────────────────────────────────────────────────────────
echo ""
echo "[ Banco de Dados ]"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='moveis_erp'" 2>/dev/null | grep -q 1 && \
    ok "Banco 'moveis_erp' existe" || fail "Banco não encontrado"

RESULT=$(sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $VENV/python -c '
from django.db import connection
try:
    connection.ensure_connection()
    c = connection.cursor()
    c.execute(\"SELECT count(*) FROM information_schema.tables WHERE table_schema=\\\"public\\\"\")
    n = c.fetchone()[0]
    print(f\"OK:{n}\")
except Exception as e:
    print(f\"FAIL:{e}\")
' 2>/dev/null" 2>/dev/null)

if echo "$RESULT" | grep -q "^OK:"; then
    N=$(echo "$RESULT" | cut -d: -f2)
    [ "$N" -gt 10 ] && ok "Banco migrado ($N tabelas)" || warn "Poucas tabelas ($N) → make migrate"
else
    fail "Conexão Django→PostgreSQL falhou: $RESULT"
fi

# ── Redis ──────────────────────────────────────────────────────────────────────
echo ""
echo "[ Redis ]"
redis-cli ping 2>/dev/null | grep -q PONG && ok "Redis PONG" || fail "Redis não responde"

REDIS=$(sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    set -a; source $ENV_FILE; set +a
    $VENV/python -c '
import redis, os
try:
    r = redis.from_url(os.environ.get(\"REDIS_URL\",\"redis://localhost:6379/0\"))
    r.ping()
    print(\"OK\")
except Exception as e:
    print(f\"FAIL:{e}\")
' 2>/dev/null" 2>/dev/null)
[ "$REDIS" = "OK" ] && ok "Python→Redis OK" || warn "Python→Redis: $REDIS"

# ── Django check ───────────────────────────────────────────────────────────────
echo ""
echo "[ Django ]"
CHKOUT=$(sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $VENV/python $APP_DIR/manage.py check 2>&1" 2>/dev/null)

if echo "$CHKOUT" | grep -q "System check identified no issues"; then
    ok "manage.py check: sem problemas"
elif echo "$CHKOUT" | grep -q "System check identified"; then
    warn "manage.py check: $(echo "$CHKOUT" | grep 'System check' | tail -1)"
else
    fail "manage.py check falhou"
    echo "$CHKOUT" | tail -5 | sed 's/^/     /'
fi

# ── Superusuário ───────────────────────────────────────────────────────────────
echo ""
echo "[ Superusuário ]"
SU=$(sudo -u "$APP_USER" bash -c "
    cd $APP_DIR
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $VENV/python -c '
from django.contrib.auth import get_user_model
U = get_user_model()
n = U.objects.filter(is_superuser=True).count()
print(n)
' 2>/dev/null" 2>/dev/null)

if [ -n "$SU" ] && [ "$SU" -gt 0 ] 2>/dev/null; then
    ok "$SU superusuário(s) cadastrado(s)"
else
    warn "Nenhum superusuário — crie com:"
    echo "       sudo -u erp $VENV/python $APP_DIR/manage.py createsuperuser"
fi

# ── Logs ───────────────────────────────────────────────────────────────────────
echo ""
echo "[ Logs recentes ]"
for log in gunicorn_error.log celery_worker.log; do
    LOG_FILE="$APP_DIR/logs/$log"
    if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
        ERRS=$(tail -20 "$LOG_FILE" | grep -iE "error|exception|traceback" | grep -v "^#" | tail -3)
        if [ -n "$ERRS" ]; then
            warn "Erros em $log:"
            echo "$ERRS" | sed 's/^/     /'
        else
            ok "$log limpo"
        fi
    else
        ok "$log vazio"
    fi
done

# ── Resumo ─────────────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
printf " ${GREEN}✓${NC} OK: ${GREEN}%d${NC}  |  ${RED}✗${NC} Falha: ${RED}%d${NC}  |  ${YELLOW}⚠${NC} Aviso: ${YELLOW}%d${NC}\n" \
    $OK $FAIL $WARN
echo "=============================================="

if [ $FAIL -eq 0 ]; then
    echo -e "\n ${GREEN}✅  Sistema operacional!${NC}\n"
    echo " → http://$SERVER_IP/"
    echo " → http://$SERVER_IP/entrar/"
    echo " → http://$SERVER_IP/admin/"
    [ $WARN -gt 0 ] && echo -e "\n ${YELLOW}⚠  $WARN aviso(s) acima${NC}"
else
    echo -e "\n ${RED}❌  $FAIL problema(s) — rode:${NC}"
    echo "   sudo bash $APP_DIR/scripts/fix_server.sh"
    echo ""
    echo " Logs:"
    echo "   journalctl -u gunicorn_erp -n 30 --no-pager"
    echo "   tail -f $APP_DIR/logs/gunicorn_error.log"
fi
echo ""
