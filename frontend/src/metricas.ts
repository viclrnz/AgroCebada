// NUEVO (Jonathan, 2026-10-18): métricas de los modelos de rendimiento.
// MODIFICADO (Jonathan, 2026-10-19): modelos nuevos de Modelado; el vigente es el ensamble RF + SVR de 16 variables.
// Calculadas con data/predictions/comparacion_modelos_rendimiento.csv del repo AgroCebada_Datos,
// comparando el rendimiento observado contra la predicción de validación cruzada en las 138 parcelas de ENTRENAMIENTO.
// No vienen de la base de datos: si Modelado entrega nuevas predicciones, hay que recalcularlas.

export type MetricasModelo = {
  modelo: string
  nombre: string
  variables: number
  rmse: number
  mae: number
  r2: number
}

export const MODELO_VIGENTE = 'ensamble_16vars'
export const PARCELAS_EVALUADAS = 138

export const METRICAS: MetricasModelo[] = [
  { modelo: 'ensamble_16vars', nombre: 'Ensamble RF + SVR', variables: 16, rmse: 0.486, mae: 0.374, r2: 0.672 },
  { modelo: 'ensamble_19vars', nombre: 'Ensamble RF + SVR', variables: 19, rmse: 0.506, mae: 0.386, r2: 0.644 },
  { modelo: 'svr_19vars', nombre: 'SVR', variables: 19, rmse: 0.51, mae: 0.39, r2: 0.638 },
  { modelo: 'rf_gridsearch_19vars', nombre: 'Random Forest optimizado', variables: 19, rmse: 0.536, mae: 0.401, r2: 0.601 },
  { modelo: 'rf_19vars', nombre: 'Random Forest', variables: 19, rmse: 0.546, mae: 0.416, r2: 0.586 },
  { modelo: 'rf_62vars', nombre: 'Random Forest', variables: 62, rmse: 0.575, mae: 0.433, r2: 0.541 },
]

// Nombre legible para mostrar en pantalla en lugar del identificador interno (p. ej. 'ensamble_16vars').
export function nombreModelo(modelo: string | null | undefined): string {
  const m = METRICAS.find((x) => x.modelo === modelo)
  return m ? `${m.nombre} (${m.variables} variables)` : (modelo ?? '')
}
