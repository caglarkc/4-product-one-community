from django.urls import path
from . import views

urlpatterns = [
    path('', views.FeedView.as_view()),
    path('projects/<uuid:project_id>/', views.ProjectTasksView.as_view()),
    path('<uuid:task_id>/refresh/', views.RefreshView.as_view()),
    path('<uuid:task_id>/retry/', views.RetryView.as_view()),
    path('<uuid:task_id>/', views.DetailView.as_view()),
]
