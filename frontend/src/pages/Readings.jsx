import { useState, useEffect } from 'react'
import { Droplets, ThermometerSun, AlertCircle, Hash } from 'lucide-react'
import TxHashDisplay from '../components/TxHashDisplay'

function Readings() {
  const [readings, setReadings] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetchReadings()
  }, [])

  const fetchReadings = async () => {
    try {
      const res = await fetch('/api/readings')
      const data = await res.json()
      setReadings(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching readings:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Cargando lecturas...</div>
  }

  const filteredReadings = filter
    ? readings.filter(r => r.sensor_id.toLowerCase().includes(filter.toLowerCase()))
    : readings

  const getAlertColor = (level) => {
    switch (level) {
      case 'Critical': return 'var(--danger-color)'
      case 'High': return '#fd7e14'
      case 'Low': return 'var(--warning-color)'
      case 'Normal': return 'var(--success-color)'
      default: return 'var(--info-color)'
    }
  }

  return (
    <div>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>Historial de Lecturas</h1>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', gap: '20px', flexWrap: 'wrap' }}>
          <h2>Total de Lecturas: {readings.length}</h2>
          <input
            type="text"
            placeholder="Filtrar por sensor ID..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              padding: '10px 15px',
              borderRadius: '8px',
              border: '2px solid var(--border-color)',
              fontSize: '14px',
              width: '300px'
            }}
          />
        </div>

        <div style={{ display: 'grid', gap: '15px' }}>
          {filteredReadings.map((reading, idx) => (
            <div
              key={idx}
              style={{
                background: 'var(--bg-light)',
                padding: '20px',
                borderRadius: '12px',
                borderLeft: `4px solid ${getAlertColor(reading.alert_level)}`
              }}
            >
              {/* Grid de información principal */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                  gap: '15px',
                  alignItems: 'center',
                  marginBottom: reading.tx_hash ? '15px' : '0'
                }}
              >
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '5px' }}>Sensor</div>
                  <div style={{ fontWeight: 600, color: 'var(--primary-color)' }}>{reading.sensor_id}</div>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                    <Droplets size={16} style={{ color: 'var(--primary-color)' }} />
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Humedad</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '18px' }}>{reading.humidity_percentage}%</div>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                    <ThermometerSun size={16} style={{ color: 'var(--primary-color)' }} />
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Temperatura</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '18px' }}>{reading.temperature_celsius}°C</div>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                    <AlertCircle size={16} style={{ color: getAlertColor(reading.alert_level) }} />
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Alerta</span>
                  </div>
                  <span
                    className="badge"
                    style={{
                      background: getAlertColor(reading.alert_level),
                      color: reading.alert_level === 'Low' ? '#000' : 'white'
                    }}
                  >
                    {reading.alert_level}
                  </span>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '5px' }}>Fecha/Hora</div>
                  <div style={{ fontSize: '14px', fontWeight: 500 }}>
                    {new Date(reading.timestamp).toLocaleString('es-ES')}
                  </div>
                </div>
              </div>

              {/* TxHash Display */}
              {reading.tx_hash ? (
                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '15px' }}>
                  <TxHashDisplay
                    txHash={reading.tx_hash}
                    explorerUrl={`https://preview.cardanoscan.io/transaction/${reading.tx_hash}`}
                  />
                </div>
              ) : (
                <div
                  style={{
                    borderTop: '1px solid var(--border-color)',
                    paddingTop: '10px',
                    marginTop: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    color: 'var(--text-secondary)',
                    fontSize: '13px',
                    fontStyle: 'italic'
                  }}
                >
                  <Hash size={16} />
                  <span>TxHash no disponible</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {filteredReadings.length === 0 && (
          <div className="text-center" style={{ padding: '40px', color: 'var(--text-secondary)' }}>
            {filter ? 'No se encontraron lecturas con ese filtro' : 'No hay lecturas registradas'}
          </div>
        )}
      </div>
    </div>
  )
}

export default Readings
