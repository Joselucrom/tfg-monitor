import { useState } from 'react'
import client from '../api/client'

export default function ModalPerfil({ usuario, onClose }) {
  const [vista,           setVista]           = useState('perfil') // 'perfil' | 'password'
  const [passwordActual,  setPasswordActual]  = useState('')
  const [passwordNuevo,   setPasswordNuevo]   = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading,         setLoading]         = useState(false)
  const [error,           setError]           = useState('')
  const [exito,           setExito]           = useState('')

  async function handleCambiarPassword(e) {
    e.preventDefault()
    setError('')
    setExito('')

    if (passwordNuevo !== passwordConfirm) {
      setError('Las contraseñas nuevas no coinciden.')
      return
    }
    if (passwordNuevo.length < 4) {
      setError('La contraseña nueva debe tener al menos 4 caracteres.')
      return
    }

    setLoading(true)
    try {
      await client.post('/api/usuarios/me/password', {
        password_actual: passwordActual,
        password_nuevo:  passwordNuevo,
      })
      setExito('Contraseña actualizada correctamente.')
      setPasswordActual('')
      setPasswordNuevo('')
      setPasswordConfirm('')
    } catch (err) {
      const msg = err.response?.data?.detail
      setError(typeof msg === 'string' ? msg : 'Error al cambiar la contraseña.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-sm shadow-lg">

        {/* Cabecera */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-medium text-gray-900">Mi perfil</h2>
          <button
            onClick={onClose}
            className="text-xs text-gray-600 hover:text-gray-700 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Avatar y datos */}
        <div className="flex items-center gap-3 mb-5 p-3 bg-gray-50 rounded-lg">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center
                          text-sm font-medium text-blue-700 shrink-0">
            {usuario?.nombre?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{usuario?.nombre}</p>
            <p className="text-xs text-gray-600 truncate">{usuario?.email}</p>
            <span className={`text-xs px-1.5 py-0.5 rounded-full mt-0.5 inline-block ${
              usuario?.rol === 'admin'
                ? 'bg-blue-50 text-blue-700'
                : 'bg-gray-100 text-gray-600'
            }`}>
              {usuario?.rol}
            </span>
          </div>
        </div>

        {/* Toggle perfil / contraseña */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5 mb-4">
          <button
            onClick={() => { setVista('perfil'); setError(''); setExito('') }}
            className={`flex-1 text-xs py-1.5 rounded-md transition-colors ${
              vista === 'perfil'
                ? 'bg-white text-gray-900 shadow-sm font-medium'
                : 'text-gray-700 hover:text-gray-700'
            }`}
          >
            Datos
          </button>
          <button
            onClick={() => { setVista('password'); setError(''); setExito('') }}
            className={`flex-1 text-xs py-1.5 rounded-md transition-colors ${
              vista === 'password'
                ? 'bg-white text-gray-900 shadow-sm font-medium'
                : 'text-gray-700 hover:text-gray-700'
            }`}
          >
            Cambiar contraseña
          </button>
        </div>

        {/* Vista datos */}
        {vista === 'perfil' && (
          <div className="space-y-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-0.5">Nombre</p>
              <p className="text-sm text-gray-800">{usuario?.nombre}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-0.5">Email</p>
              <p className="text-sm text-gray-800">{usuario?.email}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-0.5">Rol</p>
              <p className="text-sm text-gray-800 capitalize">{usuario?.rol}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-0.5">Cuenta creada</p>
              <p className="text-sm text-gray-800">
                {usuario?.created_at
                  ? new Date(usuario.created_at).toLocaleDateString('es-ES', {
                      day: '2-digit', month: 'long', year: 'numeric'
                    })
                  : '—'
                }
              </p>
            </div>
          </div>
        )}

        {/* Vista cambio de contraseña */}
        {vista === 'password' && (
          <form onSubmit={handleCambiarPassword} className="space-y-3">
            {error && (
              <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
            )}
            {exito && (
              <p className="text-xs text-green-700 bg-green-50 px-3 py-2 rounded-lg">{exito}</p>
            )}

            <div>
              <label className="block text-xs text-gray-700 mb-1">Contraseña actual *</label>
              <input
                type="password"
                required
                value={passwordActual}
                onChange={e => setPasswordActual(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-700 mb-1">Nueva contraseña *</label>
              <input
                type="password"
                required
                value={passwordNuevo}
                onChange={e => setPasswordNuevo(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-700 mb-1">Confirmar nueva contraseña *</label>
              <input
                type="password"
                required
                value={passwordConfirm}
                onChange={e => setPasswordConfirm(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-gray-900 text-white rounded-lg text-sm
                         font-medium hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Guardando...' : 'Cambiar contraseña'}
            </button>
          </form>
        )}

      </div>
    </div>
  )
}