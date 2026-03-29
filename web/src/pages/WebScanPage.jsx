import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'
import { 
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  LockClosedIcon,
  GlobeAltIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import { auth } from '../config/firebase'
import WebScanResults from '../components/WebScanResults'
import LoadingSpinner from '../components/LoadingSpinner'
import LoginForm from '../components/LoginForm'
import PageContainer, { PageCard } from '../components/PageContainer'
import useAuthStore from '../stores/authStore'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Module configuration with friendly names
const SCAN_MODULES = [
  { id: 'axe', nameKey: 'webScan.modules.axe.name', descKey: 'webScan.modules.axe.description' },
  { id: 'nu', nameKey: 'webScan.modules.nu.name', descKey: 'webScan.modules.nu.description' },
  { id: 'axTree', nameKey: 'webScan.modules.axTree.name', descKey: 'webScan.modules.axTree.description' },
  { id: 'galen', nameKey: 'webScan.modules.galen.name', descKey: 'webScan.modules.galen.description' },
  { id: 'links', nameKey: 'webScan.modules.links.name', descKey: 'webScan.modules.links.description' }
]

const WebScanPage = () => {
  const { t } = useTranslation()
  const { user, loading: authLoading } = useAuthStore()
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [isScanning, setIsScanning] = useState(false)
  const [scanResults, setScanResults] = useState(null)
  const [error, setError] = useState('')
  const [showLoginForm, setShowLoginForm] = useState(false)
  
  // Module selection state - default all enabled
  const [selectedModules, setSelectedModules] = useState(SCAN_MODULES.map(m => m.id))

  // Load user's module preferences from backend API
  useEffect(() => {
    const loadModulePreferences = async () => {
      if (!user) return
      
      try {
        const token = await auth.currentUser.getIdToken()
        const response = await fetch(`${API_BASE_URL}/user/preferences`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.web_scan_modules && Array.isArray(data.web_scan_modules) && data.web_scan_modules.length > 0) {
            setSelectedModules(data.web_scan_modules)
            logger.log('Loaded module preferences from API:', data.web_scan_modules)
          }
        } else {
          logger.warn('Failed to load module preferences, using defaults')
        }
      } catch (error) {
        logger.warn('Failed to load module preferences, using defaults:', error)
        // Use default preferences if API call fails
      }
    }
    
    loadModulePreferences()
  }, [user])

  // Save module preferences to backend API when they change
  const saveModulePreferences = async (modules) => {
    if (!user) return
    
    try {
      const token = await auth.currentUser.getIdToken()
      const response = await fetch(`${API_BASE_URL}/user/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          web_scan_modules: modules
        })
      })
      
      if (response.ok) {
        logger.log('Saved module preferences to API:', modules)
      } else {
        logger.warn('Failed to save module preferences')
      }
    } catch (error) {
      logger.warn('Failed to save module preferences:', error)
      // Silently fail - preferences just won't persist, but scans will still work
    }
  }

  // Handle module toggle
  const handleModuleToggle = (moduleId) => {
    setSelectedModules(prev => {
      const newModules = prev.includes(moduleId)
        ? prev.filter(id => id !== moduleId)
        : [...prev, moduleId]
      
      // Save to Firebase
      saveModulePreferences(newModules)
      
      return newModules
    })
  }

  // Reset scan state when component mounts
  useEffect(() => {
    // Only reset if we're not currently scanning
    if (!isScanning) {
      setScanResults(null)
      setError('')
      setUrl('')
      logger.log('ScanPage mounted - reset scan state')
    }
  }, [isScanning])

  const validateUrl = (url) => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const pollForResults = async (taskId, maxAttempts = 60) => {
    // Poll every 5 seconds for up to 5 minutes
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await fetch(`${API_BASE_URL}/web-scan/result/${taskId}`)
        
        if (response.ok) {
          const result = await response.json()
          logger.log('Scan result received:', result)
          setIsScanning(false)
          setScanResults(null)  // Clear processing state
          toast.success(t('webScan.toasts.scanCompleted'))
          
          // Dispatch credits update event for sidebar to refresh
          window.dispatchEvent(new CustomEvent('credits-updated'))
          
          // Navigate to results view with auto-open (same as PDF)
          navigate('/my-scans', { 
            state: { 
              autoViewScan: result,
              scanType: 'web'
            } 
          })
          return
        }
        
        // If result not ready yet, wait 5 seconds before next attempt
        if (response.status === 404) {
          logger.log(`Attempt ${attempt + 1}: Result not ready yet, waiting...`)
          await new Promise(resolve => setTimeout(resolve, 5000))
          continue
        }
        
        // If other error, break the loop - log technical details but throw user-friendly error
        logger.error(`Polling error: status ${response.status}`)
        throw new Error('scan_polling_error')
        
      } catch (err) {
        logger.error(`Polling attempt ${attempt + 1} failed:`, err)
        
        // If it's the last attempt, show error
        if (attempt === maxAttempts - 1) {
          setError(t('webScan.toasts.scanTimeout'))
          toast.error(t('webScan.toasts.scanTimeout'))
          setIsScanning(false)
          return
        }
        
        // Otherwise wait and continue
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!url.trim()) {
      setError(t('webScan.errors.enterUrl'))
      return
    }

    if (!validateUrl(url)) {
      setError(t('webScan.errors.invalidUrl'))
      return
    }

    if (!user) {
      setError(t('webScan.errors.loginRequired'))
      return
    }

    if (selectedModules.length === 0) {
      setError(t('webScan.errors.selectModule'))
      toast.error(t('webScan.toasts.selectModule'))
      return
    }

    setError('')
    setIsScanning(true)
    setScanResults(null)

    try {
      // Get user's ID token for authentication
      const token = await auth.currentUser.getIdToken()
      
      logger.log('Creating scan for:', url)
      logger.log('Selected modules:', selectedModules)
      const response = await fetch(`${API_BASE_URL}/web-scan/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          url,
          modules: selectedModules
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        // Handle insufficient credits (402) specifically
        if (response.status === 402) {
          const insufficientCreditsMsg = t('webScan.toasts.insufficientCredits')
          setError(insufficientCreditsMsg)
          toast.error(insufficientCreditsMsg)
          setIsScanning(false)
          return
        }
        // Handle other errors - detail might be object or string
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : errorData.detail?.message || t('webScan.errors.scanFailed')
        throw new Error(errorMessage)
      }

      const taskInfo = await response.json()
      logger.log('Task created:', taskInfo)
      toast.success(t('webScan.toasts.scanQueued'))
      
      // Set loading state with task info
      // Don't set scanResults here - let the loading widget show
      
      // Start polling for results
      await pollForResults(taskInfo.task_id)
      
    } catch (err) {
      logger.error('Scan error:', err)
      // Always show user-friendly translated message, never technical error details
      const userMessage = t('webScan.errors.scanFailed')
      setError(userMessage)
      toast.error(userMessage)
      setIsScanning(false)
    }
  }

  const resetScan = () => {
    setScanResults(null)
    setError('')
    setUrl('')
    setIsScanning(false)
    logger.log('Scan reset - ready for new scan')
  }

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <PageContainer className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner className="h-12 w-12" />
      </PageContainer>
    )
  }

  // Show login requirement if user is not authenticated
  if (!user) {
    return (
      <PageContainer>
        <div className="max-w-lg mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 text-white shadow-lg shadow-primary-500/25 mb-6">
              <LockClosedIcon className="h-8 w-8" aria-hidden="true" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
              {t('auth.loginRequired')}
            </h1>
            <p className="mt-3 text-gray-500 dark:text-gray-400">
              {t('webScan.loginToAccess')}
            </p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <PageCard className="mt-8 text-center">
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {t('webScan.loginDescription')}
              </p>
              <button
                onClick={() => setShowLoginForm(true)}
                className="btn-primary"
              >
                {t('auth.signInToContinue')}
              </button>
            </PageCard>
          </motion.div>
        </div>
        
        <LoginForm isOpen={showLoginForm} onClose={() => setShowLoginForm(false)} />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <div className="max-w-4xl mx-auto">
        {!scanResults && (
          <>
            {/* Header */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center mb-6 sm:mb-8"
            >
              <div className="inline-flex items-center justify-center h-12 w-12 sm:h-16 sm:w-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 text-white shadow-lg shadow-primary-500/25 mb-4 sm:mb-6">
                <GlobeAltIcon className="h-6 w-6 sm:h-8 sm:w-8" aria-hidden="true" />
              </div>
              <h1 className="text-xl xs:text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                {t('webScan.title')}
              </h1>
              <p className="mt-2 sm:mt-3 text-sm sm:text-base text-gray-500 dark:text-gray-400 max-w-xl mx-auto px-2">
                {t('webScan.description')}
              </p>
            </motion.div>

            {/* Scan Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <PageCard>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="website-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('webScan.urlLabel')}
                    </label>
                    <div className="relative">
                      <input
                        type="url"
                        id="website-url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder={t('webScan.urlPlaceholder')}
                        className={`input-field pr-12 ${error ? 'border-red-300 dark:border-red-600' : ''}`}
                        disabled={isScanning}
                        aria-describedby={error ? "url-error" : "url-help"}
                        aria-invalid={error ? 'true' : 'false'}
                      />
                      <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                        <MagnifyingGlassIcon 
                          className="h-5 w-5 text-gray-400" 
                          aria-hidden="true" 
                        />
                      </div>
                    </div>
                    {error && (
                      <p id="url-error" className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                        <ExclamationTriangleIcon className="h-4 w-4" aria-hidden="true" />
                        <span>{error}</span>
                      </p>
                    )}
                    {!error && (
                      <p id="url-help" className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                        {t('webScan.urlHelp')}
                      </p>
                    )}
                  </div>

                  {/* Module Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      {t('webScan.modules.title')}
                      <span className="ml-2 text-xs font-normal text-amber-600 dark:text-amber-400">
                        {t('webScan.modules.creditNote')}
                      </span>
                    </label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {SCAN_MODULES.map((module) => (
                        <div key={module.id} className="relative flex items-start">
                          <div className="flex items-center h-5">
                            <input
                              id={`module-${module.id}`}
                              type="checkbox"
                              checked={selectedModules.includes(module.id)}
                              onChange={() => handleModuleToggle(module.id)}
                              disabled={isScanning}
                              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded disabled:opacity-50"
                            />
                          </div>
                          <div className="ml-3 text-sm">
                            <label 
                              htmlFor={`module-${module.id}`} 
                              className="font-medium text-gray-700 dark:text-gray-300 cursor-pointer"
                            >
                              {t(module.nameKey)}
                            </label>
                            <p className="text-gray-500 dark:text-gray-400 text-xs">
                              {t(module.descKey)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {t('webScan.modules.selected', { count: selectedModules.length, total: SCAN_MODULES.length })}
                      </p>
                      <p className="text-xs font-medium text-amber-600 dark:text-amber-400">
                        {t('webScan.modules.cost', { count: selectedModules.length, plural: selectedModules.length !== 1 ? 's' : '' })}
                      </p>
                    </div>
                  </div>

                  <div>
                    <button
                      type="submit"
                      disabled={isScanning || !url.trim()}
                      className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isScanning ? (
                        <>
                          <LoadingSpinner className="h-5 w-5" />
                          <span>{t('webScan.scanning')}</span>
                        </>
                      ) : (
                        <>
                          <MagnifyingGlassIcon className="h-5 w-5" aria-hidden="true" />
                          <span>{t('webScan.startScan')}</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </PageCard>
            </motion.div>

            {/* Scanning Progress */}
            {isScanning && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="mt-8"
              >
                <PageCard className="text-center">
                  <div className="py-4">
                    <div className="relative inline-flex">
                      <LoadingSpinner className="h-16 w-16" />
                      <div className="absolute inset-0 h-16 w-16 rounded-full bg-primary-400/20 animate-ping" />
                    </div>
                    <h3 className="mt-6 text-lg font-semibold text-gray-900 dark:text-white">
                      {t('webScan.scanningProgress.title')}
                    </h3>
                    <p className="mt-2 text-gray-500 dark:text-gray-400">
                      {t('webScan.scanningProgress.description')}
                    </p>
                    <div className="mt-6 flex flex-wrap justify-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        <span>{t('webScan.scanningProgress.wcagTests')}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-primary-500 animate-pulse" />
                        <span>{t('webScan.scanningProgress.analyzingContent')}</span>
                      </div>
                    </div>
                  </div>
                </PageCard>
              </motion.div>
            )}

            {/* Information Section */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-12 grid gap-4 sm:grid-cols-3"
            >
              {[
                { icon: CheckCircleIcon, titleKey: 'webScan.info.wcag.title', descKey: 'webScan.info.wcag.description', color: 'text-green-500' },
                { icon: XCircleIcon, titleKey: 'webScan.info.issues.title', descKey: 'webScan.info.issues.description', color: 'text-red-500' },
                { icon: SparklesIcon, titleKey: 'webScan.info.quick.title', descKey: 'webScan.info.quick.description', color: 'text-primary-500' }
              ].map((item, index) => (
                <div key={t(item.titleKey)} className="bg-white dark:bg-gray-800/50 rounded-xl p-5 text-center border border-gray-100 dark:border-gray-700/50">
                  <item.icon className={`mx-auto h-8 w-8 ${item.color} mb-3`} aria-hidden="true" />
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t(item.titleKey)}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t(item.descKey)}</p>
                </div>
              ))}
            </motion.div>
          </>
        )}

        {/* Scan Results */}
        {scanResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <WebScanResults 
              results={scanResults} 
              url={url} 
              onNewScan={resetScan} 
            />
          </motion.div>
        )}
      </div>
    </PageContainer>
  )
}

export default WebScanPage
