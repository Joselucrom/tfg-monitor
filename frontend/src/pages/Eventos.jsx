import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import client from '../api/client'

const TIPOS = [
  { value: '',              label: 'Todos' },
  { value: 'cpu_alta',      label: 'CPU alta' },
  { value: 'ram_alta',      label: 'RAM alta' },
  { value: 'disco_alto',    label: 'Disco alto' },
  { value: 'http_down',     label: 'HTTP caído' },
  { value: 'http_lento',    label: 'HTTP lento' },
  { value: 'login_fallido', label: 'Login fallido' },
  { value: 'agente_caido',  label: 'Agente caído' },
]

function BadgeTipo({ tipo }) {
  const styles = {
    cpu_alta:      'bg-orange-50 text-orange-700',
    ram_alta:      'bg-purple-50 text-purple-700',
    disco_alto:    'bg-yellow-50 text-yellow-700',
    http_down:     'bg-red-50 text-red-700',
    http_lento:    'bg-amber-50 text-amber-700',
    login_fallido: 'bg-pink-50 text-pink-700',
    agente_caido:  'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${styles[tipo] || 'bg-gray-100 text-gray-500'}`}>
      {tipo}
    </span>
  )
}

function formatFecha(fecha) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleString('es-ES', {
    day:    '2-digit',
    month:  '2-digit',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function tiempoRelativo(fecha) {
  if (!fecha) return '—'
  const diff = Math.floor((Date.now() - new Date(fecha)) / 1000)
  if (diff < 60)   return `hace ${diff}s`
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}min`
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)}h`
  return `hace ${Math.floor(diff / 86400)}d`
}

export default function Eventos() {
  const [eventosSistema, setEventosSistema] = useState([])
  const [eventosWeb,     setEventosWeb]     = useState([])
  const [sistemas,       setSistemas]       = useState([])
  const [loading,        setLoading]        = useState(true)
  const [tab,            setTab]            = useState('sistema') // sistema | web
  const [filtroSistema,  setFiltroSistema]  = useState('')
  const [filtroTipo,     setFiltroTipo]     = useState('')

  useEffect(() => {
    cargarDatos()
  }, [])

  async function cargarDatos() {
    setLoading(true)
    try {
      const [resSistemas, resEvSis, resEvWeb] = await Promise.all([
        client.get('/api/sistemas/'),
        client.get('/api/eventos/sistema?limite=200'),
        client.get('/api/eventos/web?limite=200'),
      ])
      setSistemas(resSistemas.data)
      setEventosSistema(resEvSis.data)
      setEventosWeb(resEvWeb.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Filtrado en cliente
  const eventosFiltrados = (tab === 'sistema' ? eventosSistema : eventosWeb).filter(e => {
    const coincideTipo    = !filtroTipo    || e.tipo === filtroTipo
    const coincideSistema = !filtroSistema || e.sistema_id === filtroSistema
    return coincideTipo && coincideSistema
  })

  function nombreSistema(id) {
    return sistemas.find(s => s.id === id)?.nombre || id?.slice(0, 8) + '...'
  }

  return (
    <Layout>
      <div className="p-6">

        {/* Cabecera */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-lg font-medium text-gray-900">Eventos</h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Historial de eventos recibidos por el sistema
            </p>
          </div>
          <button
            onClick={cargarDatos}
            className="text-sm px-3 py-1.5 border border-gray-200 rounded-lg
                       text-gray-600 hover:bg-gray-50 transition-colors"
          >
            ↻ Actualizar
          </button>
        </div>

        {/* Tabs sistema / web */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit mb-4">
          {[
            { key: 'sistema', label: `Servidores (${eventosSistema.length})` },
            { key: 'web',     label: `Servicios web (${eventosWeb.length})` },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`text-xs px-4 py-1.5 rounded-md transition-colors ${
                tab === t.key
                  ? 'bg-white text-gray-900 shadow-sm font-medium'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Filtros */}
        <div className="flex gap-3 mb-4">
          <select
            value={filtroTipo}
            onChange={e => setFiltroTipo(e.target.value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs
                       focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-600"
          >
            {TIPOS.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>

          {tab === 'sistema' && (
            <select
              value={filtroSistema}
              onChange={e => setFiltroSistema(e.target.value)}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs
                         focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-600"
            >
              <option value="">Todos los sistemas</option>
              {sistemas.map(s => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          )}

          {(filtroTipo || filtroSistema) && (
            <button
              onClick={() => { setFiltroTipo(''); setFiltroSistema('') }}
              className="text-xs text-gray-400 hover:text-gray-600 px-2"
            >
              ✕ Limpiar filtros
            </button>
          )}

          <span className="text-xs text-gray-400 self-center ml-auto">
            {eventosFiltrados.length} eventos
          </span>
        </div>

        {/* Tabla */}
        {loading ? (
          <p className="text-sm text-gray-400">Cargando...</p>
        ) : eventosFiltrados.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl">
            <p className="text-sm text-gray-400">No hay eventos</p>
            <p className="text-xs text-gray-300 mt-1">
              Los eventos aparecen aquí cuando el agente los envía
            </p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-400 font-medium">
                  <th className="text-left px-4 py-3 border-b border-gray-200">Tipo</th>
                  {tab === 'sistema' && (
                    <th className="text-left px-4 py-3 border-b border-gray-200">Sistema</th>
                  )}
                  {tab === 'web' && (
                    <th className="text-left px-4 py-3 border-b border-gray-200">URL</th>
                  )}
                  <th className="text-left px-4 py-3 border-b border-gray-200">Valor</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Origen</th>
                  <th className="text-left px-4 py-3 border-b border-gray-200">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {eventosFiltrados.map((e, i) => (
                  <tr
                    key={e.id}
                    className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}
                  >
                    <td className="px-4 py-3">
                      <BadgeTipo tipo={e.tipo} />
                    </td>
                    {tab === 'sistema' && (
                      <td className="px-4 py-3 text-gray-600 text-xs">
                        {nombreSistema(e.sistema_id)}
                      </td>
                    )}
                    {tab === 'web' && (
                      <td className="px-4 py-3 text-gray-600 text-xs truncate max-w-xs">
                        {e.origen || '—'}
                      </td>
                    )}
                    <td className="px-4 py-3 text-gray-700">
                      {e.valor != null ? (
                        <span className="text-xs font-mono">
                          {e.valor.toFixed(1)}
                          {tab === 'web' && e.tipo === 'http_lento' ? 'ms' : '%'}
                        </span>
                      ) : (
                        tab === 'web' && e.http_status ? (
                          <span className="text-xs font-mono">{e.http_status}</span>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{e.origen || '—'}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs" title={formatFecha(e.timestamp)}>
                      {tiempoRelativo(e.timestamp)}
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