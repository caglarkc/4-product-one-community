from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_safe


@require_safe
def health(request):
    """Process health only, not a database or auth readiness check."""
    return JsonResponse({"status": "ok"})


urlpatterns = [path("health/", health), path("api/auth/", include("accounts.urls"))]
