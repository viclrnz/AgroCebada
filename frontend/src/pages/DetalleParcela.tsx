import { useNavigate, useParams } from 'react-router-dom'
import '../App.css'

function DetalleParcela() {
  const navigate = useNavigate()
  const { id } = useParams()

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">INFORMACIÓN AGRÍCOLA</div>
          <h1>Detalle de parcela</h1>
          <p>Consulta la información disponible de una parcela.</p>
        </div>

        <div className="date-chip">Datos de demostración</div>
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
          <div className="kpi-foot">ID ilustrativo de la ruta</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Rendimiento</div>
          <div className="kpi-value">— <small>t/ha</small></div>
          <div className="kpi-foot">Dato real pendiente de integración</div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Estado del registro</div>
          <div className="kpi-value model-value">Por verificar</div>
          <div className="kpi-foot">Sin conexión a la base de datos</div>
        </article>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-heading">
          <div>
            <h2>Información de la parcela</h2>
            <p>Los datos reales se mostrarán cuando conectemos la API.</p>
          </div>
        </div>

        <p><strong>ID:</strong> {id ?? 'No especificado'}</p>
        <p><strong>Ubicación:</strong> Pendiente de integración</p>
        <p><strong>Superficie:</strong> Pendiente de integración</p>
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