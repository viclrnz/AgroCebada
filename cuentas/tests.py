# NUEVO: pruebas del flujo de cuentas: registro -> pendiente -> autorizar -> entrar -> salir, y los casos
# que antes daban error 500 o dejaban pasar datos inválidos.
import json
from io import StringIO

from django.contrib.admin.sites import site
from django.contrib.auth.models import Group, Permission, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, RequestFactory, TestCase

CONTRASENA = 'cebada-de-hidalgo-2026'


class FlujoCuentasTests(TestCase):

    def setUp(self):
        cache.clear()
        # enforce_csrf_checks=True: igual que el navegador, sin token CSRF el POST se rechaza.
        # HTTP_REFERER: en HTTPS Django exige que la petición diga de qué página viene (el navegador lo hace solo).
        self.c = Client(enforce_csrf_checks=True, HTTP_REFERER='https://testserver/')
        self.c.get('/api/csrf/', secure=True)

    def post(self, url, datos):
        return self.c.post(url, json.dumps(datos), content_type='application/json', secure=True,
                           HTTP_X_CSRFTOKEN=self.c.cookies['csrftoken'].value)

    def registrar(self, usuario='ana', correo='Ana@Ejemplo.com', contrasena=CONTRASENA):
        return self.post('/api/auth/register/', {'username': usuario, 'email': correo,
                                                 'password': contrasena, 'confirm_password': contrasena})

    def test_flujo_completo(self):
        # 1. Registro: queda en auth_user, inactiva, sin permisos y con la contraseña cifrada.
        self.assertEqual(self.registrar().status_code, 201)
        cuenta = User.objects.get(username='ana')
        self.assertEqual(cuenta.email, 'ana@ejemplo.com')
        self.assertFalse(cuenta.is_active or cuenta.is_staff or cuenta.is_superuser)
        self.assertNotEqual(cuenta.password, CONTRASENA)
        # 2. Pendiente: con la contraseña correcta avisa que falta autorización.
        r = self.post('/api/auth/login/', {'username': 'ana', 'password': CONTRASENA})
        self.assertEqual(r.status_code, 403)
        # 3. Un admin la autoriza y la persona entra (sin necesitar is_staff), aunque cambie mayúsculas.
        cuenta.is_active = True
        cuenta.save()
        r = self.post('/api/auth/login/', {'username': 'ANA', 'password': CONTRASENA})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()['es_administrador'])
        self.assertTrue(self.c.get('/api/auth/me/', secure=True).json()['autenticado'])
        # 4. Salir.
        self.assertEqual(self.post('/api/auth/logout/', {}).status_code, 200)
        self.assertFalse(self.c.get('/api/auth/me/', secure=True).json()['autenticado'])

    def test_pendiente_no_se_revela_sin_contrasena(self):
        self.registrar()
        r = self.post('/api/auth/login/', {'username': 'ana', 'password': 'equivocada'})
        self.assertEqual(r.status_code, 401)  # mismo mensaje que si la cuenta no existiera

    def test_registro_rechaza_datos_invalidos(self):
        self.assertEqual(self.registrar(contrasena='1234567890').status_code, 400)
        self.assertEqual(self.registrar(correo='noesemail').status_code, 400)
        self.assertEqual(self.registrar(usuario='c c<>').status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_no_permite_duplicados(self):
        self.registrar()
        self.assertEqual(self.registrar(usuario='ANA', correo='otro@ejemplo.com').status_code, 400)
        self.assertEqual(self.registrar(usuario='otra', correo='ana@ejemplo.com').status_code, 400)

    def test_cuerpos_raros_no_dan_500(self):
        r = self.c.post('/api/auth/register/', '[1]', content_type='application/json', secure=True,
                        HTTP_X_CSRFTOKEN=self.c.cookies['csrftoken'].value)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.post('/api/auth/login/', {'username': 5, 'password': 'x'}).status_code, 400)

    def test_sin_csrf_se_rechaza(self):
        r = self.c.post('/api/auth/login/', json.dumps({'username': 'a', 'password': 'b'}),
                        content_type='application/json', secure=True)
        self.assertEqual(r.status_code, 403)

    def test_limite_de_intentos_de_login(self):
        codigos = [self.post('/api/auth/login/', {'username': 'x', 'password': 'y'}).status_code
                   for _ in range(11)]
        self.assertEqual(codigos[-1], 429)

    

class PanelAdministradoresTests(TestCase):
    """Un Administrador (staff + grupo) autoriza cuentas pero no puede darse permisos."""

    def setUp(self):
        call_command('crear_grupos', stdout=StringIO())
        self.admin_normal = User.objects.create_user('admin1', 'a1@ejemplo.com', CONTRASENA, is_staff=True)
        self.admin_normal.groups.add(Group.objects.get(name='Administradores'))
        self.pendiente = User.objects.create_user('nuevo', 'n@ejemplo.com', CONTRASENA, is_active=False)
        self.modelo_admin = site._registry[User]
        self.peticion = RequestFactory().get('/')
        self.peticion.user = self.admin_normal

    def test_campos_de_permisos_bloqueados(self):
        bloqueados = self.modelo_admin.get_readonly_fields(self.peticion, self.admin_normal)
        for campo in ('is_superuser', 'is_staff', 'groups', 'user_permissions'):
            self.assertIn(campo, bloqueados)

    def test_no_edita_a_otros_admins_ni_borra(self):
        otro_admin = User.objects.create_user('admin2', 'a2@ejemplo.com', CONTRASENA, is_staff=True)
        self.assertFalse(self.modelo_admin.has_change_permission(self.peticion, otro_admin))
        self.assertTrue(self.modelo_admin.has_change_permission(self.peticion, self.pendiente))
        self.assertFalse(self.modelo_admin.has_delete_permission(self.peticion, self.pendiente))

    def test_accion_autorizar(self):
        self.modelo_admin.message_user = lambda *a, **k: None
        self.modelo_admin.autorizar_cuentas(self.peticion, User.objects.filter(pk=self.pendiente.pk))
        self.pendiente.refresh_from_db()
        self.assertTrue(self.pendiente.is_active)
        self.assertFalse(self.pendiente.is_staff)
