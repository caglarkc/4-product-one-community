from django.contrib import admin
from django.urls import path
from core.api import Endpoint
from .health import health
urlpatterns = [path('health/', health), path('admin/', admin.site.urls), path('api/v1/<path:route>', Endpoint.as_view())]
