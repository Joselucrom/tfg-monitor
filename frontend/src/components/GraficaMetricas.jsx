import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import client from '../api/client'

const VENTANAS = [
  { label: '30 min', minutos: 30 },
  { label: '1 hora', minutos: 60 },
  { label: '24 horas', minutos: 1440 },
]

const COLORES_METRICAS = {
  cpu_percent:   '#3B82F6',  // azul
  ram_percent:   '#8B5CF6',  // morado
  disco_percent: '#F59E0B',  // ámbar
}

const COLORES_SISTEMAS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#14B8A6', '#F97316',
]

function formatHora(timestamp) {
  return new Date(timestamp).toLocaleTimeString('es-ES', {
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatTooltip(value) {
  return [`${value?.toFixed(1)}%`]
}

// ══════════════════════════════════════════════════════════
// Modo 1 — Un sistema, varias métricas (para vista Sistemas)
// ══════════════════════════════════════════════════════════

export function GraficaSistema({ sistemaId, nombreSistema }) {
  const [datos,   setDatos]   = useState([])
  const [ventana, setVentana] = useState(60)
  const [loading, setLoading] = useState(true)
  const [metricas, setMetricas] = useState({
    cpu_percent:   true,
    ram_percent:   true,
    disco_percent: true,
  })

  const cargar = useCallback(async () => {
    try {
      const { data } = await client.get(
        `/api/metricas/historico/${sistemaId}?minutos=${ventana}`
      )
      setDatos(data.map(d => ({
        ...d,
        hora: formatHora(d.timestamp),
      })))
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [sistemaId, ventana])

  useEffect(() => {
    setLoading(true)
    cargar()
    const intervalo = setInterval(cargar, 30000)
    return () => clearInterval(intervalo)
  }, [cargar])

  return (
    <div className="border border-gray-200 rounded-xl p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-medium text-gray-800">
          Métricas — {nombreSistema}
        </h2>
        <div className="flex items-center gap-3">
          {/* Toggle métricas */}
          <div className="flex gap-2">
            {Object.entries(metricas).map(([key, activa]) => (
              <button
                key={key}
                onClick={() => setMetricas(m => ({ ...m, [key]: !m[key] }))}
                className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                  activa
                    ? 'text-white border-transparent'
                    : 'bg-white text-gray-400 border-gray-200'
                }`}
                style={activa ? { backgroundColor: COLORES_METRICAS[key] } : {}}
              >
                {key === 'cpu_percent' ? 'CPU' : key === 'ram_percent' ? 'RAM' : 'Disco'}
              </button>
            ))}
          </div>
          {/* Selector de ventana */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
            {VENTANAS.map(v => (
              <button
                key={v.minutos}
                onClick={() => setVentana(v.minutos)}
                className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
                  ventana === v.minutos
                    ? 'bg-white text-gray-900 shadow-sm font-medium'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-400">
          Cargando datos...
        </div>
      ) : datos.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-400">
          Sin datos en este período — el agente debe estar en ejecución
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={datos} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6"/>
            <XAxis
              dataKey="hora"
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              tickLine={false}
              tickFormatter={v => `${v}%`}
            />
            <Tooltip
              formatter={(value, name) => [
                `${value?.toFixed(1)}%`,
                name === 'cpu_percent' ? 'CPU' : name === 'ram_percent' ? 'RAM' : 'Disco'
              ]}
              labelStyle={{ fontSize: 11, color: '#374151' }}
              contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E5E7EB' }}
            />
            <Legend
              formatter={name =>
                name === 'cpu_percent' ? 'CPU' : name === 'ram_percent' ? 'RAM' : 'Disco'
              }
              wrapperStyle={{ fontSize: 11 }}
            />
            {metricas.cpu_percent && (
              <Line
                type="monotone"
                dataKey="cpu_percent"
                stroke={COLORES_METRICAS.cpu_percent}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3 }}
              />
            )}
            {metricas.ram_percent && (
              <Line
                type="monotone"
                dataKey="ram_percent"
                stroke={COLORES_METRICAS.ram_percent}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3 }}
              />
            )}
            {metricas.disco_percent && (
              <Line
                type="monotone"
                dataKey="disco_percent"
                stroke={COLORES_METRICAS.disco_percent}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}


// ══════════════════════════════════════════════════════════
// Modo 2 — Varios sistemas, una métrica (para Dashboard)
// ══════════════════════════════════════════════════════════

export function GraficaDashboard({ sistemas }) {
  const [datos,   setDatos]   = useState([])
  const [ventana, setVentana] = useState(60)
  const [metrica, setMetrica] = useState('cpu_percent')
  const [loading, setLoading] = useState(true)

  const lineKeys = useMemo(
    () => sistemas.slice(0, 6).map((s, index) => ({
      key: `line_${index}`,
      sistema: s,
    })),
    [sistemas]
  )

  const cargar = useCallback(async () => {
    if (!lineKeys.length) return
    try {
      const resultados = await Promise.all(
        lineKeys.map(({ sistema }) =>
          client.get(`/api/metricas/historico/${sistema.id}?minutos=${ventana}`)
            .then(r => ({ sistema, datos: r.data }))
            .catch(() => ({ sistema, datos: [] }))
        )
      )

      // Combinar timestamps en un mapa unificado
      const mapa = {}
      resultados.forEach(({ sistema, datos }) => {
        const lineKey = lineKeys.find(l => l.sistema.id === sistema.id)?.key
        datos.forEach(snap => {
          const hora = formatHora(snap.timestamp)
          if (!mapa[hora]) mapa[hora] = { hora }
          if (lineKey) mapa[hora][lineKey] = snap[metrica]
        })
      })

      setDatos(Object.values(mapa).sort((a, b) => a.hora.localeCompare(b.hora)))
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [lineKeys, ventana, metrica])

  useEffect(() => {
    setLoading(true)
    cargar()
    const intervalo = setInterval(cargar, 30000)
    return () => clearInterval(intervalo)
  }, [cargar])

  const METRICAS_OPTS = [
    { value: 'cpu_percent',   label: 'CPU' },
    { value: 'ram_percent',   label: 'RAM' },
    { value: 'disco_percent', label: 'Disco' },
  ]

  return (
    <div className="border border-gray-200 rounded-xl p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-medium text-gray-800">
          Evolución de métricas
        </h2>
        <div className="flex items-center gap-3">
          {/* Selector de métrica */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
            {METRICAS_OPTS.map(m => (
              <button
                key={m.value}
                onClick={() => setMetrica(m.value)}
                className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
                  metrica === m.value
                    ? 'bg-white text-gray-900 shadow-sm font-medium'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          {/* Selector de ventana */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
            {VENTANAS.map(v => (
              <button
                key={v.minutos}
                onClick={() => setVentana(v.minutos)}
                className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
                  ventana === v.minutos
                    ? 'bg-white text-gray-900 shadow-sm font-medium'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-400">
          Cargando datos...
        </div>
      ) : datos.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-400">
          Sin datos en este período — el agente debe estar en ejecución
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={datos} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6"/>
            <XAxis
              dataKey="hora"
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              tickLine={false}
              tickFormatter={v => `${v}%`}
            />
            <Tooltip
              formatter={(value, name) => {
                const entry = lineKeys.find(l => l.key === name)
                return [`${value?.toFixed(1)}%`, entry?.sistema.nombre || name]
              }}
              labelStyle={{ fontSize: 11, color: '#374151' }}
              contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E5E7EB' }}
            />
            <Legend
              formatter={name => lineKeys.find(l => l.key === name)?.sistema.nombre || name}
              wrapperStyle={{ fontSize: 11 }}
            />
            {lineKeys.map(({ key, sistema }, i) => (
              <Line
                key={sistema.id}
                type="monotone"
                dataKey={key}
                stroke={COLORES_SISTEMAS[i % COLORES_SISTEMAS.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3 }}
                connectNulls={true}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}