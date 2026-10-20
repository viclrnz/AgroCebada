import { useEffect, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import AppRoutes from './AppRoutes'
import Chatbot from './Chatbot'
import './App.css'
import { SesionContext, SESION_INICIAL, type Sesion } from './SesionContext'

const navigation = [
  { label: 'Dashboard', icon: '▦', path: '/' },
  { label: 'Mapa de parcelas', icon: '⌖', path: '/mapa' },
  { label: 'Parcelas', icon: '▤', path: '/parcelas' },
  { label: 'Análisis del modelo', icon: '⌁', path: '/analisis' },
]

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sesion, setSesion] = useState<Sesion>(SESION_INICIAL)
  const [cerrandoSesion, setCerrandoSesion] = useState(false)

  const enPaginaDeAcceso =
    location.pathname === '/login' || location.pathname === '/registro'

  // Consulta la sesión real en Django al cargar y cada vez que se entra o se sale
  // de /login o /registro (así el encabezado se actualiza después de iniciar sesión).
  useEffect(() => {
    let cancelado = false

    fetch('/api/auth/me/', { credentials: 'same-origin', cache: 'no-store' })
      .then((respuesta) => (respuesta.ok ? respuesta.json() : null))
      .then((datos) => {
        if (cancelado) return
        setSesion({
          autenticado: datos?.autenticado === true,
          usuario: datos?.usuario ?? '',
          esAdministrador: datos?.es_administrador === true,
          cargando: false,
        })
      })
      .catch(() => {
        if (!cancelado) setSesion({ ...SESION_INICIAL, cargando: false })
      })

    return () => {
      cancelado = true
    }
  }, [enPaginaDeAcceso])

  async function cerrarSesion() {
    setCerrandoSesion(true)

    try {
      const csrfRespuesta = await fetch('/api/csrf/', {
        credentials: 'same-origin',
      })

      const csrfDatos = csrfRespuesta.ok
        ? await csrfRespuesta.json()
        : null

      const respuesta = await fetch('/api/auth/logout/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfDatos?.csrfToken
            ? { 'X-CSRFToken': csrfDatos.csrfToken }
            : {}),
        },
        body: JSON.stringify({}),
      })

      if (!respuesta.ok) {
        throw new Error('No se pudo cerrar la sesión.')
      }

      setSesion({ ...SESION_INICIAL, cargando: false })
      navigate('/', { replace: true })
    } catch {
      window.alert('No se pudo cerrar la sesión. Inténtalo de nuevo.')
    } finally {
      setCerrandoSesion(false)
    }
  }

  // Login y registro son páginas opcionales, no requisitos para entrar.
  if (enPaginaDeAcceso) {
    return (
      <SesionContext.Provider value={sesion}>
        <AppRoutes />
      </SesionContext.Provider>
    )
  }

  const ruta = location.pathname.startsWith('/prediccion')
    ? '/parcelas'
    : location.pathname

  const seccion =
    [...navigation]
      .reverse()
      .find((item) =>
        item.path === '/'
          ? ruta === '/'
          : ruta.startsWith(item.path),
      )?.label ?? 'Dashboard'

  const autenticado = sesion.autenticado
  const iniciales = autenticado
    ? sesion.usuario.slice(0, 2).toUpperCase()
    : 'SD'

  return (
    <SesionContext.Provider value={sesion}>
      <div className="app-shell">
        <aside className="sidebar">
          <div className="brand">
            <img src="/LogoSocieData.svg" alt="Logo de SocieData" />
          </div>

          <div className="sidebar-label">MENÚ PRINCIPAL</div>

          <nav className="navigation">
            {navigation.map((item) => (
              <NavLink
                to={item.path}
                key={item.label}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'active' : ''}`
                }
              >
                {({ isActive }) => (
                  <>
                    <span className="nav-icon">{item.icon}</span>
                    <span>{item.label}</span>
                    {isActive && <span className="active-dot" />}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-bottom">
            <div className="status-indicator" />
            <div>
              <strong>AgroCebada</strong>
              <span>Plataforma de análisis</span>
            </div>
          </div>
        </aside>

        <main className="main-content">
          <header className="topbar">
            <span className="breadcrumb">
              AgroCebada <span>/</span> {seccion}
            </span>

            <div className="user-profile">
              <div className="user-avatar">{iniciales}</div>
              <div>
                <strong>
                  {autenticado ? sesion.usuario : 'SocieData'}
                </strong>
                <span>
                  {autenticado
                    ? sesion.esAdministrador
                      ? 'Administrador · Sesión iniciada'
                      : 'Sesión iniciada'
                    : 'Consulta pública'}
                </span>
              </div>

              {autenticado && (
                <button
                  type="button"
                  onClick={cerrarSesion}
                  disabled={cerrandoSesion}
                >
                  {cerrandoSesion ? 'Cerrando...' : 'Cerrar sesión'}
                </button>
              )}
            </div>
          </header>

          <AppRoutes />
        </main>

        <Chatbot />
      </div>
    </SesionContext.Provider>
  )
}

export default App