from django.urls import path
from . import views

urlpatterns = [
    path('projects/<uuid:project_id>/files/', views.FilesView.as_view()),
    path('projects/<uuid:project_id>/files/<uuid:file_id>/', views.FileView.as_view()),
    path('projects/<uuid:project_id>/files/<uuid:file_id>/preview/', views.PreviewView.as_view()),
    path('projects/<uuid:project_id>/browse/', views.BrowseView.as_view()),
    path('projects/<uuid:project_id>/prepare/', views.PrepareView.as_view()),
    path('projects/<uuid:project_id>/prepare/<uuid:preview_id>/', views.PreparedView.as_view()),
    path('projects/<uuid:project_id>/publish/', views.PublishView.as_view()),
]
