from django.conf import settings
from django.db import models  # CORREGIDO: este import estaba repetido dos veces


class ChatSession(models.Model):
    # NUEVO (login): dueño de la conversación. Solo él puede verla, continuarla o deshacerla.
    # null=True porque las conversaciones guardadas antes del login no tienen dueño (nadie podrá abrirlas).
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='chats')
    # Equivalente a guardar si eligió "es" o "en"
    idioma = models.CharField(max_length=2, default='es')
    creado = models.DateTimeField(auto_now_add=True)

class Mensaje(models.Model):
    # Vincula el mensaje a una sesión específica
    sesion = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='mensajes')
    # CORREGIDO: 'choices' documenta y valida (en el admin y en formularios) los dos valores posibles.
    # No cambia la tabla, así que la migración que genera no toca datos.
    role = models.CharField(max_length=20, choices=[('user', 'Usuario'), ('assistant', 'Asistente')])
    content = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)