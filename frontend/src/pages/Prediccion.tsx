
import { useNavigate, useParams } from 'react-router-dom'
import '../App.css'
import { useParcela } from '../api'
import { nombreModelo } from '../metricas'
import { CloudSun, Droplets, Sprout, Mountain } from 'lucide-react'

const gruposVariables = [
  {
    titulo: 'Clima',
    descripcion: 'Condiciones atmosféricas durante las etapas críticas del cultivo.',
    variables: [
      {
        nombre: 'era5_vpd_medio_flor_kpa',
        etiqueta: 'Déficit de presión de vapor en floración',
        unidad: 'kPa',
      },
      {
        nombre: 'era5_sm2_flor',
        etiqueta: 'Humedad del suelo en floración',
        unidad: 'Por confirmar',
      },
      {
        nombre: 'era5_vpd_medio_llen_kpa',
        etiqueta: 'Déficit de presión de vapor durante el llenado',
        unidad: 'kPa',
      },
    ],
  },
  {
    titulo: 'Agua',
    descripcion: 'Disponibilidad y balance hídrico del cultivo.',
    variables: [
      { nombre: 'ac_lluvia_ciclo_mm', etiqueta: 'Lluvia acumulada del ciclo', unidad: 'mm' },
      {
        nombre: 'ac_lluvia_ciclo_anom_rel',
        etiqueta: 'Anomalía relativa de la lluvia del ciclo',
        unidad: 'Adimensional',
      },
      { nombre: 'ac_gdd_ciclo', etiqueta: 'Grados-día acumulados del ciclo', unidad: 'Por confirmar' },
      {
        nombre: 'ac_lluvia_max_dia_ciclo_mm',
        etiqueta: 'Lluvia máxima diaria del ciclo',
        unidad: 'mm',
      },
      { nombre: 'ac_balance_flor_mm', etiqueta: 'Balance hídrico en floración', unidad: 'mm' },
      { nombre: 'ac_balance_ciclo_mm', etiqueta: 'Balance hídrico del ciclo', unidad: 'mm' },
    ],
  },
  {
    titulo: 'Fenología',
    descripcion: 'Indicadores del desarrollo y duración del ciclo de cultivo.',
    variables: [
      {
        nombre: 'pl_eos50_doy',
        etiqueta: 'Día del año en que el NDVI cae al 50 % tras su pico',
        unidad: 'Día del año',
      },
      { nombre: 'pl_ndvi_int_abr_oct', etiqueta: 'NDVI integrado de abril a octubre', unidad: 'Adimensional' },
      { nombre: 'pl_lai_int_ciclo', etiqueta: 'Índice de área foliar integrado del ciclo', unidad: 'Adimensional' },
    ],
  },
  {
    titulo: 'Suelo y topografía',
    descripcion: 'Características del terreno relacionadas con el rendimiento.',
    variables: [
      { nombre: 'soil_arcilla_pct', etiqueta: 'Contenido de arcilla del suelo', unidad: '%' },
      { nombre: 'pend_media_grados', etiqueta: 'Pendiente media del terreno', unidad: '°' },
      { nombre: 'elev_media_m', etiqueta: 'Elevación media del terreno', unidad: 'm' },
      { nombre: 'area_ha_geod', etiqueta: 'Superficie de la parcela', unidad: 'ha' },
    ],
  },
]

function Prediccion() {
  const navigate = useNavigate()
  const { id } = useParams()
  const { parcela: p, aviso } = useParcela(id)

  const esEntrenamiento = p?.origen === 'observado'
  const conjunto = p
    ? esEntrenamiento
      ? 'Entrenamiento'
      : 'Predicción'
    : '—'

  const rendimiento = p?.rendimiento_estimado_t_ha

  const iconosVariables = {
  Clima: CloudSun,
  Agua: Droplets,
  Fenología: Sprout,
  'Suelo y topografía': Mountain,
}

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">ESTIMACIÓN AGRÍCOLA</div>
          <h1>Información de la parcela</h1>
          <p>
            Consulta el rendimiento y las variables seleccionadas para el
            análisis agrícola.
          </p>
        </div>
        <div className="date-chip">Ciclo abril–octubre de 2025</div>
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
          <div className="kpi-value">#{p?.id_poligono ?? id ?? '—'}</div>
          <div className="kpi-foot">
            {p ? `${p.municipio}, ${p.estado}` : aviso}
          </div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">
            {p
              ? esEntrenamiento
                ? 'Rendimiento reportado'
                : 'Rendimiento predicho por el modelo'
              : 'Rendimiento'}
          </div>
          <div className="kpi-value">
            {rendimiento != null && Number.isFinite(Number(rendimiento))
              ? Number(rendimiento).toFixed(2)
              : '—'}{' '}
            <small>t/ha</small>
          </div>
          <div className="kpi-foot">
            {p
              ? esEntrenamiento
                ? 'Dato reportado para el ciclo de referencia'
                : `Estimación del modelo ${p.modelo ? nombreModelo(p.modelo) : 'disponible'}`
              : aviso}
          </div>
        </article>

        <article className="kpi-card">
          <div className="kpi-label">Conjunto</div>
          <div className="kpi-value model-value">{conjunto}</div>
          <div className="kpi-foot">
            {p
              ? esEntrenamiento
                ? 'Rendimiento previamente reportado'
                : 'Rendimiento generado por el modelo'
              : 'Consultando información'}
          </div>
        </article>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-heading">
          <div>
            <h2>Información de la parcela</h2>
            <p>
              Las 16 variables predictoras del Modelo 5 se organizan en
              cuatro grupos. Sus valores por parcela se mostrarán cuando estén
              disponibles en la API.
            </p>
          </div>
        </div>

        <div className="variable-summary">
          <p><strong>ID de parcela:</strong> {p?.id_poligono ?? id ?? '—'}</p>
          <p><strong>Estado:</strong> {p?.estado ?? '—'}</p>
          <p><strong>Municipio:</strong> {p?.municipio ?? '—'}</p>
          <p>
            <strong>Superficie:</strong>{' '}
            {p?.superficie_ha != null ? `${p.superficie_ha} ha` : '—'}
          </p>
          <p><strong>Periodo de referencia:</strong> abril–octubre de 2025</p>
        </div>

        <div className="variables-grid">
          {gruposVariables.map((grupo) => {
            return (
              <article className="variable-group" key={grupo.titulo}>
                <div className="variable-group-heading">
                  <div
                    className={`variable-icon variable-icon-${
                      grupo.titulo === 'Suelo y topografía'
                        ? 'suelo'
                        : grupo.titulo.toLowerCase()
                    }`}
                  >
                    {(() => {
                      const Icono = iconosVariables[
                        grupo.titulo as keyof typeof iconosVariables
                      ]

                      return <Icono size={23} strokeWidth={1.7} />
                    })()}
                  </div>

                  <div className="variable-group-title">
                    <h3>{grupo.titulo}</h3>
                    <p>{grupo.descripcion}</p>
                  </div>
                </div>

                <ul>
                  {grupo.variables.map((variable) => (
                    <li key={variable.nombre}>
                      <strong>{variable.etiqueta}</strong>
                      <span>{variable.nombre}</span>
                      <small>Unidad: {variable.unidad}</small>
                    </li>
                  ))}
                </ul>
              </article>
            )
          })}
        </div>


        <p className="kpi-foot" style={{ marginTop: 20 }}>
          El rendimiento reportado corresponde al ciclo de producción de
          abril a octubre de 2025. Las variables enumeradas son las
          seleccionadas para el modelo; esta pantalla aún no muestra sus
          valores individuales.
        </p>

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
