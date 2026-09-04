import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import { GraficaSistema } from '../components/GraficaMetricas'
import client from '../api/client'

function BadgeEstado({ sistema, snap }) {
  if (!sistema.activo)
    return <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">inactivo</span>
  if (!snap)
    return <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">sin datos</span>
  if (snap.cpu_percent >= 90 || snap.ram_percent >= 90)
    return <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700">crítico</span>
  if (snap.cpu_percent >= 75 || snap.ram_percent >= 75)
    return <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">alerta</span>
  return <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">OK</span>
}

function ModalInstrucciones({ sistema, onClose }) {
  const [copiado, setCopiado] = useState(false)
  const backendUrl = window.location.origin.replace('5173', '8000')
  const comandos = `# 1. Activa el entorno virtual
source .venv/bin/activate

# 2. Configura las variables de entorno
export SISTEMA_ID="${sistema.id}"
export BACKEND_URL="${backendUrl}"
export INTERVALO=30
export UMBRAL_CPU=85
export UMBRAL_RAM=85
export UMBRAL_DISCO=85

# 3. Arranca el agente
cd agente
python agente.py`

  function copiar() {
    navigator.clipboard.writeText(comandos)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-lg shadow-lg">
        <h2 className="text-base font-medium text-gray-900 mb-1">
          Instrucciones de instalación del agente
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Ejecuta estos comandos en el servidor <strong>{sistema.nombre}</strong>
        </p>

        <div className="bg-gray-900 rounded-lg p-4 mb-4 relative">
          <pre className="text-xs text-green-400 overflow-x-auto whitespace-pre">
            {comandos}
          </pre>
          <button
            onClick={copiar}
            className="absolute top-3 right-3 text-xs px-2 py-1 rounded
                       bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
          >
            {copiado ? '✓ Copiado' : 'Copiar'}
          </button>
        </div>

        <div className="bg-blue-50 rounded-lg px-3 py-2.5 mb-4">
          <p className="text-xs text-blue-700">
            Sustituye <code className="bg-blue-100 px-1 rounded">TU-IP-BACKEND</code> por
            la IP del servidor donde corre el backend, o usa <code className="bg-blue-100 px-1 rounded">localhost</code> si
            el agente corre en la misma máquina.
          </p>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 border border-gray-200 rounded-lg text-sm
                     text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}

function BarraMetrica({ valor, umbral = 85 }) {
  const color = valor >= umbral ? 'bg-red-400' : valor >= umbral * 0.8 ? 'bg-amber-400' : 'bg-green-400'
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 h-1.5 bg-gray-200 rounded-full">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${Math.min(valor, 100)}%` }} />
      </div>
      <span className="text-xs text-gray-500">{valor?.toFixed(0)}%</span>
    </div>
  )
}

function tiempoRelativo(fecha) {
  if (!fecha) return 'nunca'
  const diff = Math.floor((Date.now() - new Date(fecha)) / 1000)
  if (diff < 60) return `hace ${diff}s`
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}min`
  return `hace ${Math.floor(diff / 3600)}h`
}

function ModalCrear({ onClose, onCreado }) {
  const [form, setForm] = useState({ nombre: '', ip: '', descripcion: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await client.post('/api/sistemas/', form)
      onCreado()
      onClose()
    } catch {
      setError('Error al crear el sistema. Inténtalo de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-md shadow-lg">
        <h2 className="text-base font-medium text-gray-900 mb-4">Nuevo sistema</h2>
        {error && (
          <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-3">{error}</p>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nombre *</label>
            <input
              required
              value={form.nombre}
              onChange={e => setForm({ ...form, nombre: e.target.value })}
              placeholder="web-server-01"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">IP</label>
            <input
              value={form.ip}
              onChange={e => setForm({ ...form, ip: e.target.value })}
              placeholder="192.168.1.10"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Descripción</label>
            <textarea
              value={form.descripcion}
              onChange={e => setForm({ ...form, descripcion: e.target.value })}
              placeholder="Servidor de producción..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600
                         hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium
                         hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Creando...' : 'Crear sistema'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Sistemas() {
  const [sistemas,   setSistemas]   = useState([])
  const [snapshots,  setSnapshots]  = useState({})
  const [loading,    setLoading]    = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const [toast, setToast] = useState(null)
  const [modalAbrir, setModalAbrir] = useState(false)
  const [modalInstrucciones, setModalInstrucciones] = useState(null)
  const [sistemaDetalle, setSistemaDetalle] = useState(null)

  useEffect(() => {
    cargarSistemas()
    const intervalo = setInterval(cargarSistemas, 30000)
    return () => clearInterval(intervalo)
  }, [])

  async function cargarSistemas() {
    try {
      const { data } = await client.get('/api/sistemas/')
      setSistemas(data)
      const snaps = {}
      await Promise.all(
        data.map(async (s) => {
          try {
            const res = await client.get(`/api/metricas/ultimo/${s.id}`)
            snaps[s.id] = res.data
          } catch {
            snaps[s.id] = null
          }
        })
      )
      setSnapshots(snaps)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function toggleSistema(sistema) {
    try {
      await client.patch(`/api/sistemas/${sistema.id}`, { activo: !sistema.activo })
      cargarSistemas()
    } catch (err) {
      console.error(err)
    }
  }

  async function eliminarSistema(id) {
    if (!confirm('¿Eliminar este sistema? Se borrarán todos sus datos.')) return
    try {
      setDeletingId(id)
      await client.delete(`/api/sistemas/${id}`)
      setToast('Sistema eliminado')
      setTimeout(() => setToast(null), 2500)
      await cargarSistemas()
    } catch (err) {
      console.error(err)
      const detail = err.response?.data?.detail || err.message || 'Error al eliminar el sistema.'
      setToast(detail)
      setTimeout(() => setToast(null), 5000)
      // If 401, redirect handled by client interceptor; otherwise log for debugging
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <Layout>
      <div className="p-6">

        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-lg font-medium text-gray-900">Sistemas</h1>
            <p className="text-xs text-gray-400 mt-0.5">{sistemas.length} sistemas registrados</p>
          </div>
          <button
            onClick={() => setModalAbrir(true)}
            className="text-sm px-3 py-1.5 bg-gray-900 text-white rounded-lg
                       hover:bg-gray-700 transition-colors"
          >
            + Nuevo sistema
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-400">Cargando...</p>
        ) : sistemas.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl">
            <p className="text-sm text-gray-400">No hay sistemas registrados</p>
            <p className="text-xs text-gray-300 mt-1">
              Crea uno y configura el agente para empezar a monitorizar
            </p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-400 font-medium">
                  <th className="text-left px-4 py-3 border-b border-gray-200">Nombre</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">IP</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">CPU</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">RAM</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Disco</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Último contacto</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Estado</th>
                  <th className="px-4 py-3 border-b border-gray-200 w-24"></th>
                </tr>
              </thead>
              <tbody>
                {sistemas.map((s, i) => {
                  const snap = snapshots[s.id]
                  return (
                    <tr
                      key={s.id}
                      onClick={() => setSistemaDetalle(s)}
                      className={`${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                                  cursor-pointer hover:bg-blue-50/30 transition-colors`}
                    >
                      <td className="px-4 py-3 font-medium text-gray-800">{s.nombre}</td>
                      <td className="px-4 py-3 text-gray-500">{s.ip || '—'}</td>
                      <td className="px-4 py-3">
                        {snap ? <BarraMetrica valor={snap.cpu_percent} /> : <span className="text-gray-300 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {snap ? <BarraMetrica valor={snap.ram_percent} /> : <span className="text-gray-300 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {snap ? <BarraMetrica valor={snap.disco_percent} /> : <span className="text-gray-300 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {tiempoRelativo(s.ultimo_contacto)}
                      </td>
                      <td className="px-4 py-3">
                        <BadgeEstado sistema={s} snap={snap} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={(event) => {
                              event.stopPropagation()
                              toggleSistema(s)
                            }}
                            className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
                            title={s.activo ? 'Desactivar' : 'Activar'}
                          >
                            {s.activo ? 'Desactivar' : 'Activar'}
                          </button>
                          <button
                            onClick={(event) => {
                              event.stopPropagation()
                              eliminarSistema(s.id)
                            }}
                            disabled={deletingId === s.id}
                            className={`text-xs text-red-400 hover:text-red-600 transition-colors ${deletingId === s.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                            title="Eliminar"
                          >
                            {deletingId === s.id ? 'Eliminando...' : 'Eliminar'}
                          </button>
                          <button
                            onClick={(event) => {
                              event.stopPropagation()
                              setModalInstrucciones(s)
                            }}
                            className="text-xs text-green-600 hover:underline"
                          >
                            Instalar agente
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {modalAbrir && (
          <ModalCrear
            onClose={() => setModalAbrir(false)}
            onCreado={cargarSistemas}
          />
        )}
        {modalInstrucciones && (
          <ModalInstrucciones
            sistema={modalInstrucciones}
            onClose={() => setModalInstrucciones(null)}
          />
        )}
        {sistemaDetalle && (
          <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-3xl shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-base font-medium text-gray-900">
                  {sistemaDetalle.nombre}
                </h2>
                <button
                  onClick={() => setSistemaDetalle(null)}
                  className="text-xs text-gray-400 hover:text-gray-700"
                >
                  ✕ Cerrar
                </button>
              </div>
              <GraficaSistema
                sistemaId={sistemaDetalle.id}
                nombreSistema={sistemaDetalle.nombre}
              />
            </div>
          </div>
        )}
        {toast && (
          <div className="fixed bottom-6 right-6 z-50 bg-gray-900 text-white
                          text-sm px-4 py-3 rounded-lg shadow-lg
                          animate-fade-in transition-all duration-300">
            {toast}
          </div>
        )}
      </div>
    </Layout>
  )
}