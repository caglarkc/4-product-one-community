"""Redis-only ephemeral security state. No database or local-memory fallback."""
import hashlib
import json
import secrets
from functools import lru_cache
from django.conf import settings
import redis


class SecurityUnavailable(Exception):
    pass


@lru_cache
def client():
    return redis.Redis.from_url(settings.AUTH_REDIS_URL, decode_responses=True,
                               socket_connect_timeout=2, socket_timeout=2)


def execute(method, *args, **kwargs):
    try:
        return getattr(client(), method)(*args, **kwargs)
    except redis.RedisError as exc:
        raise SecurityUnavailable from exc


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def key(kind, value):
    return 'first:auth:' + kind + ':' + digest(value)


COUNTER_SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return n
"""


def count(kind, value, ttl=900):
    return int(execute('eval', COUNTER_SCRIPT, 1, key(kind, value), ttl))


def attempts(kind, value):
    return int(execute('get', key(kind, value)) or 0)


def clear(kind, value):
    execute('delete', key(kind, value))


def issue_token(purpose, payload, ttl):
    token = secrets.token_urlsafe(32)
    execute('set', key(purpose, token), json.dumps(payload), ex=ttl)
    return token


def peek_token(purpose, token):
    raw = execute('get', key(purpose, token))
    return json.loads(raw) if raw else None


def consume_token(purpose, token):
    raw = execute('getdel', key(purpose, token))
    return json.loads(raw) if raw else None


RELEASE_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


def acquire_password_lock(email):
    owner = secrets.token_urlsafe(16)
    acquired = execute('set', key('password-lock', email), owner, nx=True, ex=30)
    return owner if acquired else None


def release_password_lock(email, owner):
    execute('eval', RELEASE_SCRIPT, 1, key('password-lock', email), owner)
