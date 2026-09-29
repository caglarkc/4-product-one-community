from django.urls import path
from . import views

urlpatterns = [
    path('', views.SummaryView.as_view()),
    path('reports/', views.ReportsView.as_view()),
    path('reports/<uuid:report_id>/', views.ReportView.as_view()),
    path('users/', views.UsersView.as_view()),
    path('users/<int:user_id>/', views.UserView.as_view()),
    path('projects/', views.ProjectsView.as_view()),
    path('projects/<uuid:project_id>/', views.ProjectView.as_view()),
    path('audit/', views.AuditView.as_view()),
]
