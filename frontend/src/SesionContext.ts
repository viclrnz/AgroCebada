import { createContext, useContext } from 'react'

export type Sesion = {
  autenticado: boolean
  usuario: string
  esAdministrador: boolean
  cargando: boolean
}

export const SESION_INICIAL: Sesion = {
  autenticado: false,
  usuario: '',
  esAdministrador: false,
  cargando: true,
}

export const SesionContext = createContext<Sesion>(SESION_INICIAL)

export function useSesion() {
  return useContext(SesionContext)
}