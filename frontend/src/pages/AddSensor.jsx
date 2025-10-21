import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlusCircle, Loader } from 'lucide-react'
import TxHashDisplay from '../components/TxHashDisplay'

function AddSensor() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [txData, setTxData] = useState(null)
  const [formData, setFormData] = useState({
    latitude: '',
    longitude: '',
    zone_name: '',
    min_humidity_threshold: 30,
    max_humidity_threshold: 70,
    reading_interval_minutes: 60
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name.includes('threshold') || name === 'reading_interval_minutes' || name === 'latitude' || name === 'longitude'
        ? parseFloat(value)
        : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const payload = {
        // sensor_id se auto-genera en el backend
        location: {
          latitude: formData.latitude,
          longitude: formData.longitude,
          zone_name: formData.zone_name
        },
        min_humidity_threshold: formData.min_humidity_threshold,
        max_humidity_threshold: formData.max_humidity_threshold,
        reading_interval_minutes: formData.reading_interval_minutes
      }

      const res = await fetch('/api/sensors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await res.json()

      if (res.ok) {
        setMessage({ type: 'success', text: 'Sensor registrado exitosamente!' })
        setTxData({
          tx_hash: data.tx_hash,
          explorer_url: data.explorer_url
        })
        setTimeout(() => navigate('/sensors'), 5000) // 5s para que vean el TxHash
      } else {
        setMessage({ type: 'error', text: data.detail || 'Error al registrar sensor' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Error: ${error.message}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>Registrar Nuevo Sensor</h1>

      <div className="card">
        <h2>Informaci�n del Sensor</h2>

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
          <div style={{
            padding: '15px',
            borderRadius: '8px',
            marginBottom: '20px',
            background: '#d1ecf1',
            color: '#0c5460',
            border: '1px solid #bee5eb'
          }}>
            <strong>Nota:</strong> El ID del sensor se genera automáticamente de forma secuencial (SENSOR_001, SENSOR_002, etc.)
          </div>

          <div className="form-group">
            <label>Nombre de la Zona *</label>
            <input
              type="text"
              name="zone_name"
              className="form-control"
              value={formData.zone_name}
              onChange={handleChange}
              placeholder="Ej: Campo Norte - Parcela A"
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
            <div className="form-group">
              <label>Latitud *</label>
              <input
                type="number"
                step="0.000001"
                name="latitude"
                className="form-control"
                value={formData.latitude}
                onChange={handleChange}
                placeholder="-34.58"
                required
              />
            </div>

            <div className="form-group">
              <label>Longitud *</label>
              <input
                type="number"
                step="0.000001"
                name="longitude"
                className="form-control"
                value={formData.longitude}
                onChange={handleChange}
                placeholder="-58.45"
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
            <div className="form-group">
              <label>Humedad M�nima (%) *</label>
              <input
                type="number"
                name="min_humidity_threshold"
                min="0"
                max="100"
                className="form-control"
                value={formData.min_humidity_threshold}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Humedad M�xima (%) *</label>
              <input
                type="number"
                name="max_humidity_threshold"
                min="0"
                max="100"
                className="form-control"
                value={formData.max_humidity_threshold}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Intervalo de Lectura (min) *</label>
              <input
                type="number"
                name="reading_interval_minutes"
                min="1"
                className="form-control"
                value={formData.reading_interval_minutes}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn" disabled={loading}>
            {loading ? (
              <>
                <Loader size={20} className="spinner" />
                Registrando... (puede tomar 20-30 segundos)
              </>
            ) : (
              <>
                <PlusCircle size={20} />
                Registrar Sensor
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AddSensor
