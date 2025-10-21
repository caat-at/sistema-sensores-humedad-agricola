import { useState, useEffect } from 'react'
import { MapPin, Activity, Clock } from 'lucide-react'

function Sensors() {
  const [sensors, setSensors] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSensors()
  }, [])

  const fetchSensors = async () => {
    try {
      const res = await fetch('/api/sensors')
      const data = await res.json()
      setSensors(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching sensors:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Cargando sensores...</div>
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active': return 'var(--success-color)'
      case 'Inactive': return 'var(--text-secondary)'
      case 'Maintenance': return 'var(--warning-color)'
      case 'Error': return 'var(--danger-color)'
      default: return 'var(--text-secondary)'
    }
  }

  return (
    <div>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>Sensores Registrados</h1>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>Total de Sensores: {sensors.length}</h2>
        </div>

        <div className="grid">
          {sensors.map((sensor, idx) => (
            <div key={idx} className="sensor-card">
              <h3 style={{ color: 'var(--primary-color)', marginBottom: '15px' }}>
                {sensor.sensor_id}
              </h3>

              <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: getStatusColor(sensor.status), fontWeight: 600 }}>
                  <Activity size={18} />
                  Estado: {sensor.status}
                </div>
              </div>

              <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'start', gap: '8px' }}>
                <MapPin size={18} style={{ marginTop: '3px', color: 'var(--primary-color)' }} />
                <div>
                  <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{sensor.location.zone_name}</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Lat: {sensor.location.latitude.toFixed(2)}, Lon: {sensor.location.longitude.toFixed(2)}
                  </div>
                </div>
              </div>

              <div style={{ background: 'var(--bg-light)', padding: '15px', borderRadius: '8px', marginTop: '15px' }}>
                <div style={{ marginBottom: '8px' }}>
                  <strong>Humedad:</strong> {sensor.min_humidity_threshold}% - {sensor.max_humidity_threshold}%
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Clock size={16} />
                  <span><strong>Intervalo:</strong> {sensor.reading_interval_minutes} min</span>
                </div>
              </div>

              <div style={{ marginTop: '15px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Instalado: {new Date(sensor.installed_date).toLocaleDateString('es-ES')}
              </div>
            </div>
          ))}
        </div>

        {sensors.length === 0 && (
          <div className="text-center" style={{ padding: '40px', color: 'var(--text-secondary)' }}>
            No hay sensores registrados
          </div>
        )}
      </div>
    </div>
  )
}

export default Sensors
