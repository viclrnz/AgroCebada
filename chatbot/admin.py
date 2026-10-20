from django.contrib import admin

from .models import ChatSession, Mensaje


# CORREGIDO: antes estaba vacío. Registrar los modelos permite revisar conversaciones desde el admin
# (por ejemplo, para ver qué preguntan los usuarios o investigar una respuesta errónea del bot).
class MensajeEnLinea(admin.TabularInline):
    model = Mensaje
    extra = 0
    readonly_fields = ('role', 'content', 'creado')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'idioma', 'creado')
    inlines = [MensajeEnLinea]
