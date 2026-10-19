// NUEVO (Jonathan, 2026-10-18): el Dashboard vivía dentro de App.tsx con datos de prueba y este archivo
// estaba vacío (por eso fallaba "npm run build"). Ahora está aquí y usa los datos reales de /api/parcelas/.
import { useNavigate } from 'react-router-dom'
import '../App.css'
import { etiquetaOrigen, promedio, useParcelas } from '../api'
import MapaRendimiento, { LeyendaMapa } from '../components/MapaRendimiento'
import { METRICAS, MODELO_VIGENTE, nombreModelo } from '../metricas'

function Dashboard() {
  const navigate = useNavigate()
  const { parcelas, cargando, error } = useParcelas()
  const vigente = METRICAS.find((m) => m.modelo === MODELO_VIGENTE)!
  const rendimientoPromedio = promedio(parcelas.map((p) => p.rendimiento_estimado_t_ha))
  const estimadas = parcelas.filter((p) => p.origen === 'modelo').length

  return (
    <div className="page-content">
      <section className="page-heading">
        <div>
          <div className="eyebrow">PANEL GENERAL</div>
          <h1>Dashboard</h1>
          <p>Resumen del rendimiento de las parcelas de cebada.</p>
        </div>
        <div className="heading-actions">
          <div className="date-chip">
            <span className="date-icon">◷</span>
            Vista general
          </div>

          <button
            type="button"
            className="login-access-button"
            onClick={() => navigate('/login')}
          >
            Iniciar sesión
          </button>
        </div>
      </section>

      <section className="kpi-grid">
        <article className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-label">Parcelas analizadas</span>
            <span className="kpi-icon olive">▦</span>
          </div>
          <div className="kpi-value">{cargando ? '—' : parcelas.length}</div>
          <div className="kpi-foot">
            <span className="mini-dot" /> {error || `${parcelas.length - estimadas} medidas y ${estimadas} estimadas`}
          </div>
        </article>

        <article className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-label">Rendimiento promedio</span>
            <span className="kpi-icon sage">↗</span>
          </div>
          <div className="kpi-value">{cargando ? '—' : rendimientoPromedio.toFixed(2)} <small>t/ha</small></div>
          <div className="kpi-foot">Promedio de las {parcelas.length} parcelas</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-top">
            <span className="kpi-label">Modelo activo</span>
            <span className="kpi-icon brown">⌘</span>
          </div>
          <div className="kpi-value model-value">{vigente.nombre} {vigente.variables} vars</div>
          <div className="kpi-foot"><span className="status-pill">R² {vigente.r2.toFixed(2)}</span></div>
        </article>
      </section>

      <section className="overview-grid">
        <article className="panel map-panel">
          <div className="panel-heading">
            <div>
              <h2>Mapa de parcelas</h2>
              <p>Distribución geográfica de las parcelas.</p>
            </div>
            <button className="text-button" onClick={() => navigate('/mapa')}>
              Explorar mapa ↗
            </button>
          </div>
          <MapaRendimiento parcelas={parcelas} alto={245} />
          <LeyendaMapa />
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
              <b>{vigente.rmse.toFixed(2)} t/ha</b>
            </div>
            <div className="metric-row">
              <div><strong>MAE</strong><span>Error absoluto medio</span></div>
              <b>{vigente.mae.toFixed(2)} t/ha</b>
            </div>
            <div className="metric-row">
              <div><strong>R²</strong><span>Coeficiente de determinación</span></div>
              <b>{vigente.r2.toFixed(2)}</b>
            </div>
          </div>
          <div className="model-footer">
            <span>Versión del modelo</span>
            <strong>{nombreModelo(MODELO_VIGENTE)}</strong>
          </div>
          <button className="text-button" onClick={() => navigate('/analisis')} style={{ marginTop: 12 }}>
            Ver análisis del modelo →
          </button>
        </article>
      </section>

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Parcelas con mayor rendimiento</h2>
            <p>Las 5 parcelas con más toneladas por hectárea.</p>
          </div>
          <button className="text-button" onClick={() => navigate('/parcelas')}>
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
                <th>Origen del dato</th>
              </tr>
            </thead>
            <tbody>
              {[...parcelas]
                .sort((a, b) => b.rendimiento_estimado_t_ha - a.rendimiento_estimado_t_ha)
                .slice(0, 5)
                .map((p) => (
                  <tr key={p.id_poligono}>
                    <td>
                      <button className="text-button" onClick={() => navigate(`/parcelas/${p.id_poligono}`)}>
                        #{p.id_poligono}
                      </button>
                    </td>
                    <td>{p.estado}</td>
                    <td>{p.municipio}</td>
                    <td>{p.superficie_ha.toFixed(2)} ha</td>
                    <td className="yield-value">{p.rendimiento_estimado_t_ha.toFixed(2)} t/ha</td>
                    <td>
                      <span className={`table-status ${p.origen === 'modelo' ? 'estimated' : 'pending'}`}>
                        <span /> {etiquetaOrigen(p)}
                      </span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <div className="table-footer">Datos de la tabla rendimientos_estimados.</div>
      </section>

      <footer className="page-footer">
        <span>AgroCebada <span className="footer-separator">/</span> SocieData</span>
        <span>Plataforma de análisis de rendimiento agrícola</span>
      </footer>
    </div>
  )
}

export default Dashboard
