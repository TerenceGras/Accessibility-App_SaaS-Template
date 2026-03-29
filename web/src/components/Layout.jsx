import React, { useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Footer from './Footer'
import PageTransition from './PageTransition'
import { useTranslation } from '../hooks/useTranslation'

const Layout = ({ children }) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const location = useLocation()
  const { t } = useTranslation()

  return (
    <div className="min-h-screen">
      {/* Skip to main content link for screen readers */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[60] 
          bg-primary-500 text-white px-4 py-2 rounded-lg font-medium
          focus:outline-none focus:ring-2 focus:ring-primary-300 focus:ring-offset-2"
      >
        {t('accessibility.skipToMain')}
      </a>
      
      {/* Sidebar Navigation */}
      <Sidebar isMobileOpen={isMobileOpen} setIsMobileOpen={setIsMobileOpen} />
      
      {/* Main Content Area - offset by sidebar on desktop */}
      <div className="lg:pl-64 flex flex-col min-h-screen">
        {/* Add top padding on mobile for fixed header */}
        <main 
          id="main-content" 
          className="flex-grow pt-16 lg:pt-0"
          aria-label={t('accessibility.mainContent')}
        >
          <AnimatePresence mode="wait">
            <PageTransition key={location.pathname}>
              {children}
            </PageTransition>
          </AnimatePresence>
        </main>
        
        <Footer />
      </div>
    </div>
  )
}

export default Layout
