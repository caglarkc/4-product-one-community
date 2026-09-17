from django.urls import path
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
