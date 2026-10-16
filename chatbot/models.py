from django.db import models

# Create your models here.

from django.db import models

class ChatSession(models.Model):
    # Equivalente a guardar si eligió "es" o "en"
    idioma = models.CharField(max_length=2, default='es')
    creado = models.DateTimeField(auto_now_add=True)

class Mensaje(models.Model):
    # Vincula el mensaje a una sesión específica
    sesion = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='mensajes')
    role = models.CharField(max_length=20) # Puede ser 'user' o 'assistant'
    content = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)