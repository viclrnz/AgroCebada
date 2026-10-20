import { useNavigate, useParams } from 'react-router-dom'
import '../App.css'
import { etiquetaOrigen, useParcela } from '../api'
import { nombreModelo } from '../metricas'

// MODIFICADO (Jonathan, 2026-10-18): antes mostraba textos "Pendiente de integración".
// Ahora pide la parcela a /api/parcelas/<id>/ y muestra sus datos reales.
function DetalleParcela() {
  const navigate = useNavigate()
  const { id } = useParams()
  const { parcela: p, aviso } = useParcela(id)

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">INFORMACIÓN AGRÍCOLA</div>
          <h1>Detalle de parcela</h1>
          <p>Consulta la información disponible de una parcela.</p>
        </div>

        <div className="date-chip">Datos reales</div>
      </div>

      <button
        className="text-button"
        onClick={() => navigate('/parcelas')}
        style={{ marginBottom: 20 }}
      >
        ← Volver al listado
      </button>

      <section className="kpi-grid">
        <article className="kpi-card">
          <div className="kpi-label">Identificador</div>
          <div className="kpi-value">#{id ?? 'Sin seleccionar'}</div>
          <div className="kpi-foot">{p ? `${p.municipio}, ${p.estado}` : aviso}</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Rendimiento</div>
          <div className="kpi-value">{p ? p.rendimiento_estimado_t_ha.toFixed(2) : '—'} <small>t/ha</small></div>
          <div className="kpi-foot">{p ? (p.origen === 'observado' ? 'Medido en campo' : `Estimado con ${nombreModelo(p.modelo)}`) : aviso}</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Origen del dato</div>
          <div className="kpi-value model-value">{p ? etiquetaOrigen(p) : '—'}</div>
          <div className="kpi-foot">{p ? `Conjunto ${p.conjunto}` : aviso}</div>
        </article>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-heading">
          <div>
            <h2>Información de la parcela</h2>
            <p>Datos de la tabla rendimientos_estimados.</p>
          </div>
        </div>

        <p><strong>ID:</strong> {id ?? 'No especificado'}</p>
        <p><strong>Ubicación:</strong> {p ? `${p.municipio}, ${p.estado} (${p.latitud.toFixed(5)}, ${p.longitud.toFixed(5)})` : aviso}</p>
        <p><strong>Superficie:</strong> {p ? `${p.superficie_ha.toFixed(2)} ha` : aviso}</p>
        <p><strong>Variables ambientales:</strong> Pendientes de integración</p>

        <button
          className="text-button"
          onClick={() => navigate(`/prediccion/${id ?? ''}`)}
          style={{ marginTop: 15 }}
        >
          Consultar predicción →
        </button>
      </section>
    </section>
  )
}

export default DetalleParcela