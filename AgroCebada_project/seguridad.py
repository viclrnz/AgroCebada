# NUEVO: utilidades de seguridad que comparten el login, el registro y el chatbot.
# Antes el límite de peticiones vivía solo en chatbot/views.py; ahora también lo usa auth_views.py.
import os
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def ip_cliente(request):
    """IP real del cliente. Detrás del proxy del hosting, REMOTE_ADDR es la IP del proxy (todos compartirían el
    mismo límite). Solo se confía en X-Forwarded-For si el .env lo indica, porque cualquiera puede inventar esa
    cabecera; se toma el ÚLTIMO valor, que es el que agrega nuestro proxy."""
    if os.getenv('DJANGO_DETRAS_DE_PROXY') == 'True':
        reenviada = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if reenviada:
            return reenviada.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', 'desconocida')


def limite_superado(request, nombre, maximo, ventana_s):
    """Cuenta peticiones por IP en la caché de Django y avisa cuando se pasa de 'maximo' en 'ventana_s' segundos.
    'nombre' separa los contadores (chat, login, registro) para que uno no gaste el cupo del otro."""
    clave = f'limite:{nombre}:{ip_cliente(request)}'
    # cache.add solo crea la llave si no existe: el contador arranca en 0 al empezar cada ventana.
    cache.add(clave, 0, timeout=ventana_s)
    try:
        usados = cache.incr(clave)
    except ValueError:  # la llave expiró justo entre add e incr
        cache.set(clave, 1, timeout=ventana_s)
        usados = 1
    return usados > maximo


def login_requerido(vista):
    """Como @login_required de Django, pero para una API: responde 401 en JSON en lugar de redirigir a una
    página HTML de login (React no sabría qué hacer con esa redirección)."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Inicia sesión para continuar.'}, status=401)
        return vista(request, *args, **kwargs)
    return envoltura
