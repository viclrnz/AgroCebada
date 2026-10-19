// NUEVO (Jonathan, 2026-10-18): métricas de los modelos de rendimiento.
// MODIFICADO (Jonathan, 2026-10-19): modelos nuevos de Modelado; el vigente es el Modelo 5 (ensamble final de 16 variables).
// MODIFICADO (Jonathan, 2026-10-19): nombres oficiales de los modelos.
// Calculadas con data/predictions/comparacion_modelos_rendimiento.csv del repo AgroCebada_Datos,
// comparando el rendimiento observado contra la predicción de validación cruzada en las 138 parcelas de ENTRENAMIENTO.
// No vienen de la base de datos: si Modelado entrega nuevas predicciones, hay que recalcularlas.

export type MetricasModelo = {
  modelo: string
  nombre: string
  corto: string
  variables: number
  rmse: number
  mae: number
  r2: number
}

export const MODELO_VIGENTE = 'ensamble_16vars'
export const PARCELAS_EVALUADAS = 138

// Nombres oficiales de Modelado (Edgardo). `corto` es para espacios reducidos (tarjetas, etiquetas).
// El Modelo 4 (paso intermedio) no aparece porque no tiene predicciones propias.
export const METRICAS: MetricasModelo[] = [
  { modelo: 'ensamble_16vars', nombre: 'Modelo 5: Ensamble Final tras selección de variables SBE (16 variables predictoras)', corto: 'Modelo 5 (final)', variables: 16, rmse: 0.486, mae: 0.374, r2: 0.672 },
  { modelo: 'ensamble_19vars', nombre: 'Modelo 3: Ensamble con Blending: 0.27 Random Forest + 0.73 SVR (19 variables predictoras)', corto: 'Modelo 3', variables: 19, rmse: 0.506, mae: 0.386, r2: 0.644 },
  { modelo: 'svr_19vars', nombre: 'Modelo de prueba: SVR con StandardScaler y kernel RBF (19 variables predictoras)', corto: 'Modelo de prueba (SVR)', variables: 19, rmse: 0.51, mae: 0.39, r2: 0.638 },
  { modelo: 'rf_gridsearch_19vars', nombre: 'Modelo 2: Random Forest con GridSearchCV (19 variables predictoras)', corto: 'Modelo 2', variables: 19, rmse: 0.536, mae: 0.401, r2: 0.601 },
  { modelo: 'rf_19vars', nombre: 'Modelo 1: Random Forest con Permutation Importance Out-of-Fold (OOF) (19 variables predictoras)', corto: 'Modelo 1', variables: 19, rmse: 0.546, mae: 0.416, r2: 0.586 },
  { modelo: 'rf_62vars', nombre: 'Modelo base: Random Forest Original (62 variables predictoras, KFold simple)', corto: 'Modelo base', variables: 62, rmse: 0.575, mae: 0.433, r2: 0.541 },
]

// Nombre oficial para mostrar en pantalla en lugar del identificador interno (p. ej. 'ensamble_16vars').
export function nombreModelo(modelo: string | null | undefined): string {
  const m = METRICAS.find((x) => x.modelo === modelo)
  return m ? m.nombre : (modelo ?? '')
}

// Nombre corto para espacios reducidos.
export function nombreCorto(modelo: string | null | undefined): string {
  const m = METRICAS.find((x) => x.modelo === modelo)
  return m ? m.corto : (modelo ?? '')
}
