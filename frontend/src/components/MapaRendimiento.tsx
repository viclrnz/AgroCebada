// NUEVO (Jonathan, 2026-10-18): mapa real de las parcelas con Leaflet (react-leaflet).
// Cada punto es el centroide de la parcela; el color indica el rendimiento.
// Lo usan el Dashboard (vista chica) y la página Mapa de parcelas (vista grande).
import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import type { Parcela } from '../api'

// Rangos de rendimiento (t/ha) para la leyenda: bajo, medio y alto.
const RANGOS = [
  { hasta: 3.5, color: '#c98b4f', texto: 'Menos de 3.5 t/ha' },
  { hasta: 4.5, color: '#b5b36a', texto: '3.5 a 4.5 t/ha' },
  { hasta: Infinity, color: '#4f6b3a', texto: 'Más de 4.5 t/ha' },
]

function colorRendimiento(valor: number): string {
  return RANGOS.find((rango) => valor < rango.hasta)!.color
}

type Props = {
  parcelas: Parcela[]
  alto: number
}

export default function MapaRendimiento({ parcelas, alto }: Props) {
  const navigate = useNavigate()

  if (parcelas.length === 0) {
    return <div className="map-placeholder" style={{ height: alto }} />
  }

  const limites = parcelas.map((p) => [p.latitud, p.longitud] as [number, number])

  return (
    <div className="map-real" style={{ height: alto }}>
      <MapContainer bounds={limites} boundsOptions={{ padding: [20, 20] }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {parcelas.map((p) => (
          <CircleMarker
            key={p.id_poligono}
            center={[p.latitud, p.longitud]}
            radius={6}
            pathOptions={{
              color: '#ffffff',
              weight: 1,
              fillColor: colorRendimiento(p.rendimiento_estimado_t_ha),
              // Las parcelas medidas en campo van más opacas que las estimadas por el modelo.
              fillOpacity: p.origen === 'observado' ? 0.95 : 0.6,
            }}
          >
            <Popup>
              <strong>{p.id_poligono}</strong>
              <br />
              {p.municipio}, {p.estado}
              <br />
              {p.rendimiento_estimado_t_ha.toFixed(2)} t/ha ({p.origen === 'observado' ? 'observado' : 'estimado'})
              <br />
              <button className="text-button" onClick={() => navigate(`/parcelas/${p.id_poligono}`)}>
                Ver detalle →
              </button>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}

export function LeyendaMapa() {
  return (
    <div className="map-legend-real">
      {RANGOS.map((rango) => (
        <span key={rango.texto}>
          <i style={{ background: rango.color }} /> {rango.texto}
        </span>
      ))}
    </div>
  )
}
