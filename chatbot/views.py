import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from openai import APIError
from .services import procesar_mensaje
from .models import ChatSession
from AgroCebada_project.seguridad import limite_superado  # NUEVO: compartido con el login

logger = logging.getLogger(__name__)  # para ver los errores reales en consola

MAX_CHARS_MENSAJE = 2000              # tope para evitar costos por textos enormes
ACCIONES_VALIDAS = ('chat', 'undo', 'reroll')


def chat_interface(request):
    # Interfaz HTML de pruebas del chat. CORREGIDO: chatbot/urls.py solo la monta con DEBUG=True.
    return render(request, 'chatbot/chat.html')


CLAVE_SESIONES_ANONIMAS = 'chat_sesiones'  # IDs de conversaciones que abrió este navegador sin iniciar sesión


# CORREGIDO: el chat funciona con o sin login, pero cada conversación solo la abre quien la creó.
# - Con sesión iniciada, el dueño queda en la base de datos (ChatSession.usuario) y sirve desde cualquier navegador.
# - Sin sesión, los IDs propios se guardan en la sesión de Django (cookie del navegador) y la conversación no tiene
#   usuario. Así nadie abre una conversación ajena aunque adivine el número.
def _sesion_propia(request, sesion_id):
    try:
        sesion_id = int(sesion_id)
    except (TypeError, ValueError):
        return None
    if request.user.is_authenticated:
        return ChatSession.objects.filter(id=sesion_id, usuario=request.user).first()
    if sesion_id not in request.session.get(CLAVE_SESIONES_ANONIMAS, []):
        return None
    return ChatSession.objects.filter(id=sesion_id, usuario__isnull=True).first()


def _crear_sesion(request, idioma):
    if request.user.is_authenticated:
        return ChatSession.objects.create(usuario=request.user, idioma=idioma)
    sesion = ChatSession.objects.create(idioma=idioma)
    request.session[CLAVE_SESIONES_ANONIMAS] = request.session.get(CLAVE_SESIONES_ANONIMAS, []) + [sesion.id]
    return sesion


@require_POST  # CORREGIDO: reemplaza el "if request.method != 'POST'" manual; devuelve 405 igual
def chat_endpoint(request):
    # 1. El JSON se decodifica aparte para responder 400 solo por errores del cliente
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)

    # El cuerpo debe ser un objeto (no una lista ni un número) para que data.get no falle
    if not isinstance(data, dict):
        return JsonResponse({'error': 'El cuerpo debe ser un objeto JSON.'}, status=400)

    # Se aceptan los dos formatos de campos: React ('texto', 'idioma') y chat.html ('mensaje', 'language').
    texto_usuario = data.get('texto')
    if texto_usuario is None:
        texto_usuario = data.get('mensaje', '')
    if not isinstance(texto_usuario, str):
        return JsonResponse({'error': 'El campo "texto" debe ser texto.'}, status=400)
    texto_usuario = texto_usuario.strip()[:MAX_CHARS_MENSAJE]

    idioma = data.get('idioma') or data.get('language') or 'es'
    if idioma not in ('es', 'en'):
        idioma = 'es'

    accion = data.get('accion', 'chat')
    if accion not in ACCIONES_VALIDAS:
        accion = 'chat'

    # Solo se exige texto cuando se envía un mensaje nuevo; undo y reroll no llevan texto
    if accion == 'chat' and not texto_usuario:
        return JsonResponse({'error': 'El mensaje está vacío.'}, status=400)

    # CORREGIDO: 'chat' y 'reroll' llaman a la IA (cuestan dinero), así que cuentan para el límite. 'undo' no.
    if accion != 'undo' and limite_superado(request, 'chat', settings.CHATBOT_LIMITE_MENSAJES,
                                            settings.CHATBOT_LIMITE_VENTANA_S):
        return JsonResponse(
            {'error': 'Enviaste demasiados mensajes. Espera unos minutos e intenta de nuevo.'},
            status=429,
        )

    # 3. Sesión: solo se reutiliza si es de este usuario o de este navegador; si no, se crea una nueva.
    # CORREGIDO: antes se buscaba con ChatSession.objects.filter(id=...) sin comprobar el dueño.
    sesion = _sesion_propia(request, data.get('sesion_id'))
    if sesion is None:
        if accion != 'chat':
            # CORREGIDO: 'undo' o 'reroll' sobre una sesión ajena o inexistente no tienen nada que hacer.
            return JsonResponse({'error': 'La conversación no existe.'}, status=404)
        sesion = _crear_sesion(request, idioma)  # CORREGIDO: con o sin login, queda ligada a quien la abrió

    # 4. Procesar la respuesta con services.py
    try:
        respuesta_ia = procesar_mensaje(
            sesion=sesion, texto_usuario=texto_usuario, idioma=idioma, accion=accion
        )
    except APIError:
        # Falla del proveedor de IA (timeout, límite de uso, etc.): 503 con mensaje para reintentar
        logger.exception("Fallo del proveedor de IA")
        return JsonResponse(
            {'error': 'El asistente no está disponible por ahora. Intenta de nuevo en un momento.'},
            status=503,
        )
    except Exception:
        logger.exception("Error inesperado en chat_endpoint")
        return JsonResponse({'error': 'Ocurrió un error interno en el servidor.'}, status=500)

    # Se devuelve sesion_id para que React lo guarde y lo reenvíe (sin él, cada mensaje abriría una sesión nueva).
    return JsonResponse({
        'status': 'success',
        'respuesta': respuesta_ia,
        'sesion_id': str(sesion.id),
    })


@ensure_csrf_cookie
@require_GET
def get_csrf_token(request):
    # ensure_csrf_cookie garantiza que Django envíe la cookie 'csrftoken'. Se devuelve también en el JSON para que
    # funcione tanto si el front lee la cookie como si lee la respuesta.
    return JsonResponse({'status': 'ok', 'csrfToken': get_token(request)})

# CORREGIDO: se eliminó el alias "csrf = get_csrf_token"; ahora las dos rutas usan get_csrf_token directamente.
