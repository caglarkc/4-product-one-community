from rest_framework.authentication import BaseAuthentication


class DjangoSessionAuthentication(BaseAuthentication):
    """Preserve middleware authentication; AuthView explicitly applies CSRF."""
    def authenticate(self, request):
        user = request._request.user
        if user.is_authenticated and user.is_active:
            return user, None
        return None

    def authenticate_header(self, request):
        return 'Bearer'
