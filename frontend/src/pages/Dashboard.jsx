import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'
import { GraficaDashboard } from '../components/GraficaMetricas'

// ── Helpers ───────────────────────────────────────────────

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

function BarraMetrica({ valor, umbral = 85 }) {
  const color = valor >= umbral
    ? 'bg-red-400'
    : valor >= umbral * 0.8
    ? 'bg-amber-400'
    : 'bg-green-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full">
        <div
          className={`h-1.5 rounded-full transition-all ${color}`}
          style={{ width: `${Math.min(valor, 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8 text-right">{valor?.toFixed(0)}%</span>
    </div>
  )
}

function tiempoRelativo(fecha) {
  const diff = Math.floor((Date.now() - new Date(fecha)) / 1000)
  if (diff < 60)  return `hace ${diff}s`
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}min`
  return `hace ${Math.floor(diff / 3600)}h`
}

// ── Dashboard ─────────────────────────────────────────────

export default function Dashboard() {
  const [sistemas,  setSistemas]  = useState([])
  const [alertas,   setAlertas]   = useState([])
  const [snapshots, setSnapshots] = useState({})
  const [loading,   setLoading]   = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    cargarDatos()
    const intervalo = setInterval(cargarDatos, 30000)
    return () => clearInterval(intervalo)
  }, [])

  async function cargarDatos() {
    try {
      const [resSistemas, resAlertas] = await Promise.all([
        client.get('/api/sistemas/'),
        client.get('/api/alertas/?resuelta=false&limite=5'),
      ])
      setSistemas(resSistemas.data)
      setAlertas(resAlertas.data)

      // Cargar último snapshot de cada sistema
      const snaps = {}
      await Promise.all(
        resSistemas.data.map(async (s) => {
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
      console.error('Error cargando dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const totalSistemas  = sistemas.length
  const sistemasOk     = sistemas.filter(s => s.activo).length
  const alertasCriticas = alertas.filter(a => a.severidad === 'critical').length

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full text-gray-400 text-sm">
          Cargando...
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="p-6">

        {/* Cabecera */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-lg font-medium text-gray-900">Dashboard</h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Actualización automática cada 30s
            </p>
          </div>
          <button
            onClick={() => navigate('/sistemas')}
            className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg
                       text-gray-600 hover:bg-gray-50 transition-colors"
          >
            + Añadir sistema
          </button>
        </div>

        {/* Tarjetas resumen */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs text-gray-400 mb-1">Sistemas activos</p>
            <p className="text-2xl font-medium text-gray-900">{sistemasOk}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs text-gray-400 mb-1">Total sistemas</p>
            <p className="text-2xl font-medium text-gray-900">{totalSistemas}</p>
          </div>
          <div className={`rounded-lg p-4 ${alertas.length > 0 ? 'bg-amber-50' : 'bg-gray-50'}`}>
            <p className={`text-xs mb-1 ${alertas.length > 0 ? 'text-amber-600' : 'text-gray-400'}`}>
              Alertas activas
            </p>
            <p className={`text-2xl font-medium ${alertas.length > 0 ? 'text-amber-800' : 'text-gray-900'}`}>
              {alertas.length}
            </p>
          </div>
          <div className={`rounded-lg p-4 ${alertasCriticas > 0 ? 'bg-red-50' : 'bg-gray-50'}`}>
            <p className={`text-xs mb-1 ${alertasCriticas > 0 ? 'text-red-600' : 'text-gray-400'}`}>
              Críticas
            </p>
            <p className={`text-2xl font-medium ${alertasCriticas > 0 ? 'text-red-800' : 'text-gray-900'}`}>
              {alertasCriticas}
            </p>
          </div>
        </div>
        {sistemas.length > 0 && (
          <div className="mb-4">
            <GraficaDashboard sistemas={sistemas} />
          </div>
        )}
        {/* Bloques principales */}
        <div className="grid grid-cols-2 gap-4">

          {/* Estado de sistemas */}
          <div className="border border-gray-200 rounded-xl p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-medium text-gray-800">Estado de sistemas</h2>
              <button
                onClick={() => navigate('/sistemas')}
                className="text-xs text-blue-600 hover:underline"
              >
                Ver todos
              </button>
            </div>

            {sistemas.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-6">
                No hay sistemas registrados
              </p>
            ) : (
              <div className="space-y-3">
                {sistemas.slice(0, 5).map((s) => {
                  const snap = snapshots[s.id]
                  return (
                    <div key={s.id} className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${
                        !s.activo ? 'bg-gray-300'
                        : snap?.cpu_percent >= 90 || snap?.ram_percent >= 90
                        ? 'bg-red-400'
                        : snap?.cpu_percent >= 75 || snap?.ram_percent >= 75
                        ? 'bg-amber-400'
                        : 'bg-green-400'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-800 truncate">{s.nombre}</p>
                        {snap ? (
                          <div className="mt-1 space-y-0.5">
                            <BarraMetrica valor={snap.cpu_percent} />
                            <BarraMetrica valor={snap.ram_percent} />
                          </div>
                        ) : (
                          <p className="text-xs text-gray-400">Sin datos</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 shrink-0">
                        {s.ultimo_contacto
                          ? tiempoRelativo(s.ultimo_contacto)
                          : 'nunca'
                        }
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Alertas recientes */}
          <div className="border border-gray-200 rounded-xl p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-medium text-gray-800">Alertas recientes</h2>
              <button
                onClick={() => navigate('/alertas')}
                className="text-xs text-blue-600 hover:underline"
              >
                Ver todas
              </button>
            </div>

            {alertas.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-sm text-gray-400">Sin alertas activas</p>
                <p className="text-xs text-gray-300 mt-1">El sistema funciona correctamente</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alertas.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => navigate(`/alertas/${a.id}`)}
                    className="cursor-pointer hover:bg-gray-50 rounded-lg p-2 -mx-2 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <p className="text-xs font-medium text-gray-800 line-clamp-1 flex-1 mr-2">
                        {a.mensaje}
                      </p>
                      <BadgeSeveridad severidad={a.severidad} />
                    </div>
                    <p className="text-xs text-gray-400">{tiempoRelativo(a.timestamp)}</p>
                  </div>
                ))}
              </div>
            )}

            {alertas.length > 0 && (
              <button
                onClick={() => navigate('/alertas')}
                className="w-full mt-3 text-xs text-gray-500 border border-gray-200
                           rounded-lg py-2 hover:bg-gray-50 transition-colors"
              >
                Ver todas las alertas
              </button>
            )}
          </div>

        </div>
      </div>
    </Layout>
  )
}