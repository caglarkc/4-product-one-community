from django.urls import path
from . import views

urlpatterns = [
    path('', views.TeamsView.as_view()),
    path('mine/', views.MineView.as_view()),
    path('bookmarks/', views.BookmarksView.as_view()),
    path('<uuid:team_id>/', views.TeamDetailView.as_view()),
    path('<uuid:team_id>/apply/', views.ApplyView.as_view()),
    path('<uuid:team_id>/invitations/', views.InvitationsView.as_view()),
    path('<uuid:team_id>/requests/<uuid:request_id>/action/', views.RequestActionView.as_view()),
    path('<uuid:team_id>/members/<str:username>/role/', views.MemberRoleView.as_view()),
    path('<uuid:team_id>/members/<str:username>/', views.MemberView.as_view()),
    path('<uuid:team_id>/transfer/', views.TransferView.as_view()),
    path('<uuid:team_id>/leave/', views.LeaveView.as_view()),
    path('<uuid:team_id>/projects/', views.TeamProjectsView.as_view()),
    path('<uuid:team_id>/projects/<uuid:project_id>/', views.TeamProjectView.as_view()),
    path('<uuid:team_id>/bookmark/', views.BookmarkView.as_view()),
]
