import { useState } from 'react'
import '../App.css'
import { useParcelas } from '../api'
import MapaRendimiento, { LeyendaMapa } from '../components/MapaRendimiento'

// MODIFICADO (Jonathan, 2026-10-18): antes era un dibujo ilustrativo sin coordenadas.
// Ahora muestra las 197 parcelas en un mapa real con su rendimiento (centroides del shapefile).
function MapaParcelas() {
  const { parcelas, cargando, error } = useParcelas()
  const [estado, setEstado] = useState('Todos')
  const [origen, setOrigen] = useState('Todos')

  const visibles = parcelas.filter(
    (p) => (estado === 'Todos' || p.estado === estado) && (origen === 'Todos' || p.origen === origen),
  )

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">EXPLORACIÓN GEOGRÁFICA</div>
          <h1>Mapa de parcelas</h1>
          <p>
            Consulta la distribución geográfica de las parcelas productoras de cebada.
          </p>
        </div>

        <div className="date-chip">Datos reales</div>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Distribución geográfica</h2>
            <p>{cargando ? 'Cargando...' : error || `${visibles.length} parcelas en el mapa. Da clic en un punto para ver su detalle.`}</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
          <select
            value={estado}
            onChange={(event) => setEstado(event.target.value)}
            aria-label="Filtrar por estado"
            style={{ padding: 10, border: '1px solid #e8e7de', borderRadius: 8, background: '#fffefa' }}
          >
            <option value="Todos">Todos los estados</option>
            <option value="Hidalgo">Hidalgo</option>
            <option value="Tlaxcala">Tlaxcala</option>
            <option value="Puebla">Puebla</option>
          </select>
          <select
            value={origen}
            onChange={(event) => setOrigen(event.target.value)}
            aria-label="Filtrar por origen"
            style={{ padding: 10, border: '1px solid #e8e7de', borderRadius: 8, background: '#fffefa' }}
          >
            <option value="Todos">Observadas y estimadas</option>
            <option value="observado">Solo observadas</option>
            <option value="modelo">Solo estimadas</option>
          </select>
        </div>

        {/* key: al cambiar el filtro el mapa se vuelve a encuadrar en las parcelas visibles */}
        <MapaRendimiento key={`${estado}-${origen}`} parcelas={visibles} alto={520} />
        <LeyendaMapa />
        <p className="data-note">Puntos opacos: rendimiento medido en campo. Puntos claros: estimado por el modelo.</p>
      </section>
    </section>
  )
}

export default MapaParcelas
