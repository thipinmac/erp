"""
Base settings compartilhadas entre todos os ambientes.
"""
import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ─── Applications ────────────────────────────────────────────────────────────

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "django_htmx",
    "django_extensions",
    "django_filters",
    "crispy_forms",
    "crispy_tailwind",
    "widget_tweaks",
]

LOCAL_APPS = [
    "apps.core",
    "apps.administracao",
    "apps.cadastros",
    "apps.crm",
    "apps.orcamentos",
    "apps.engenharia",
    "apps.contratos",
    "apps.pedidos",
    "apps.compras",
    "apps.estoque",
    "apps.producao",
    "apps.entrega",
    "apps.portal_cliente",
    "apps.assistencia",
    "apps.financeiro",
    "apps.fiscal",
    "apps.comunicacao",
    "apps.bi",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ───────────────────────────────────────────────────────────────

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.core.middleware.tenant.TenantMiddleware",
    "apps.core.middleware.audit.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"

# ─── Templates ────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.tenant_info",
                "apps.core.context_processors.menu_items",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─── Database ────────────────────────────────────────────────────────────────

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR}/db.sqlite3")
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Auth ─────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = "administracao.Usuario"
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/entrar/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internacionalização ──────────────────────────────────────────────────────

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ─── Static & Media ──────────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Crispy Forms ────────────────────────────────────────────────────────────

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# ─── Celery ──────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ─── Email ───────────────────────────────────────────────────────────────────

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@moveis-erp.com.br")

# ─── Configurações do ERP ────────────────────────────────────────────────────

ERP_NOME = "MóveisERP"
ERP_VERSAO = "1.0.0"

# Integrations (configurados via .env)
WHATSAPP_API_URL = env("WHATSAPP_API_URL", default="")
WHATSAPP_API_TOKEN = env("WHATSAPP_API_TOKEN", default="")
ASSINATURA_API_URL = env("ASSINATURA_API_URL", default="")
ASSINATURA_API_TOKEN = env("ASSINATURA_API_TOKEN", default="")
FISCAL_PROVEDOR = env("FISCAL_PROVEDOR", default="nfse")
FISCAL_API_URL = env("FISCAL_API_URL", default="")
FISCAL_API_TOKEN = env("FISCAL_API_TOKEN", default="")
