"""Load a deployment-provided offline SHA-256 denylist; never transmit passwords."""
from pathlib import Path
import re
from django.core.exceptions import ImproperlyConfigured


def load_corpus(path):
    if not path:
        return frozenset()
    try:
        lines = Path(path).read_text(encoding='ascii').splitlines()
    except (OSError, UnicodeError) as exc:
        raise ImproperlyConfigured('AUTH_BREACHED_PASSWORD_FILE cannot be read.') from exc
    hashes = set()
    for line in lines:
        value = line.strip().lower()
        if not value or value.startswith('#'):
            continue
        if not re.fullmatch('[0-9a-f]{64}', value):
            raise ImproperlyConfigured('AUTH_BREACHED_PASSWORD_FILE must contain one SHA-256 hash per line.')
        hashes.add(value)
    if not hashes:
        raise ImproperlyConfigured('AUTH_BREACHED_PASSWORD_FILE must not be empty.')
    return frozenset(hashes)
