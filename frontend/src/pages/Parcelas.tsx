import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../App.css'

const parcelasDemo = [
  { id: '001', estado: 'Hidalgo', municipio: 'Municipio A', area: '4.2 ha', rendimiento: '3.85 t/ha', status: 'Estimado' },
  { id: '002', estado: 'Tlaxcala', municipio: 'Municipio B', area: '2.8 ha', rendimiento: '4.12 t/ha', status: 'Estimado' },
  { id: '003', estado: 'Puebla', municipio: 'Municipio C', area: '5.1 ha', rendimiento: '—', status: 'Pendiente' },
]

function Parcelas() {
  const navigate = useNavigate()
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState('Todos')

  const parcelasFiltradas = parcelasDemo.filter((parcela) => {
    const coincideBusqueda =
      `${parcela.id} ${parcela.municipio} ${parcela.estado}`
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
        <div className="date-chip">Datos de demostración</div>
      </div>

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Listado de parcelas</h2>
            <p>{parcelasFiltradas.length} resultados de demostración</p>
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
                <th>Estado del dato</th>
              </tr>
            </thead>
            <tbody>
              {parcelasFiltradas.map((parcela) => (
                <tr key={parcela.id}>
                <td>
                <button
                    className="text-button"
                    onClick={() => navigate(`/parcelas/${parcela.id}`)}
                >
                    #{parcela.id}
                </button>
                </td>
                  <td>{parcela.estado}</td>
                  <td>{parcela.municipio}</td>
                  <td>{parcela.area}</td>
                  <td className="yield-value">{parcela.rendimiento}</td>
                  <td>
                    <span className={`table-status ${parcela.status === 'Estimado' ? 'estimated' : 'pending'}`}>
                      <span /> {parcela.status}
                    </span>
                  </td>
                </tr>
              ))}
              {parcelasFiltradas.length === 0 && (
                <tr>
                  <td colSpan={6}>No se encontraron parcelas.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <p className="data-note">
          Datos ficticios para el prototipo. No representan registros reales ni resultados validados del modelo.
        </p>
      </section>
    </section>
  )
}

export default Parcelas