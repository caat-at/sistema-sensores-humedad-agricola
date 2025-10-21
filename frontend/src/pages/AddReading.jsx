import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlusCircle, Loader } from 'lucide-react'
import TxHashDisplay from '../components/TxHashDisplay'

function AddReading() {
  const navigate = useNavigate()
  const [sensors, setSensors] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [txData, setTxData] = useState(null)
  const [formData, setFormData] = useState({
    sensor_id: '',
    humidity_percentage: 50,
    temperature_celsius: 20
  })

  useEffect(() => {
    fetchSensors()
  }, [])

  const fetchSensors = async () => {
    try {
      const res = await fetch('/api/sensors')
      const data = await res.json()
      setSensors(data.filter(s => s.status === 'Active'))
    } catch (error) {
      console.error('Error fetching sensors:', error)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'sensor_id' ? value : parseFloat(value)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const res = await fetch('/api/readings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      const data = await res.json()

      if (res.ok) {
        setMessage({ type: 'success', text: 'Lectura agregada exitosamente!' })
        setTxData({
          tx_hash: data.tx_hash,
          explorer_url: data.explorer_url
        })
        setTimeout(() => navigate('/readings'), 5000) // 5s para que vean el TxHash
      } else {
        setMessage({ type: 'error', text: data.detail || 'Error al agregar lectura' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Error: ${error.message}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>Agregar Nueva Lectura</h1>

      <div className="card">
        <h2>Datos de la Lectura</h2>

        {message && (
          <div
            style={{
              padding: '15px',
              borderRadius: '8px',
              marginBottom: '20px',
              background: message.type === 'success' ? '#d4edda' : '#f8d7da',
              color: message.type === 'success' ? '#155724' : '#721c24',
              border: `1px solid ${message.type === 'success' ? '#c3e6cb' : '#f5c6cb'}`
            }}
          >
            {message.text}
          </div>
        )}

        {txData && (
          <TxHashDisplay
            txHash={txData.tx_hash}
            explorerUrl={txData.explorer_url}
          />
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Seleccionar Sensor *</label>
            <select
              name="sensor_id"
              className="form-control"
              value={formData.sensor_id}
              onChange={handleChange}
              required
            >
              <option value="">-- Seleccionar sensor activo --</option>
              {sensors.map(sensor => (
                <option key={sensor.sensor_id} value={sensor.sensor_id}>
                  {sensor.sensor_id} - {sensor.location.zone_name}
                </option>
              ))}
            </select>
            <small style={{ display: 'block', marginTop: '5px', color: 'var(--text-secondary)' }}>
              Solo se muestran sensores activos
            </small>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
            <div className="form-group">
              <label>Humedad (%) *</label>
              <input
                type="number"
                name="humidity_percentage"
                min="0"
                max="100"
                step="0.1"
                className="form-control"
                value={formData.humidity_percentage}
                onChange={handleChange}
                required
              />
              <small style={{ display: 'block', marginTop: '5px', color: 'var(--text-secondary)' }}>
                Valor entre 0 y 100
              </small>
            </div>

            <div className="form-group">
              <label>Temperatura (�C) *</label>
              <input
                type="number"
                name="temperature_celsius"
                min="-40"
                max="85"
                step="0.1"
                className="form-control"
                value={formData.temperature_celsius}
                onChange={handleChange}
                required
              />
              <small style={{ display: 'block', marginTop: '5px', color: 'var(--text-secondary)' }}>
                Valor entre -40�C y 85�C
              </small>
            </div>
          </div>

          {formData.sensor_id && sensors.find(s => s.sensor_id === formData.sensor_id) && (
            <div
              style={{
                background: 'var(--bg-light)',
                padding: '15px',
                borderRadius: '8px',
                marginTop: '20px'
              }}
            >
              <h4 style={{ marginBottom: '10px', color: 'var(--primary-color)' }}>Informaci�n del Sensor Seleccionado</h4>
              {(() => {
                const sensor = sensors.find(s => s.sensor_id === formData.sensor_id)
                return (
                  <div>
                    <p><strong>Zona:</strong> {sensor.location.zone_name}</p>
                    <p><strong>Umbral de Humedad:</strong> {sensor.min_humidity_threshold}% - {sensor.max_humidity_threshold}%</p>
                    <p><strong>Intervalo:</strong> {sensor.reading_interval_minutes} minutos</p>
                  </div>
                )
              })()}
            </div>
          )}

          <button type="submit" className="btn" disabled={loading || !formData.sensor_id} style={{ marginTop: '20px' }}>
            {loading ? (
              <>
                <Loader size={20} className="spinner" />
                Agregando... (puede tomar 20-30 segundos)
              </>
            ) : (
              <>
                <PlusCircle size={20} />
                Agregar Lectura
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AddReading
