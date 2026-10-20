
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

function Registro() {
  const [usuario, setUsuario] = useState('')
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [cargando, setCargando] = useState(false)

  async function registrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMensaje('')

    if (contrasena !== confirmar) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setCargando(true)

    try {
      const csrfRespuesta = await fetch('/api/csrf/', {
        credentials: 'same-origin',
      })

      if (!csrfRespuesta.ok) {
        throw new Error('No se pudo establecer la protección de seguridad.')
      }

      const csrfDatos = await csrfRespuesta.json()

      const respuesta = await fetch('/api/auth/register/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfDatos.csrfToken,
        },
        body: JSON.stringify({
          username: usuario.trim(),
          email: correo.trim(),
          password: contrasena,
          confirm_password: confirmar,
        }),
      })

      const datos = await respuesta.json()

      if (!respuesta.ok) {
        throw new Error(datos.error || 'No se pudo completar el registro.')
      }

      setMensaje(
        datos.mensaje ||
          'Tu solicitud se registró. Espera la autorización del equipo.'
      )
      setUsuario('')
      setCorreo('')
      setContrasena('')
      setConfirmar('')
    } catch (errorDesconocido) {
      setError(
        errorDesconocido instanceof Error
          ? errorDesconocido.message
          : 'Ocurrió un error al registrar la cuenta.'
      )
    } finally {
      setCargando(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="eyebrow">SOCIEDATA · AGROCEBADA</div>
        <h1>Crear cuenta</h1>
        <p>
          Registra tus datos para solicitar acceso administrativo a la
          plataforma.
        </p>

        <form onSubmit={registrar}>
          <label htmlFor="registro-usuario">Usuario</label>
          <input
            id="registro-usuario"
            name="username"
            autoComplete="username"
            value={usuario}
            onChange={(event) => setUsuario(event.target.value)}
            required
          />

          <label htmlFor="registro-correo">Correo electrónico</label>
          <input
            id="registro-correo"
            name="email"
            type="email"
            autoComplete="email"
            value={correo}
            onChange={(event) => setCorreo(event.target.value)}
            required
          />

          <label htmlFor="registro-contrasena">Contraseña</label>
          <input
            id="registro-contrasena"
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={10}
            value={contrasena}
            onChange={(event) => setContrasena(event.target.value)}
            required
          />

          <label htmlFor="registro-confirmar">Confirmar contraseña</label>
          <input
            id="registro-confirmar"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            minLength={10}
            value={confirmar}
            onChange={(event) => setConfirmar(event.target.value)}
            required
          />

          {error && (
            <p role="alert" className="login-error">
              {error}
            </p>
          )}

          {mensaje && (
            <p role="status" className="registro-success">
              {mensaje}
            </p>
          )}

          <button type="submit" disabled={cargando}>
            {cargando ? 'Registrando…' : 'Registrarse'}
          </button>
        </form>

        <p className="login-footer">
          ¿Ya tienes una cuenta? <Link to="/login">Inicia sesión</Link>
        </p>

        <p className="login-footer">
          El acceso administrativo requiere autorización del equipo.
        </p>
      </section>
    </main>
  )
}

export default Registro
