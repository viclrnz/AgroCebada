import { useNavigate, useParams } from 'react-router-dom'
import '../App.css'

function Prediccion() {
  const navigate = useNavigate()
  const { id } = useParams()

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
        <div className="date-chip">Vista de demostración</div>
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
          <div className="kpi-value">— <small>t/ha</small></div>
          <div className="kpi-foot">Pendiente de ejecutar el modelo</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Estado de la predicción</div>
          <div className="kpi-value model-value">Pendiente</div>
          <div className="kpi-foot">Modelo aún no conectado</div>
        </article>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-heading">
          <div>
            <h2>Información de la estimación</h2>
            <p>
              Los resultados se mostrarán cuando integremos el modelo de
              aprendizaje automático.
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