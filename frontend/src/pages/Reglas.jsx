import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import client from '../api/client'

const METRICAS = [
  { value: 'cpu_alta',      label: 'CPU alta',      tipo: 'numerico' },
  { value: 'ram_alta',      label: 'RAM alta',      tipo: 'numerico' },
  { value: 'disco_alto',    label: 'Disco alto',    tipo: 'numerico' },
  { value: 'http_down',     label: 'HTTP caído',    tipo: 'binario'  },
  { value: 'http_lento',    label: 'HTTP lento',    tipo: 'numerico' },
  { value: 'login_fallido', label: 'Login fallido', tipo: 'conteo'   },
  { value: 'agente_caido',  label: 'Agente caído',  tipo: 'binario'  },
]

const OPERADORES  = ['>', '<', '>=', '<=', '=']
const SEVERIDADES = ['info', 'warning', 'critical']

// Métricas que no necesitan umbral — se activan cuando ocurren
const METRICAS_BINARIAS = ['http_down', 'agente_caido']

function esBinaria(metrica) {
  return METRICAS_BINARIAS.includes(metrica)
}

function BadgeSeveridad({ severidad }) {
  const styles = {
    critical: 'bg-red-50 text-red-700',
    warning:  'bg-amber-50 text-amber-700',
    info:     'bg-blue-50 text-blue-700',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${styles[severidad] || styles.info}`}>
      {severidad}
    </span>
  )
}

function ModalRegla({ regla, onClose, onGuardado }) {
  const editando = !!regla
  const [form, setForm] = useState(
    regla
      ? { ...regla }
      : { nombre: '', metrica: 'cpu_alta', operador: '>', umbral: 85, severidad: 'warning' }
  )
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  // Cuando cambia la métrica, ajustar operador y umbral si es binaria
  function handleMetricaChange(metrica) {
    if (esBinaria(metrica)) {
      setForm(f => ({ ...f, metrica, operador: '=', umbral: 1 }))
    } else {
      setForm(f => ({ ...f, metrica, operador: '>', umbral: 85 }))
    }
  }

  const binaria = esBinaria(form.metrica)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (editando) {
        // Al editar solo mandamos los campos editables
        await client.patch(`/api/reglas/${regla.id}`, {
          operador:  form.operador,
          umbral:    form.umbral,
          severidad: form.severidad,
        })
      } else {
        await client.post('/api/reglas/', form)
      }
      onGuardado()
      onClose()
    } catch {
      setError('Error al guardar la regla.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-md shadow-lg">
        <h2 className="text-base font-medium text-gray-900 mb-1">
          {editando ? 'Editar regla' : 'Nueva regla'}
        </h2>
        {editando && (
          <p className="text-xs text-gray-400 mb-4">
            El nombre y la métrica no se pueden cambiar. Crea una nueva regla si necesitas algo distinto.
          </p>
        )}
        {!editando && <div className="mb-4" />}

        {error && (
          <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-3">{error}</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">

          {/* Nombre — bloqueado al editar */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Nombre {!editando && '*'}
            </label>
            <input
              required={!editando}
              disabled={editando}
              value={form.nombre}
              onChange={e => setForm({ ...form, nombre: e.target.value })}
              placeholder="CPU crítica"
              className={`w-full px-3 py-2 border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500
                         ${editando
                           ? 'border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed'
                           : 'border-gray-200'
                         }`}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Métrica — bloqueada al editar */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Métrica {!editando && '*'}
              </label>
              {editando ? (
                <div className="px-3 py-2 border border-gray-100 bg-gray-50 rounded-lg text-sm text-gray-400 cursor-not-allowed">
                  {METRICAS.find(m => m.value === form.metrica)?.label || form.metrica}
                </div>
              ) : (
                <select
                  value={form.metrica}
                  onChange={e => handleMetricaChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                             focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  {METRICAS.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              )}
            </div>

            {/* Severidad — siempre editable */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Severidad *</label>
              <select
                value={form.severidad}
                onChange={e => setForm({ ...form, severidad: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                {SEVERIDADES.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Operador y umbral — ocultos si es métrica binaria */}
          {binaria ? (
            <div className="bg-blue-50 rounded-lg px-3 py-2.5">
              <p className="text-xs text-blue-700">
                Esta regla se activa automáticamente cuando se detecta el evento,
                sin necesidad de umbral numérico.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Operador *</label>
                <select
                  value={form.operador}
                  onChange={e => setForm({ ...form, operador: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                             focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  {OPERADORES.map(o => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Umbral * {
                    form.metrica === 'login_fallido' ? '(intentos)' :
                    form.metrica === 'http_lento'    ? '(ms)'       : '(%)'
                  }
                </label>
                <input
                  type="number"
                  required
                  min="0"
                  max={form.metrica === 'login_fallido' ? 100 : 100}
                  step="0.1"
                  value={form.umbral}
                  onChange={e => setForm({ ...form, umbral: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm
                             focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {/* Vista previa */}
          <div className="bg-gray-50 rounded-lg px-3 py-2">
            <p className="text-xs text-gray-400 mb-0.5">Vista previa</p>
            <code className="text-xs text-gray-700">
              {binaria
                ? `Si ocurre ${form.metrica} → alerta ${form.severidad}`
                : `Si ${form.metrica} ${form.operador} ${form.umbral} → alerta ${form.severidad}`
              }
            </code>
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
              {loading ? 'Guardando...' : editando ? 'Guardar cambios' : 'Crear regla'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Reglas() {
  const [reglas,  setReglas]  = useState([])
  const [loading, setLoading] = useState(true)
  const [modal,   setModal]   = useState(null)

  useEffect(() => { cargarReglas() }, [])

  async function cargarReglas() {
    try {
      const { data } = await client.get('/api/reglas/')
      setReglas(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function toggleRegla(id) {
    try {
      await client.patch(`/api/reglas/${id}/toggle`)
      cargarReglas()
    } catch (err) {
      console.error(err)
    }
  }

  async function eliminarRegla(id) {
    if (!confirm('¿Eliminar esta regla? Las alertas asociadas se eliminarán también.')) return
    try {
      await client.delete(`/api/reglas/${id}`)
      cargarReglas()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <Layout>
      <div className="p-6">

        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-lg font-medium text-gray-900">Reglas y umbrales</h1>
            <p className="text-xs text-gray-400 mt-0.5">
              El motor evalúa estas reglas en cada evento recibido
            </p>
          </div>
          <button
            onClick={() => setModal('crear')}
            className="text-sm px-3 py-1.5 bg-gray-900 text-white rounded-lg
                       hover:bg-gray-700 transition-colors"
          >
            + Nueva regla
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-400">Cargando...</p>
        ) : reglas.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl">
            <p className="text-sm text-gray-400">No hay reglas configuradas</p>
            <p className="text-xs text-gray-300 mt-1">
              Crea una regla para empezar a recibir alertas automáticas
            </p>
          </div>
        ) : (
          <>
            <div className="border border-gray-200 rounded-xl overflow-hidden mb-4">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs text-gray-400 font-medium">
                    <th className="text-left px-4 py-3 border-b border-gray-200">Nombre</th>
                    <th className="text-left px-4 py-3 border-b border-gray-200">Métrica</th>
                    <th className="text-left px-4 py-3 border-b border-gray-200">Condición</th>
                    <th className="text-left px-4 py-3 border-b border-gray-200">Severidad</th>
                    <th className="text-left px-4 py-3 border-b border-gray-200">Activa</th>
                    <th className="px-4 py-3 border-b border-gray-200 w-32"></th>
                  </tr>
                </thead>
                <tbody>
                  {reglas.map((r, i) => (
                    <tr
                      key={r.id}
                      className={`${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                                  ${!r.activa ? 'opacity-50' : ''}`}
                    >
                      <td className="px-4 py-3 font-medium text-gray-800">{r.nombre}</td>
                      <td className="px-4 py-3">
                        <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
                          {r.metrica}
                        </code>
                      </td>
                      <td className="px-4 py-3">
                        {esBinaria(r.metrica) ? (
                          <span className="text-xs text-gray-400 italic">al ocurrir</span>
                        ) : (
                          <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
                            {r.operador} {r.umbral}
                          </code>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <BadgeSeveridad severidad={r.severidad} />
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => toggleRegla(r.id)}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full
                                      transition-colors focus:outline-none
                                      ${r.activa ? 'bg-green-500' : 'bg-gray-300'}`}
                        >
                          <span className={`inline-block h-3.5 w-3.5 transform rounded-full
                                           bg-white shadow transition-transform
                                           ${r.activa ? 'translate-x-4' : 'translate-x-1'}`}
                          />
                        </button>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-3 justify-end">
                          <button
                            onClick={() => setModal(r)}
                            className="text-xs text-blue-600 hover:underline"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => eliminarRegla(r.id)}
                            className="text-xs text-red-400 hover:text-red-600"
                          >
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex gap-2 bg-gray-50 rounded-lg px-4 py-3 text-xs text-gray-500">
              <svg className="shrink-0 mt-0.5" width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="#9CA3AF" strokeWidth="1"/>
                <path d="M7 6v4M7 4v1" stroke="#9CA3AF" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Cada vez que un evento satisface una regla activa, se genera una alerta automáticamente.
              Puedes desactivar reglas temporalmente sin eliminarlas.
            </div>
          </>
        )}

        {modal && (
          <ModalRegla
            regla={modal === 'crear' ? null : modal}
            onClose={() => setModal(null)}
            onGuardado={cargarReglas}
          />
        )}
      </div>
    </Layout>
  )
}