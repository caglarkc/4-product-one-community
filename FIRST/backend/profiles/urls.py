from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.StudentView.as_view()),
    path('student/request/', views.StudentRequestView.as_view()),
    path('student/verify/', views.StudentVerifyView.as_view()),
    path('settings/', views.SettingsView.as_view()),
    path('stats/', views.StatsView.as_view()),
    path('stats/refresh/', views.StatsRefreshView.as_view()),
    path('portfolio/', views.PortfolioView.as_view()),
    path('portfolio/<uuid:item_id>/', views.PortfolioItemView.as_view()),
    path('certificates/', views.CertificatesView.as_view()),
    path('certificates/<uuid:certificate_id>/', views.CertificateView.as_view()),
    path('certificates/<uuid:certificate_id>/preview/', views.CertificatePreviewView.as_view()),
    path('people/<str:username>/', views.PublicExtensionView.as_view()),
]
