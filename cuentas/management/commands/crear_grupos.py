# NUEVO: crea (o actualiza) el grupo "Administradores" con los permisos justos para autorizar cuentas.
# Uso:  python manage.py crear_grupos
# Después, en el admin, a cada uno de los administradores: marcar "Es staff" y agregarlo al grupo.
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

PERMISOS_ADMINISTRADORES = [
    ('auth', 'view_user'),              # ver la lista de cuentas
    ('auth', 'change_user'),            # autorizar / desactivar (los campos de permisos quedan bloqueados)
    ('chatbot', 'view_chatsession'),    # revisar conversaciones del chat (quítalo si no deben verlas)
    ('chatbot', 'view_mensaje'),
]


class Command(BaseCommand):
    help = 'Crea el grupo Administradores con permisos para autorizar cuentas.'

    def handle(self, *args, **options):
        grupo, creado = Group.objects.get_or_create(name='Administradores')
        permisos = [Permission.objects.get(content_type__app_label=app, codename=codigo)
                    for app, codigo in PERMISOS_ADMINISTRADORES]
        grupo.permissions.set(permisos)
        accion = 'creado' if creado else 'actualizado'
        self.stdout.write(self.style.SUCCESS(f'Grupo "Administradores" {accion} con {len(permisos)} permisos.'))
