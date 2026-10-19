
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
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
def registrar_usuario(request):
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'error': 'La solicitud no contiene JSON válido.'},
            status=400,
        )

    usuario = datos.get('username', '').strip()
    correo = datos.get('email', '').strip().lower()
    contrasena = datos.get('password', '')
    confirmar = datos.get('confirm_password', '')

    if not usuario or not correo or not contrasena or not confirmar:
        return JsonResponse(
            {'error': 'Completa todos los campos.'},
            status=400,
        )

    if contrasena != confirmar:
        return JsonResponse(
            {'error': 'Las contraseñas no coinciden.'},
            status=400,
        )

    if len(contrasena) < 10:
        return JsonResponse(
            {'error': 'La contraseña debe tener al menos 10 caracteres.'},
            status=400,
        )

    if User.objects.filter(username__iexact=usuario).exists():
        return JsonResponse(
            {'error': 'Ese nombre de usuario ya está registrado.'},
            status=400,
        )

    if User.objects.filter(email__iexact=correo).exists():
        return JsonResponse(
            {'error': 'Ese correo ya está registrado.'},
            status=400,
        )

    # La cuenta nace inactiva y sin permisos administrativos.
    User.objects.create_user(
        username=usuario,
        email=correo,
        password=contrasena,
        is_active=False,
        is_staff=False,
        is_superuser=False,
    )

    return JsonResponse({
        'registrado': True,
        'mensaje': 'Solicitud registrada. Espera a que el equipo autorice tu cuenta.',
    }, status=201)


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

    # Evita iniciar sesión con cuentas pendientes de aprobación.
    cuenta = User.objects.filter(username__iexact=usuario).first()

    if cuenta and not cuenta.is_active:
        return JsonResponse(
            {'error': 'Tu cuenta está pendiente de autorización o desactivada.'},
            status=403,
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

    if not user.is_staff and not user.is_superuser:
        return JsonResponse(
            {'error': 'Esta cuenta no tiene acceso administrativo.'},
            status=403,
        )

    login(request, user)

    return JsonResponse({
        'autenticado': True,
        'usuario': user.get_username(),
        'es_administrador': True,
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
