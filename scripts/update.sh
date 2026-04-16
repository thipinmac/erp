#!/bin/bash
# =============================================================================
# MóveisERP — Atualização do sistema (rodar após cada novo deploy)
# Uso: sudo bash /var/www/moveis_erp/scripts/update.sh
# =============================================================================
set -e

APP_DIR="/var/www/moveis_erp"
APP_USER="erp"
ENV_FILE="$APP_DIR/.env"

echo "=============================="
echo " MóveisERP — Atualizando..."
echo "=============================="

cd "$APP_DIR"

# 1. Instala/atualiza dependências Python
echo "[1/5] Atualizando dependências..."
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r requirements/production.txt -q --upgrade
echo "  ✓ Dependências OK"

# 2. Roda migrações
echo "[2/5] Migrando banco..."
sudo -u "$APP_USER" bash -c "
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $APP_DIR/venv/bin/python manage.py migrate --noinput
"
echo "  ✓ Banco migrado"

# 3. Coleta static files
echo "[3/5] Coletando static..."
sudo -u "$APP_USER" bash -c "
    set -a; source $ENV_FILE; set +a
    DJANGO_SETTINGS_MODULE=config.settings.production \
    $APP_DIR/venv/bin/python manage.py collectstatic --noinput --clear
"
echo "  ✓ Static coletado"

# 4. Reinicia serviços
echo "[4/5] Reiniciando serviços..."
systemctl restart gunicorn_erp
systemctl restart celery_erp
systemctl restart celerybeat_erp
echo "  ✓ Serviços reiniciados"

# 5. Reload Nginx (recarrega config se mudou)
echo "[5/5] Recarregando Nginx..."
nginx -t && systemctl reload nginx
echo "  ✓ Nginx OK"

echo ""
echo "=============================="
echo " ✅  Atualização concluída!"
echo "=============================="
systemctl status gunicorn_erp --no-pager | grep "Active:"
