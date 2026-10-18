from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),
    path('api/chat/', views.chat_endpoint, name='chat_endpoint'),
    path('api/csrf/', views.get_csrf_token, name='csrf_token'),
]

