import { Navigate, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import MapaParcelas from './pages/MapaParcelas'
import Parcelas from './pages/Parcelas'
import DetalleParcela from './pages/DetalleParcela'
import Prediccion from './pages/Prediccion'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/mapa" element={<MapaParcelas />} />
      <Route path="/parcelas" element={<Parcelas />} />
      <Route path="/parcelas/:id" element={<DetalleParcela />} />
      <Route path="/prediccion/:id" element={<Prediccion />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default AppRoutes