import sys

DEBUG = True
TESTING = "pytest" in sys.modules

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "github_actions",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "",  # Set to empty string for localhost
        "PORT": "",  # Set to empty string for default
        "autocommit": True,
    }
}
