import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/index.css'
import { initializeAnalytics } from './config/analytics.js'

// Initialize Google Analytics (production only, essential cookies)
initializeAnalytics()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
