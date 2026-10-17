import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import MapaParcelas from './pages/MapaParcelas'
import Parcelas from './pages/Parcelas'
import DetalleParcela from './pages/DetalleParcela'
import Prediccion from './pages/Prediccion'
import Chatbot from './Chatbot'
import './App.css'

const navigation = [
  { label: 'Dashboard', icon: '▦', path: '/', active: false },
  { label: 'Mapa de parcelas', icon: '⌖', path: '/mapa', active: false },
  { label: 'Parcelas', icon: '▤', path: '/parcelas', active: false },
  { label: 'Análisis del modelo', icon: '⌁', path: '/analisis', active: false },
]

const parcels = [
  { id: '001', location: 'Hidalgo', municipality: 'Municipio A', area: '4.2 ha', yield: '3.85 t/ha', status: 'Estimado' },
  { id: '002', location: 'Tlaxcala', municipality: 'Municipio B', area: '2.8 ha', yield: '4.12 t/ha', status: 'Estimado' },
  { id: '003', location: 'Puebla', municipality: 'Municipio C', area: '5.1 ha', yield: '—', status: 'Pendiente' },
]

function App() {
  const location = useLocation()
  const navigate = useNavigate()

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
          <span className="breadcrumb">AgroCebada <span>/</span> Dashboard</span>
          <div className="user-profile">
            <div className="user-avatar">SD</div>
            <div>
              <strong>SocieData</strong>
              <span>Equipo de análisis</span>
            </div>
          </div>
        </header>

        {location.pathname.startsWith('/prediccion/') ? (
          <Prediccion />
        ) : /^\/parcelas\/[^/]+\/?$/.test(location.pathname) ? (
          <DetalleParcela />
        ) : location.pathname === '/mapa' ? (
          <MapaParcelas />
        ) : location.pathname === '/parcelas' ? (
          <Parcelas />
        ) : (

        <div className="page-content">
          <section className="page-heading">
            <div>
              <div className="eyebrow">PANEL GENERAL</div>
              <h1>Dashboard</h1>
              <p>Resumen del rendimiento de las parcelas de cebada.</p>
            </div>
            <div className="date-chip">
              <span className="date-icon">◷</span>
              Vista general
            </div>
          </section>

          <section className="kpi-grid">
            <article className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Parcelas analizadas</span>
                <span className="kpi-icon olive">▦</span>
              </div>
              <div className="kpi-value">197</div>
              <div className="kpi-foot"><span className="mini-dot" /> Parcelas del conjunto de datos</div>
            </article>

            <article className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Rendimiento estimado</span>
                <span className="kpi-icon sage">↗</span>
              </div>
              <div className="kpi-value">— <small>t/ha</small></div>
              <div className="kpi-foot">Pendiente de conectar el modelo</div>
            </article>

            <article className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Modelo activo</span>
                <span className="kpi-icon brown">⌘</span>
              </div>
              <div className="kpi-value model-value">Por integrar</div>
              <div className="kpi-foot"><span className="status-pill">En desarrollo</span></div>
            </article>
          </section>

          <section className="overview-grid">
            <article className="panel map-panel">
              <div className="panel-heading">
                <div>
                  <h2>Mapa de parcelas</h2>
                  <p>Distribución geográfica de las parcelas.</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => navigate('/mapa')}
                >
                  Explorar mapa ↗
                </button>
              </div>
              <div className="map-placeholder">
                <div className="map-grid" />
                <div className="map-river river-one" />
                <div className="map-river river-two" />
                <span className="map-label label-one">HIDALGO</span>
                <span className="map-label label-two">TLAXCALA</span>
                <span className="map-label label-three">PUEBLA</span>
                <span className="map-pin pin-one" />
                <span className="map-pin pin-two" />
                <span className="map-pin pin-three" />
                <span className="map-pin pin-four" />
                <span className="map-pin pin-five" />
                <div className="map-legend"><span /> Parcelas de cebada</div>
                <span className="map-disclaimer">Vista ilustrativa · Sin coordenadas reales</span>
              </div>
            </article>

            <article className="panel metrics-panel">
              <div className="panel-heading">
                <div>
                  <h2>Desempeño del modelo</h2>
                  <p>Métricas de evaluación</p>
                </div>
                <span className="metric-symbol">⌁</span>
              </div>
              <div className="metric-list">
                <div className="metric-row">
                  <div><strong>RMSE</strong><span>Error cuadrático medio</span></div>
                  <b>—</b>
                </div>
                <div className="metric-row">
                  <div><strong>MAE</strong><span>Error absoluto medio</span></div>
                  <b>—</b>
                </div>
                <div className="metric-row">
                  <div><strong>R²</strong><span>Coeficiente de determinación</span></div>
                  <b>—</b>
                </div>
              </div>
              <div className="model-footer">
                <span>Versión del modelo</span>
                <strong>Pendiente de integración</strong>
              </div>
              <p className="data-note">Las métricas se mostrarán al conectar el modelo validado.</p>
            </article>
          </section>

          <section className="panel table-panel">
            <div className="panel-heading">
              <div>
                <h2>Parcelas recientes</h2>
                <p>Vista rápida de parcelas del conjunto de datos.</p>
              </div>
              <button
                className="text-button"
                onClick={() => navigate('/parcelas')}
              >
                Ver todas →
              </button>
            </div>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Estado</th>
                    <th>Municipio</th>
                    <th>Área</th>
                    <th>Rendimiento</th>
                    <th>Estado del dato</th>
                  </tr>
                </thead>
                <tbody>
                  {parcels.map((parcel) => (
                    <tr key={parcel.id}>
                      <td><span className="parcel-id">#{parcel.id}</span></td>
                      <td>{parcel.location}</td>
                      <td>{parcel.municipality}</td>
                      <td>{parcel.area}</td>
                      <td className="yield-value">{parcel.yield}</td>
                      <td>
                        <span className={`table-status ${parcel.status === 'Estimado' ? 'estimated' : 'pending'}`}>
                          <span /> {parcel.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="table-footer">Datos ilustrativos para el prototipo · Se conectará el conjunto real.</div>
          </section>

          <footer className="page-footer">
            <span>AgroCebada <span className="footer-separator">/</span> SocieData</span>
            <span>Plataforma de análisis de rendimiento agrícola</span>
          </footer>
        </div>
        )}
      </main>
      
      <Chatbot />
    </div>
  )
}

export default App
