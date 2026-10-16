from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'), # Carga la interfaz visual (HTML)
    path('api/chat/', views.chat_endpoint, name='chat_endpoint'), # Recibe mensajes en JSON
]