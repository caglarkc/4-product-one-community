"""Merge supplied settings into server-only config; preserve persistent credentials."""
import json
import os
from pathlib import Path
import secrets
import sys

path = Path(sys.argv[1])
if str(path) != '/opt/first/backend/shared/.env':
    raise SystemExit('Unexpected configuration path')
incoming = json.load(sys.stdin)
allowed = {'AUTH_PROXY_SECRET', 'FRONTEND_ORIGIN', 'CSRF_TRUSTED_ORIGINS', 'DJANGO_ALLOWED_HOSTS',
           'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_FROM', 'SMTP_TLS', 'SMTP_SSL', 'GOOGLE_ENABLED', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI', 'GOOGLE_LOCAL_REDIRECT_URI',
           'GITHUB_ENABLED', 'GITHUB_CLIENT_ID', 'GITHUB_CLIENT_SECRET', 'GITHUB_REDIRECT_URI',
           'GITHUB_APP_ENABLED', 'GITHUB_APP_ID', 'GITHUB_APP_SLUG', 'GITHUB_APP_CLIENT_ID',
           'GITHUB_APP_CLIENT_SECRET', 'GITHUB_APP_REDIRECT_URI', 'GITHUB_APP_TOKEN_KEY'}
if set(incoming) - allowed or any(not isinstance(v, str) or '\n' in v or '\r' in v for v in incoming.values()):
    raise SystemExit('Invalid configuration payload')
settings = {}
if path.exists():
    for line in path.read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep:
            # We write dotenv values as single-quoted literals, escaping apostrophes.
            settings[key] = value[1:-1].replace("\\'", "'") if value.startswith("'") and value.endswith("'") else value
defaults = {'DJANGO_SECRET_KEY': secrets.token_hex(48), 'POSTGRES_DB': 'first', 'POSTGRES_USER': 'first',
            'POSTGRES_PASSWORD': secrets.token_hex(32), 'REDIS_PASSWORD': secrets.token_hex(32),
            'POSTGRES_HOST': 'db', 'POSTGRES_PORT': '5432', 'SMTP_PORT': '587', 'SMTP_TLS': 'true',
            'SMTP_SSL': 'false', 'FIRST_BACKEND_PORT': '18081'}
for key, value in defaults.items():
    settings.setdefault(key, value)
settings.update(incoming)
settings['AUTH_REDIS_URL'] = 'redis://:' + settings['REDIS_PASSWORD'] + '@redis:6379/0'
if not settings.get('AUTH_PROXY_SECRET') or len(settings['AUTH_PROXY_SECRET']) < 32:
    raise SystemExit('A strong proxy secret is required')
if any(value.endswith('\\') for value in settings.values()):
    raise SystemExit('Configuration values ending in a backslash are not supported')
path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
if path.exists():
    backup = path.with_name('.env.previous')
    backup.write_bytes(path.read_bytes()); backup.chmod(0o600)
text = ''.join(key + "='" + value.replace("'", "\\'") + "'\n" for key, value in sorted(settings.items()))
temp = path.with_name('.env.tmp')
fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.write(text)
os.replace(temp, path)
print('FIRST server configuration saved (values hidden).')
if not all(settings.get(k) for k in ['SMTP_HOST', 'SMTP_FROM']):
    print('WARNING: SMTP is not configured; email-dependent auth will return a service error.')
