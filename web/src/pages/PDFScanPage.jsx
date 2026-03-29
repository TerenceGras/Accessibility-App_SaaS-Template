import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'
import { 
  DocumentArrowUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  LockClosedIcon,
  InformationCircleIcon,
  SparklesIcon,
  DocumentIcon
} from '@heroicons/react/24/outline'
import { auth } from '../config/firebase'
import LoadingSpinner from '../components/LoadingSpinner'
import LoginForm from '../components/LoginForm'
import PageContainer, { PageCard } from '../components/PageContainer'
import useAuthStore from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const PDFScanPage = () => {
  const { t } = useTranslation()
  const { user, loading: authLoading } = useAuthStore()
  const { isDarkMode } = useThemeStore()
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanResults, setScanResults] = useState(null)
  const [error, setError] = useState('')
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  // Reset scan state when component mounts
  useEffect(() => {
    if (!isScanning) {
      setScanResults(null)
      setError('')
      setFile(null)
      logger.log('PDFScanPage mounted - reset scan state')
    }
  }, [isScanning])

  const validateFile = (file) => {
    if (!file) return { valid: false, message: t('pdfScan.errors.selectFile') }
    
    if (file.type !== 'application/pdf') {
      return { valid: false, message: t('pdfScan.errors.pdfOnly') }
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB
      return { valid: false, message: t('pdfScan.errors.maxSize') }
    }
    
    return { valid: true }
  }

  const pollForResults = async (taskId, maxAttempts = 60) => {
    // Poll every 5 seconds for up to 5 minutes
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await fetch(`${API_BASE_URL}/pdf-scan/result/${taskId}`)
        
        if (response.ok) {
          const result = await response.json()
          logger.log('PDF scan result received:', result)
          setIsScanning(false)
          setScanResults(result)
          toast.success(t('pdfScan.toasts.scanCompleted'))
          
          // Dispatch credits update event for sidebar to refresh
          window.dispatchEvent(new CustomEvent('credits-updated'))
          
          // Navigate to results view with auto-open
          navigate('/my-scans', { 
            state: { 
              autoViewScan: result,
              scanType: 'pdf'
            } 
          })
          return
        } else if (response.status === 404) {
          // Task not found yet, continue polling
          await new Promise(resolve => setTimeout(resolve, 5000))
          continue
        } else {
          // Log technical details but throw user-friendly error
          logger.error(`Polling error: status ${response.status}`)
          throw new Error('scan_polling_error')
        }
      } catch (error) {
        logger.error('Polling error:', error)
        // Continue polling on error
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
    }
    
    // Timeout reached
    setIsScanning(false)
    setError(t('pdfScan.toasts.scanTimeout'))
    toast.error(t('pdfScan.toasts.scanTimeout'))
  }

  const handleScan = async () => {
    if (!file) {
      setError(t('pdfScan.errors.selectFile'))
      return
    }

    const validation = validateFile(file)
    if (!validation.valid) {
      setError(validation.message)
      return
    }

    if (!user) {
      setError(t('pdfScan.errors.loginRequired'))
      return
    }

    setError('')
    setIsScanning(true)
    setScanResults(null)

    try {
      // Get user's ID token for authentication
      const token = await auth.currentUser.getIdToken()
      
      logger.log('Creating PDF scan for:', file.name)
      
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${API_BASE_URL}/pdf-scan/scan`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        // Handle insufficient credits (402) specifically
        if (response.status === 402) {
          const insufficientCreditsMsg = t('pdfScan.toasts.insufficientCredits')
          setError(insufficientCreditsMsg)
          toast.error(insufficientCreditsMsg)
          setIsScanning(false)
          return
        }
        // Handle other errors - detail might be object or string
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : errorData.detail?.message || t('pdfScan.errors.scanFailed')
        throw new Error(errorMessage)
      }

      const taskInfo = await response.json()
      logger.log('PDF scan task created:', taskInfo)
      toast.success(t('pdfScan.toasts.scanQueued'))
      
      // Set loading state with task info
      setScanResults({
        file_name: file.name,
        taskId: taskInfo.task_id,
        status: 'processing',
        message: 'Your PDF is being analyzed using AI for accessibility issues...'
      })
      
      // Start polling for results
      pollForResults(taskInfo.task_id)
      
    } catch (error) {
      logger.error('PDF scan error:', error)
      // Always show user-friendly translated message, never technical error details
      const userMessage = t('pdfScan.errors.scanFailed')
      setError(userMessage)
      setIsScanning(false)
      toast.error(userMessage)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      const validation = validateFile(droppedFile)
      
      if (validation.valid) {
        setFile(droppedFile)
        setError('')
      } else {
        setError(validation.message)
      }
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      const validation = validateFile(selectedFile)
      
      if (validation.valid) {
        setFile(selectedFile)
        setError('')
      } else {
        setError(validation.message)
      }
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (authLoading) {
    return (
      <PageContainer className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner className="h-12 w-12" />
      </PageContainer>
    )
  }

  if (!user && showLoginForm) {
    return (
      <PageContainer>
        <LoginForm isOpen={showLoginForm} onClose={() => setShowLoginForm(false)} />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <div className="max-w-4xl mx-auto px-2 sm:px-0">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-6 sm:mb-8"
        >
          <div className="inline-flex items-center justify-center h-12 w-12 sm:h-16 sm:w-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 text-white shadow-lg shadow-primary-500/25 mb-4 sm:mb-6">
            <DocumentIcon className="h-6 w-6 sm:h-8 sm:w-8" aria-hidden="true" />
          </div>
          <h1 className="text-xl xs:text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {t('pdfScan.title')}
          </h1>
          <p className="mt-2 sm:mt-3 text-sm sm:text-base text-gray-500 dark:text-gray-400 max-w-xl mx-auto px-2">
            {t('pdfScan.description')}
          </p>
        </motion.div>

        {/* File Upload Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <PageCard className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('pdfScan.uploadTitle')}</h2>
              <span className="badge badge-warning">{t('pdfScan.creditNote')}</span>
            </div>
          
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                dragActive 
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {file ? (
                <div className="space-y-4">
                  <div className="inline-flex items-center justify-center h-14 w-14 rounded-xl bg-green-100 dark:bg-green-900/30">
                    <CheckCircleIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">{file.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{t('pdfScan.fileSelected.size', { size: formatFileSize(file.size) })}</p>
                  </div>
                  <button
                    onClick={() => setFile(null)}
                    className="text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                  >
                    {t('pdfScan.fileSelected.remove')}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="inline-flex items-center justify-center h-14 w-14 rounded-xl bg-gray-100 dark:bg-gray-800">
                    <DocumentArrowUpIcon className="h-8 w-8 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      {t('pdfScan.dropzone.title')}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{t('pdfScan.dropzone.maxSize')}</p>
                  </div>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="pdf-upload"
                  />
                  <label
                    htmlFor="pdf-upload"
                    className="btn-secondary cursor-pointer inline-flex"
                  >
                    {t('pdfScan.dropzone.selectFile')}
                  </label>
                </div>
              )}
            </div>
          </PageCard>
        </motion.div>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6"
          >
            <div className="flex gap-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-red-800 dark:text-red-300">{t('pdfScan.results.error')}</h3>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Scan Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-center mb-8"
        >
          {!user ? (
            <div className="space-y-4">
              <PageCard className="text-left">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <LockClosedIcon className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-300">{t('pdfScan.loginRequired.title')}</h3>
                    <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                      {t('pdfScan.loginRequired.description')}
                    </p>
                  </div>
                </div>
              </PageCard>
              <button
                onClick={() => setShowLoginForm(true)}
                className="btn-primary"
              >
                <LockClosedIcon className="h-5 w-5" />
                {t('pdfScan.loginRequired.signIn')}
              </button>
            </div>
          ) : (
            <button
              onClick={handleScan}
              disabled={!file || isScanning}
              className="btn-primary text-lg px-8 py-4"
            >
              {isScanning ? (
                <>
                  <LoadingSpinner className="h-5 w-5" />
                  <span>{t('pdfScan.scanning')}</span>
                </>
              ) : (
                <>
                  <SparklesIcon className="h-5 w-5" />
                  <span>{t('pdfScan.startScan')}</span>
                </>
              )}
            </button>
          )}
        </motion.div>

        {/* Scanning Progress */}
        {isScanning && scanResults && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <PageCard className="mb-6">
              <div className="flex items-start gap-4">
                <div className="relative">
                  <LoadingSpinner className="h-8 w-8" />
                  <div className="absolute inset-0 h-8 w-8 rounded-full bg-primary-400/20 animate-ping" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Scanning {scanResults.file_name}
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400 mt-1">
                    {scanResults.message}
                  </p>
                </div>
              </div>
            </PageCard>
          </motion.div>
        )}

        {/* Information Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800/50 rounded-2xl p-6"
        >
          <div className="flex gap-4">
            <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
              <SparklesIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                {t('pdfScan.aiInfo.title')}
              </h3>
              <p className="text-blue-800 dark:text-blue-200 text-sm mt-1">
                {t('pdfScan.aiInfo.description')}
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </PageContainer>
  )
}

export default PDFScanPage
