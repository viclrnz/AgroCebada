import { useNavigate, useParams } from 'react-router-dom'
import '../App.css'
import { useParcela } from '../api'

// MODIFICADO (Jonathan, 2026-10-18): ahora muestra el rendimiento real de /api/parcelas/<id>/.
// Las variables satelitales y climáticas siguen pendientes.
function Prediccion() {
  const navigate = useNavigate()
  const { id } = useParams()
  const { parcela: p, aviso } = useParcela(id)

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">ESTIMACIÓN AGRÍCOLA</div>
          <h1>Predicción de rendimiento</h1>
          <p>
            Consulta la estimación de rendimiento y la información utilizada
            para generarla.
          </p>
        </div>
        <div className="date-chip">Datos reales</div>
      </div>

      <button
        className="text-button"
        onClick={() => navigate(id ? `/parcelas/${id}` : '/parcelas')}
        style={{ marginBottom: 20 }}
      >
        ← Volver al detalle
      </button>

      <section className="kpi-grid">
        <article className="kpi-card">
          <div className="kpi-label">Parcela analizada</div>
          <div className="kpi-value">#{id ?? '—'}</div>
          <div className="kpi-foot">Identificador de la parcela</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Rendimiento estimado</div>
          <div className="kpi-value">{p ? p.rendimiento_estimado_t_ha.toFixed(2) : '—'} <small>t/ha</small></div>
          <div className="kpi-foot">{p ? (p.origen === 'observado' ? 'Valor medido en campo' : 'Valor predicho') : aviso}</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Estado de la predicción</div>
          <div className="kpi-value model-value">{p ? (p.origen === 'observado' ? 'Observado' : 'Estimado') : '—'}</div>
          <div className="kpi-foot">{p ? (p.modelo ? `Modelo ${p.modelo}` : 'No requiere modelo') : aviso}</div>
        </article>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-heading">
          <div>
            <h2>Información de la estimación</h2>
            <p>
              El rendimiento ya viene del modelo; las variables usadas aún
              están pendientes de integración.
            </p>
          </div>
        </div>

        <p><strong>Parcela:</strong> #{id ?? 'No especificada'}</p>
        <p><strong>Variables satelitales:</strong> Pendientes de integración</p>
        <p><strong>Variables climáticas:</strong> Pendientes de integración</p>
        <p><strong>Fecha de predicción:</strong> Pendiente</p>

        <button
          className="text-button"
          onClick={() => navigate('/analisis')}
          style={{ marginTop: 15 }}
        >
          Consultar análisis del modelo →
        </button>
      </section>
    </section>
  )
}

export default Prediccion