import os
from loguru import logger as log
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

logpath = os.path.join(BASE_DIR, "logs.log")

log.add(
    logpath,
    enqueue=True,
    level="DEBUG",
    retention="1 week",
)


load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    default="django-insecure-@ur(_!x(@5ps_lvfpe&myyzg=q3+x3-7hio(s2m=!p)uzw8#oj",
)
APP_URL = os.getenv("APP_URL")
BASE_REDIRECT_URL = APP_URL.replace("https://", "")

true_vals = ["1", "true", "yes", "y"]

# App envs

LOGIN_USERNAME = os.getenv("LOGIN_USERNAME")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_POSTING_ACTIVE = os.getenv("LINKEDIN_POSTING_ACTIVE").lower() in true_vals
LINKEDIN_REDIRECT_URI = APP_URL + "/linkedin/callback/"

X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
X_POSTING_ACTIVE = os.getenv("X_POSTING_ACTIVE").lower() in true_vals
X_REDIRECT_URI = APP_URL + "/X/callback/"

THREADS_CLIENT_ID = os.getenv("THREADS_CLIENT_ID")
THREADS_CLIENT_SECRET = os.getenv("THREADS_CLIENT_SECRET")
THREADS_POSTING_ACTIVE = os.getenv("THREADS_POSTING_ACTIVE").lower() in true_vals
THREADS_REDIRECT_URI = APP_URL + "/threads/callback/"
THREADS_UNINSTALL_URI = APP_URL + "/threads/uninstall/"

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")
FACEBOOK_POSTING_ACTIVE = os.getenv("FACEBOOK_POSTING_ACTIVE").lower() in true_vals
FACEBOOK_REDIRECT_URI = APP_URL + "/facebook/callback/"
FACEBOOK_UNINSTALL_URI = APP_URL + "/facebook/uninstall/"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", BASE_REDIRECT_URL]

CSRF_TRUSTED_ORIGINS = [APP_URL]


# INTERNAL_IPS = []


# Application definition

INSTALLED_APPS = [
    "socialsched",
    "integrations",
    "django_browser_reload",
    "django_cleanup.apps.CleanupConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = "core.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


LOGIN_URL = "/login/"


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("TIME_ZONE", default="UTC")

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_USE_FINDERS = True

os.makedirs(STATIC_ROOT, exist_ok=True)


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Database

DB_DIR = BASE_DIR / "data"
os.makedirs(DB_DIR, exist_ok=True)


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_DIR / "db.sqlite",
    },
    "OPTIONS": {
        "timeout": 20,
        "transaction_mode": "IMMEDIATE",
        "init_command": "PRAGMA synchronous=3; PRAGMA cache_size=2000;",
    },
}


CACHE_DIR = BASE_DIR / "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": CACHE_DIR,
    }
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
