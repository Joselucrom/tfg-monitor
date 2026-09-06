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

function hexToRgb(hex) {
  const h = hex.replace('#', '')
  const bigint = parseInt(h, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  return { r, g, b }
}

function srgbToLinear(c) {
  const cs = c / 255
  return cs <= 0.03928 ? cs / 12.92 : Math.pow((cs + 0.055) / 1.055, 2.4)
}

function relativeLuminance(hex) {
  const { r, g, b } = hexToRgb(hex)
  const R = srgbToLinear(r)
  const G = srgbToLinear(g)
  const B = srgbToLinear(b)
  return 0.2126 * R + 0.7152 * G + 0.0722 * B
}

function contrastRatio(hex1, hex2) {
  const L1 = relativeLuminance(hex1)
  const L2 = relativeLuminance(hex2)
  const lighter = Math.max(L1, L2)
  const darker = Math.min(L1, L2)
  return (lighter + 0.05) / (darker + 0.05)
}

function getBestTextColor(backgroundHex) {
  if (!backgroundHex) return '#111827' // tailwind gray-900 fallback
  const white = '#ffffff'
  const black = '#111827'
  const contrastWithWhite = contrastRatio(backgroundHex, white)
  const contrastWithBlack = contrastRatio(backgroundHex, black)
  return contrastWithWhite >= contrastWithBlack ? white : black
}

function darkenHex(hex, percent) {
  const { r, g, b } = hexToRgb(hex)
  const factor = 1 - percent
  const nr = Math.max(0, Math.round(r * factor))
  const ng = Math.max(0, Math.round(g * factor))
  const nb = Math.max(0, Math.round(b * factor))
  const toHex = n => n.toString(16).padStart(2, '0')
  return `#${toHex(nr)}${toHex(ng)}${toHex(nb)}`
}

function getAccessibleTextColor(backgroundHex, minContrast = 4.5) {
  if (!backgroundHex) return { textColor: '#111827', background: backgroundHex }
  const white = '#ffffff'
  const black = '#111827'

  const contrastWithWhite = contrastRatio(backgroundHex, white)
  const contrastWithBlack = contrastRatio(backgroundHex, black)

  // If either meets threshold, pick the best one
  if (contrastWithWhite >= minContrast || contrastWithBlack >= minContrast) {
    const pick = contrastWithWhite >= contrastWithBlack ? white : black
    return { textColor: pick, background: backgroundHex }
  }

  // Try darkening the background progressively to reach the threshold
  for (let p = 0.1; p <= 0.6; p += 0.1) {
    const darker = darkenHex(backgroundHex, p)
    const cWhite = contrastRatio(darker, white)
    const cBlack = contrastRatio(darker, black)
    if (cWhite >= minContrast || cBlack >= minContrast) {
      const pick = cWhite >= cBlack ? white : black
      return { textColor: pick, background: darker }
    }
  }

  // Fallback: devuelve el que tenga mayor contraste aunque sea insuficiente
  return {
    textColor: contrastWithWhite >= contrastWithBlack ? white : black,
    background: backgroundHex,
  }
}

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
            {Object.entries(metricas).map(([key, activa]) => {
              const originalBg = activa ? COLORES_METRICAS[key] : undefined
              const { textColor, background: bgAdjusted } = activa
                ? getAccessibleTextColor(originalBg)
                : { textColor: undefined, background: undefined }
              return (
                <button
                  key={key}
                  onClick={() => setMetricas(m => ({ ...m, [key]: !m[key] }))}
                  className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                    activa
                      ? 'border-transparent'
                      : 'bg-white text-gray-600 border-gray-200'
                  }`}
                  style={activa ? { backgroundColor: bgAdjusted, color: textColor } : {}}
                >
                  {key === 'cpu_percent' ? 'CPU' : key === 'ram_percent' ? 'RAM' : 'Disco'}
                </button>
              )
            })}
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
                    : 'text-gray-700 hover:text-gray-700'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-600">
          Cargando datos...
        </div>
      ) : datos.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-600">
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
                    : 'text-gray-700 hover:text-gray-700'
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
                    : 'text-gray-700 hover:text-gray-700'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-600">
          Cargando datos...
        </div>
      ) : datos.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-xs text-gray-600">
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