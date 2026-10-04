#!/usr/bin/env python3
"""Generate fresh host secrets. Never overwrite an existing environment."""
import argparse
import os
from pathlib import Path
import secrets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / '.env.hosted')
    args = parser.parse_args()
    values = {
        'STEP_SECRET_KEY': secrets.token_urlsafe(64),
        'STEP_FIELD_ENCRYPTION_KEY': secrets.token_hex(32),
        'STEP_DEBUG': '0',
        'STEP_MODE': 'live',
        'STEP_PAYMENT_PROVIDER': 'iyzico_live',
        'STEP_TRUST_PROXY': '1',
        'STEP_ALLOWED_HOSTS': 'step-api.ack-techs.com,127.0.0.1,localhost',
        'STEP_WEB_ORIGINS': 'https://step.ack-techs.com',
        'STEP_WEB_URL': 'https://step.ack-techs.com',
        # Payment callbacks append /api/v1/ themselves; this is the API origin.
        'STEP_API_URL': 'https://step-api.ack-techs.com',
        'STEP_COOKIE_SAMESITE': 'Lax',
        'STEP_DB_NAME': 'step',
        'STEP_DB_USER': 'step',
        'STEP_DB_PASSWORD': secrets.token_urlsafe(48),
        'STEP_DB_HOST': 'db',
        'STEP_DB_PORT': '5432',
        'STEP_PRIVATE_ROOT': '/app/private',
        'STEP_SMTP_HOST': '',
        'STEP_SMTP_PORT': '587',
        'STEP_SMTP_USER': '',
        'STEP_SMTP_PASSWORD': '',
        'STEP_SMTP_FROM': '',
        'STEP_SMTP_TLS': '1',
        'STEP_IYZICO_API_KEY': '',
        'STEP_IYZICO_SECRET_KEY': '',
        'STEP_NETGSM_USER': '',
        'STEP_NETGSM_PASSWORD': '',
        'STEP_NETGSM_HEADER': '',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL prevents accidental secret rotation and an environment symlink overwrite.
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(''.join(f'{key}={value}\n' for key, value in values.items()))
    static = args.output.parent / 'static'
    static.mkdir(mode=0o755, exist_ok=True)
    if os.geteuid() == 0:
        os.chown(static, 1000, 1000)
    print(f'Created {args.output} (0600). External provider credentials remain unset.')


if __name__ == '__main__':
    main()
