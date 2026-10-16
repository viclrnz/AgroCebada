import re
import os
import json
import uuid  # NUEVO: genera IDs de llamadas a herramientas cuando el modelo las escribe como XML
import logging  # NUEVO (v2): para registrar qué herramienta se ejecutó y qué resultado vio el modelo
from openai import OpenAI
from django.db import connections, transaction  # MODIFICADO: se agrega transaction para usar transacciones READ ONLY seguras
from dotenv import load_dotenv
from .models import Mensaje

# ELIMINADO: "from parcelas.models import ParcelaApp" -> no se usaba en ningún lado del archivo.

load_dotenv()

# NUEVO (v2): logger del módulo. Sirve para diagnosticar si un dato erróneo viene de la base de datos
# (el log muestra una cifra incorrecta) o del modelo (el log muestra la cifra correcta y el bot responde otra).
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURACIÓN
# ==========================================
# NUEVO: el modelo y el alias de BD se leen del .env, así puedes cambiarlos sin tocar el código
# (por ejemplo, probar otro modelo con mejor soporte de tool calls).
MODELO = os.getenv("CHATBOT_MODEL", "zai-org/GLM-4.7-Flash")
ALIAS_DB_LECTURA = os.getenv("CHATBOT_DB_ALIAS", "default")  # idealmente un alias "readonly" con rol de solo lectura
MAX_PASOS = 8                # NUEVO: máximo de rondas de herramientas (explorar -> consultar -> responder), evita bucles infinitos
                             # MODIFICADO (v3): 6 -> 8 para dar margen a un reintento tras un error de SQL
MAX_FILAS = 100              # NUEVO: límite de filas por consulta, protege memoria y tokens
MAX_CHARS_RESULTADO = 12000  # NUEVO: recorta resultados enormes antes de mandarlos al modelo
TIMEOUT_SQL_MS = 10000       # NUEVO: ninguna consulta de la IA puede tardar más de 10 s
MAX_HISTORIAL = 20           # NUEVO (v4): solo los últimos 20 mensajes de la sesión se envían al modelo (controla costo y tokens)

PROMPT_SISTEMA = """Eres un ingeniero agrónomo y asistente de ciencia de datos para el proyecto AgroCebada. 
Tu objetivo es ayudar a analizar datos de parcelas de cebada en Hidalgo, Puebla y Tlaxcala.
Tienes acceso de SOLO LECTURA a la base de datos maestra en PostgreSQL.
Si no conoces el nombre exacto de las tablas o columnas, usa primero la herramienta 'explorar_estructura_db'.
Usa tus herramientas para extraer datos reales. No inventes métricas, índices ni rendimientos.
REGLAS CRÍTICAS PARA TUS HERRAMIENTAS:
1. SÓLO puedes usar las funciones que se te pasaron: 'explorar_estructura_db', 'ejecutar_consulta_select' y 'resumen_parcelas'.
2. Tienes ESTRICTAMENTE PROHIBIDO inventar nombres de funciones como 'query_database' o 'ejecutar_sql'.
3. NO uses etiquetas XML. Debes ejecutar tus herramientas silenciosamente en formato JSON.
4. NUNCA des cifras que no provengan del resultado de una herramienta. Si no hay datos, dilo claramente.
5. Para contar o resumir parcelas usa agregaciones (COUNT, GROUP BY) en lugar de listar todos los registros.
6. El argumento de 'ejecutar_consulta_select' se llama exactamente 'query_sql'.
7. NUNCA sumes ni restes números tú mismo. Los totales y subtotales deben venir calculados por SQL (COUNT, SUM, GROUP BY ROLLUP). Cita el total exactamente como lo devuelve la herramienta.
8. Para preguntas de cuántas parcelas hay o dónde están, usa 'resumen_parcelas'.
9. Si una consulta devuelve 0 registros o un error, corrígela (revisa mayúsculas/minúsculas y nombres de columnas) y vuelve a intentar UNA vez; después responde con lo que tengas.
10. Cuando ya tengas los datos necesarios, responde al usuario sin llamar más herramientas.
PISTA DE ESQUEMA: los datos del proyecto están en solo dos objetos:
- 'v_parcelas_app': municipio, estado, conjunto, area_ha_geod, rendimiento_t_ha.
- 'matriz_caracteristicas': estado, municipio, area_ha_geod, elev_media_m, pend_media_grados, pl_ndvi_pico, clima_pixel_id, id_poligono.
Las demás tablas (auth_*, django_*, chatbot_*, etl_*) son internas: NUNCA las consultes.
VALORES: los estados se guardan con inicial mayúscula: 'Hidalgo', 'Puebla', 'Tlaxcala'. Para filtrar texto usa ILIKE o LOWER(columna); nunca asumas mayúsculas (por ejemplo 'PUEBLA' no existe).
MODOS DE RESPUESTA:
- Si la pregunta requiere datos de AgroCebada (conteos, rendimientos, índices, ubicaciones), usa tus herramientas y cita solo cifras devueltas por ellas.
- Si la pregunta es conceptual (qué es el NDVI, qué significa rendimiento en t/ha, cómo se interpreta un resultado, qué es un polígono o un conjunto de datos), responde directamente con tu conocimiento agronómico y estadístico, sin consultar la base de datos.
- Si el usuario pide que le expliques un resultado que ya diste, explícalo en lenguaje sencillo, con ejemplos, y sin repetir la consulta.
- Puedes mezclar ambos: primero los datos reales y después una explicación breve de qué significan.
- Distingue siempre lo que viene de la base de datos de lo que es conocimiento general. Los valores de referencia de un concepto (por ejemplo, rangos típicos de NDVI) son conocimiento general y no datos de AgroCebada.
- Usa un tono claro y didáctico, evita jerga innecesaria y define los términos técnicos la primera vez que los uses.
- Si no sabes algo con certeza, dilo en lugar de inventar.
GLOSARIO DEL PROYECTO:
- area_ha_geod: área de la parcela en hectáreas, calculada geodésicamente.
- rendimiento_t_ha: rendimiento del cultivo en toneladas por hectárea.
- conjunto: grupo de datos al que pertenece la parcela (por ejemplo, entrenamiento o validación).
- NDVI / EVI: índices de vegetación calculados con imágenes satelitales; valores más altos indican vegetación más vigorosa."""
# NUEVO (v4): se integraron al archivo los bloques MODOS DE RESPUESTA y GLOSARIO que ya habías agregado a mano en tu
# repo, para que al reemplazar services.py no se pierdan. VERIFICA la definición de 'conjunto': fue una suposición
# mía a partir del nombre de la columna; corrígela con lo que realmente significa en tu proyecto.
# NUEVO (reglas 4 a 6 y pista de esquema): el modelo inventó cifras y usó el argumento "sql" en vez de "query_sql".
# Dar el esquema en el prompt evita llamar a explorar_estructura_db (devuelve TODAS las columnas y gasta muchos tokens).
# NUEVO (v2, reglas 7 y 8 y mención de 'resumen_parcelas' en la regla 1): el modelo sumó mal (207 en vez de 197).
# Los LLM fallan con la aritmética, así que se le prohíbe sumar y se le dirige a una herramienta que ya trae el total.
# NUEVO (v3, reglas 9 y 10, PISTA DE ESQUEMA y VALORES): en la prueba de Puebla el modelo filtró por 'PUEBLA' y
# 'pu' (en la BD el valor es 'Puebla'), obtuvo 0 registros, consultó tablas internas y agotó los pasos sin responder.
# Ahora conoce las dos únicas tablas útiles, la forma exacta de los valores y cuándo detenerse.
# IMPORTANTE: verifica que las columnas de la pista coincidan con tu BD. Las de v_parcelas_app y
# area_ha_geod/estado/municipio de matriz_caracteristicas ya se vieron funcionar en tus pruebas; revisa
# pl_ndvi_pico, clima_pixel_id e id_poligono (salieron en consultas del modelo que fallaron antes de ejecutarse).


def obtener_cliente_ia():
    llave = os.getenv("SINOX_API_KEY", "")
    # MODIFICADO: timeout y reintentos para que una caída del proveedor no deje colgado al usuario.
    return OpenAI(base_url="https://api.meganova.ai/v1", api_key=llave, timeout=60, max_retries=2)


# ==========================================
# MOTOR DE LECTURA SQL BLINDADO (100% READ-ONLY)
# ==========================================
# MODIFICADO: lista negra con regex y límites de palabra (\b). Antes, 'INSERT ' con espacio no detectaba
# "INSERT\n" ni "UPDATE(" y podía dar falsos positivos dentro de otras palabras. Se agregan COPY y PG_SLEEP.
PROHIBIDAS = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|PG_SLEEP)\b',
    re.IGNORECASE,
)


def ejecutar_sql_lectura(query, params=None):
    query_limpio = (query or "").strip().rstrip(';')  # MODIFICADO: tolera query=None sin lanzar excepción

    # 1. Prohibir múltiples sentencias y palabras clave de escritura
    if ';' in query_limpio:
        return "Error de seguridad: No se permiten múltiples sentencias SQL."
    # MODIFICADO: regex con \b para exigir SELECT/WITH como palabra completa al inicio.
    if not re.match(r'^\s*(SELECT|WITH)\b', query_limpio, re.IGNORECASE):
        return "Error de seguridad: Solo se permiten consultas SELECT."
    if PROHIBIDAS.search(query_limpio):
        return "Error de seguridad: Operación de escritura detectada y bloqueada."

    try:
        # MODIFICADO: antes se usaba "SET SESSION CHARACTERISTICS ... READ ONLY" y luego se restauraba a READ WRITE.
        # Con el pooler de Supabase (pgbouncer en modo transaction) eso puede filtrarse a otras conexiones/usuarios
        # o no aplicarse. Con transaction.atomic + SET TRANSACTION el efecto vive SOLO dentro de esta transacción
        # y se revierte solo, sin necesidad del bloque "finally" de restauración.
        with transaction.atomic(using=ALIAS_DB_LECTURA):
            with connections[ALIAS_DB_LECTURA].cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                # NUEVO: timeout local a la transacción, evita consultas pesadas que bloqueen la app.
                cursor.execute(f"SET LOCAL statement_timeout = {int(TIMEOUT_SQL_MS)}")
                # MODIFICADO (v3): antes era "params or []". Pasar una lista vacía hace que Django/psycopg trate
                # cada '%' del SQL como un marcador de parámetro y falle con "only '%s', '%b', '%t' are allowed".
                # Eso rompía TODOS los LIKE/ILIKE ('Pue%'). Con params=None el SQL se envía tal cual y '%' es literal.
                cursor.execute(query_limpio, params)
                columns = [col[0] for col in cursor.description]
                filas = cursor.fetchmany(MAX_FILAS)  # MODIFICADO: fetchmany en lugar de fetchall (límite de filas)

        data = [dict(zip(columns, fila)) for fila in filas]
        if not data:
            return "Consulta exitosa, pero no se encontraron registros."
        # MODIFICADO: ensure_ascii=False conserva acentos/ñ y se recorta el resultado para no saturar al modelo.
        return json.dumps(data, default=str, ensure_ascii=False)[:MAX_CHARS_RESULTADO]

    except Exception as e:
        return f"Error SQL: {e}"


# ==========================================
# HERRAMIENTAS DE CONSULTA PARA LA IA
# ==========================================
def explorar_estructura_db():
    """Descubre qué tablas y columnas existen en la base de datos de Supabase"""
    # Consejo: para ahorrar tokens, puedes agregar AND table_name IN ('v_parcelas_app', ...) al WHERE.
    query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
          AND table_name IN ('v_parcelas_app', 'matriz_caracteristicas')
        ORDER BY table_name, ordinal_position
    """  # MODIFICADO: se quitó el ';' final; el validador rechaza cualquier ';'
    # MODIFICADO (v3): antes devolvía TODAS las tablas (auth_*, django_*, ...) ordenadas alfabéticamente. Con el
    # tope de 12,000 caracteres, las columnas de 'matriz_caracteristicas' quedaban cortadas y el modelo nunca
    # veía el esquema real. Ahora solo devuelve las dos tablas del proyecto, y además no expone tablas internas.
    return ejecutar_sql_lectura(query)


def ejecutar_consulta_select(query_sql):
    """Permite a la IA hacer consultas SELECT precisas sobre las tablas que descubra"""
    return ejecutar_sql_lectura(query_sql)


# NUEVO (v2): herramienta con consulta FIJA. El total y los subtotales los calcula PostgreSQL, no el modelo.
# Esto corrige el error de 207 vs 197 (el modelo sumaba mal el desglose por municipio).
def resumen_parcelas():
    """Total de parcelas y desglose por estado y municipio, calculados 100% en SQL."""
    # GROUP BY ROLLUP genera, en una sola consulta, el detalle por municipio, el subtotal por estado
    # y el total general. COALESCE pone etiquetas legibles en las filas de subtotal/total para que
    # el modelo no tenga que interpretar NULLs. GROUPING() en el ORDER BY deja el total al final.
    query = """
        SELECT
            COALESCE(estado, 'TOTAL GENERAL') AS estado,
            COALESCE(municipio, CASE WHEN estado IS NULL THEN '' ELSE 'SUBTOTAL ESTADO' END) AS municipio,
            COUNT(*) AS parcelas
        FROM v_parcelas_app
        GROUP BY ROLLUP (estado, municipio)
        ORDER BY GROUPING(estado), estado, GROUPING(municipio), municipio
    """
    return ejecutar_sql_lectura(query)


funciones_disponibles = {
    "explorar_estructura_db": explorar_estructura_db,
    "ejecutar_consulta_select": ejecutar_consulta_select,
    "resumen_parcelas": resumen_parcelas,  # NUEVO (v2): registro de la herramienta
}

herramientas_ia = [
    {
        "type": "function",
        "function": {
            "name": "explorar_estructura_db",
            "description": "Obtiene la lista de todas las tablas y columnas disponibles en la base de datos de AgroCebada. Úsala siempre que necesites saber cómo se llaman las tablas o las variables antes de hacer una consulta.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_consulta_select",
            "description": "Ejecuta una consulta SQL (únicamente SELECT) en la base de datos de AgroCebada para obtener datos de parcelas, clima, relieve, índices NDVI/EVI o rendimientos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_sql": {
                        "type": "string",
                        "description": "La consulta SQL SELECT válida para PostgreSQL (ej. 'SELECT * FROM parcelas LIMIT 5')"
                    }
                },
                "required": ["query_sql"]
            }
        }
    },
    # NUEVO (v2): esquema de la herramienta para que el modelo sepa que existe y cuándo usarla.
    {
        "type": "function",
        "function": {
            "name": "resumen_parcelas",
            "description": "Devuelve el total de parcelas y el desglose por estado y municipio, ya calculados en SQL. Úsala para preguntas como 'cuántas parcelas hay' o 'dónde están'. No requiere argumentos.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# ==========================================
# NUEVO: UTILIDADES PARA LLAMADAS A HERRAMIENTAS EN XML
# ==========================================
# GLM-4.7-Flash a veces NO usa tool_calls nativos y escribe dentro de "content":
#   <tool_call>nombre<arg_key>sql</arg_key><arg_value>SELECT ...</arg_value></tool_call>
# El CASO 2 original buscaba <parameter=sql>, que es el formato de OTRO modelo, por eso nunca coincidía
# y el XML llegaba crudo al usuario. Estas funciones interpretan el formato real de GLM.
RE_TOOL_XML = re.compile(r'<tool_call>\s*([\w\-]+)\s*(.*?)</tool_call>', re.DOTALL)
RE_ARG_XML = re.compile(r'<arg_key>(.*?)</arg_key>\s*<arg_value>(.*?)</arg_value>', re.DOTALL)


def extraer_llamadas_xml(texto):
    """Convierte el XML de GLM en una lista de (nombre_herramienta, {argumentos})."""
    llamadas = []
    for nombre, cuerpo in RE_TOOL_XML.findall(texto):
        args = {k.strip(): v.strip() for k, v in RE_ARG_XML.findall(cuerpo)}
        llamadas.append((nombre.strip(), args))
    return llamadas


def limpiar_xml(texto):
    """Quita cualquier bloque <tool_call> para que el usuario nunca vea XML."""
    return re.sub(r'<tool_call>.*?</tool_call>', '', texto, flags=re.DOTALL).strip()


def ejecutar_herramienta(nombre, args):
    """Despacha la herramienta de forma segura y tolera nombres de argumento inventados por el modelo."""
    if nombre == "explorar_estructura_db":
        return explorar_estructura_db()
    if nombre == "resumen_parcelas":  # NUEVO (v2): despacha la herramienta de totales calculados en SQL
        return resumen_parcelas()
    if nombre == "ejecutar_consulta_select":
        # El modelo usó "sql" en lugar de "query_sql"; aceptamos las variantes comunes.
        q = args.get("query_sql") or args.get("sql") or args.get("query")
        return ejecutar_consulta_select(q) if q else "Error: falta la consulta SQL."
    return f"Error: la herramienta '{nombre}' no existe."


# ==========================================
# MOTOR PRINCIPAL DE MENSAJERÍA
# ==========================================
def procesar_mensaje(sesion, texto_usuario, idioma, accion="chat"):
    if accion == "undo":
        # MODIFICADO (v4): antes borraba siempre los 2 últimos mensajes. Desde que el mensaje de fallo ya no se
        # guarda (v3), un turno fallido deja solo el mensaje del usuario, y "borrar 2" se llevaba además la
        # respuesta del turno anterior. Ahora se borra la última respuesta (si existe) y luego el último mensaje del usuario.
        ultimo = sesion.mensajes.order_by('-creado', '-id').first()
        if ultimo and ultimo.role == "assistant":
            ultimo.delete()
            ultimo = sesion.mensajes.order_by('-creado', '-id').first()
        if ultimo and ultimo.role == "user":
            ultimo.delete()
        return "undo_ok"

    elif accion == "reroll":
        ultimo_msg = sesion.mensajes.order_by('-creado').first()
        if ultimo_msg and ultimo_msg.role == "assistant":
            ultimo_msg.delete()
    else:
        Mensaje.objects.create(sesion=sesion, role="user", content=texto_usuario)

    prompt_dinamico = PROMPT_SISTEMA
    if idioma == 'en':
        prompt_dinamico += "\n<rule>CRITICAL: You must ALWAYS respond in English.</rule>"
    else:
        prompt_dinamico += "\n<rule>CRITICO: Debes responder SIEMPRE en Español.</rule>"

    historial = [{"role": "system", "content": prompt_dinamico}]
    # MODIFICADO (v4): antes se enviaba TODO el historial. En sesiones largas el costo y la latencia crecen sin límite
    # y el modelo se confunde con contexto viejo. Ahora se toman los últimos MAX_HISTORIAL mensajes en orden cronológico.
    recientes = list(sesion.mensajes.order_by('-creado', '-id')[:MAX_HISTORIAL])
    recientes.reverse()
    for msg in recientes:
        historial.append({"role": msg.role, "content": msg.content})

    client = obtener_cliente_ia()
    texto_final = None

    # MODIFICADO: antes había UNA sola ronda de herramientas y la segunda llamada al modelo no recibía "tools".
    # Explorar estructura -> consultar -> responder necesita varias rondas, así que ahora es un bucle con tope
    # (MAX_PASOS). Se eliminaron los CASOS 1, 2 y 3 separados: este bucle los cubre a todos.
    for _ in range(MAX_PASOS):
        resp = client.chat.completions.create(
            model=MODELO,                 # MODIFICADO: modelo único y configurable (se eliminó MiMo-V2.6-Pro de respaldo)
            messages=historial,
            tools=herramientas_ia,        # MODIFICADO: se pasan las tools en TODAS las rondas
            tool_choice="auto",
            temperature=0,                # MODIFICADO (v2): 0.2 -> 0, respuestas deterministas para que el modelo no "improvise" cifras
        )
        msg = resp.choices[0].message
        texto = msg.content or ""

        # NUEVO: unificamos llamadas nativas (tool_calls) y llamadas escritas como XML en una sola lista.
        llamadas = []  # elementos: (id, nombre, args)
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}  # argumentos mal formados: la herramienta responderá con un error controlado
                llamadas.append((tc.id, tc.function.name, args))
        else:
            for nombre, args in extraer_llamadas_xml(texto):
                llamadas.append((f"call_{uuid.uuid4().hex[:8]}", nombre, args))

        # Sin llamadas = el modelo ya dio su respuesta final.
        if not llamadas:
            texto_final = limpiar_xml(texto)  # NUEVO: nunca se devuelve XML al usuario
            break

        # Registramos la intención del asistente (solo en memoria, NO en la base de datos).
        historial.append({
            "role": "assistant",
            "content": limpiar_xml(texto),
            "tool_calls": [
                {
                    "id": i,
                    "type": "function",
                    "function": {"name": n, "arguments": json.dumps(a)},
                } for i, n, a in llamadas
            ],
        })

        # Ejecutamos cada herramienta y devolvemos el resultado REAL al modelo.
        for i, n, a in llamadas:
            resultado = str(ejecutar_herramienta(n, a))  # MODIFICADO (v2): se guarda en variable para poder registrarlo
            # NUEVO (v2): log de diagnóstico. Si aquí aparece 197 y el bot responde 207, el error es del modelo;
            # si aquí aparece 207, el error viene de la base de datos/vista. Quita o baja a logger.info en producción.
            logger.warning("TOOL %s args=%s -> %s", n, a, resultado[:800])
            historial.append({
                "role": "tool",
                "tool_call_id": i,
                "name": n,
                "content": resultado,
            })

    es_fallo = False  # NUEVO (v3): marca si tuvimos que usar el mensaje de error genérico

    # NUEVO (v3): si se agotaron los pasos sin respuesta, hacemos UNA última llamada con tool_choice="none" para
    # forzar al modelo a resumir lo que sí encontró, en lugar de rendirnos con un mensaje genérico.
    if not texto_final:
        try:
            historial.append({
                "role": "user",
                "content": "Con la información obtenida hasta ahora, responde de la mejor forma posible. "
                           "Si no obtuviste datos, dilo claramente y no inventes cifras. No uses herramientas.",
            })
            resp = client.chat.completions.create(
                model=MODELO,
                messages=historial,
                tools=herramientas_ia,
                tool_choice="none",
                temperature=0,
            )
            texto_final = limpiar_xml(resp.choices[0].message.content or "")
        except Exception as e:
            logger.warning("Fallo la respuesta final forzada: %s", e)

    # NUEVO: si aun así no hay respuesta, damos un mensaje seguro en vez de dejar texto_final vacío.
    if not texto_final:
        es_fallo = True
        texto_final = ("I couldn't complete the query. Please try rephrasing your question."
                       if idioma == 'en'
                       else "No pude completar la consulta. Intenta reformular tu pregunta.")

    # GUARDADO FINAL DEL HISTORIAL
    # MODIFICADO (importante): solo se guarda el texto final limpio. Antes se guardaba la respuesta con XML crudo,
    # y en el siguiente turno el modelo creía que ya había consultado y terminaba inventando datos.
    # MODIFICADO (v3): el mensaje de fallo NO se guarda. Si se guardara, en el siguiente turno el modelo vería
    # en el historial que "ya falló" y tendería a rendirse de nuevo.
    if not es_fallo:
        Mensaje.objects.create(sesion=sesion, role="assistant", content=texto_final)

    return texto_final