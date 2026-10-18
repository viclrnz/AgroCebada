import { NavLink, useLocation } from 'react-router-dom'
import AppRoutes from './AppRoutes'
import Chatbot from './Chatbot'
import './App.css'

const navigation = [
  { label: 'Dashboard', icon: '▦', path: '/', active: false },
  { label: 'Mapa de parcelas', icon: '⌖', path: '/mapa', active: false },
  { label: 'Parcelas', icon: '▤', path: '/parcelas', active: false },
  { label: 'Análisis del modelo', icon: '⌁', path: '/analisis', active: false },
]


function App() {
  const location = useLocation()
  // NUEVO (Jonathan, 2026-10-18): la ruta de arriba mostraba siempre "Dashboard".
  const ruta = location.pathname.startsWith('/prediccion') ? '/parcelas' : location.pathname
  const seccion = [...navigation].reverse().find((item) => ruta.startsWith(item.path))?.label ?? 'Dashboard'

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
          <span className="breadcrumb">AgroCebada <span>/</span> {seccion}</span>
          <div className="user-profile">
            <div className="user-avatar">SD</div>
            <div>
              <strong>SocieData</strong>
              <span>Equipo de análisis</span>
            </div>
          </div>
        </header>

        {/* MODIFICADO (Jonathan, 2026-10-18): antes aquí había un if/else por ruta y el Dashboard completo
            con datos de prueba. Ahora cada página está en pages/ y las rutas en AppRoutes.tsx
            (así useParams recibe el id de la parcela y existe la página /analisis). */}
        <AppRoutes />
      </main>
      
      <Chatbot />
    </div>
  )
}

export default App
