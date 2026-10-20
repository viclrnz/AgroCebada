from django.apps import AppConfig


# NUEVO: app solo para la administración de cuentas (panel de usuarios y grupo Administradores).
# No tiene modelos propios: usa las tablas de Django (auth_user, auth_group).
class CuentasConfig(AppConfig):
    name = 'cuentas'
    verbose_name = 'Cuentas'
