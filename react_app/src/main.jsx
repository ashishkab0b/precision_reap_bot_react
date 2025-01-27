import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext'
import { DonationDialogProvider } from './contexts/DonationDialogContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <DonationDialogProvider>
        <App />
      </DonationDialogProvider>
    </AuthProvider>
  </StrictMode>
);
