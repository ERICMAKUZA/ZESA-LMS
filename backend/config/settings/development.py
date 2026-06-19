from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_extensions"]  # noqa: F405

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
