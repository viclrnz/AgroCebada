import json
import logging
from django.http import JsonResponse
from django.shortcuts import render  # NUEVO: la vista chat_interface sigue existiendo en urls.py
from openai import APIError
from .services import procesar_mensaje
from .models import ChatSession
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)  # NUEVO: para ver los errores reales en consola

MAX_CHARS_MENSAJE = 2000              # NUEVO: tope para evitar costos por textos enormes
ACCIONES_VALIDAS = ('chat', 'undo', 'reroll')


def chat_interface(request):
    # Se conserva de tu versión anterior: carga la interfaz HTML del chat (chatbot/urls.py la sigue usando).
    return render(request, 'chatbot/chat.html')


def chat_endpoint(request):
    # 1. Bloquear peticiones que no sean POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Usa POST.'}, status=405)

    # 2. MODIFICADO: el JSON se decodifica aparte para responder 400 solo por errores del cliente
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)

    # NUEVO: validar que el cuerpo sea un objeto (no una lista ni un número) para que data.get no falle
    if not isinstance(data, dict):
        return JsonResponse({'error': 'El cuerpo debe ser un objeto JSON.'}, status=400)

    # NUEVO: validar el tipo de "texto"; antes, un número o null hacía fallar .strip() con un 500
    texto_usuario = data.get('texto', '')
    if not isinstance(texto_usuario, str):
        return JsonResponse({'error': 'El campo "texto" debe ser texto.'}, status=400)
    texto_usuario = texto_usuario.strip()[:MAX_CHARS_MENSAJE]  # NUEVO: recorte de longitud

    # NUEVO: solo se aceptan idiomas conocidos
    idioma = data.get('idioma', 'es')
    if idioma not in ('es', 'en'):
        idioma = 'es'

    # NUEVO: se soportan las acciones undo y reroll (antes se perdían y siempre se trabajaba en modo chat)
    accion = data.get('accion', 'chat')
    if accion not in ACCIONES_VALIDAS:
        accion = 'chat'

    # MODIFICADO: solo se exige texto cuando se envía un mensaje nuevo; undo y reroll no llevan texto
    if accion == 'chat' and not texto_usuario:
        return JsonResponse({'error': 'El mensaje está vacío.'}, status=400)

    # 3. MODIFICADO: ya no se crean sesiones con un ID inventado por el cliente (get_or_create).
    # Se busca la sesión existente; si no existe o el ID no es válido, se crea una nueva.
    # Cuando conectes el login, vincula la sesión al usuario y comprueba aquí que le pertenece.
    sesion = None
    sesion_id = data.get('sesion_id')
    if sesion_id:
        try:
            sesion = ChatSession.objects.filter(id=int(sesion_id)).first()
        except (TypeError, ValueError):
            sesion = None  # ID con formato inválido: se ignora en lugar de provocar un 500
    if sesion is None:
        sesion = ChatSession.objects.create(idioma=idioma)

    # 4. Procesar la respuesta con services.py
    try:
        respuesta_ia = procesar_mensaje(
            sesion=sesion, texto_usuario=texto_usuario, idioma=idioma, accion=accion
        )
    except APIError:
        # NUEVO: falla del proveedor de IA (timeout, límite de uso, etc.); no es un bug de tu servidor,
        # por eso se responde 503 con un mensaje que invita a reintentar.
        logger.exception("Fallo del proveedor de IA")
        return JsonResponse(
            {'error': 'El asistente no está disponible por ahora. Intenta de nuevo en un momento.'},
            status=503,
        )
    except Exception:
        # MODIFICADO: antes el error se descartaba en silencio; ahora queda registrado completo en la consola
        logger.exception("Error inesperado en chat_endpoint")
        return JsonResponse({'error': 'Ocurrió un error interno en el servidor.'}, status=500)

    return JsonResponse({
        'status': 'success',            # NUEVO: por compatibilidad con el chat.html actual
        'respuesta': respuesta_ia,
        'sesion_id': str(sesion.id),
    })

@ensure_csrf_cookie
@require_GET
def get_csrf_token(request):
    # ensure_csrf_cookie garantiza que Django envíe la cookie 'csrftoken'
    # y get_token entrega el mismo valor en el JSON para que React lo use en el header.
    return JsonResponse({'csrfToken': get_token(request)})