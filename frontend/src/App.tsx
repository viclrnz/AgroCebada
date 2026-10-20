
import { useEffect, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import AppRoutes from './AppRoutes'
import Chatbot from './Chatbot'
import './App.css'

const navigation = [
  { label: 'Dashboard', icon: '▦', path: '/' },
  { label: 'Mapa de parcelas', icon: '⌖', path: '/mapa' },
  { label: 'Parcelas', icon: '▤', path: '/parcelas' },
  { label: 'Análisis del modelo', icon: '⌁', path: '/analisis' },
]

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [autenticado, setAutenticado] = useState(false)
  const [cerrandoSesion, setCerrandoSesion] = useState(false)

  // Consultar si existe una sesión de administrador.
  // Si no existe, la aplicación pública sigue funcionando.
  useEffect(() => {
    fetch('/api/auth/me/', { credentials: 'same-origin' })
      .then((respuesta) => {
        if (!respuesta.ok) return null
        return respuesta.json()
      })
      .then((datos) => {
        setAutenticado(datos?.autenticado === true)
      })
      .catch(() => {
        setAutenticado(false)
      })
  }, [])

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

      setAutenticado(false)
      navigate('/', { replace: true })
    } catch {
      window.alert('No se pudo cerrar la sesión. Inténtalo de nuevo.')
    } finally {
      setCerrandoSesion(false)
    }
  }

  // Login y registro son páginas opcionales, no requisitos para entrar.
  if (location.pathname === '/login' || location.pathname === '/registro') {
    return <AppRoutes />
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

  return (
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
            <div className="user-avatar">SD</div>
            <div>
              <strong>
                {autenticado ? 'Administrador' : 'SocieData'}
              </strong>
              <span>
                {autenticado ? 'Sesión iniciada' : 'Consulta pública'}
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
  )
}

export default App
