# CORREGIDO: antes este archivo estaba vacío. Estas pruebas cubren lo que se corrigió en la revisión:
# dueño de la sesión, límite de mensajes, validación de entrada y filtro de SQL. No llaman a la IA real.
# Se corren con:  DB_ENGINE=django.db.backends.sqlite3 DB_NAME=pruebas.sqlite3 python manage.py test
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings

from . import services
from .models import ChatSession, Mensaje


# secure=True simula HTTPS: con DEBUG=False, settings.py redirige todo lo que llega por http://
def _post(client, cuerpo):
    return client.post('/api/chatbot/', json.dumps(cuerpo), content_type='application/json', secure=True)


@patch.dict('os.environ', {'SINOX_API_KEY': 'llave-de-prueba'})
@patch('chatbot.views.procesar_mensaje', return_value='respuesta de prueba')
class ChatEndpointTests(TestCase):

    def setUp(self):
        cache.clear()  # el contador del límite vive en la caché; cada prueba empieza en cero
        # NUEVO (login): el chat exige sesión iniciada.
        self.usuario = User.objects.create_user('ana', 'ana@ejemplo.com', 'una-contrasena-larga')
        self.client.force_login(self.usuario)

    def test_sin_login_responde_401(self, _mock):
        self.client.logout()
        self.assertEqual(_post(self.client, {'texto': 'hola'}).status_code, 401)

    def test_solo_post(self, _mock):
        self.assertEqual(self.client.get('/api/chatbot/', secure=True).status_code, 405)

    def test_json_invalido(self, _mock):
        r = self.client.post('/api/chatbot/', 'no es json', content_type='application/json', secure=True)
        self.assertEqual(r.status_code, 400)

    def test_mensaje_vacio(self, _mock):
        self.assertEqual(_post(self.client, {'texto': '   '}).status_code, 400)

    def test_reutiliza_su_propia_sesion(self, _mock):
        r1 = _post(self.client, {'texto': 'hola'})
        r2 = _post(self.client, {'texto': 'otra', 'sesion_id': r1.json()['sesion_id']})
        self.assertEqual(r1.json()['sesion_id'], r2.json()['sesion_id'])

    def test_no_puede_usar_sesion_ajena(self, _mock):
        # Otra persona tiene una conversación con mensajes.
        otra = User.objects.create_user('beto', 'beto@ejemplo.com', 'otra-contrasena-larga')
        ajena = ChatSession.objects.create(usuario=otra)
        Mensaje.objects.create(sesion=ajena, role='user', content='dato privado')
        # Ana intenta borrarla y luego escribir en ella.
        self.assertEqual(_post(self.client, {'sesion_id': ajena.id, 'accion': 'undo'}).status_code, 404)
        r = _post(self.client, {'texto': 'repite lo anterior', 'sesion_id': ajena.id})
        self.assertNotEqual(r.json()['sesion_id'], str(ajena.id))  # se le abrió una sesión nueva
        self.assertEqual(ajena.mensajes.count(), 1)                 # la ajena sigue intacta

    @override_settings(CHATBOT_LIMITE_MENSAJES=2)
    def test_limite_de_mensajes(self, _mock):
        codigos = [_post(self.client, {'texto': 'hola'}).status_code for _ in range(3)]
        self.assertEqual(codigos, [200, 200, 429])


class FiltroSqlTests(TestCase):
    """El filtro se prueba sin base de datos: las consultas bloqueadas nunca llegan a ejecutarse."""

    def setUp(self):
        # Se simula que la conexión de solo lectura existe y es válida.
        p = patch('chatbot.services._conexion_lectura_valida', return_value=True)
        p.start()
        self.addCleanup(p.stop)

    def bloqueada(self, sql):
        return services.ejecutar_sql_lectura(sql).startswith('Error de seguridad')

    def test_bloquea_escrituras_y_varias_sentencias(self):
        self.assertTrue(self.bloqueada('DELETE FROM rendimientos_estimados'))
        self.assertTrue(self.bloqueada('SELECT 1; DROP TABLE x'))
        self.assertTrue(self.bloqueada('WITH x AS (UPDATE t SET a=1 RETURNING *) SELECT * FROM x'))

    def test_bloquea_tablas_internas(self):
        self.assertTrue(self.bloqueada('SELECT password FROM auth_user'))
        self.assertTrue(self.bloqueada('SELECT content FROM "chatbot_mensaje"'))
        self.assertTrue(self.bloqueada('SELECT * FROM pg_stat_activity'))
        self.assertTrue(self.bloqueada("SELECT query_to_xml('select * from au' || 'th_user', true, true, '')"))

    @override_settings(DEBUG=False)
    def test_sin_conexion_readonly_no_ejecuta(self):
        patch.stopall()  # se quita la simulación: se usa la comprobación real
        with patch.object(services, 'ALIAS_DB_LECTURA', 'default'):
            self.assertIn('no está disponible', services.ejecutar_sql_lectura('SELECT 1'))
