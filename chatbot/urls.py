from django.conf import settings
from django.urls import path
from . import views

# CORREGIDO: antes se montaban aquí también 'api/chat/' y 'api/csrf/', que duplicaban /api/chatbot/ y /api/csrf/
# (las únicas que usa React). Quedaba una ruta extra por proteger y probar. Ahora solo queda la página de pruebas.
urlpatterns = []

# CORREGIDO: la página de pruebas /bot/ pinta la respuesta del bot como HTML sin sanitizar (marked + innerHTML),
# así que una respuesta manipulada podría ejecutar código en el navegador. Solo se publica en desarrollo.
if settings.DEBUG:
    urlpatterns += [
        path('', views.chat_interface, name='chat_interface'),
    ]
