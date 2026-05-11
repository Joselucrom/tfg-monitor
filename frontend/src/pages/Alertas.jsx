import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

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

function tiempoRelativo(fecha) {
  if (!fecha) return '—'
  const diff = Math.floor((Date.now() - new Date(fecha)) / 1000)
  if (diff < 60)   return `hace ${diff}s`
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}min`
  return `hace ${Math.floor(diff / 3600)}h`
}

// ── Detalle de alerta ─────────────────────────────────────

function DetalleAlerta({ alerta, onVolver, onResuelta }) {
  const [confirmar, setConfirmar] = useState(false)
  const [recs,    setRecs]    = useState([])
  const [loading, setLoading] = useState(false)
  const [resolviendo, setResolviendo] = useState(false)

  useEffect(() => {
    cargarRecomendaciones()
  }, [alerta.id])

  async function cargarRecomendaciones() {
    try {
      const { data } = await client.get(`/api/alertas/${alerta.id}/recomendaciones`)
      setRecs(data)
    } catch (err) {
      console.error(err)
    }
  }

  async function marcarAplicada(recId, aplicada) {
    try {
      await client.patch(
        `/api/alertas/${alerta.id}/recomendaciones/${recId}`,
        { aplicada }
      )
      cargarRecomendaciones()
    } catch (err) {
      console.error(err)
    }
  }

  async function resolver() {
    setResolviendo(true)
    try {
      await client.post(`/api/alertas/${alerta.id}/resolver`)
      onResuelta()
    } catch (err) {
      console.error(err)
    } finally {
      setResolviendo(false)
    }
  }

  return (
    <div className="p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-gray-400 mb-4">
        <button onClick={onVolver} className="hover:text-gray-700 transition-colors">
          ← Alertas
        </button>
        <span>/</span>
        <span className="text-gray-600">Detalle</span>
      </div>

      {/* Cabecera */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-medium text-gray-900">Detalle de alerta</h1>
          <BadgeSeveridad severidad={alerta.severidad} />
          {alerta.resuelta && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">
              resuelta
            </span>
          )}
        </div>
        {!alerta.resuelta && (
          <>
            <button
              onClick={() => setConfirmar(true)}
              className="text-sm px-3 py-1.5 bg-green-600 text-white rounded-lg
                        hover:bg-green-700 transition-colors"
            >
              Marcar como resuelta
            </button>

            {confirmar && (
              <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl border border-gray-200 p-6 w-full max-w-sm shadow-lg">
                  <h3 className="text-base font-medium text-gray-900 mb-2">
                    ¿Marcar como resuelta?
                  </h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Esta acción no se puede deshacer. La alerta quedará cerrada definitivamente.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfirmar(false)}
                      className="flex-1 py-2 border border-gray-200 rounded-lg text-sm
                                text-gray-600 hover:bg-gray-50 transition-colors"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={() => { setConfirmar(false); resolver() }}
                      disabled={resolviendo}
                      className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm
                                font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      {resolviendo ? 'Resolviendo...' : 'Confirmar'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Info */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Mensaje</p>
          <p className="text-sm text-gray-800">{alerta.mensaje}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Severidad</p>
          <p className="text-sm font-medium text-gray-800 capitalize">{alerta.severidad}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Detectada</p>
          <p className="text-sm text-gray-800">{tiempoRelativo(alerta.timestamp)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Estado</p>
          <p className="text-sm text-gray-800">{alerta.resuelta ? `Resuelta ${tiempoRelativo(alerta.resuelta_at)}` : 'Pendiente'}</p>
        </div>
      </div>

      {/* Recomendaciones */}
      <div className="border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-5 h-5 rounded bg-blue-50 flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <circle cx="6" cy="6" r="5" stroke="#3B82F6" strokeWidth="1"/>
              <path d="M6 5v4M6 3v1" stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
          </div>
          <h2 className="text-sm font-medium text-gray-800">Recomendaciones</h2>
        </div>

        {recs.length === 0 ? (
          <p className="text-xs text-gray-400">No hay recomendaciones para esta alerta.</p>
        ) : (
          <div className="space-y-3">
            {recs.map((rec) => (
              <div
                key={rec.recomendacion_id}
                className={`p-3 rounded-lg border transition-colors ${
                  rec.aplicada
                    ? 'bg-green-50 border-green-200'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex justify-between items-start gap-3">
                  <p className="text-sm text-gray-700 flex-1">{rec.texto}</p>
                  <button
                    onClick={() => marcarAplicada(rec.recomendacion_id, !rec.aplicada)}
                    className={`text-xs px-2 py-1 rounded shrink-0 transition-colors ${
                      rec.aplicada
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-white border border-gray-200 text-gray-500 hover:bg-gray-100'
                    }`}
                  >
                    {rec.aplicada ? '✓ Aplicada' : 'Marcar aplicada'}
                  </button>
                </div>
                {rec.aplicada && rec.aplicada_at && (
                  <p className="text-xs text-green-600 mt-1">
                    Aplicada {tiempoRelativo(rec.aplicada_at)}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Lista de alertas ──────────────────────────────────────

export default function Alertas() {
  const [alertas,   setAlertas]   = useState([])
  const [loading,   setLoading]   = useState(true)
  const [filtro,    setFiltro]    = useState('pendientes') // pendientes | todas | resueltas
  const [seleccionada, setSeleccionada] = useState(null)
  const { id } = useParams()
  const navigate = useNavigate()

  useEffect(() => {
    cargarAlertas()
  }, [filtro])

  useEffect(() => {
    if (id) {
      cargarAlertaPorId(id)
    }
  }, [id])

  async function cargarAlertas() {
    setLoading(true)
    try {
      const params = filtro === 'pendientes'
        ? '?resuelta=false'
        : filtro === 'resueltas'
        ? '?resuelta=true'
        : ''
      const { data } = await client.get(`/api/alertas/${params}&limite=100`)
      setAlertas(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function cargarAlertaPorId(alertaId) {
    try {
      const { data } = await client.get(`/api/alertas/${alertaId}`)
      setSeleccionada(data)
    } catch (err) {
      console.error(err)
    }
  }

  function handleVolver() {
    setSeleccionada(null)
    navigate('/alertas')
    cargarAlertas()
  }

  if (seleccionada) {
    return (
      <Layout>
        <DetalleAlerta
          alerta={seleccionada}
          onVolver={handleVolver}
          onResuelta={handleVolver}
        />
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-lg font-medium text-gray-900">Alertas</h1>
            <p className="text-xs text-gray-400 mt-0.5">{alertas.length} alertas</p>
          </div>
          {/* Filtros */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            {['pendientes', 'todas', 'resueltas'].map(f => (
              <button
                key={f}
                onClick={() => setFiltro(f)}
                className={`text-xs px-3 py-1.5 rounded-md transition-colors capitalize ${
                  filtro === f
                    ? 'bg-white text-gray-900 shadow-sm font-medium'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-400">Cargando...</p>
        ) : alertas.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl">
            <p className="text-sm text-gray-400">
              {filtro === 'pendientes' ? 'No hay alertas pendientes' : 'No hay alertas'}
            </p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-400 font-medium">
                  <th className="text-left px-4 py-3 border-b border-gray-200">Mensaje</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Severidad</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Detectada</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Estado</th>
                  <th className="px-4 py-3 border-b border-gray-200 w-20"></th>
                </tr>
              </thead>
              <tbody>
                {alertas.map((a, i) => (
                  <tr
                    key={a.id}
                    className={`${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                                hover:bg-blue-50/30 transition-colors cursor-pointer`}
                    onClick={() => setSeleccionada(a)}
                  >
                    <td className="px-4 py-3 text-gray-700 max-w-xs truncate">{a.mensaje}</td>
                    <td className="px-4 py-3">
                      <BadgeSeveridad severidad={a.severidad} />
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {tiempoRelativo(a.timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      {a.resuelta
                        ? <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">resuelta</span>
                        : <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">pendiente</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-xs text-blue-600 hover:underline">Ver →</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}