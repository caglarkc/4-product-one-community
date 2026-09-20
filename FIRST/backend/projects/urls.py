from django.urls import path
from . import views, participation_views as participation

urlpatterns = [
    path('', views.CreateView.as_view()),
    path('config/', views.ConfigView.as_view()),
    path('mine/', views.MineView.as_view()),
    path('github/status/', views.StatusView.as_view()),
    path('github/start/', views.StartView.as_view()),
    path('github/callback/', views.CallbackView.as_view()),
    path('github/repositories/', views.RepositoriesView.as_view()),
    path('github/issues/', views.IssueChoicesView.as_view()),
    path('github/preview/', views.PreviewView.as_view()),
    path('participation/', participation.DashboardView.as_view()),
    path('participation/<uuid:participation_id>/action/', participation.ActionView.as_view()),
    path('notifications/', participation.NotificationsView.as_view()),
    path('notifications/<uuid:notification_id>/read/', participation.NotificationReadView.as_view()),
    path('<uuid:project_id>/apply/', participation.ApplyView.as_view()),
    path('<uuid:project_id>/invitations/', participation.InvitationView.as_view()),
    path('<uuid:project_id>/viewers/', participation.ViewersView.as_view()),
    path('<uuid:project_id>/collaboration/', participation.CollaborationView.as_view()),
    path('<uuid:project_id>/issue/', participation.IssueView.as_view()),
    path('<uuid:project_id>/', views.DetailView.as_view()),
]
