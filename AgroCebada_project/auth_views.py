# Registro, inicio y cierre de sesión con las cuentas de Django (tabla auth_user de Supabase).
# Escrito por Ren; las líneas marcadas con CORREGIDO son de la revisión del 2026-10-19.
import json

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .seguridad import limite_superado

# CORREGIDO: se quitó la vista 'csrf' de este archivo. Hacía lo mismo que chatbot.views.get_csrf_token, que ya
# atiende /api/csrf/ y también devuelve 'csrfToken' (Login.tsx y Registro.tsx siguen funcionando igual).

# CORREGIDO: límites de intentos por IP. Sin ellos se pueden probar contraseñas sin parar o llenar auth_user de
# cuentas falsas.
LIMITE_LOGIN = (10, 15 * 60)       # 10 intentos cada 15 minutos
LIMITE_REGISTRO = (5, 60 * 60)     # 5 registros por hora


# CORREGIDO: lee el JSON y comprueba que sea un objeto con campos de texto. Antes, un cuerpo como [1] o
# {"username": 5} provocaba un error 500 ('list' object has no attribute 'get' / int no tiene .strip()).
def _leer_campos(request, *nombres):
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, 'La solicitud no contiene JSON válido.'
    if not isinstance(datos, dict):
        return None, 'La solicitud debe ser un objeto JSON.'
    campos = {}
    for nombre in nombres:
        valor = datos.get(nombre, '')
        if not isinstance(valor, str):
            return None, 'Todos los campos deben ser texto.'
        campos[nombre] = valor
    return campos, None


@require_POST
def registrar_usuario(request):
    if limite_superado(request, 'registro', *LIMITE_REGISTRO):  # CORREGIDO
        return JsonResponse({'error': 'Demasiados registros desde esta conexión. Intenta más tarde.'}, status=429)

    campos, error = _leer_campos(request, 'username', 'email', 'password', 'confirm_password')
    if error:
        return JsonResponse({'error': error}, status=400)

    usuario = campos['username'].strip()
    correo = campos['email'].strip().lower()
    contrasena = campos['password']
    confirmar = campos['confirm_password']

    if not usuario or not correo or not contrasena or not confirmar:
        return JsonResponse({'error': 'Completa todos los campos.'}, status=400)

    if contrasena != confirmar:
        return JsonResponse({'error': 'Las contraseñas no coinciden.'}, status=400)

    # CORREGIDO: el nombre de usuario pasa por el mismo validador que usa Django (letras, números y @ . + - _,
    # máximo 150). Antes se aceptaba cualquier cosa, por ejemplo 'c c<>'.
    try:
        User.username_validator(usuario)
        if len(usuario) > 150:
            raise ValidationError('Máximo 150 caracteres.')
    except ValidationError:
        return JsonResponse(
            {'error': 'El usuario solo puede tener letras, números y @ . + - _ (máximo 150 caracteres).'},
            status=400,
        )

    # CORREGIDO: antes no se revisaba el formato del correo ('noesemail' se aceptaba).
    try:
        validate_email(correo)
    except ValidationError:
        return JsonResponse({'error': 'Escribe un correo válido.'}, status=400)

    # CORREGIDO: antes solo se exigían 10 caracteres y '1234567890' pasaba. validate_password aplica los
    # validadores de AUTH_PASSWORD_VALIDATORS en settings.py: largo mínimo, contraseñas comunes, solo números y
    # parecida al usuario o al correo (por eso recibe un User con esos datos).
    try:
        validate_password(contrasena, user=User(username=usuario, email=correo))
    except ValidationError as e:
        return JsonResponse({'error': ' '.join(e.messages)}, status=400)

    if User.objects.filter(username__iexact=usuario).exists():
        return JsonResponse({'error': 'Ese nombre de usuario ya está registrado.'}, status=400)

    if User.objects.filter(email__iexact=correo).exists():
        return JsonResponse({'error': 'Ese correo ya está registrado.'}, status=400)

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
    if limite_superado(request, 'login', *LIMITE_LOGIN):  # CORREGIDO
        return JsonResponse({'error': 'Demasiados intentos. Espera unos minutos e intenta de nuevo.'}, status=429)

    campos, error = _leer_campos(request, 'username', 'password')
    if error:
        return JsonResponse({'error': error}, status=400)

    usuario = campos['username'].strip()
    contrasena = campos['password']

    if not usuario or not contrasena:
        return JsonResponse({'error': 'Escribe tu usuario y contraseña.'}, status=400)

    # CORREGIDO: se busca la cuenta sin distinguir mayúsculas (igual que el registro, que impide 'ana' y 'ANA').
    # Antes el chequeo de inactiva usaba iexact pero authenticate() distinguía mayúsculas, así que 'ANA' con la
    # contraseña correcta recibía "usuario o contraseña incorrectos".
    cuenta = User.objects.filter(username__iexact=usuario).first()

    # CORREGIDO: primero se revisa la contraseña y SOLO después si la cuenta está pendiente. Antes el mensaje
    # "pendiente de autorización" salía sin revisar la contraseña, y cualquiera podía averiguar qué cuentas existen.
    if cuenta is None or not cuenta.check_password(contrasena):
        if cuenta is None:
            # Calcula un hash aunque la cuenta no exista, para que la respuesta tarde lo mismo y no delate
            # por el tiempo si el usuario existe (es lo mismo que hace Django en su login).
            User().set_password(contrasena)
        return JsonResponse({'error': 'Usuario o contraseña incorrectos.'}, status=401)

    if not cuenta.is_active:
        return JsonResponse({'error': 'Tu cuenta está pendiente de autorización o desactivada.'}, status=403)

    # CORREGIDO: se quitó el bloqueo "Esta cuenta no tiene acceso administrativo". Antes solo entraban cuentas
    # is_staff, así que para dejar usar la app a alguien había que abrirle también el panel /admin/.
    # Ahora entra cualquier cuenta activa; 'es_administrador' le dice al front si mostrar opciones de admin.
    # (Decisión pendiente de confirmar en el hilo: si solo deben entrar administradores, se vuelve a poner aquí.)
    login(request, cuenta, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({
        'autenticado': True,
        'usuario': cuenta.get_username(),
        'es_administrador': cuenta.is_staff,  # CORREGIDO: antes siempre True
    })


@require_GET
def sesion_actual(request):
    if not request.user.is_authenticated:
        return JsonResponse({'autenticado': False})

    return JsonResponse({
        'autenticado': True,
        'usuario': request.user.get_username(),
        # is_superuser sin is_staff no puede entrar al admin, así que basta con is_staff.
        'es_administrador': request.user.is_staff,
    })


@require_POST
def cerrar_sesion(request):
    logout(request)
    return JsonResponse({'status': 'ok'})
