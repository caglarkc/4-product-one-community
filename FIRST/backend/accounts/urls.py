from django.urls import path
from . import views

urlpatterns = [path('csrf/', views.CsrfView.as_view()), path('config/', views.ConfigView.as_view()),
    path('me/', views.MeView.as_view()), path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()), path('logout/', views.LogoutView.as_view())]
