
import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token


@ensure_csrf_cookie
@require_GET
def csrf(request):
    return JsonResponse({
        'status': 'ok',
        'csrfToken': get_token(request),
    })


@require_POST
def iniciar_sesion(request):
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'error': 'La solicitud no contiene JSON válido.'},
            status=400,
        )

    usuario = datos.get('username', '').strip()
    contrasena = datos.get('password', '')

    if not usuario or not contrasena:
        return JsonResponse(
            {'error': 'Escribe tu usuario y contraseña.'},
            status=400,
        )

    user = authenticate(
        request,
        username=usuario,
        password=contrasena,
    )

    if user is None:
        return JsonResponse(
            {'error': 'Usuario o contraseña incorrectos.'},
            status=401,
        )

    if not user.is_active:
        return JsonResponse(
            {'error': 'Esta cuenta está desactivada.'},
            status=403,
        )

    login(request, user)

    return JsonResponse({
        'autenticado': True,
        'usuario': user.get_username(),
        'es_administrador': user.is_staff or user.is_superuser,
    })


@require_GET
def sesion_actual(request):
    if not request.user.is_authenticated:
        return JsonResponse({'autenticado': False})

    return JsonResponse({
        'autenticado': True,
        'usuario': request.user.get_username(),
        'es_administrador': (
            request.user.is_staff or request.user.is_superuser
        ),
    })


@require_POST
def cerrar_sesion(request):
    logout(request)
    return JsonResponse({'status': 'ok'})
