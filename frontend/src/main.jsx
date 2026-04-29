import React from 'react'
import ReactDOM from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: '#1a1d2e',
          color: '#fff',
          border: '1px solid rgba(255,255,255,0.1)',
          fontFamily: 'Inter, sans-serif',
        },
        success: { iconTheme: { primary: '#34d399', secondary: '#1a1d2e' } },
        error: { iconTheme: { primary: '#f87171', secondary: '#1a1d2e' } },
      }}
    />
  </React.StrictMode>
)
