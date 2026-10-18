# AgroCebada
Plataforma de SocieData para consultar el rendimiento estimado de cebada en 197 parcelas
de Hidalgo, Puebla y Tlaxcala. Los datos los carga el repo AgroCebada_Datos en Supabase
(tabla `rendimientos_estimados`).

## Cómo correrlo en local

1. Crea el archivo `.env` en esta carpeta con DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD,
   DB_HOST, DB_PORT, CHATBOT_DB_USER, CHATBOT_DB_PASSWORD, CHATBOT_DB_ALIAS=readonly y
   SINOX_API_KEY. No se sube a git. Opcionales: CHATBOT_MODEL y CHATBOT_API_URL.
2. Backend (Django), en una terminal:
   ```
   pip install -r requirements.txt
   pip install "psycopg[binary]"
   python manage.py migrate
   python manage.py runserver
   ```
3. Frontend (React), en otra terminal (necesita Node.js):
   ```
   cd frontend
   npm install
   npm run dev
   ```
4. Abre http://localhost:5173

## Rutas de la API

| Ruta | Qué devuelve |
|---|---|
| `GET /api/parcelas/` | Las 197 parcelas. Filtros opcionales `?estado=Puebla` y `?origen=modelo` u `observado`. |
| `GET /api/parcelas/<id>/` | Una parcela, por ejemplo `/api/parcelas/AGC_003/`. |
| `POST /api/chatbot/` | Mensaje al asistente: `{"texto": "...", "idioma": "es", "sesion_id": 1}`. |
| `GET /api/csrf/` | Deja la cookie CSRF que necesita el POST del chatbot. |
