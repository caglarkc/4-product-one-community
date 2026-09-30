from django.contrib import admin
from django.urls import path
from core.api import Endpoint
urlpatterns = [path('admin/', admin.site.urls), path('api/v1/<path:route>', Endpoint.as_view())]
