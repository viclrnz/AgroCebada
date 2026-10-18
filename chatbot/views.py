import json
import logging
from django.http import JsonResponse
from django.shortcuts import render  # se conserva: chatbot/urls.py usa chat_interface
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from openai import APIError
from .services import procesar_mensaje
from .models import ChatSession

# FUSIONADO: se eliminaron los imports duplicados que dejó el conflicto (ensure_csrf_cookie y ChatSession
# aparecían en ambas ramas).

logger = logging.getLogger(__name__)  # para ver los errores reales en consola

MAX_CHARS_MENSAJE = 2000              # tope para evitar costos por textos enormes
ACCIONES_VALIDAS = ('chat', 'undo', 'reroll')


def chat_interface(request):
    # Carga la interfaz HTML de pruebas del chat (chatbot/urls.py la sigue usando).
    return render(request, 'chatbot/chat.html')


def chat_endpoint(request):
    # 1. Bloquear peticiones que no sean POST (de las dos ramas: ya devolvía 405 y Jonathan evitó el 500 por None)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Usa POST.'}, status=405)

    # 2. El JSON se decodifica aparte para responder 400 solo por errores del cliente
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)

    # El cuerpo debe ser un objeto (no una lista ni un número) para que data.get no falle
    if not isinstance(data, dict):
        return JsonResponse({'error': 'El cuerpo debe ser un objeto JSON.'}, status=400)

    # FUSIONADO (aporte de Jonathan): se aceptan los DOS formatos de campos.
    #   React:        'texto' e 'idioma'
    #   chat.html:    'mensaje' y 'language'
    # Se mantiene la validación de tipo y el recorte de longitud de nuestra versión.
    texto_usuario = data.get('texto')
    if texto_usuario is None:
        texto_usuario = data.get('mensaje', '')
    if not isinstance(texto_usuario, str):
        return JsonResponse({'error': 'El campo "texto" debe ser texto.'}, status=400)
    texto_usuario = texto_usuario.strip()[:MAX_CHARS_MENSAJE]

    idioma = data.get('idioma') or data.get('language') or 'es'
    if idioma not in ('es', 'en'):
        idioma = 'es'

    # Se soportan las acciones undo y reroll
    accion = data.get('accion', 'chat')
    if accion not in ACCIONES_VALIDAS:
        accion = 'chat'

    # Solo se exige texto cuando se envía un mensaje nuevo; undo y reroll no llevan texto
    if accion == 'chat' and not texto_usuario:
        return JsonResponse({'error': 'El mensaje está vacío.'}, status=400)

    # 3. Sesión: se busca la existente; si no existe o el ID no es válido, se crea una nueva
    # (ya no se usa get_or_create con un ID inventado por el cliente).
    # Cuando exista login, vincula la sesión al usuario y comprueba aquí que le pertenece.
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
        # Falla del proveedor de IA (timeout, límite de uso, etc.): 503 con mensaje para reintentar
        logger.exception("Fallo del proveedor de IA")
        return JsonResponse(
            {'error': 'El asistente no está disponible por ahora. Intenta de nuevo en un momento.'},
            status=503,
        )
    except Exception:
        logger.exception("Error inesperado en chat_endpoint")
        return JsonResponse({'error': 'Ocurrió un error interno en el servidor.'}, status=500)

    # FUSIONADO (aporte de Jonathan): se devuelve sesion_id para que React lo guarde y lo reenvíe;
    # sin él, cada mensaje abriría una sesión nueva y el bot no recordaría la conversación.
    # Se devuelve como texto (str), igual que en nuestra versión.
    return JsonResponse({
        'status': 'success',
        'respuesta': respuesta_ia,
        'sesion_id': str(sesion.id),
    })


@ensure_csrf_cookie
@require_GET
def get_csrf_token(request):
    # ensure_csrf_cookie garantiza que Django envíe la cookie 'csrftoken'.
    # FUSIONADO: la versión de Jonathan devolvía solo {'status': 'ok'} (el front leía la cookie);
    # la nuestra devolvía el token en el JSON. Esta respuesta incluye ambos campos, así que
    # funciona con cualquiera de los dos frontends.
    return JsonResponse({'status': 'ok', 'csrfToken': get_token(request)})


# FUSIONADO: alias para que la ruta de Jonathan (views.csrf) siga funcionando sin cambios.
# Cuando el equipo decida un solo nombre, borra el que no se use.
csrf = get_csrf_token