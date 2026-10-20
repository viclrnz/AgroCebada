# AgroCebada

<p align="center">
  <a href="https://agrocebada-alss.onrender.com/"><img src="https://img.shields.io/badge/Ver%20la%20aplicaci%C3%B3n-en%20l%C3%ADnea-2e7d32?style=for-the-badge" alt="Ver la aplicación en línea"></a>
  <a href="https://github.com/viclrnz/AgroCebada_Datos"><img src="https://img.shields.io/badge/Repositorio-de%20datos-24292e?style=for-the-badge&logo=github" alt="Repositorio de datos"></a>
<a href="https://youtu.be/5i2wEbqDBFk"><img src="https://img.shields.io/badge/Ver%20el%20video-demostrativo-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Ver el video demostrativo"></a>
</p>

> **Aplicación en línea:** [https://agrocebada-alss.onrender.com/](https://agrocebada-alss.onrender.com/)<br>
> **Video demostrativo:** [https://youtu.be/5i2wEbqDBFk](https://youtu.be/5i2wEbqDBFk)<br>
> **Repositorio de datos (ETL, notebooks y modelo):** [https://github.com/viclrnz/AgroCebada_Datos](https://github.com/viclrnz/AgroCebada_Datos)<br>
> La aplicación está en un servidor gratuito: la primera carga puede tardar alrededor de un minuto mientras el servidor despierta.

Plataforma de SocieData para consultar el rendimiento estimado de cebada en 197 parcelas
de Hidalgo, Puebla y Tlaxcala. Los datos los carga el repo AgroCebada_Datos en Supabase
(tabla `rendimientos_estimados`).

## Cómo correrlo en local

1. Copia `.env.example` como `.env` y llena los valores (cada variable está explicada ahí).
   Para trabajar en local pon `DJANGO_DEBUG=True`. El `.env` no se sube a git.
2. Backend (Django), en una terminal:
   ```
   pip install -r requirements.txt
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

## Cuentas y administradores

```
python manage.py migrate
python manage.py crear_grupos        # crea el grupo "Administradores"
python manage.py createsuperuser     # 1 o 2 responsables técnicos
```
Para cada administrador: en el admin, abrir su cuenta, marcar **Es staff** y agregarlo al grupo
**Administradores**. Los registros nuevos aparecen arriba en la lista de usuarios con "Activo: No";
se autorizan con la acción **Autorizar cuentas seleccionadas**.

## Rutas de la API

| Ruta | Qué devuelve |
|---|---|
| `GET /api/parcelas/` | Las 197 parcelas. Filtros opcionales `?estado=Puebla` y `?origen=modelo` u `observado`. |
| `GET /api/parcelas/<id>/` | Una parcela, por ejemplo `/api/parcelas/AGC_003/`. |
| `POST /api/chatbot/` | Mensaje al asistente: `{"texto": "...", "idioma": "es", "sesion_id": 1}`. |
| `GET /api/csrf/` | Deja la cookie CSRF que necesitan todos los POST. |
| `POST /api/auth/register/` | Registro: `{"username", "email", "password", "confirm_password"}`. La cuenta queda inactiva. |
| `POST /api/auth/login/` | `{"username", "password"}`. 403 si la cuenta está pendiente. |
| `GET /api/auth/me/` | `{"autenticado", "usuario", "es_administrador"}`. |
| `POST /api/auth/logout/` | Cierra la sesión. |

`/api/parcelas/` y `/api/chatbot/` exigen sesión iniciada (responden 401 sin ella).

## Producción

```
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn AgroCebada_project.wsgi
```
Con `DJANGO_DEBUG=False` y `python manage.py check --deploy` sin errores.
