import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import client from '../api/client'

function BadgeEstado({ activo }) {
  return activo
    ? <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">activo</span>
    : <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">inactivo</span>
}

function ModalServicio({ servicio, onClose, onGuardado }) {
  const editando = !!servicio
  const [form, setForm] = useState(
    servicio
      ? { nombre: servicio.nombre, url: servicio.url, intervalo_s: servicio.intervalo_s }
      : { nombre: '', url: '', intervalo_s: 60 }
  )
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (editando) {
        await client.patch(`/api/servicios-web/${servicio.id}`, form)
      } else {
        await client.post('/api/servicios-web/', form)
      }
      onGuardado()
      onClose()
    } catch {
      setError('Error al guardar el servicio.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-md shadow-lg">
        <h2 className="text-base font-medium text-gray-900 mb-4">
          {editando ? 'Editar servicio' : 'Nuevo servicio web'}
        </h2>

        {error && (
          <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-3">{error}</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-gray-700 mb-1">Nombre *</label>
            <input
              required
              value={form.nombre}
              onChange={e => setForm({ ...form, nombre: e.target.value })}
              placeholder="API producción"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-700 mb-1">URL *</label>
            <input
              required
              type="url"
              value={form.url}
              onChange={e => setForm({ ...form, url: e.target.value })}
              placeholder="https://api.ejemplo.com"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-700 mb-1">
              Intervalo de comprobación (segundos) *
            </label>
            <input
              required
              type="number"
              min="10"
              max="3600"
              value={form.intervalo_s}
              onChange={e => setForm({ ...form, intervalo_s: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-600 mt-1">Mínimo 10 segundos. Recomendado: 60s</p>
          </div>

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-gray-200 rounded-lg text-sm
                         text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 bg-gray-900 text-white rounded-lg text-sm
                         font-medium hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Guardando...' : editando ? 'Guardar cambios' : 'Crear servicio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ModalInstruccionesWeb({ servicio, onClose }) {
  const [copiado, setCopiado] = useState(null) // null | 'remoto' | 'local'
  const backendUrl = window.location.origin.replace(':5173', ':8000')

  const comandosRemoto = `# ── 1. Copia la carpeta del agente al servidor remoto ──
scp -r agente/ usuario@IP-DEL-SERVIDOR:/home/usuario/tfg-agente

# ── 2. Conéctate al servidor por SSH ──
ssh usuario@IP-DEL-SERVIDOR

# ── 3. Dentro del servidor: instala dependencias ──
cd tfg-agente
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ── 4. Configura y arranca, vigilando esta URL ──
export SISTEMA_ID="UUID-DEL-SISTEMA-DONDE-CORRE-EL-AGENTE"
export BACKEND_URL="${backendUrl}"
export URLS_VIGILAR="${servicio.url}"
export INTERVALO=30

python agente.py`

  const comandosLocal = `# Si el agente corre en ESTA misma máquina
# (por ejemplo para pruebas), basta con:

cd agente
export SISTEMA_ID="UUID-DEL-SISTEMA-DONDE-CORRE-EL-AGENTE"
export BACKEND_URL="${backendUrl}"
export URLS_VIGILAR="${servicio.url}"
export INTERVALO=30

python agente.py`

  function copiar(texto, tipo) {
    navigator.clipboard.writeText(texto)
    setCopiado(tipo)
    setTimeout(() => setCopiado(null), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-2xl shadow-lg max-h-[85vh] overflow-y-auto">
        <h2 className="text-base font-medium text-gray-900 mb-1">
          Instrucciones de monitorización web
        </h2>
        <p className="text-xs text-gray-600 mb-4">
          Configura el agente para vigilar <strong>{servicio.nombre}</strong> ({servicio.url})
        </p>

        <p className="text-xs font-medium text-gray-700 mb-2">
          Si el agente va a correr en un servidor remoto (caso habitual)
        </p>
        <div className="bg-gray-900 rounded-lg p-4 mb-4 relative">
          <pre className="text-xs text-green-400 overflow-x-auto whitespace-pre leading-relaxed">
            {comandosRemoto}
          </pre>
          <button
            onClick={() => copiar(comandosRemoto, 'remoto')}
            className="absolute top-3 right-3 text-xs px-2 py-1 rounded
                       bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
          >
            {copiado === 'remoto' ? '✓ Copiado' : 'Copiar'}
          </button>
        </div>

        <p className="text-xs font-medium text-gray-700 mb-2">
          Si el agente va a correr en esta misma máquina (pruebas locales)
        </p>
        <div className="bg-gray-900 rounded-lg p-4 mb-4 relative">
          <pre className="text-xs text-green-400 overflow-x-auto whitespace-pre leading-relaxed">
            {comandosLocal}
          </pre>
          <button
            onClick={() => copiar(comandosLocal, 'local')}
            className="absolute top-3 right-3 text-xs px-2 py-1 rounded
                       bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
          >
            {copiado === 'local' ? '✓ Copiado' : 'Copiar'}
          </button>
        </div>

        <div className="bg-blue-50 rounded-lg px-3 py-2.5 mb-4 space-y-1.5">
          <p className="text-xs text-blue-700">
            Sustituye <code className="bg-blue-100 px-1 rounded">UUID-DEL-SISTEMA</code> por
            el ID del servidor donde se ejecuta (o se ejecutará) el agente — no el servicio web.
          </p>
          <p className="text-xs text-blue-700">
            Puedes vigilar varias URLs desde el mismo agente separándolas por comas
            en <code className="bg-blue-100 px-1 rounded">URLS_VIGILAR</code>.
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

export default function ServiciosWeb() {
  const [servicios, setServicios] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [modal,     setModal]     = useState(null)
  const [modalInstrucciones, setModalInstrucciones] = useState(null)

  useEffect(() => { cargarServicios() }, [])

  async function cargarServicios() {
    try {
      const { data } = await client.get('/api/servicios-web/')
      setServicios(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function toggleServicio(s) {
    try {
      await client.patch(`/api/servicios-web/${s.id}`, { activo: !s.activo })
      cargarServicios()
    } catch (err) {
      console.error(err)
    }
  }

  async function eliminarServicio(id) {
    if (!confirm('¿Eliminar este servicio? Se borrarán todos sus eventos asociados.')) return
    try {
      await client.delete(`/api/servicios-web/${id}`)
      cargarServicios()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <Layout>
      <div className="p-6">

        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-lg font-medium text-gray-900">Servicios web</h1>
            <p className="text-xs text-gray-600 mt-0.5">
              URLs monitorizadas por el agente mediante HTTP checks
            </p>
          </div>
          <button
            onClick={() => setModal('crear')}
            className="text-sm px-3 py-1.5 bg-gray-900 text-white rounded-lg
                       hover:bg-gray-700 transition-colors"
          >
            + Nuevo servicio
          </button>
        </div>

        <div className="flex gap-2 bg-blue-50 rounded-lg px-4 py-3 text-xs text-blue-700 mb-4">
          <svg className="shrink-0 mt-0.5" width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="6" stroke="#3B82F6" strokeWidth="1"/>
            <path d="M7 6v4M7 4v1" stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          Para monitorizar una URL, regístrala aquí y pulsa "Instrucciones" para configurar el agente.
        </div>

        {loading ? (
          <p className="text-sm text-gray-600">Cargando...</p>
        ) : servicios.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl">
            <p className="text-sm text-gray-600">No hay servicios web registrados</p>
            <p className="text-xs text-gray-300 mt-1">
              Añade una URL para empezar a monitorizar su disponibilidad
            </p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-600 font-medium">
                  <th className="text-left px-4 py-3 border-b border-gray-200">Nombre</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">URL</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Intervalo</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Estado</th>
                  <th className="px-4 py-3 border-b border-gray-200 w-40"></th>
                </tr>
              </thead>
              <tbody>
                {servicios.map((s, i) => (
                  <tr
                    key={s.id}
                    className={`${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                                ${!s.activo ? 'opacity-50' : ''}`}
                  >
                    <td className="px-4 py-3 font-medium text-gray-800">{s.nombre}</td>
                    <td className="px-4 py-3">
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline truncate block max-w-xs"
                      >
                        {s.url}
                      </a>
                    </td>
                    <td className="px-4 py-3 text-gray-700 text-xs">{s.intervalo_s}s</td>
                    <td className="px-4 py-3">
                      <BadgeEstado activo={s.activo} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-3 justify-end">
                        <button
                          onClick={() => setModal(s)}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => toggleServicio(s)}
                          className="text-xs text-gray-600 hover:text-gray-700"
                        >
                          {s.activo ? 'Desactivar' : 'Activar'}
                        </button>
                        <button
                          onClick={() => eliminarServicio(s.id)}
                          className="text-xs text-red-400 hover:text-red-600"
                        >
                          Eliminar
                        </button>
                        <button
                          onClick={() => setModalInstrucciones(s)}
                          className="text-xs text-green-600 hover:underline"
                        >
                          Instrucciones
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {modal && (
          <ModalServicio
            servicio={modal === 'crear' ? null : modal}
            onClose={() => setModal(null)}
            onGuardado={cargarServicios}
          />
        )}

        {modalInstrucciones && (
          <ModalInstruccionesWeb
            servicio={modalInstrucciones}
            onClose={() => setModalInstrucciones(null)}
          />
        )}
      </div>
    </Layout>
  )
}