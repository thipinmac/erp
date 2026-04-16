# =============================================================================
# MóveisERP — Makefile
# Uso: make <comando>
# =============================================================================

APP_DIR    = /var/www/moveis_erp
APP_USER   = erp
VENV       = $(APP_DIR)/venv/bin
ENV_FILE   = $(APP_DIR)/.env
PYTHON     = $(VENV)/python
MANAGE     = $(PYTHON) $(APP_DIR)/manage.py
SETTINGS   = config.settings.production

.PHONY: help deploy update logs status restart shell migrate static superuser backup

help:
	@echo ""
	@echo "  MóveisERP — comandos disponíveis:"
	@echo ""
	@echo "  make deploy       Primeiro deploy (instala tudo)"
	@echo "  make update       Atualiza após novo código"
	@echo "  make migrate      Roda migrações"
	@echo "  make static       Coleta arquivos estáticos"
	@echo "  make superuser    Cria superusuário Django"
	@echo "  make shell        Abre Django shell"
	@echo "  make logs         Mostra logs do Gunicorn ao vivo"
	@echo "  make status       Status de todos os serviços"
	@echo "  make restart      Reinicia todos os serviços"
	@echo "  make backup       Faz backup do banco PostgreSQL"
	@echo ""

deploy:
	sudo bash $(APP_DIR)/scripts/deploy.sh

update:
	sudo bash $(APP_DIR)/scripts/update.sh

migrate:
	sudo -u $(APP_USER) bash -c "set -a; source $(ENV_FILE); set +a; DJANGO_SETTINGS_MODULE=$(SETTINGS) $(MANAGE) migrate --noinput"

static:
	sudo -u $(APP_USER) bash -c "set -a; source $(ENV_FILE); set +a; DJANGO_SETTINGS_MODULE=$(SETTINGS) $(MANAGE) collectstatic --noinput --clear"

superuser:
	sudo -u $(APP_USER) bash -c "set -a; source $(ENV_FILE); set +a; DJANGO_SETTINGS_MODULE=$(SETTINGS) $(MANAGE) createsuperuser"

shell:
	sudo -u $(APP_USER) bash -c "set -a; source $(ENV_FILE); set +a; DJANGO_SETTINGS_MODULE=$(SETTINGS) $(MANAGE) shell"

logs:
	journalctl -u gunicorn_erp -f

logs-celery:
	journalctl -u celery_erp -f

status:
	@echo "--- Gunicorn ---"
	@systemctl status gunicorn_erp --no-pager | grep -E "Active:|Main PID:"
	@echo "--- Celery Worker ---"
	@systemctl status celery_erp --no-pager | grep -E "Active:|Main PID:"
	@echo "--- Celery Beat ---"
	@systemctl status celerybeat_erp --no-pager | grep -E "Active:|Main PID:"
	@echo "--- Nginx ---"
	@systemctl status nginx --no-pager | grep -E "Active:|Main PID:"
	@echo "--- PostgreSQL ---"
	@systemctl status postgresql --no-pager | grep -E "Active:|Main PID:"
	@echo "--- Redis ---"
	@systemctl status redis-server --no-pager | grep -E "Active:|Main PID:"

restart:
	sudo systemctl restart gunicorn_erp celery_erp celerybeat_erp
	sudo systemctl reload nginx
	@echo "✓ Serviços reiniciados"

backup:
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	BACKUP_FILE="$(APP_DIR)/backups/db_$$TIMESTAMP.sql.gz"; \
	mkdir -p $(APP_DIR)/backups; \
	sudo -u postgres pg_dump moveis_erp | gzip > $$BACKUP_FILE; \
	echo "✓ Backup salvo em $$BACKUP_FILE"

check:
	sudo -u $(APP_USER) bash -c "set -a; source $(ENV_FILE); set +a; DJANGO_SETTINGS_MODULE=$(SETTINGS) $(MANAGE) check"
