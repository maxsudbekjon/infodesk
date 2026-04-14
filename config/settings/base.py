from pathlib import Path
from environs import Env

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"

env = Env()
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env.str("SECRET_KEY", "django-insecure-change-me")

DEBUG = env.bool("DEBUG", False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", [])

print("ALLOWED_HOSTS", ALLOWED_HOSTS)

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", [])
CORS_ALLOWED_ORIGIN_REGEXES = env.list("CORS_ALLOWED_ORIGIN_REGEXES", [])
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", True)
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", False)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", [])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", True)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", True)
SECURE_BROWSER_XSS_FILTER = env.bool("SECURE_BROWSER_XSS_FILTER", True)
X_FRAME_OPTIONS = env.str("X_FRAME_OPTIONS", "DENY")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_celery_beat",

    "apps.teacher",
    "apps.pupil",
    "apps.lead",
    "apps.group",
    "apps.market",
    "apps.dashboard",
    "apps.user",
    "apps.settings",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DBS = {
    "SQLITE": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "POSTGRES": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST", default="localhost"),
        "PORT": env.int("DB_PORT", default=5432),
    },
}

DATABASES = {
    "default": DBS.get(env.str("DB_TYPE", "SQLITE")),
}

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]

LANGUAGE_CODE = "uz"

LANGUAGES = [
    ("uz", _("Uzbek")),
]

TIME_ZONE = "Asia/Tashkent"
USE_TZ = True

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [STATIC_DIR] if STATIC_DIR.exists() else []
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "user.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Infodesk API",
    "DESCRIPTION": "API documentation",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "PREPROCESSING_HOOKS": [
        "config.schema.filter_schema_endpoints",
    ],
}

CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CELERY_BEAT_SCHEDULE = {
    "daily-lead-job": {
        "task": "apps.lead.tasks.daily_lead_job",
        "schedule": crontab(hour=14, minute=36),
    },
    "penalize-stale-leads": {
        "task": "apps.lead.tasks.penalize_operators_for_stale_leads",
        "schedule": crontab(hour=9, minute=0),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "ON_LOGIN_SUCCESS": "rest_framework_simplejwt.serializers.default_on_login_success",
    "ON_LOGIN_FAILED": "rest_framework_simplejwt.serializers.default_on_login_failed",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",

    "CHECK_REVOKE_TOKEN": False,
    "REVOKE_TOKEN_CLAIM": "hash_password",
    "CHECK_USER_IS_ACTIVE": True,
}

# =============================================================================
# UNFOLD — Admin Panel Configuration
# =============================================================================

UNFOLD = {
    # ── Branding ──────────────────────────────────────────────────────────────
    "SITE_TITLE": "Infodesk",
    "SITE_HEADER": "Boshqaruv Paneli",
    "SITE_URL": "/",
    "SITE_SYMBOL": "school",  # Material Symbols icon
    "SHOW_HISTORY": True,
    "SHOW_BACK_BUTTON": True,
    "SHOW_VIEW_ON_SITE": True,

    # ── Dashboard ─────────────────────────────────────────────────────────────
    "DASHBOARD_CALLBACK": "apps.dashboard.admin_ui.dashboard_callback",

    # ── Custom assets ─────────────────────────────────────────────────────────
    "STYLES": [
        lambda request: static("admin/css/custom_admin.css"),
    ],
    "SCRIPTS": [
        lambda request: static("admin/js/custom_admin.js"),
    ],

    # ── Colors (blue theme) ───────────────────────────────────────────────────
    "COLORS": {
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",
            "default-light": "17 24 39",
            "default-dark": "243 244 246",
            "important-light": "17 24 39",
            "important-dark": "249 250 251",
        },
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },

    # ── Sidebar Navigation ────────────────────────────────────────────────────
    "SIDEBAR": {
        "show_search": True,
        "show_all_links": False,
        "navigation": [
            {
                "title": _("Asosiy"),
                "items": [
                    {
                        "title": _("Bosh sahifa"),
                        "icon": "home",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Statistika"),
                        "icon": "bar_chart",
                        "link": reverse_lazy("admin:ui_statistics"),
                    },
                    {
                        "title": _("Jadval"),
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:ui_schedule"),
                    },
                ],
            },
            {
                "title": _("O'quv jarayoni"),
                "separator": True,
                "items": [
                    {
                        "title": _("Guruhlar"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:group_group_changelist"),
                        "permission": lambda request: request.user.has_perm("group.view_group"),
                    },
                    {
                        "title": _("Fanlar"),
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:group_coursetemplate_changelist"),
                        "permission": lambda request: request.user.has_perm("group.view_coursetemplate"),
                    },
                    {
                        "title": _("O'quvchilar"),
                        "icon": "school",
                        "link": reverse_lazy("admin:pupil_student_changelist"),
                        "permission": lambda request: request.user.has_perm("pupil.view_student"),
                    },
                    {
                        "title": _("O'qituvchilar"),
                        "icon": "person_raised_hand",
                        "link": reverse_lazy("admin:teacher_teacher_changelist"),
                        "permission": lambda request: request.user.has_perm("teacher.view_teacher"),
                    },
                    {
                        "title": _("Davomat"),
                        "icon": "fact_check",
                        "link": reverse_lazy("admin:group_attendance_changelist"),
                        "permission": lambda request: request.user.has_perm("group.view_attendance"),
                    },
                    {
                        "title": _("Baholar"),
                        "icon": "grade",
                        "link": reverse_lazy("admin:group_grade_changelist"),
                        "permission": lambda request: request.user.has_perm("group.view_grade"),
                    },
                    {
                        "title": _("Coin tarixi"),
                        "icon": "token",
                        "link": reverse_lazy("admin:group_groupscore_changelist"),
                        "permission": lambda request: request.user.has_perm("group.view_groupscore"),
                    },
                    {
                        "title": _("Xonalar"),
                        "icon": "meeting_room",
                        "link": reverse_lazy("admin:group_room_changelist"),
                        "permission": lambda request: request.user.has_perm("group.view_room"),
                    },
                ],
            },
            {
                "title": _("Sotish va buyurtmalar"),
                "separator": True,
                "items": [
                    {
                        "title": _("Buyurtmalar (Lead)"),
                        "icon": "filter_alt",
                        "link": reverse_lazy("admin:lead_lead_changelist"),
                        "permission": lambda request: request.user.has_perm("lead.view_lead"),
                    },
                    {
                        "title": _("Manbalar"),
                        "icon": "sensors",
                        "link": reverse_lazy("admin:lead_source_changelist"),
                        "permission": lambda request: request.user.has_perm("lead.view_source"),
                    },
                    {
                        "title": _("Vaziyatlar"),
                        "icon": "layers",
                        "link": reverse_lazy("admin:lead_situation_changelist"),
                        "permission": lambda request: request.user.has_perm("lead.view_situation"),
                    },
                ],
            },
            {
                "title": _("Market"),
                "separator": True,
                "items": [
                    {
                        "title": _("Mahsulotlar"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:market_product_changelist"),
                        "permission": lambda request: request.user.has_perm("market.view_product"),
                    },
                    {
                        "title": _("Market buyurtmalari"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:market_marketorder_changelist"),
                        "permission": lambda request: request.user.has_perm("market.view_marketorder"),
                    },
                ],
            },
            {
                "title": _("Sozlamalar"),
                "separator": True,
                "items": [
                    {
                        "title": _("Tashkilotlar"),
                        "icon": "business",
                        "link": reverse_lazy("admin:settings_organization_changelist"),
                        "permission": lambda request: request.user.has_perm("settings.view_organization"),
                    },
                    {
                        "title": _("Filiallar"),
                        "icon": "location_on",
                        "link": reverse_lazy("admin:settings_branch_changelist"),
                        "permission": lambda request: request.user.has_perm("settings.view_branch"),
                    },
                    {
                        "title": _("To'lov usullari"),
                        "icon": "credit_card",
                        "link": reverse_lazy("admin:settings_paymentmethod_changelist"),
                        "permission": lambda request: request.user.has_perm("settings.view_paymentmethod"),
                    },
                    {
                        "title": _("Dam olish kunlari"),
                        "icon": "event_busy",
                        "link": reverse_lazy("admin:settings_weekend_changelist"),
                        "permission": lambda request: request.user.has_perm("settings.view_weekend"),
                    },
                    {
                        "title": _("Chek sozlamalari"),
                        "icon": "receipt",
                        "link": reverse_lazy("admin:settings_receiptsettings_changelist"),
                        "permission": lambda request: request.user.has_perm("settings.view_receiptsettings"),
                    },
                ],
            },
            {
                "title": _("Foydalanuvchilar"),
                "separator": True,
                "items": [
                    {
                        "title": _("Foydalanuvchilar"),
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:user_user_changelist"),
                        "permission": lambda request: request.user.has_perm("user.view_user"),
                    },
                    {
                        "title": _("Operatorlar"),
                        "icon": "support_agent",
                        "link": reverse_lazy("admin:user_operator_changelist"),
                        "permission": lambda request: request.user.has_perm("user.view_operator"),
                    },
                    {
                        "title": _("Yo'nalishlar"),
                        "icon": "category",
                        "link": reverse_lazy("admin:teacher_specialty_changelist"),
                        "permission": lambda request: request.user.has_perm("teacher.view_specialty"),
                    },
                    {
                        "title": _("Ruxsat guruhlari"),
                        "icon": "shield",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.has_perm("auth.view_group"),
                    },
                ],
            },
        ],
    },
}
