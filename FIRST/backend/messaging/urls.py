from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConversationsView.as_view()),
    path('<uuid:conversation_id>/', views.MessagesView.as_view()),
    path('<uuid:conversation_id>/read/', views.ReadView.as_view()),
]
