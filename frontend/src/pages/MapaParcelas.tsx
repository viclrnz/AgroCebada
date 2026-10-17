import '../App.css'

function MapaParcelas() {
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

        <div className="date-chip">Vista ilustrativa</div>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Distribución geográfica</h2>
            <p>Vista de demostración; todavía no contiene coordenadas reales.</p>
          </div>
        </div>

        <div className="map-placeholder">
          <div className="map-grid" />
          <div className="map-river river-one" />
          <div className="map-river river-two" />

          <span className="map-label label-one">HIDALGO</span>
          <span className="map-label label-two">TLAXCALA</span>
          <span className="map-label label-three">PUEBLA</span>

          <span className="map-pin pin-one" />
          <span className="map-pin pin-two" />
          <span className="map-pin pin-three" />
          <span className="map-pin pin-four" />
          <span className="map-pin pin-five" />

          <div className="map-legend">
            <span />
            Parcelas ilustrativas
          </div>

          <span className="map-disclaimer">Sin coordenadas reales</span>
        </div>
      </section>
    </section>
  )
}

export default MapaParcelas