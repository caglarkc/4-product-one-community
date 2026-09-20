from django.urls import path, include
from . import views

urlpatterns = [path('csrf/', views.CsrfView.as_view()), path('config/', views.ConfigView.as_view()),
    path('me/', views.MeView.as_view()), path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()), path('logout/', views.LogoutView.as_view())]

from . import account_views as account
urlpatterns += [
    path('profile/', account.ProfileView.as_view()),
    path('reauthenticate/', account.ReauthenticateView.as_view()),
    path('password/change/', account.PasswordChangeView.as_view()),
    path('password/reset/', account.PasswordResetView.as_view()),
    path('password/reset/confirm/', account.PasswordResetConfirmView.as_view()),
    path('email/resend/', account.EmailResendView.as_view()),
    path('email/change/', account.EmailChangeView.as_view()),
    path('email/verify/', account.EmailVerifyView.as_view()),
    path('sessions/', account.SessionsView.as_view()),
    path('sessions/revoke/', account.SessionsRevokeView.as_view()),
    path('sessions/<uuid:session_id>/', account.SessionRevokeView.as_view()),
]

from . import google_views as google
urlpatterns += [
    path('google/start/', google.GoogleStartView.as_view()),
    path('google/callback/', google.GoogleCallbackView.as_view()),
    path('google/signup/', google.GoogleSignupView.as_view()),
    path('google/email/request/', google.GoogleEmailRequestView.as_view()),
    path('google/email/verify/', google.GoogleEmailVerifyView.as_view()),
]

from . import github_views as github
urlpatterns += [
    path('github/start/', github.GitHubStartView.as_view()),
    path('github/callback/', github.GitHubCallbackView.as_view()),
    path('github/signup/', github.GitHubSignupView.as_view()),
    path('github/email/request/', github.GitHubEmailRequestView.as_view()),
    path('github/email/verify/', github.GitHubEmailVerifyView.as_view()),
]

urlpatterns += [path('projects/', include('projects.urls'))]

from . import reset_views as reset
urlpatterns += [
    path('github/disconnect/', reset.GitHubDisconnectView.as_view()),
    path('projects/github/disconnect/', reset.RepositoryDisconnectView.as_view()),
    path('account/', reset.AccountDeleteView.as_view()),
]


from . import community_views as community
from projects import community_views as project_community
urlpatterns += [
    path('community/config/', community.CommunityConfigView.as_view()),
    path('community/profile/', community.CommunityProfileView.as_view()),
    path('people/', community.PeopleView.as_view()),
    path('people/<str:username>/', community.PersonView.as_view()),
    path('bookmarks/', project_community.BookmarksView.as_view()),
    path('reports/', project_community.ReportsView.as_view()),
]
