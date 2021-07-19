import sys

DEBUG = True
TESTING = "pytest" in sys.modules

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "github_actions",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "autocommit": True,
    }
}

SECRET_KEY = "django-insecure-bwr8c@lu$d*l)7538h$43jj78r0r8+^#tufa496-xykap@5)o9"
