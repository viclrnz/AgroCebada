"""
URL configuration for AgroCebada_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.urls import path, include 
from chatbot import views as chatbot_views  # NUEVO (Jonathan, 2026-10-18): para la ruta del widget de React

# MODIFICADO (Jonathan, 2026-10-18): había dos 'urlpatterns =' y el segundo borraba al primero,
# así que las rutas del bot nunca se registraban. Ahora es una sola lista.
urlpatterns = [
    path('admin/', admin.site.urls),
    path('bot/', include('chatbot.urls')), # <-- rutas del bot
    # NUEVO (Jonathan, 2026-10-18): ruta que usa el widget de React (frontend/src/Chatbot.tsx hace fetch a /api/chatbot/).
    path('api/chatbot/', chatbot_views.chat_endpoint, name='chat_endpoint_react'),
    path('api/csrf/', chatbot_views.csrf, name='csrf'),  # NUEVO (Jonathan, 2026-10-18): cookie CSRF para React
    # NUEVO (Jonathan, 2026-10-18): API de parcelas para el Front (listado y detalle).
    path('api/parcelas/', include('parcelas.urls')),
]
