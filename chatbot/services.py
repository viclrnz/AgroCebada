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
# NUEVO (Jonathan, 2026-10-18): dirección del proveedor de IA configurable (sirve para pruebas locales).
URL_API_IA = os.getenv("CHATBOT_API_URL", "https://api.meganova.ai/v1")
ALIAS_DB_LECTURA = os.getenv("CHATBOT_DB_ALIAS", "default")  # idealmente un alias "readonly" con rol de solo lectura
MAX_PASOS = 8                # NUEVO: máximo de rondas de herramientas (explorar -> consultar -> responder), evita bucles infinitos
                             # MODIFICADO (v3): 6 -> 8 para dar margen a un reintento tras un error de SQL
MAX_FILAS = 100              # NUEVO: límite de filas por consulta, protege memoria y tokens
MAX_CHARS_RESULTADO = 12000  # NUEVO: recorta resultados enormes antes de mandarlos al modelo
TIMEOUT_SQL_MS = 10000       # NUEVO: ninguna consulta de la IA puede tardar más de 10 s
MAX_HISTORIAL = 20           # NUEVO (v4): solo los últimos 20 mensajes de la sesión se envían al modelo (controla costo y tokens)

# MODIFICADO (Jonathan, 2026-10-18): el bot se presentaba como "asistente de ciencia de datos" y ofrecía análisis
# técnicos. Ahora su papel es orientar a quien usa la app: explicar qué hay en cada sección, cómo leer los datos y
# contestar preguntas sobre las parcelas en lenguaje sencillo. Las reglas de herramientas no cambian.
# MODIFICADO (Jonathan, 2026-10-18): el asistente se llama Cebas (de "cebada"). La variable SINOX_API_KEY conserva su nombre.
PROMPT_SISTEMA = """Eres Cebas, asistente de SocieData para el proyecto AgroCebada. Si te preguntan tu nombre, di que te llamas Cebas.
Tu papel es orientar a las personas que usan la app: ayudarles a encontrar información, explicarles qué significa
lo que ven y contestar sus preguntas sobre las 197 parcelas de cebada de Hidalgo, Puebla y Tlaxcala.
Quien te escribe puede no saber nada de datos ni de programación: habla claro, sin tecnicismos.
NUNCA menciones SQL, tablas, columnas, consultas, herramientas ni nombres internos (por ejemplo 'rendimiento_estimado_t_ha'
o 'ensamble_16vars'); di "rendimiento", "el modelo", etc. Tampoco muestres datos en formato JSON.
Responde corto: 2 a 5 frases o una lista breve. Si la persona quiere más detalle, que lo pida.
Si te preguntan algo que no tiene que ver con AgroCebada o la cebada, di amablemente que solo puedes ayudar con la plataforma.
Tienes acceso de SOLO LECTURA a la base de datos del proyecto.
Si no conoces el nombre exacto de las tablas o columnas, usa primero la herramienta 'explorar_estructura_db'.
Usa tus herramientas para extraer datos reales. No inventes métricas, índices ni rendimientos.
GUÍA DE LA APP (úsala para orientar; menciona la sección donde la persona puede verlo por sí misma):
- Dashboard: resumen general. Total de parcelas, rendimiento promedio, el modelo que se usa, un mapa pequeño y las 5 parcelas con mayor rendimiento.
- Mapa de parcelas: todas las parcelas en el mapa. Se puede filtrar por estado y por tipo de dato. Color café = menos de 3.5 t/ha, verde claro = 3.5 a 4.5, verde oscuro = más de 4.5. Los puntos más opacos son medidos en campo; los más claros, estimados. Al dar clic en un punto se abre su detalle.
- Parcelas: lista de las 197 parcelas con buscador (por ID, estado o municipio) y filtro por estado. Al dar clic en un ID se abre su detalle.
- Detalle de parcela: rendimiento, si fue medido o estimado, ubicación, coordenadas y superficie. Desde ahí se llega a "Consultar predicción".
- Análisis del modelo: compara los modelos probados y muestra el rendimiento promedio por estado y por municipio.
- Los ID de parcela van de AGC_001 a AGC_197.
CÓMO EXPLICAR LOS DATOS:
- El rendimiento se mide en toneladas por hectárea (t/ha): cuánta cebada se cosecha en una hectárea (10,000 m², un poco más que una cancha de fútbol).
- "Observado" o "medido": dato real tomado en campo (138 parcelas). "Estimado": lo calculó un modelo con imágenes de satélite, clima, suelo y relieve porque no había medición (59 parcelas).
- Si preguntan qué tan confiable es una estimación: el modelo se equivoca en promedio unas 0.37 t/ha (validación cruzada con las 138 parcelas medidas). Recomiéndales ver la sección Análisis del modelo.
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
11. Para preguntas de rendimiento usa 'rendimiento_estimado_t_ha' y aclara siempre si el valor es observado o predicho por el modelo (columna 'origen').
PISTA DE ESQUEMA: los datos del proyecto están en tres objetos (197 parcelas, una fila por id_poligono):
- 'rendimientos_estimados' (TABLA PRINCIPAL, úsala por defecto): id_poligono, estado, municipio, conjunto, superficie_ha, latitud, longitud, rendimiento_estimado_t_ha, origen, modelo.
- 'v_parcelas_app': id_poligono, municipio, estado, conjunto, area_ha_geod, rendimiento_t_ha, elev_media_m, pend_media_grados, pl_ndvi_pico, pl_sos50_doy, pl_eos50_doy, ac_lluvia_ciclo_mm, soil_ph, rendimiento_estimado_t_ha, origen_rendimiento, modelo_rendimiento, latitud, longitud.
- 'matriz_caracteristicas': todas las variables satelitales, de clima, suelo y relieve (98 columnas) por id_poligono. Úsala solo si la variable no está en las anteriores; une por id_poligono.
Las demás tablas (auth_*, django_*, chatbot_*, etl_*) son internas: NUNCA las consultes.
VALORES: los estados se guardan con inicial mayúscula: 'Hidalgo', 'Puebla', 'Tlaxcala'. Para filtrar texto usa ILIKE o LOWER(columna); nunca asumas mayúsculas (por ejemplo 'PUEBLA' no existe).
'conjunto' vale 'ENTRENAMIENTO' (138 parcelas) o 'PREDICCION' (59). 'origen' vale 'observado' o 'modelo'.
MODOS DE RESPUESTA:
- Si la pregunta requiere datos de AgroCebada (conteos, rendimientos, índices, ubicaciones), usa tus herramientas y cita solo cifras devueltas por ellas.
- Si la pregunta es conceptual (qué es el NDVI, qué significa rendimiento en t/ha, cómo se interpreta un resultado, qué es un polígono o un conjunto de datos), responde directamente con tu conocimiento agronómico y estadístico, sin consultar la base de datos.
- Si el usuario pide que le expliques un resultado que ya diste, explícalo en lenguaje sencillo, con ejemplos, y sin repetir la consulta.
- Puedes mezclar ambos: primero los datos reales y después una explicación breve de qué significan.
- Distingue siempre lo que viene de la base de datos de lo que es conocimiento general. Los valores de referencia de un concepto (por ejemplo, rangos típicos de NDVI) son conocimiento general y no datos de AgroCebada.
- Usa un tono amable, claro y cercano. Si usas un término técnico (por ejemplo NDVI), explícalo en una frase sencilla.
- Si no sabes algo con certeza, dilo en lugar de inventar.
GLOSARIO DEL PROYECTO:
- area_ha_geod / superficie_ha: área de la parcela en hectáreas, calculada geodésicamente (es el mismo valor).
- rendimiento_t_ha: rendimiento OBSERVADO en toneladas por hectárea. Solo existe en ENTRENAMIENTO; en PREDICCION es nulo.
- rendimiento_estimado_t_ha: el rendimiento que muestra la app. En ENTRENAMIENTO es el observado; en PREDICCION es el que predijo el modelo.
- conjunto: ENTRENAMIENTO son parcelas con rendimiento medido en campo, usadas para entrenar el modelo; PREDICCION son parcelas sin medición, cuyo rendimiento estima el modelo.
- origen: 'observado' (medido en campo) o 'modelo' (predicho).
- modelo: nombre del modelo que generó la predicción (por ejemplo, 'ensamble_16vars' = ensamble de Random Forest y SVR con 16 variables). Es nulo si el valor es observado.
- latitud / longitud: ubicación de la parcela en grados (WGS84), en el centro del polígono.
- NDVI / EVI: índices de vegetación calculados con imágenes satelitales; valores más altos indican vegetación más vigorosa."""
# NUEVO (v4): se integraron al archivo los bloques MODOS DE RESPUESTA y GLOSARIO que ya habías agregado a mano en tu
# repo, para que al reemplazar services.py no se pierdan.
# MODIFICADO (Jonathan, 2026-10-18): se corrigió 'conjunto' (ENTRENAMIENTO/PREDICCION, no validación), se agregó 'rendimientos_estimados'
# como tabla principal y se explican rendimiento observado vs. estimado, origen, modelo y coordenadas.
# Sin esto el bot respondía que las 59 parcelas de PREDICCION no tienen rendimiento (rendimiento_t_ha es nulo ahí).
# NUEVO (reglas 4 a 6 y pista de esquema): el modelo inventó cifras y usó el argumento "sql" en vez de "query_sql".
# Dar el esquema en el prompt evita llamar a explorar_estructura_db (devuelve TODAS las columnas y gasta muchos tokens).
# NUEVO (v2, reglas 7 y 8 y mención de 'resumen_parcelas' en la regla 1): el modelo sumó mal (207 en vez de 197).
# Los LLM fallan con la aritmética, así que se le prohíbe sumar y se le dirige a una herramienta que ya trae el total.
# NUEVO (v3, reglas 9 y 10, PISTA DE ESQUEMA y VALORES): en la prueba de Puebla el modelo filtró por 'PUEBLA' y
# 'pu' (en la BD el valor es 'Puebla'), obtuvo 0 registros, consultó tablas internas y agotó los pasos sin responder.
# Ahora conoce las dos únicas tablas útiles, la forma exacta de los valores y cuándo detenerse.
# MODIFICADO (Jonathan, 2026-10-18): las columnas de la pista se verificaron contra sql/005 y sql/006 del repo AgroCebada_Datos.


def obtener_cliente_ia():
    llave = os.getenv("SINOX_API_KEY", "")
    # MODIFICADO: timeout y reintentos para que una caída del proveedor no deje colgado al usuario.
    return OpenAI(base_url=URL_API_IA, api_key=llave, timeout=60, max_retries=2)


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
          AND table_name IN ('rendimientos_estimados', 'v_parcelas_app', 'matriz_caracteristicas')
        ORDER BY CASE table_name WHEN 'rendimientos_estimados' THEN 1 WHEN 'v_parcelas_app' THEN 2 ELSE 3 END,
                 ordinal_position
    """  # MODIFICADO: se quitó el ';' final; el validador rechaza cualquier ';'
    # MODIFICADO (v3): antes devolvía TODAS las tablas (auth_*, django_*, ...) ordenadas alfabéticamente. Con el
    # tope de 12,000 caracteres, las columnas de 'matriz_caracteristicas' quedaban cortadas y el modelo nunca
    # veía el esquema real. Ahora solo devuelve las dos tablas del proyecto, y además no expone tablas internas.
    # MODIFICADO (Jonathan, 2026-10-18): se agrega 'rendimientos_estimados' y va primero. Si el tope de caracteres corta algo,
    # que sea la matriz (98 columnas), no las tablas principales.
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
    # MODIFICADO (Jonathan, 2026-10-18): se lee de 'rendimientos_estimados', la tabla principal (mismas 197 parcelas).
    query = """
        SELECT
            COALESCE(estado, 'TOTAL GENERAL') AS estado,
            COALESCE(municipio, CASE WHEN estado IS NULL THEN '' ELSE 'SUBTOTAL ESTADO' END) AS municipio,
            COUNT(*) AS parcelas
        FROM rendimientos_estimados
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
                        "description": "La consulta SQL SELECT válida para PostgreSQL (ej. 'SELECT municipio, AVG(rendimiento_estimado_t_ha) FROM rendimientos_estimados GROUP BY municipio')"  # MODIFICADO (Jonathan, 2026-10-18): la tabla 'parcelas' del ejemplo no existe
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
    # NUEVO (Jonathan, 2026-10-18): sin llave el cliente de OpenAI lanza una excepción y Django respondía 500.
    if not os.getenv("SINOX_API_KEY"):
        return "El asistente aún no está configurado: falta SINOX_API_KEY en el archivo .env."
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
    error_ia = False  # NUEVO (Jonathan, 2026-10-18): la IA no respondió (sin internet, llave inválida, caída)

    # MODIFICADO: antes había UNA sola ronda de herramientas y la segunda llamada al modelo no recibía "tools".
    # Explorar estructura -> consultar -> responder necesita varias rondas, así que ahora es un bucle con tope
    # (MAX_PASOS). Se eliminaron los CASOS 1, 2 y 3 separados: este bucle los cubre a todos.
    for _ in range(MAX_PASOS):
        # NUEVO (Jonathan, 2026-10-18): antes un error de conexión o de llave salía de la función y Django
        # respondía 500; el usuario solo veía "No pude conectar con el asistente".
        try:
            resp = client.chat.completions.create(
                model=MODELO,                 # MODIFICADO: modelo único y configurable (se eliminó MiMo-V2.6-Pro de respaldo)
                messages=historial,
                tools=herramientas_ia,        # MODIFICADO: se pasan las tools en TODAS las rondas
                tool_choice="auto",
                temperature=0,                # MODIFICADO (v2): 0.2 -> 0, respuestas deterministas para que el modelo no "improvise" cifras
            )
        except Exception as e:
            logger.warning("Fallo la llamada a la IA: %s", e)
            error_ia = True
            break
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
    if not texto_final and not error_ia:
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
    if error_ia:
        es_fallo = True
        texto_final = ("The AI service is not responding right now. Please try again in a moment."
                       if idioma == 'en'
                       else "El servicio de IA no responde en este momento. Intenta de nuevo en un momento.")
    elif not texto_final:
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