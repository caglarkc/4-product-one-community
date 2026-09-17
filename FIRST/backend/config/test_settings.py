import os
os.environ.setdefault('DJANGO_SECRET_KEY', 'isolated-test-only-key-' * 4)
from .settings import *  # noqa: F403
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ALLOWED_HOSTS = ['testserver']
FRONTEND_ORIGIN = 'https://first.test'
