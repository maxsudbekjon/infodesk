from pathlib import Path
from environs import Env

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
    "jazzmin",
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
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
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
# JAZZMIN — Production Admin Panel Configuration
# =============================================================================

JAZZMIN_SETTINGS = {
    # ── Branding ──────────────────────────────────────────────────────────────
    "site_title": "Admin panel",
    "site_header": "Boshqaruv paneli",
    "site_brand": "Infodesk",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Infodesk Boshqaruv Paneliga Xush Kelibsiz",
    "copyright": "Infodesk © 2025",

    # ── Global Search ─────────────────────────────────────────────────────────
    # Models that appear in the top search bar
    "search_model": [
        "user.User",
        "pupil.Student",
        "lead.Lead",
        "teacher.Teacher",
    ],

    # Field on user model for avatar (None = use default gravatar)
    "user_avatar": None,

    # ── Top Menu ──────────────────────────────────────────────────────────────
    "topmenu_links": [
        {
            "name": "Bosh sahifa",
            "url": "admin:index",
            "permissions": ["auth.view_user"],
            "icon": "fas fa-home",
        },
        {
            "name": "API hujjatlari",
            "url": "/api/docs/",
            "new_window": True,
            "icon": "fas fa-book",
        },
        {"app": "lead"},
        {"app": "pupil"},
        {"app": "group"},
    ],

    # ── User Dropdown Menu ────────────────────────────────────────────────────
    "usermenu_links": [
        {
            "name": "API hujjatlari",
            "url": "/api/docs/",
            "new_window": True,
            "icon": "fas fa-book-open",
        },
        {"model": "user.user"},
    ],

    # ── Sidebar ───────────────────────────────────────────────────────────────
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # App ordering in sidebar
    "order_with_respect_to": [
        "settings",
        "user",
        "teacher",
        "lead",
        "pupil",
        "group",
        "market",
        "django_celery_beat",
        "auth",
    ],

    # Custom quick links per app section
    "custom_links": {
        "pupil": [
            {
                "name": "O'quvchilar ro'yxati",
                "url": "admin:pupil_student_changelist",
                "icon": "fas fa-list-ul",
                "permissions": ["pupil.view_student"],
            },
        ],
        "lead": [
            {
                "name": "Lidlar ro'yxati",
                "url": "admin:lead_lead_changelist",
                "icon": "fas fa-list-ul",
                "permissions": ["lead.view_lead"],
            },
        ],
        "group": [
            {
                "name": "Guruhlar ro'yxati",
                "url": "admin:group_group_changelist",
                "icon": "fas fa-list-ul",
                "permissions": ["group.view_group"],
            },
        ],
    },

    # ── Icons (FontAwesome 5 Free) ────────────────────────────────────────────
    "icons": {
        # Built-in Django auth
        "auth":                              "fas fa-users-cog",
        "auth.user":                         "fas fa-user-shield",
        "auth.group":                        "fas fa-users",

        # django-celery-beat
        # "django_celery_beat":                "fas fa-clock",
        # "django_celery_beat.periodictask":   "fas fa-tasks",
        # "django_celery_beat.crontabschedule":"fas fa-calendar-alt",
        # "django_celery_beat.intervalschedule":"fas fa-stopwatch",
        # "django_celery_beat.solarschedule":  "fas fa-sun",
        # "django_celery_beat.clockedschedule":"fas fa-bell",

        # user app
        "user":                              "fas fa-user-circle",
        "user.user":                         "fas fa-user",
        "user.operator":                     "fas fa-headset",

        # settings app  (app label: "settings")
        # "settings":                          "fas fa-cogs",
        # "settings.organization":             "fas fa-building",
        # "settings.branch":                   "fas fa-code-branch",
        # "settings.receiptsettings":          "fas fa-receipt",
        # "settings.paymentmethod":            "fas fa-credit-card",
        # "settings.weekend":                  "fas fa-calendar-times",

        # teacher app
        "teacher":                           "fas fa-chalkboard-teacher",
        "teacher.teacher":                   "fas fa-chalkboard-teacher",
        "teacher.specialty":                 "fas fa-graduation-cap",

        # lead app
        # "lead":                              "fas fa-filter",
        # "lead.lead":                         "fas fa-funnel-dollar",
        # "lead.note":                         "fas fa-comment-alt",
        # "lead.situation":                    "fas fa-sitemap",
        # "lead.source":                       "fas fa-broadcast-tower",

        # pupil app
        "pupil":                             "fas fa-user-graduate",
        "pupil.student":                     "fas fa-user-graduate",
        "pupil.parent":                      "fas fa-users",
        "pupil.studentnote":                 "fas fa-sticky-note",
        "pupil.studnettransfer":             "fas fa-exchange-alt",

        # group app
        "group":                             "fas fa-layer-group",
        # "group.group":                       "fas fa-layer-group",
        # "group.coursetemplate":              "fas fa-book",
        # "group.day":                         "fas fa-calendar-day",
        # "group.room":                        "fas fa-door-open",
        # "group.attendance":                  "fas fa-clipboard-check",
        # "group.grade":                       "fas fa-star",
        # "group.groupscore":                  "fas fa-coins",
        # "group.groupnote":                   "fas fa-clipboard",
        # "group.groupdiscount":               "fas fa-tags",
        # "group.groupfreeze":                 "fas fa-snowflake",
        # "group.grouphistory":                "fas fa-history",
        # "group.grouprankingcomment":         "fas fa-medal",
        # "group.exam":                        "fas fa-file-alt",

        # market app
        "market":                            "fas fa-store",
        "market.product":                    "fas fa-box",
        "market.marketorder":                "fas fa-shopping-cart",
    },

    # Fallback icons for apps/models without explicit icon
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # ── UX Options ────────────────────────────────────────────────────────────
    # Open related object in a modal instead of a new page
    "related_modal_active": True,

    # Custom static assets
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,

    # Disable the UI builder in production (prevents accidental style changes)
    "show_ui_builder": True,

    # ── Change Form Layout ────────────────────────────────────────────────────
    # Options: single | horizontal_tabs | vertical_tabs | collapsible | carousel
    "changeform_format": "horizontal_tabs",
    "changeform_format_override": {
        "user.user":      "collapsible",
        "pupil.student":  "collapsible",
        "teacher.teacher":"collapsible",
        "group.group":    "collapsible",
        "lead.lead":      "collapsible",
    },

    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    # Matn o'lchami
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    # Rang sxemasi — oq/yengil interfeys
    "brand_colour": "navbar-white",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,

    # Joylashuv
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,

    # Yon panel — yorqin va oddiy
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,

    # Mavzu — eng sodda va toza ko'rinish
    "theme": "default",
    "dark_mode_theme": None,

    # Tugma stillari — oddiy to'liq tugmalar
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },

    # Amallar paneli doim ko'rinib tursin
    "actions_sticky_top": True,
}
