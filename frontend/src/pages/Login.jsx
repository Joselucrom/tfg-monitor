import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

export default function Login() {
  const [modo,     setModo]     = useState('login') // 'login' | 'registro'
  const [nombre,   setNombre]   = useState('')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [rol,      setRol]      = useState('operador')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const { login } = useAuth()
  const navigate  = useNavigate()

  function cambiarModo(nuevoModo) {
    setModo(nuevoModo)
    setError('')
    setNombre('')
    setEmail('')
    setPassword('')
    setRol('operador')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (modo === 'login') {
        const form = new URLSearchParams()
        form.append('username', email)
        form.append('password', password)

        const { data } = await client.post('/api/auth/login', form, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        const { data: user } = await client.get('/api/usuarios/me', {
          headers: { Authorization: `Bearer ${data.access_token}` }
        })

        login(data.access_token, user)
        navigate('/')

      } else {
        // Registro
        await client.post('/api/usuarios/', {
          nombre, email, password, rol,
        })
        // Login automático tras registro
        const form = new URLSearchParams()
        form.append('username', email)
        form.append('password', password)

        const { data } = await client.post('/api/auth/login', form, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        const { data: user } = await client.get('/api/usuarios/me', {
          headers: { Authorization: `Bearer ${data.access_token}` }
        })

        login(data.access_token, user)
        navigate('/')
      }

    } catch (err) {
      const msg = err.response?.data?.detail
      if (modo === 'login') {
        setError('Credenciales incorrectas. Inténtalo de nuevo.')
      } else {
        if (typeof msg === 'string') {
          setError(msg)
        } else {
          setError('Error al crear la cuenta. Inténtalo de nuevo.')
        }
      }
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

        {/* Toggle login/registro */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6">
          <button
            type="button"
            onClick={() => cambiarModo('login')}
            className={`flex-1 text-sm py-1.5 rounded-md transition-colors ${
              modo === 'login'
                ? 'bg-white text-gray-900 shadow-sm font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Iniciar sesión
          </button>
          <button
            type="button"
            onClick={() => cambiarModo('registro')}
            className={`flex-1 text-sm py-1.5 rounded-md transition-colors ${
              modo === 'registro'
                ? 'bg-white text-gray-900 shadow-sm font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Crear cuenta
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-4">

          {/* Campo nombre — solo en registro */}
          {modo === 'registro' && (
            <div>
              <label className="block text-xs text-gray-500 mb-1">Nombre *</label>
              <input
                type="text"
                value={nombre}
                onChange={e => setNombre(e.target.value)}
                placeholder="Tu nombre"
                required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Correo electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="usuario@ejemplo.com"
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Campo rol — solo en registro */}
          {modo === 'registro' && (
            <div>
              <label className="block text-xs text-gray-500 mb-1">Rol</label>
              <select
                value={rol}
                onChange={e => setRol(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="operador">Operador</option>
                <option value="admin">Administrador</option>
              </select>
              <p className="text-xs text-gray-400 mt-1">
                El rol Admin solo está disponible si no existe ningún administrador previo.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-900 text-white py-2 rounded-lg text-sm font-medium
                       hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading
              ? (modo === 'login' ? 'Entrando...' : 'Creando cuenta...')
              : (modo === 'login' ? 'Entrar' : 'Crear cuenta')
            }
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          {modo === 'login'
            ? '¿Problemas para acceder? Contacta con el administrador'
            : 'Al crear una cuenta aceptas las condiciones de uso de la plataforma'
          }
        </p>
      </div>
    </div>
  )
}