
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Link } from 'react-router-dom';
import '../App.css'

function Login() {
  const navigate = useNavigate()
  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function iniciarSesion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setCargando(true)

    try {
      // Obtener el token CSRF de Django.
      const csrfRespuesta = await fetch('/api/csrf/', {
        credentials: 'same-origin',
      })

      if (!csrfRespuesta.ok) {
        throw new Error('No se pudo establecer la protección de seguridad.')
      }

      const csrfDatos = await csrfRespuesta.json()

      // Enviar las credenciales al backend.
      const respuesta = await fetch('/api/auth/login/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfDatos.csrfToken,
        },
        body: JSON.stringify({
          username: usuario,
          password: contrasena,
        }),
      })

      const datos = await respuesta.json()

      if (!respuesta.ok) {
        throw new Error(datos.error || 'No se pudo iniciar sesión.')
      }

      // El backend informa si la cuenta es administradora.
      navigate('/')
    } catch (errorDesconocido) {
      setError(
        errorDesconocido instanceof Error
          ? errorDesconocido.message
          : 'Ocurrió un error al iniciar sesión.'
      )
    } finally {
      setCargando(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="eyebrow">SOCIEDATA · AGROCEBADA</div>
        <h1>Bienvenido</h1>
        <p>Inicia sesión para consultar la plataforma agrícola.</p>

        <form onSubmit={iniciarSesion}>
          <label htmlFor="usuario">Usuario</label>
          <input
            id="usuario"
            name="username"
            autoComplete="username"
            value={usuario}
            onChange={(event) => setUsuario(event.target.value)}
            required
          />

          <label htmlFor="contrasena">Contraseña</label>
          <input
            id="contrasena"
            name="password"
            type="password"
            autoComplete="current-password"
            value={contrasena}
            onChange={(event) => setContrasena(event.target.value)}
            required
          />

          {error && (
            <p role="alert" className="login-error">
              {error}
            </p>
          )}

          <button type="submit" disabled={cargando}>
            {cargando ? 'Conectando…' : 'Iniciar sesión'}
          </button>
        </form>

        
        <p className="login-register-prompt">
            ¿Aún no tienes cuenta?{" "}
            <Link to="/registro" className="login-register-link">
                Regístrate
            </Link>
        </p>


        <p className="login-footer">
          Acceso autorizado a la plataforma AgroCebada.
        </p>
      </section>
    </main>
  )
}

export default Login
