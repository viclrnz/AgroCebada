import json
from django.shortcuts import render
from django.http import JsonResponse
from .models import ChatSession
from .services import procesar_mensaje

def chat_interface(request):
    return render(request, 'chatbot/chat.html')

def chat_endpoint(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        sesion_id = data.get('sesion_id')
        mensaje = data.get('mensaje', '')
        idioma = data.get('language', 'es')
        accion = data.get('accion', 'chat') # Capturamos la acción (chat, undo o reroll)

        sesion, created = ChatSession.objects.get_or_create(id=sesion_id)
        respuesta = procesar_mensaje(sesion, mensaje, idioma, accion)

        return JsonResponse({'status': 'success', 'respuesta': respuesta})