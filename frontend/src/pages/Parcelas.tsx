import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../App.css'
import { etiquetaOrigen, useParcelas } from '../api'

// MODIFICADO (Jonathan, 2026-10-18): antes usaba 3 parcelas de demostración (parcelasDemo).
// Ahora carga las 197 parcelas reales desde /api/parcelas/ (tabla rendimientos_estimados).

function Parcelas() {
  const navigate = useNavigate()
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState('Todos')
  const { parcelas, cargando, error } = useParcelas()

  const parcelasFiltradas = parcelas.filter((parcela) => {
    const coincideBusqueda =
      `${parcela.id_poligono} ${parcela.municipio} ${parcela.estado}`
        .toLowerCase()
        .includes(busqueda.toLowerCase())

    const coincideEstado =
      estado === 'Todos' || parcela.estado === estado

    return coincideBusqueda && coincideEstado
  })

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">GESTIÓN AGRÍCOLA</div>
          <h1>Parcelas</h1>
          <p>Consulta y filtra las parcelas registradas.</p>
        </div>
        <div className="date-chip">Datos reales</div>
      </div>

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Listado de parcelas</h2>
            <p>{cargando ? 'Cargando...' : `${parcelasFiltradas.length} resultados`}</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
          <input
            type="search"
            placeholder="Buscar por ID, estado o municipio..."
            value={busqueda}
            onChange={(event) => setBusqueda(event.target.value)}
            aria-label="Buscar parcela"
            style={{ flex: '1 1 230px', minWidth: 0, padding: 12, border: '1px solid #e8e7de', borderRadius: 8 }}
          />

          <select
            value={estado}
            onChange={(event) => setEstado(event.target.value)}
            aria-label="Filtrar por estado"
            style={{ padding: 12, border: '1px solid #e8e7de', borderRadius: 8, background: '#fffefa' }}
          >
            <option value="Todos">Todos los estados</option>
            <option value="Hidalgo">Hidalgo</option>
            <option value="Tlaxcala">Tlaxcala</option>
            <option value="Puebla">Puebla</option>
          </select>
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
              {parcelasFiltradas.map((parcela) => (
                <tr key={parcela.id_poligono}>
                <td>
                <button
                    className="text-button"
                    onClick={() => navigate(`/parcelas/${parcela.id_poligono}`)}
                >
                    #{parcela.id_poligono}
                </button>
                </td>
                  <td>{parcela.estado}</td>
                  <td>{parcela.municipio}</td>
                  <td>{parcela.superficie_ha.toFixed(2)} ha</td>
                  <td className="yield-value">{parcela.rendimiento_estimado_t_ha.toFixed(2)} t/ha</td>
                  <td>
                    {/* Verde = estimado por el modelo, ocre = medido en campo */}
                    <span className={`table-status ${parcela.origen === 'modelo' ? 'estimated' : 'pending'}`}>
                      <span /> {etiquetaOrigen(parcela)}
                    </span>
                  </td>
                </tr>
              ))}
              {!cargando && parcelasFiltradas.length === 0 && (
                <tr>
                  <td colSpan={6}>{error || 'No se encontraron parcelas.'}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <p className="data-note">
          Observado: rendimiento medido en campo. Estimado: predicción del modelo para parcelas sin medición.
        </p>
      </section>
    </section>
  )
}

export default Parcelas