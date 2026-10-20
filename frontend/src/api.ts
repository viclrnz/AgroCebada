// NUEVO (Jonathan, 2026-10-18): llamadas a la API de parcelas de Django (parcelas/views.py).
// En desarrollo Vite reenvía /api a http://localhost:8000 (ver vite.config.ts).
import { useEffect, useState } from 'react'

// Centraliza las peticiones y detecta sesiones vencidas.
export async function apiFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const respuesta = await fetch(input, {
    credentials: 'same-origin',
    ...init,
  })

  if (respuesta.status === 401) {
    window.dispatchEvent(new Event('agrocebada:unauthorized'))
  }

  return respuesta
}

export type Parcela = {
  id_poligono: string
  estado: string
  municipio: string
  conjunto: 'ENTRENAMIENTO' | 'PREDICCION'
  superficie_ha: number
  latitud: number
  longitud: number
  rendimiento_estimado_t_ha: number
  origen: 'observado' | 'modelo'
  modelo: string | null
}

export async function obtenerParcelas(): Promise<Parcela[]> {
  const respuesta = await apiFetch('/api/parcelas/')
  if (!respuesta.ok) throw new Error(`Error HTTP ${respuesta.status}`)
  const datos: { total: number; parcelas: Parcela[] } = await respuesta.json()
  return datos.parcelas
}

export async function obtenerParcela(id: string): Promise<Parcela | null> {
  const respuesta = await apiFetch(`/api/parcelas/${encodeURIComponent(id)}/`)
  if (respuesta.status === 404) return null
  if (!respuesta.ok) throw new Error(`Error HTTP ${respuesta.status}`)
  return respuesta.json()
}

// Carga todas las parcelas una vez. Lo usan Dashboard, Parcelas, Mapa y Análisis.
export function useParcelas(): { parcelas: Parcela[]; cargando: boolean; error: string } {
  const [parcelas, setParcelas] = useState<Parcela[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    obtenerParcelas()
      .then(setParcelas)
      .catch(() => setError('No se pudieron cargar las parcelas. Revisa que Django esté corriendo.'))
      .finally(() => setCargando(false))
  }, [])

  return { parcelas, cargando, error }
}

export function promedio(valores: number[]): number {
  return valores.length ? valores.reduce((a, b) => a + b, 0) / valores.length : 0
}

// Texto que se muestra en la columna "Estado del dato".
export function etiquetaOrigen(parcela: Parcela): string {
  return parcela.origen === 'observado' ? 'Observado' : 'Estimado'
}

// Carga una parcela por id. Lo usan las páginas de detalle y predicción.
// 'aviso' trae el texto a mostrar mientras no hay datos (cargando, no existe o error).
type CargaParcela =
  | { estado: 'cargando' }
  | { estado: 'ok'; parcela: Parcela }
  | { estado: 'no-existe' }
  | { estado: 'error' }

export function useParcela(id: string | undefined): { parcela: Parcela | null; aviso: string } {
  const [carga, setCarga] = useState<CargaParcela>({ estado: 'cargando' })

  useEffect(() => {
    if (!id) return
    obtenerParcela(id)
      .then((parcela) => setCarga(parcela ? { estado: 'ok', parcela } : { estado: 'no-existe' }))
      .catch(() => setCarga({ estado: 'error' }))
  }, [id])

  if (carga.estado === 'ok') return { parcela: carga.parcela, aviso: '' }
  const avisos = { cargando: 'Cargando...', 'no-existe': 'Esta parcela no existe', error: 'No se pudo conectar con la API' }
  return { parcela: null, aviso: avisos[carga.estado] }
}
