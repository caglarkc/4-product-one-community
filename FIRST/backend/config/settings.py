"""Production settings: PostgreSQL persistence and Redis-only security state."""
import os
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must contain at least 50 characters.")
DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",") if host.strip()]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "rest_framework", "accounts", "projects", "teams", "showcase", "tasks", "allauth", "allauth.account", "allauth.socialaccount", "allauth.socialaccount.providers.google"]
MIDDLEWARE = [
    "accounts.cors.CorsMiddleware",
    "accounts.middleware.AuthBoundaryMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "accounts.proxy.TrustedClientIPMiddleware",
    "accounts.middleware.RedisSessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "accounts.middleware.RegistryMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "first"), "USER": os.environ.get("POSTGRES_USER", "first"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""), "HOST": os.environ.get("POSTGRES_HOST", "db"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432")}}
AUTH_USER_MODEL = "accounts.User"
SESSION_ENGINE = "accounts.session_backend"
AUTH_REDIS_URL = os.environ.get("AUTH_REDIS_URL", "redis://redis:6379/0")
AUTH_IP_ATTEMPTS = int(os.environ.get("AUTH_IP_ATTEMPTS", "30"))
AUTH_ACCOUNT_ATTEMPTS = int(os.environ.get("AUTH_ACCOUNT_ATTEMPTS", "5"))
SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_FAILURE_VIEW = "accounts.views.csrf_failure"
CSRF_TRUSTED_ORIGINS = [v for v in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if v]
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "https://first.example.invalid").rstrip("/")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("SMTP_HOST", "")
EMAIL_PORT = int(os.environ.get("SMTP_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("SMTP_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.environ.get("SMTP_SSL", "false").lower() == "true"
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get("SMTP_FROM", "noreply@example.invalid")
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "accounts.views.errors",
}
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "tr"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Optional curated production corpus: invalid explicit configuration fails startup.
from accounts.password_corpus import load_corpus
AUTH_BREACHED_PASSWORD_HASHES = load_corpus(os.environ.get('AUTH_BREACHED_PASSWORD_FILE', ''))

# HTTPS IP endpoint is supported: authentication is an explicit opaque Bearer
# session, independent of cross-site/third-party cookies.
API_ORIGIN = os.environ.get('API_ORIGIN', 'https://167.235.158.118').rstrip('/')
TRUST_NGINX_PROXY = os.environ.get('TRUST_NGINX_PROXY', 'false').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if TRUST_NGINX_PROXY else None
CORS_ALLOWED_ORIGINS = [value.strip() for value in os.environ.get('CORS_ALLOWED_ORIGINS', FRONTEND_ORIGIN).split(',') if value.strip()]

def valid_origin(value, local=False):
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Reject malformed/non-numeric ports at startup.
    except ValueError:
        return False
    scheme_allowed = parsed.scheme == 'https' or (
        local and parsed.scheme == 'http' and parsed.netloc in ('127.0.0.1:3101', 'localhost:3101'))
    return (scheme_allowed and bool(parsed.hostname) and (port is None or port > 0)
            and not parsed.username and not parsed.password and not parsed.path
            and not parsed.query and not parsed.fragment
            and not any(character.isspace() or character in '*\\%' for character in value))

if not valid_origin(API_ORIGIN) or not valid_origin(FRONTEND_ORIGIN):
    raise ImproperlyConfigured('API_ORIGIN and FRONTEND_ORIGIN must be exact HTTPS origins.')
if not CORS_ALLOWED_ORIGINS or any(not valid_origin(origin, local=True) for origin in CORS_ALLOWED_ORIGINS):
    raise ImproperlyConfigured('CORS_ALLOWED_ORIGINS must contain exact HTTPS origins or explicit loopback development origins.')
if FRONTEND_ORIGIN not in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured('CORS_ALLOWED_ORIGINS must include FRONTEND_ORIGIN.')
# Every browser allowed to read a token must also be allowed to submit CSRF proof.
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS + CORS_ALLOWED_ORIGINS))
if any(not valid_origin(origin, local=True) for origin in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured('CSRF_TRUSTED_ORIGINS must contain exact approved origins.')

# Only the custom JSON endpoints are mounted; no allauth account/linking views.
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_REQUESTS_TIMEOUT = 10
GOOGLE_ENABLED = os.environ.get("GOOGLE_ENABLED", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
# Explicit opt-in for this development origin only; never accept an arbitrary
# redirect supplied by the browser or derive one from forwarded host headers.
GOOGLE_LOCAL_REDIRECT_URI = os.environ.get("GOOGLE_LOCAL_REDIRECT_URI", "")
if GOOGLE_LOCAL_REDIRECT_URI not in ("", "http://127.0.0.1:3101/accounts/google/login/callback/"):
    raise ImproperlyConfigured("GOOGLE_LOCAL_REDIRECT_URI must be the approved local callback URL.")

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "")
GITHUB_ENABLED = os.environ.get("GITHUB_ENABLED", "false").lower() == "true"

# Separate selected-repository GitHub App; login OAuth scopes remain unchanged.
GITHUB_APP_ENABLED = os.environ.get("GITHUB_APP_ENABLED", "false").lower() == "true"
GITHUB_APP_ID = os.environ.get("GITHUB_APP_ID", "")
GITHUB_APP_SLUG = os.environ.get("GITHUB_APP_SLUG", "")
GITHUB_APP_CLIENT_ID = os.environ.get("GITHUB_APP_CLIENT_ID", "")
GITHUB_APP_CLIENT_SECRET = os.environ.get("GITHUB_APP_CLIENT_SECRET", "")
GITHUB_APP_REDIRECT_URI = os.environ.get("GITHUB_APP_REDIRECT_URI", "")
GITHUB_APP_TOKEN_KEY = os.environ.get("GITHUB_APP_TOKEN_KEY", "")
