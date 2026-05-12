import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import client from '../api/client'

function StatCard({ label, value, highlight }) {
  return (
    <div className={`rounded-lg p-4 ${highlight ? 'bg-amber-50' : 'bg-gray-50'}`}>
      <p className={`text-xs mb-1 ${highlight ? 'text-amber-600' : 'text-gray-400'}`}>{label}</p>
      <p className={`text-2xl font-medium ${highlight ? 'text-amber-800' : 'text-gray-900'}`}>
        {value ?? '—'}
      </p>
    </div>
  )
}

function BarraRanking({ valor, max, color = 'bg-blue-400' }) {
  const pct = max > 0 ? Math.round((valor / max) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-16 text-right shrink-0">{valor} eventos</span>
    </div>
  )
}

function BarraAlerta({ valor, max }) {
  const pct = max > 0 ? Math.round((valor / max) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full">
        <div className="h-1.5 rounded-full bg-red-400" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-16 text-right shrink-0">{valor} alertas</span>
    </div>
  )
}

export default function Admin() {
  const [stats,    setStats]    = useState(null)
  const [topSis,   setTopSis]   = useState([])
  const [topReg,   setTopReg]   = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [togglingId, setTogglingId] = useState(null)

  useEffect(() => { cargarDatos() }, [])

  async function cargarDatos() {
    setLoading(true)
    try {
      const [resStats, resSis, resReg, resUsr] = await Promise.all([
        client.get('/api/admin/estadisticas'),
        client.get('/api/admin/sistemas-top?limite=5'),
        client.get('/api/admin/reglas-top?limite=5'),
        client.get('/api/admin/usuarios'),
      ])
      setStats(resStats.data)
      setTopSis(resSis.data)
      setTopReg(resReg.data)
      setUsuarios(resUsr.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function toggleUsuario(id) {
    setTogglingId(id)
    try {
      await client.patch(`/api/admin/usuarios/${id}/toggle`)
      cargarDatos()
    } catch (err) {
      console.error(err)
    } finally {
      setTogglingId(null)
    }
  }

  const maxEventos = Math.max(...topSis.map(s => s.total_eventos), 1)
  const maxAlertas = Math.max(...topReg.map(r => r.total_alertas), 1)

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
            <h1 className="text-lg font-medium text-gray-900">Panel de administración</h1>
            <p className="text-xs text-gray-400 mt-0.5">Estadísticas globales de la plataforma</p>
          </div>
          <button
            onClick={cargarDatos}
            className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg
                       text-gray-600 hover:bg-gray-50 transition-colors"
          >
            ↻ Actualizar
          </button>
        </div>

        {/* Tarjetas de estadísticas */}
        {stats && (
          <div className="grid grid-cols-3 gap-3 mb-6">
            <StatCard label="Usuarios registrados"    value={stats.total_usuarios} />
            <StatCard label="Sistemas monitorizados"  value={stats.total_sistemas} />
            <StatCard label="Servicios web"           value={stats.total_servicios_web} />
            <StatCard label="Alertas pendientes"      value={stats.alertas_pendientes} highlight={stats.alertas_pendientes > 0} />
            <StatCard label="Alertas totales"         value={stats.total_alertas} />
            <StatCard label="Eventos hoy"             value={stats.total_eventos_hoy} />
          </div>
        )}

        {/* Rankings */}
        <div className="grid grid-cols-2 gap-4 mb-6">

          {/* Sistemas top */}
          <div className="border border-gray-200 rounded-xl p-4">
            <h2 className="text-sm font-medium text-gray-800 mb-4">
              Sistemas más monitorizados
            </h2>
            {topSis.length === 0 ? (
              <p className="text-xs text-gray-400">Sin datos</p>
            ) : (
              <div className="space-y-3">
                {topSis.map(s => (
                  <div key={s.sistema_id}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-700 font-medium truncate mr-2">{s.nombre}</span>
                    </div>
                    <BarraRanking valor={s.total_eventos} max={maxEventos} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Reglas top */}
          <div className="border border-gray-200 rounded-xl p-4">
            <h2 className="text-sm font-medium text-gray-800 mb-4">
              Reglas más utilizadas
            </h2>
            {topReg.length === 0 ? (
              <p className="text-xs text-gray-400">Sin datos</p>
            ) : (
              <div className="space-y-3">
                {topReg.map(r => (
                  <div key={r.regla_id}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-700 font-medium truncate mr-2">{r.nombre}</span>
                    </div>
                    <BarraAlerta valor={r.total_alertas} max={maxAlertas} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Gestión de usuarios */}
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex justify-between items-center px-4 py-3
                          border-b border-gray-200 bg-gray-50">
            <h2 className="text-sm font-medium text-gray-800">Gestión de usuarios</h2>
            <span className="text-xs text-gray-400">{usuarios.length} usuarios</span>
          </div>

          {usuarios.length === 0 ? (
            <p className="text-sm text-gray-400 p-4">No hay usuarios</p>
          ) : (
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-xs text-gray-400 font-medium">
                  <th className="text-left px-4 py-3 border-b border-gray-200">Nombre</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Email</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Rol</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Estado</th>
                  <th className="px-4 py-3 border-b border-gray-200 w-24"></th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((u, i) => (
                  <tr
                    key={u.id}
                    className={`${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                                ${!u.activo ? 'opacity-50' : ''}`}
                  >
                    <td className="px-4 py-3 font-medium text-gray-800">{u.nombre}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{u.email}</td>
                    <td className="px-4 py-3">
                      {u.rol === 'admin'
                        ? <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">admin</span>
                        : <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">operador</span>
                      }
                    </td>
                    <td className="px-4 py-3">
                      {u.activo
                        ? <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700">activo</span>
                        : <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-600">inactivo</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => toggleUsuario(u.id)}
                        disabled={togglingId === u.id}
                        className="text-xs text-gray-400 hover:text-gray-700
                                   disabled:opacity-40 transition-colors"
                      >
                        {togglingId === u.id
                          ? '...'
                          : u.activo ? 'Desactivar' : 'Activar'
                        }
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      </div>
    </Layout>
  )
}