import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Sensors from './pages/Sensors'
import Readings from './pages/Readings'
import AddSensor from './pages/AddSensor'
import AddReading from './pages/AddReading'
import './App.css'

function App() {
  const [apiHealth, setApiHealth] = useState(null)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setApiHealth(data))
      .catch(err => console.error('API Health Check failed:', err))
  }, [])

  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="container">
            <h1 className="logo">Sensores Agricolas</h1>
            <div className="nav-links">
              <Link to="/">Dashboard</Link>
              <Link to="/sensors">Sensores</Link>
              <Link to="/readings">Lecturas</Link>
              <Link to="/add-sensor">Agregar Sensor</Link>
              <Link to="/add-reading">Agregar Lectura</Link>
            </div>
            {apiHealth && (
              <div className="api-status">
                <span className="status-dot"></span>
                API: {apiHealth.status}
              </div>
            )}
          </div>
        </nav>

        <div className="container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sensors" element={<Sensors />} />
            <Route path="/readings" element={<Readings />} />
            <Route path="/add-sensor" element={<AddSensor />} />
            <Route path="/add-reading" element={<AddReading />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
