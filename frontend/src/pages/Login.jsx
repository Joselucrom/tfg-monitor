import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

export default function Login() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const { login } = useAuth()
  const navigate  = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Login — la API espera form-data no JSON
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)

      const { data } = await client.post('/api/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })

      // Obtener datos del usuario
      const { data: user } = await client.get('/api/usuarios/me', {
        headers: { Authorization: `Bearer ${data.access_token}` }
      })

      login(data.access_token, user)
      navigate('/')
    } catch (err) {
      setError('Credenciales incorrectas. Inténtalo de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 w-full max-w-sm">

        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="3" fill="#3B82F6"/>
              <path d="M9 2v2M9 14v2M2 9h2M14 9h2M4.22 4.22l1.42 1.42M12.36 12.36l1.42 1.42M4.22 13.78l1.42-1.42M12.36 5.64l1.42-1.42"
                stroke="#3B82F6" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="text-base font-medium text-gray-800">TFG Monitor</span>
        </div>

        {/* Título */}
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Iniciar sesión</h1>
        <p className="text-sm text-gray-500 mb-6">Accede a tu panel de monitorización</p>

        {/* Error */}
        {error && (
          <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Correo electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@ejemplo.com"
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-900 text-white py-2 rounded-lg text-sm font-medium
                       hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          ¿Problemas para acceder? Contacta con el administrador
        </p>
      </div>
    </div>
  )
}