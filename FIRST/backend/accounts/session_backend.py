from django.contrib.sessions.backends.base import SessionBase, CreateError, UpdateError
from . import security


class SessionStore(SessionBase):
    def load(self):
        raw = security.execute('get', security.key('session', self.session_key)) if self.session_key else None
        if raw is None:
            self._session_key = None
            return {}
        return self.decode(raw)

    def exists(self, session_key):
        return bool(security.execute('exists', security.key('session', session_key)))

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        if self.session_key is None:
            return self.create()
        data = self._get_session(no_load=must_create)
        saved = security.execute('set', security.key('session', self.session_key),
                                 self.encode(data), ex=self.get_expiry_age(),
                                 nx=must_create, xx=not must_create)
        if not saved:
            raise CreateError if must_create else UpdateError

    def delete(self, session_key=None):
        session_key = session_key or self.session_key
        if session_key:
            security.execute('delete', security.key('session', session_key))
