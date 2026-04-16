"""Configurações de desenvolvimento."""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# SQLite para desenvolvimento rápido (mude para PostgreSQL se precisar de JSON fields)
# DATABASES já vem do base.py via DATABASE_URL

# Tailwind via CDN no dev (sem build pipeline)
TAILWIND_USE_CDN = True

# Django Debug Toolbar
try:
    import debug_toolbar  # noqa

    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# Email: console para não precisar de SMTP
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logs mais verbosos
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Mude para DEBUG para ver todas as queries
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
