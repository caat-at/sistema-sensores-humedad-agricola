import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Activity, Droplets, ThermometerSun, AlertTriangle } from 'lucide-react'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [readings, setReadings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [statsRes, readingsRes] = await Promise.all([
        fetch('/api/stats'),
        fetch('/api/readings?limit=10')
      ])

      const statsData = await statsRes.json()
      const readingsData = await readingsRes.json()

      setStats(statsData)
      setReadings(readingsData)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Cargando dashboard...</div>
  }

  const chartData = readings.map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
    humedad: r.humidity_percentage,
    temperatura: r.temperature_celsius
  })).reverse()

  const alertData = stats.alert_level_distribution ? Object.entries(stats.alert_level_distribution).map(([name, value]) => ({
    name,
    cantidad: value
  })) : []

  return (
    <div>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>Dashboard de Monitoreo</h1>

      {/* Stats Cards */}
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <Activity size={24} />
            <h3 style={{ margin: 0 }}>Sensores Activos</h3>
          </div>
          <div className="stat-value">{stats?.active_sensors || 0}</div>
          <div className="stat-label">de {stats?.total_sensors || 0} totales</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <Droplets size={24} />
            <h3 style={{ margin: 0 }}>Humedad Promedio</h3>
          </div>
          <div className="stat-value">{stats?.humidity_stats?.avg?.toFixed(1) || 0}%</div>
          <div className="stat-label">Rango: {stats?.humidity_stats?.min}% - {stats?.humidity_stats?.max}%</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <ThermometerSun size={24} />
            <h3 style={{ margin: 0 }}>Temperatura Promedio</h3>
          </div>
          <div className="stat-value">{stats?.temperature_stats?.avg?.toFixed(1) || 0}�</div>
          <div className="stat-label">Rango: {stats?.temperature_stats?.min}� - {stats?.temperature_stats?.max}�</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <AlertTriangle size={24} />
            <h3 style={{ margin: 0 }}>Total Lecturas</h3>
          </div>
          <div className="stat-value">{stats?.total_readings || 0}</div>
          <div className="stat-label">En el sistema</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', marginTop: '30px' }}>
        <div className="card">
          <h2>Humedad y Temperatura (�ltimas 10 lecturas)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="humedad" stroke="#667eea" strokeWidth={2} name="Humedad %" />
              <Line type="monotone" dataKey="temperatura" stroke="#764ba2" strokeWidth={2} name="Temperatura �C" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2>Distribuci�n de Niveles de Alerta</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={alertData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="cantidad" fill="#667eea" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Readings */}
      <div className="card" style={{ marginTop: '30px' }}>
        <h2>Lecturas Recientes</h2>
        <div style={{ overflowX: 'auto' }}>
          <table className="table" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px' }}>
            <thead>
              <tr style={{ background: '#f8f9fa' }}>
                <th style={{ padding: '12px', textAlign: 'left' }}>Sensor</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Humedad</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Temperatura</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Nivel Alerta</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Fecha/Hora</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>TX Hash</th>
              </tr>
            </thead>
            <tbody>
              {readings.map((reading, idx) => (
                <tr key={idx}>
                  <td style={{ padding: '12px' }}>{reading.sensor_id}</td>
                  <td style={{ padding: '12px' }}>{reading.humidity_percentage}%</td>
                  <td style={{ padding: '12px' }}>{reading.temperature_celsius}�C</td>
                  <td style={{ padding: '12px' }}>
                    <span className={`badge badge-${
                      reading.alert_level === 'Critical' ? 'danger' :
                      reading.alert_level === 'High' ? 'warning' :
                      reading.alert_level === 'Low' ? 'warning' : 'success'
                    }`}>
                      {reading.alert_level}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    {new Date(reading.timestamp).toLocaleString('es-ES')}
                  </td>
                  <td style={{ padding: '12px' }}>
                    {reading.tx_hash ? (
                      <a
                        href={`https://preview.cardanoscan.io/transaction/${reading.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          color: '#667eea',
                          textDecoration: 'none',
                          fontFamily: 'monospace',
                          fontSize: '0.85em'
                        }}
                        title={reading.tx_hash}
                      >
                        {reading.tx_hash.substring(0, 8)}...{reading.tx_hash.substring(reading.tx_hash.length - 8)}
                      </a>
                    ) : (
                      <span style={{ color: '#999', fontSize: '0.85em' }}>-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
