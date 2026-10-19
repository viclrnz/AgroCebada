// NUEVO (Jonathan, 2026-10-18): página "Análisis del modelo". Antes el menú llevaba a /analisis
// pero no existía la página y caía en el Dashboard.
import '../App.css'
import { promedio, useParcelas, type Parcela } from '../api'
import { METRICAS, MODELO_VIGENTE, PARCELAS_EVALUADAS, nombreModelo } from '../metricas'

type Grupo = { nombre: string; parcelas: number; promedio: number }

function agrupar(parcelas: Parcela[], clave: (p: Parcela) => string): Grupo[] {
  const grupos = new Map<string, number[]>()
  for (const p of parcelas) {
    grupos.set(clave(p), [...(grupos.get(clave(p)) ?? []), p.rendimiento_estimado_t_ha])
  }
  return [...grupos].map(([nombre, valores]) => ({ nombre, parcelas: valores.length, promedio: promedio(valores) }))
    .sort((a, b) => b.promedio - a.promedio)
}

function Barras({ grupos }: { grupos: Grupo[] }) {
  const maximo = Math.max(...grupos.map((g) => g.promedio), 1)
  return (
    <div className="bar-list">
      {grupos.map((g) => (
        <div className="bar-row" key={g.nombre}>
          <span>{g.nombre} ({g.parcelas})</span>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${(g.promedio / maximo) * 100}%` }} /></div>
          <b>{g.promedio.toFixed(2)} t/ha</b>
        </div>
      ))}
    </div>
  )
}

function Analisis() {
  const { parcelas, cargando, error } = useParcelas()
  const aviso = cargando ? 'Cargando...' : error

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">MODELO DE RENDIMIENTO</div>
          <h1>Análisis del modelo</h1>
          <p>Compara los modelos probados y revisa el rendimiento por zona.</p>
        </div>
        <div className="date-chip">Modelo activo: {nombreModelo(MODELO_VIGENTE)}</div>
      </div>

      <section className="panel table-panel" style={{ marginBottom: 20, paddingBottom: 21 }}>
        <div className="panel-heading">
          <div>
            <h2>Comparación de modelos</h2>
            <p>Error en validación cruzada contra el rendimiento medido en las {PARCELAS_EVALUADAS} parcelas de entrenamiento.</p>
          </div>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Modelo</th>
                <th>Variables</th>
                <th>RMSE (t/ha)</th>
                <th>MAE (t/ha)</th>
                <th>R²</th>
              </tr>
            </thead>
            <tbody>
              {METRICAS.map((m) => (
                <tr key={m.modelo} className={m.modelo === MODELO_VIGENTE ? 'model-active-row' : ''}>
                  <td>{m.nombre}{m.modelo === MODELO_VIGENTE ? ' (activo)' : ''}</td>
                  <td>{m.variables}</td>
                  <td>{m.rmse.toFixed(3)}</td>
                  <td>{m.mae.toFixed(3)}</td>
                  <td>{m.r2.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="data-note">
          RMSE y MAE: error promedio en toneladas por hectárea (menos es mejor). R²: qué tanto explica el
          modelo las diferencias entre parcelas (1 es perfecto). Se eligió el ensamble de Random Forest y SVR con 16 variables porque tiene el menor error.
        </p>
      </section>

      <section className="overview-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Rendimiento promedio por estado</h2>
              <p>{aviso || 'Incluye parcelas observadas y estimadas.'}</p>
            </div>
          </div>
          <Barras grupos={agrupar(parcelas, (p) => p.estado)} />
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Observado contra estimado</h2>
              <p>{aviso || 'Promedio de cada grupo de parcelas.'}</p>
            </div>
          </div>
          <Barras grupos={agrupar(parcelas, (p) => (p.origen === 'observado' ? 'Observado' : 'Estimado'))} />
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Rendimiento promedio por municipio</h2>
            <p>{aviso || 'Ordenado de mayor a menor.'}</p>
          </div>
        </div>
        <Barras grupos={agrupar(parcelas, (p) => p.municipio)} />
      </section>
    </section>
  )
}

export default Analisis
