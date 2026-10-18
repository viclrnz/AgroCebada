import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import ChatSession
from .services import procesar_mensaje

def chat_interface(request):
    return render(request, 'chatbot/chat.html')

def chat_endpoint(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        sesion_id = data.get('sesion_id')
        # MODIFICADO (Jonathan, 2026-10-18): el widget de React manda 'texto' e 'idioma'; la plantilla
        # HTML manda 'mensaje' y 'language'. Se aceptan los dos formatos.
        mensaje = data.get('mensaje') or data.get('texto', '')
        idioma = data.get('language') or data.get('idioma', 'es')
        accion = data.get('accion', 'chat') # Capturamos la acción (chat, undo o reroll)

        sesion, created = ChatSession.objects.get_or_create(id=sesion_id)
        respuesta = procesar_mensaje(sesion, mensaje, idioma, accion)

        # MODIFICADO (Jonathan, 2026-10-18): se devuelve sesion_id para que React lo guarde y lo mande en el
        # siguiente mensaje. Sin él, cada mensaje abre una sesión nueva y el bot no recuerda la conversación.
        return JsonResponse({'status': 'success', 'respuesta': respuesta, 'sesion_id': sesion.id})
    # NUEVO (Jonathan, 2026-10-18): antes un GET devolvía None y Django lanzaba un error 500.
    return JsonResponse({'status': 'error', 'respuesta': 'Usa POST.'}, status=405)


# NUEVO (Jonathan, 2026-10-18): el widget de React llama aquí al cargar para recibir la cookie 'csrftoken'
# y mandarla en el POST a /api/chatbot/. Sin ella Django responde 403.
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'status': 'ok'})
