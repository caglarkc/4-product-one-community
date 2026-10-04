import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('STEP_SECRET_KEY', '')
if not SECRET_KEY:
    raise RuntimeError('STEP_SECRET_KEY must be supplied; no development secret is generated in source.')
DEBUG = os.environ.get('STEP_DEBUG') == '1'
STEP_MODE = os.environ.get('STEP_MODE', 'test')
if STEP_MODE not in {'test', 'live'}:
    raise RuntimeError('STEP_MODE must be test or live')
if STEP_MODE == 'live' and DEBUG:
    raise RuntimeError('Live mode must disable DEBUG')
PAYMENT_PROVIDER = os.environ.get('STEP_PAYMENT_PROVIDER', 'iyzico_sandbox')
if PAYMENT_PROVIDER == 'simulator' and (STEP_MODE != 'test' or not DEBUG):
    raise RuntimeError('Simulator requires explicit local DEBUG test mode')
ALLOWED_HOSTS = os.environ.get('STEP_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'corsheaders', 'rest_framework', 'core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'corsheaders.middleware.CorsMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ.get('STEP_DB_NAME', 'step'), 'USER': os.environ.get('STEP_DB_USER', 'step'), 'PASSWORD': os.environ.get('STEP_DB_PASSWORD', ''), 'HOST': os.environ.get('STEP_DB_HOST', 'db'), 'PORT': os.environ.get('STEP_DB_PORT', '5432')}}
DATABASES['default'].update(CONN_MAX_AGE=60, CONN_HEALTH_CHECKS=True)
AUTH_USER_MODEL = 'core.User'
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
PRIVATE_ROOT = Path(os.environ.get('STEP_PRIVATE_ROOT', str(BASE_DIR / 'private')))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_NAME = 'step_session'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = os.environ.get('STEP_COOKIE_SAMESITE', 'Lax')
if SESSION_COOKIE_SAMESITE == 'None' and not SESSION_COOKIE_SECURE:
    raise RuntimeError('Cross-site cookies require HTTPS Secure')
CSRF_COOKIE_NAME = 'step_csrf'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
CSRF_TRUSTED_ORIGINS = list(filter(None, os.environ.get('STEP_WEB_ORIGINS', '').split(',')))
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['accept','authorization','content-type','x-csrftoken','idempotency-key']
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# Only enable behind a proxy that overwrites this header and a loopback-only API.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if os.environ.get('STEP_TRUST_PROXY') == '1' else None
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_REFERRER_POLICY = 'same-origin'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('STEP_SMTP_HOST', '')
EMAIL_PORT = int(os.environ.get('STEP_SMTP_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('STEP_SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('STEP_SMTP_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('STEP_SMTP_TLS', '1') == '1'
DEFAULT_FROM_EMAIL = os.environ.get('STEP_SMTP_FROM', '')
WEB_URL = os.environ.get('STEP_WEB_URL', '')
DEVICE_TOKEN_SECONDS = int(os.environ.get('STEP_DEVICE_TOKEN_SECONDS', '2592000'))
UPLOAD_MAX_BYTES = int(os.environ.get('STEP_UPLOAD_MAX_BYTES', '20971520'))
DATA_UPLOAD_MAX_MEMORY_SIZE = UPLOAD_MAX_BYTES + 1048576
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['core.security.DeviceAuthentication', 'rest_framework.authentication.SessionAuthentication'], 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'], 'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'], 'EXCEPTION_HANDLER': 'core.security.exception_handler'}
