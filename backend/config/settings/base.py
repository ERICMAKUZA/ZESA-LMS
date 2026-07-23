from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv(), default="localhost")
DEMO_MODE = config("DEMO_MODE", cast=bool, default=True)

DJANGO_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.courses",
    "apps.applications",
    "apps.workflows",
    "apps.payments",
    "apps.enrollments",
    "apps.certificates",
    "apps.reports",
    "centres",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

_database_url = config("DATABASE_URL")
DATABASES = {
    "default": dj_database_url.parse(
        _database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django defaults this to /accounts/profile/, which doesn't exist in this
# app — anyone logging in at /django-admin/login/ without a `next` param
# (e.g. a bookmarked login page) would land on a 404 instead of the admin.
LOGIN_REDIRECT_URL = "/django-admin/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", cast=int, default=60)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", cast=int, default=7)
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True

ESCALATION_DAYS_THRESHOLD = config("ESCALATION_DAYS_THRESHOLD", cast=int, default=3)

from celery.schedules import crontab  # noqa: E402
CELERY_BEAT_SCHEDULE = {
    'escalate-stale-applications': {
        'task': 'applications.escalate_stale_applications',
        'schedule': crontab(hour=8, minute=0),
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL"),
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")
TRAINING_ADMIN_EMAIL = config("TRAINING_ADMIN_EMAIL", default=DEFAULT_FROM_EMAIL)

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# Needed for the (cookie+CSRF based) Django admin login to work when it's
# reached via a host/port other than what Django infers from the request
# alone — e.g. behind nginx on a LAN IP. Without this, admin form POSTs
# (login included) 403 with "CSRF verification failed".
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8080,http://127.0.0.1:8080",
    cast=Csv(),
)

SPECTACULAR_SETTINGS = {
    "TITLE": "ZESA NTC API",
    "DESCRIPTION": "Training at ZESA National Training Centre — API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "ZNTC Admin",
    "SITE_HEADER": "ZNTC Training Centre",
    "SITE_SYMBOL": "school",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    # Matches the frontend's brand blue (frontend/tailwind.config.ts
    # `primary`: #1B3A6B) instead of Unfold's default purple.
    "COLORS": {
        "primary": {
            "50": "243 246 252",
            "100": "226 235 248",
            "200": "193 211 240",
            "300": "148 179 229",
            "400": "92 139 214",
            "500": "50 106 195",
            "600": "45 89 159",
            "700": "34 71 129",
            "800": "27 57 106",
            "900": "20 44 82",
            "950": "15 33 62",
        },
    },
    "ENVIRONMENT_TITLE_PREFIX": lambda request: "",
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "Training Management",
                "items": [
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:courses_coursecategory_changelist"),
                    },
                    {
                        "title": "Courses",
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:courses_course_changelist"),
                    },
                    {
                        "title": "Schedules / Calendar",
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:courses_courseschedule_changelist"),
                    },
                    {
                        "title": "Enquiries",
                        "icon": "help",
                        "link": reverse_lazy("admin:courses_enquiry_changelist"),
                    },
                ],
            },
            {
                "title": "Admissions",
                "items": [
                    {
                        "title": "Applications",
                        "icon": "assignment",
                        "link": reverse_lazy("admin:applications_application_changelist"),
                    },
                    {
                        "title": "Enrollments",
                        "icon": "how_to_reg",
                        "link": reverse_lazy("admin:enrollments_enrollment_changelist"),
                    },
                    {
                        "title": "Certificates",
                        "icon": "workspace_premium",
                        "link": reverse_lazy("admin:certificates_certificate_changelist"),
                    },
                ],
            },
            {
                "title": "Finance",
                "items": [
                    {
                        "title": "Payments",
                        "icon": "payments",
                        "link": reverse_lazy("admin:payments_payment_changelist"),
                    },
                    {
                        "title": "SAP Sync Log",
                        "icon": "sync",
                        "link": reverse_lazy("admin:payments_sapsynclog_changelist"),
                    },
                ],
            },
            {
                "title": "People & Access",
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "Training Centres",
                        "icon": "apartment",
                        "link": reverse_lazy("admin:centres_centre_changelist"),
                    },
                    {
                        "title": "Notifications",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:workflows_notification_changelist"),
                    },
                ],
            },
        ],
    },
}

MOODLE_BASE_URL = config("MOODLE_BASE_URL", default="")
MOODLE_WSTOKEN = config("MOODLE_WSTOKEN", default="")
PORTAL_BASE_URL = config("PORTAL_BASE_URL", default="http://localhost:3000")
MOODLE_CENTRE_COHORT_IDS = {
    'Harare NTC': 1,
    'Bulawayo Centre': 2,
    'Kariba Centre': 3,
}

PAYNOW_INTEGRATION_ID = config("PAYNOW_INTEGRATION_ID", default="")
PAYNOW_INTEGRATION_KEY = config("PAYNOW_INTEGRATION_KEY", default="")
PAYNOW_RETURN_URL = config("PAYNOW_RETURN_URL", default="")
PAYNOW_RESULT_URL = config("PAYNOW_RESULT_URL", default="")

SAP_BASE_URL = config("SAP_BASE_URL", default="")
SAP_USERNAME = config("SAP_USERNAME", default="")
SAP_PASSWORD = config("SAP_PASSWORD", default="")
SAP_TRAINING_ENTITY = config("SAP_TRAINING_ENTITY", default="ZESATraining")
