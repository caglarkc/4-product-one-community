"""Test double only; does not verify Redis atomicity, TTL scheduling or outages."""
import time


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expiry = {}

    def get(self, key):
        if self.expiry.get(key, float('inf')) <= time.time():
            self.delete(key)
        return self.values.get(key)

    def set(self, key, value, ex=None, nx=False, xx=False):
        exists = self.get(key) is not None
        if (nx and exists) or (xx and not exists):
            return None
        self.values[key] = str(value)
        self.expiry[key] = time.time() + ex if ex else float('inf')
        return True

    def exists(self, key):
        return self.get(key) is not None

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.expiry.pop(key, None)

    def getdel(self, key):
        value = self.get(key)
        self.delete(key)
        return value

    def eval(self, script, n, key, ttl):
        if 'mail-admission' in script:
            if self.exists(key) or int(self.get(ttl) or 0) >= 5:
                return 0
            self.set(key, '1', ex=60)
            count = int(self.get(ttl) or 0) + 1
            if count == 1:
                self.set(ttl, count, ex=3600)
            else:
                self.values[ttl] = str(count)
            return 1
        if "redis.call('DEL'" in script:
            if self.get(key) == ttl:
                self.delete(key)
                return 1
            return 0
        value = int(self.get(key) or 0) + 1
        if value == 1:
            self.set(key, value, ex=int(ttl))
        else:
            self.values[key] = str(value)
        return value
