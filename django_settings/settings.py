import os
import socket
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


HOST_NAMES = ["RogStrix", "MacBook-Pro.local", "MacbookPro"]
DEBUG = socket.gethostname() in HOST_NAMES
DEBUG = socket.gethostname() in HOST_NAMES


SECRET_KEY = os.getenv("SECRET_KEY")
MAIN_IP = os.getenv("MAIN_IP")
DB_TYPE = os.getenv("DB_TYPE", "sqlite3").lower()


EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip_address = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting local IP: {e}")
        ip_address = "127.0.0.1"
    return ip_address


LOCAL_IP = get_local_ip()


# Function to get the external IP address
def get_external_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            external_ip = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting external IP: {e}")
        external_ip = "127.0.0.1"
    return external_ip


EXTERNAL_IP = get_external_ip()

# Allowed hosts and CSRF trusted origins
ALLOWED_HOSTS = ["*"] + (
    [LOCAL_IP, EXTERNAL_IP] if DEBUG else ["control.krmu.edu.kz", "dot.medkrmu.edu.kz"]
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_app.middleware.ClickLoggingMiddleware",
]

ROOT_URLCONF = "django_settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_app.context_processors.current_year",
            ],
        },
    },
]

WSGI_APPLICATION = "django_settings.wsgi.application"


DATABASES = {"default": {}}


if DEBUG:
    # If debug using SQLite3
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
else:
    # If production using MySQL or PostgreSQL
    if DB_TYPE == "mysql":
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "3306"),
        }
    elif DB_TYPE == "postgresql":
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

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

LANGUAGE_CODE = "en-en"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = Path(BASE_DIR / "staticroot")

STATICFILES_DIRS = [
    Path(BASE_DIR, "static"),
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"  
MEDIA_ROOT = BASE_DIR / "media"  


# Logging configurations
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


# Custom function to generate log filenames
def get_log_filename(log_name):
    return LOG_DIR / f'{log_name}_{datetime.now().strftime("%Y-%m-%d_%H")}.log'


# Function to remove old logs
def clean_old_logs(log_directory, days_to_keep=7):
    now = datetime.now()
    for filename in os.listdir(log_directory):
        if filename.endswith(".log"):
            file_path = log_directory / filename
            file_modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if (now - file_modified_time).days > days_to_keep:
                file_path.unlink()


# Clean old logs
clean_old_logs(LOG_DIR, days_to_keep=7)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{levelname} {asctime} {name} {module} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO" if DEBUG else "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": get_log_filename("log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 24,  # Keep logs for 24 hours
            "encoding": "utf-8",
            "formatter": "standard",
            "delay": True,
        },
    },
    "loggers": {
        "": {
            "handlers": ["file"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": True,
        },
        "django": {
            "handlers": ["file"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": True,
        },
    },
}
