// NUEVO (Jonathan, 2026-10-18): métricas de los modelos de rendimiento.
// Calculadas con data/predictions/comparacion_modelos_rendimiento.csv del repo AgroCebada_Datos,
// comparando el rendimiento observado contra la predicción en las 138 parcelas de ENTRENAMIENTO.
// No vienen de la base de datos: si Modelado entrega nuevas predicciones, hay que recalcularlas.

export type MetricasModelo = {
  modelo: string
  nombre: string
  variables: number
  rmse: number
  mae: number
  r2: number
}

export const MODELO_VIGENTE = 'svr_12vars'
export const PARCELAS_EVALUADAS = 138

export const METRICAS: MetricasModelo[] = [
  { modelo: 'svr_12vars', nombre: 'SVR', variables: 12, rmse: 0.531, mae: 0.386, r2: 0.607 },
  { modelo: 'rf_12vars', nombre: 'Random Forest', variables: 12, rmse: 0.558, mae: 0.431, r2: 0.567 },
  { modelo: 'rf_50vars', nombre: 'Random Forest', variables: 50, rmse: 0.58, mae: 0.452, r2: 0.533 },
]
