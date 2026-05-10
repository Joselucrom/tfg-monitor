import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Sistemas from './pages/Sistemas'
import Alertas from './pages/Alertas'
import Reglas from './pages/Reglas'
import Eventos from './pages/Eventos'
import ServiciosWeb from './pages/ServiciosWeb'
import Admin from './pages/Admin'
import { AuthProvider, useAuth } from './context/AuthContext'

function PrivateRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  const { token, user } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (user?.rol !== 'admin') return <Navigate to="/" replace />
  return children
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login"    element={<Login />} />
          <Route path="/"         element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/sistemas" element={<PrivateRoute><Sistemas /></PrivateRoute>} />
          <Route path="/servicios"element={<PrivateRoute><ServiciosWeb /></PrivateRoute>} />
          <Route path="/alertas"  element={<PrivateRoute><Alertas /></PrivateRoute>} />
          <Route path="/alertas/:id" element={<PrivateRoute><Alertas /></PrivateRoute>} />
          <Route path="/reglas"   element={<PrivateRoute><Reglas /></PrivateRoute>} />
          <Route path="/eventos"  element={<PrivateRoute><Eventos /></PrivateRoute>} />
          <Route path="/admin"    element={<AdminRoute><Admin /></AdminRoute>} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App