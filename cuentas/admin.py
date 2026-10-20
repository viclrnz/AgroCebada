# NUEVO: panel de usuarios adaptado a los dos niveles de administración.
#   - Superusuario: puede todo (como el admin normal de Django).
#   - Administrador (is_staff + grupo "Administradores"): ve las cuentas y las autoriza o desactiva, pero NO puede
#     cambiar permisos. Sin esta clase, el formulario normal le dejaría marcar "es superusuario" en su propia cuenta.
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

CAMPOS_DE_PERMISOS = ('is_staff', 'is_superuser', 'groups', 'user_permissions')


class AgroCebadaUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')  # filtro "Activo: No" = pendientes
    ordering = ('is_active', '-date_joined')  # las cuentas pendientes salen primero
    actions = ['autorizar_cuentas', 'desactivar_cuentas']

    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            # Un Administrador ve estos campos pero no puede cambiarlos (ni en su cuenta ni en las demás).
            campos += [*CAMPOS_DE_PERMISOS, 'last_login', 'date_joined']
        return campos

    def has_change_permission(self, request, obj=None):
        # Un Administrador no puede editar a otro administrador ni a un superusuario (solo a usuarios normales).
        if obj is not None and not request.user.is_superuser and (obj.is_staff or obj.is_superuser):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Borrar cuentas queda solo para superusuarios; un Administrador puede desactivarlas.
        return request.user.is_superuser

    @admin.action(description='Autorizar cuentas seleccionadas', permissions=['change'])
    def autorizar_cuentas(self, request, queryset):
        # Solo cambia is_active. Nunca da is_staff ni permisos, aunque lo use un superusuario.
        n = queryset.filter(is_active=False, is_staff=False, is_superuser=False).update(is_active=True)
        self.message_user(request, f'{n} cuenta(s) autorizada(s).', messages.SUCCESS)

    @admin.action(description='Desactivar cuentas seleccionadas', permissions=['change'])
    def desactivar_cuentas(self, request, queryset):
        qs = queryset.exclude(pk=request.user.pk)  # nadie se desactiva a sí mismo por error
        if not request.user.is_superuser:
            qs = qs.filter(is_staff=False, is_superuser=False)  # un Administrador no desactiva a otro admin
        n = qs.update(is_active=False)
        self.message_user(request, f'{n} cuenta(s) desactivada(s).', messages.WARNING)


admin.site.unregister(User)
admin.site.register(User, AgroCebadaUserAdmin)
