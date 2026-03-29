import React from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useThemeStore } from './stores/themeStore'
import useAuthStore from './stores/authStore'
import { LanguageProvider } from './hooks/useTranslation'
import Layout from './components/Layout'
import RequireVerifiedEmail from './components/RequireVerifiedEmail'
import ScrollToTop from './components/ScrollToTop'
import HomePage from './pages/HomePage'
import WebScanPage from './pages/WebScanPage'
import PDFScanPage from './pages/PDFScanPage'
import MyScansPage from './pages/MyScansPage'
import IntegrationsPage from './pages/IntegrationsPage'
import APIPage from './pages/APIPage'
import PricingPage from './pages/PricingPage'
import ProfilePage from './pages/ProfilePage'
import PrivacyPolicyPage from './pages/PrivacyPolicyPage'
import CookiePolicyPage from './pages/CookiePolicyPage'
import LegalNoticePage from './pages/LegalNoticePage'
import TermsOfServicePage from './pages/TermsOfServicePage'
import AccessibilityStatementPage from './pages/AccessibilityStatementPage'
import ContactPage from './pages/ContactPage'
import DataProcessingAgreementPage from './pages/DataProcessingAgreementPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import FAQPage from './pages/FAQPage'
import AboutForAIPage from './pages/AboutForAIPage'
import AffiliatesPage from './pages/AffiliatesPage'

// Wrapper component to provide location for Layout
const AppRoutes = () => {
  return (
    <Layout>
      <RequireVerifiedEmail>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/scan" element={<WebScanPage />} />
          <Route path="/pdf-scan" element={<PDFScanPage />} />
          <Route path="/my-scans" element={<MyScansPage />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/api" element={<APIPage />} />
          <Route path="/privacy" element={<PrivacyPolicyPage />} />
          <Route path="/cookies" element={<CookiePolicyPage />} />
          <Route path="/legal" element={<LegalNoticePage />} />
          <Route path="/terms" element={<TermsOfServicePage />} />
          <Route path="/accessibility" element={<AccessibilityStatementPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/dpa" element={<DataProcessingAgreementPage />} />
          <Route path="/faq" element={<FAQPage />} />
          <Route path="/about-for-ai" element={<AboutForAIPage />} />
          <Route path="/affiliates" element={<AffiliatesPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </RequireVerifiedEmail>
    </Layout>
  )
}

function App() {
  const { isDarkMode } = useThemeStore()
  const { initializeAuth } = useAuthStore()

  React.useEffect(() => {
    // Apply theme class to document
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDarkMode])

  React.useEffect(() => {
    // Initialize Firebase auth listener
    initializeAuth()
  }, [initializeAuth])

  return (
    <LanguageProvider>
      <div className={`min-h-screen transition-colors duration-200 ${
        isDarkMode ? 'dark bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'
      }`}>
        <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          <ScrollToTop />
          <AppRoutes />
        </Router>
        <Toaster 
          position="top-right"
          containerStyle={{
            top: 80, // Account for mobile header
          }}
          toastOptions={{
            duration: 4000,
            className: 'text-sm font-medium',
            style: {
              background: isDarkMode ? '#1f2937' : '#ffffff',
              color: isDarkMode ? '#f3f4f6' : '#111827',
              border: isDarkMode ? '1px solid #374151' : '1px solid #e5e7eb',
              borderRadius: '12px',
              boxShadow: isDarkMode 
                ? '0 10px 25px -5px rgba(0, 0, 0, 0.4)' 
                : '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: isDarkMode ? '#1f2937' : '#ffffff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: isDarkMode ? '#1f2937' : '#ffffff',
              },
            },
          }}
        />
      </div>
    </LanguageProvider>
  )
}

export default App
