"""
URL configuration for AgroCebada_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
import os

from django.contrib import admin
from django.urls import path, include  # CORREGIDO: este import estaba repetido dos veces

from chatbot import views as chatbot_views
from AgroCebada_project import auth_views  # NUEVO (Ren): registro, login y logout

urlpatterns = [
    # CORREGIDO: la ruta del admin sale del .env (DJANGO_ADMIN_URL). '/admin/' es lo primero que prueban los bots
    # que buscan contraseñas débiles; con otra ruta reciben un 404.
    path(os.getenv('DJANGO_ADMIN_URL', 'admin/'), admin.site.urls),
    path('bot/', include('chatbot.urls')),  # página de pruebas del chat (solo existe con DEBUG=True)
    # Rutas que usa React (frontend/src/Chatbot.tsx y frontend/src/api.ts).
    # CORREGIDO: el nombre pasa de 'chat_endpoint_react' a 'chat_endpoint' porque chat.html lo busca así
    # ({% url "chat_endpoint" %}) y antes lo encontraba en la ruta duplicada /bot/api/chat/, que se eliminó.
    path('api/chatbot/', chatbot_views.chat_endpoint, name='chat_endpoint'),
    path('api/csrf/', chatbot_views.get_csrf_token, name='csrf'),  # CORREGIDO: antes usaba el alias views.csrf
    path('api/parcelas/', include('parcelas.urls')),
    # NUEVO (Ren): autenticación de usuarios con las cuentas de Django (auth_user).
    path('api/auth/register/', auth_views.registrar_usuario, name='registro_api'),
    path('api/auth/login/', auth_views.iniciar_sesion, name='login_api'),
    path('api/auth/me/', auth_views.sesion_actual, name='sesion_actual_api'),
    path('api/auth/logout/', auth_views.cerrar_sesion, name='logout_api'),
]
