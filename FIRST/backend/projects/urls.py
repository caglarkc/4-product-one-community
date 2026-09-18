from django.urls import path
from . import views

urlpatterns = [
    path('', views.CreateView.as_view()),
    path('config/', views.ConfigView.as_view()),
    path('mine/', views.MineView.as_view()),
    path('github/status/', views.StatusView.as_view()),
    path('github/start/', views.StartView.as_view()),
    path('github/callback/', views.CallbackView.as_view()),
    path('github/repositories/', views.RepositoriesView.as_view()),
    path('github/preview/', views.PreviewView.as_view()),
    path('<uuid:project_id>/', views.DetailView.as_view()),
]
