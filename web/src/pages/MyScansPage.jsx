import React, { useState, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  DocumentTextIcon,
  CalendarIcon,
  GlobeAltIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  LockClosedIcon,
  DocumentIcon,
  TrashIcon,
  FolderIcon
} from '@heroicons/react/24/outline'
import { auth } from '../config/firebase'
import LoadingSpinner from '../components/LoadingSpinner'
import WebScanResults from '../components/WebScanResults'
import PDFScanResults from '../components/PDFScanResults'
import LoginForm from '../components/LoginForm'
import DeleteConfirmationDialog from '../components/DeleteConfirmationDialog'
import PageContainer, { PageCard } from '../components/PageContainer'
import useAuthStore from '../stores/authStore'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || ''
const REPORT_GENERATOR_URL = import.meta.env.VITE_REPORT_GENERATOR_URL || ''

const MyScansPage = () => {
  const { t } = useTranslation()
  const { user, loading: authLoading } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [activeTab, setActiveTab] = useState('web') // 'web' or 'pdf'
  const [webScans, setWebScans] = useState([])
  const [pdfScans, setPdfScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedScan, setSelectedScan] = useState(null)
  const [viewingScan, setViewingScan] = useState(false)
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [deletingScans, setDeletingScans] = useState({})
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [scanToDelete, setScanToDelete] = useState(null)

  useEffect(() => {
    if (user) {
      fetchWebScans()
      fetchPdfScans()
    }
  }, [user])

  // Check if we should automatically open a scan view (from navigation state)
  useEffect(() => {
    if (location.state?.autoViewScan) {
      const scanToView = location.state.autoViewScan
      const scanType = location.state.scanType || 'web'
      logger.log('Auto-opening scan view:', scanToView, 'type:', scanType)
      
      setActiveTab(scanType)
      setSelectedScan(scanToView)
      setViewingScan(true)
      
      // Clear the navigation state to prevent re-opening on refresh
      navigate(location.pathname, { replace: true, state: {} })
    }
  }, [location.state, navigate, location.pathname])

  const fetchWebScans = async () => {
    try {
      setLoading(true)
      setError('')
      
      const token = await auth.currentUser.getIdToken()
      
      const response = await fetch(`${API_BASE_URL}/web-scan/my-scans`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch web scans')
      }

      const data = await response.json()
      setWebScans(data.scans || [])
      
    } catch (err) {
      logger.error('Error fetching web scans:', err)
      setError(t('myScans.toasts.loadWebScansFailed'))
      toast.error(t('myScans.toasts.loadWebScansFailed'))
    } finally {
      setLoading(false)
    }
  }

  const fetchPdfScans = async () => {
    try {
      const token = await auth.currentUser.getIdToken()
      
      const response = await fetch(`${API_BASE_URL}/pdf-scan/my-scans`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch PDF scans')
      }

      const data = await response.json()
      setPdfScans(data.scans || [])
      
    } catch (err) {
      logger.error('Error fetching PDF scans:', err)
      // Don't show error for PDF scans if web scans worked
      if (webScans.length === 0) {
        setError(t('myScans.toasts.loadPdfScansFailed'))
        toast.error(t('myScans.toasts.loadPdfScansFailed'))
      }
    }
  }

  const getCurrentScans = () => {
    return activeTab === 'web' ? webScans : pdfScans
  }

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      return 'Invalid date'
    }
  }

  // Format large numbers with k, M suffixes
  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'k'
    }
    return num.toString()
  }

  const getSeverityColor = (violationsCount) => {
    if (violationsCount === 0) return 'text-green-600 bg-green-50 dark:bg-green-900/20'
    if (violationsCount <= 5) return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20'
    if (violationsCount <= 15) return 'text-orange-600 bg-orange-50 dark:bg-orange-900/20'
    return 'text-red-600 bg-red-50 dark:bg-red-900/20'
  }

  const [loadingFullScan, setLoadingFullScan] = useState(false)

  const handleViewScan = async (scan) => {
    // If scan already has full results (from autoViewScan navigation state), use directly
    if (scan.violations || scan.unified_results || scan.accessibility_report) {
      setSelectedScan(scan)
      setViewingScan(true)
      return
    }

    // Otherwise, fetch full results from API
    try {
      setLoadingFullScan(true)
      const token = await auth.currentUser.getIdToken()
      
      // Different endpoints for web vs PDF scans
      const endpoint = activeTab === 'pdf'
        ? `${API_BASE_URL}/pdf-scan/result/${scan.id}`
        : `${API_BASE_URL}/web-scan/result/${scan.id}/full`
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch scan details')
      }

      const fullResult = await response.json()
      
      // Merge metadata with full result
      const scanWithFullResult = {
        ...scan,
        full_result: fullResult,
        // Also spread the full result fields directly for compatibility
        ...fullResult
      }
      
      setSelectedScan(scanWithFullResult)
      setViewingScan(true)
      
    } catch (err) {
      logger.error('Error fetching full scan details:', err)
      toast.error(t('myScans.toasts.loadDetailsFailed'))
    } finally {
      setLoadingFullScan(false)
    }
  }

  const handleCloseScanView = () => {
    setViewingScan(false)
    setSelectedScan(null)
  }

  const handleStartNewScan = () => {
    if (activeTab === 'pdf') {
      navigate('/pdf-scan')
    } else {
      navigate('/scan')
    }
  }

  const handleDownloadPDF = async (scan) => {
    const scanType = activeTab
    const identifier = scanType === 'pdf' ? scan.file_name : scan.url
    
    try {
      toast.loading(`Generating PDF report for ${identifier}...`)
      
      let endpoint = ''
      let payload = {}
      
      if (scanType === 'pdf') {
        // PDF scan report - use full_result if available, otherwise use scan data
        const reportData = scan.full_result || scan
        
        // Get accessibility_report from multiple possible locations
        const accessibilityReport = 
          reportData.accessibility_report || 
          reportData.unified_results?.accessibility_report ||
          scan.accessibility_report ||
          scan.unified_results?.accessibility_report
        
        endpoint = `${REPORT_GENERATOR_URL}/generate/pdf-scan`
        payload = {
          file_name: reportData.file_name || scan.file_name,
          accessibility_report: accessibilityReport,
          unified_results: reportData.unified_results || scan.unified_results,
          timestamp: reportData.timestamp || scan.timestamp || scan.created_at,
          analysis_type: reportData.analysis_type || scan.analysis_type
        }
      } else {
        // Web scan report - use full_result if available, otherwise use scan data
        const reportData = scan.full_result || scan
        
        endpoint = `${REPORT_GENERATOR_URL}/generate/web-scan`
        payload = {
          url: reportData.url || scan.url,
          violations: reportData.violations || [],
          passes: reportData.passes || [],
          incomplete: reportData.incomplete || [],
          inapplicable: reportData.inapplicable || [],
          unified_results: reportData.unified_results,
          timestamp: reportData.timestamp || scan.timestamp || scan.created_at,
          testEngine: reportData.testEngine,
          taskId: scan.id,
          accessibility_score: reportData.accessibility_score || scan.accessibility_score
        }
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        throw new Error('Failed to generate PDF report')
      }
      
      // Get the PDF blob
      const blob = await response.blob()
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // Generate filename
      const date = new Date().toISOString().split('T')[0]
      const filename = scanType === 'pdf' 
        ? `pdf-accessibility-report-${scan.file_name.replace('.pdf', '')}-${date}.pdf`
        : `web-accessibility-report-${scan.url.replace(/https?:\/\//, '').replace(/[^a-z0-9]/gi, '-').substring(0, 50)}-${date}.pdf`
      
      link.download = filename
      document.body.appendChild(link)
      link.click()
      
      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.dismiss()
      toast.success(t('myScans.pdfDownloadSuccess'))
      
    } catch (error) {
      logger.error('Error downloading PDF report:', error)
      toast.dismiss()
      toast.error(t('myScans.pdfDownloadError'))
    }
  }

  const handleDeleteClick = (scan) => {
    setScanToDelete(scan)
    setShowDeleteDialog(true)
  }

  const handleDeleteConfirm = async () => {
    if (!scanToDelete) return

    const scanId = scanToDelete.id
    const scanType = activeTab
    
    setDeletingScans(prev => ({ ...prev, [scanId]: true }))
    
    try {
      const token = await auth.currentUser.getIdToken()
      const endpoint = scanType === 'pdf' 
        ? `${API_BASE_URL}/pdf-scan/my-scans/${scanId}`
        : `${API_BASE_URL}/web-scan/my-scans/${scanId}`
      
      const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to delete scan')
      }

      toast.success(t('myScans.deleteSuccess'))
      
      // Remove from local state
      if (scanType === 'pdf') {
        setPdfScans(prev => prev.filter(s => s.id !== scanId))
      } else {
        setWebScans(prev => prev.filter(s => s.id !== scanId))
      }
      
      // Close dialog
      setShowDeleteDialog(false)
      setScanToDelete(null)
      
    } catch (err) {
      logger.error('Error deleting scan:', err)
      toast.error(t('myScans.deleteError'))
    } finally {
      setDeletingScans(prev => {
        const newState = { ...prev }
        delete newState[scanId]
        return newState
      })
    }
  }

  const handleDeleteDialogClose = () => {
    setShowDeleteDialog(false)
    setScanToDelete(null)
  }

  // ScanCard component for rendering individual scan items
  const ScanCard = ({ scan, scanType, onView, onDownload, onDelete, formatDate, getSeverityColor }) => (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 sm:p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
      <div className="flex items-start sm:items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* Title and Date */}
          <div className="flex items-center space-x-2 sm:space-x-3 mb-2">
            {scanType === 'web' ? (
              <GlobeAltIcon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 flex-shrink-0" />
            ) : (
              <DocumentIcon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 flex-shrink-0" />
            )}
            <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-white truncate max-w-[150px] sm:max-w-none">
              {scanType === 'web' ? scan.url : scan.file_name}
            </p>
          </div>
          
          {/* Date */}
          <div className="flex items-center space-x-3 mb-3">
            <CalendarIcon className="h-4 w-4 text-gray-400" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {formatDate(scan.created_at)}
            </p>
          </div>
          
          {/* Results Summary - wrap on mobile */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-sm">
            {/* For PDF scans with free-text format, show different summary */}
            {scanType === 'pdf' && (scan.analysis_type === 'ai_vision_free_text' || scan.accessibility_report) ? (
              <>
                <span className="inline-flex items-center px-2 sm:px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 dark:bg-blue-900/20">
                  <DocumentTextIcon className="h-3 w-3 mr-1" />
                  <span className="hidden xs:inline">{t('myScans.aiAnalysisComplete')}</span>
                  <span className="xs:hidden">{t('myScans.aiDone')}</span>
                </span>
                {scan.pages_analyzed && (
                  <span className="inline-flex items-center text-gray-500 dark:text-gray-400 text-xs">
                    <DocumentIcon className="h-3 w-3 mr-1" />
                    {scan.pages_analyzed} {t('myScans.pages')}
                  </span>
                )}
              </>
            ) : (
              <>
                {/* For web scans, show comprehensive issue breakdown */}
                {scanType === 'web' ? (
                  <>
                    {/* WCAG Violations - use total_violations (individual nodes count) */}
                    {(scan.summary?.total_violations || 0) > 0 && (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(scan.summary?.total_violations || 0)}`}>
                        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                        {formatNumber(scan.summary.total_violations)} WCAG
                      </span>
                    )}
                    {/* HTML Errors */}
                    {(scan.summary?.total_html_errors || 0) > 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-50 text-orange-600 dark:bg-orange-900/20">
                        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                        {formatNumber(scan.summary.total_html_errors)} HTML
                      </span>
                    )}
                    {/* Broken Links */}
                    {(scan.summary?.total_broken_links || 0) > 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20">
                        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                        {formatNumber(scan.summary.total_broken_links)} Links
                      </span>
                    )}
                    {/* All Clean */}
                    {(scan.summary?.total_violations || 0) === 0 && 
                     (scan.summary?.total_html_errors || 0) === 0 && 
                     (scan.summary?.total_broken_links || 0) === 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-green-600 bg-green-50 dark:bg-green-900/20">
                        <CheckCircleIcon className="h-3 w-3 mr-1" />
                        {t('myScans.allClean')}
                      </span>
                    )}
                    {/* Passes count */}
                    {(scan.summary?.total_passes || 0) > 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-green-600 bg-green-50 dark:bg-green-900/20">
                        <CheckCircleIcon className="h-3 w-3 mr-1" />
                        {formatNumber(scan.summary.total_passes)} {t('myScans.passed')}
                      </span>
                    )}
                    {/* Scan duration */}
                    {scan.scan_duration && (
                      <span className="inline-flex items-center text-gray-500 dark:text-gray-400 text-xs">
                        <ClockIcon className="h-3 w-3 mr-1" />
                        {Math.round(scan.scan_duration / 1000)}s
                      </span>
                    )}
                  </>
                ) : scanType === 'pdf' ? (
                  /* For PDF scans with AI vision, just show the scan type badge */
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 dark:bg-blue-900/20">
                    <DocumentTextIcon className="h-3 w-3 mr-1" />
                    AI Vision
                  </span>
                ) : (
                  /* For PDF scans with old format (legacy), show issues/passes */
                  <>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(scan.violations_count)}`}>
                      <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                      {scan.violations_count || 0} {t('myScans.issues')}
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-green-600 bg-green-50 dark:bg-green-900/20">
                      <CheckCircleIcon className="h-3 w-3 mr-1" />
                      {scan.passes_count || 0} {t('myScans.passed')}
                    </span>
                  </>
                )}
              </>
            )}
          </div>
        </div>
        
        {/* Actions - responsive for small screens */}
        <div className="flex items-center space-x-1 sm:space-x-2 ml-2 sm:ml-4 flex-shrink-0">
          <button
            onClick={() => onView(scan)}
            className="btn-secondary px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium flex items-center space-x-1"
          >
            <EyeIcon className="h-4 w-4" />
            <span className="hidden xs:inline sm:inline">{t('common.view')}</span>
          </button>
          <button
            onClick={() => onDownload(scan)}
            className="btn-primary px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium flex items-center space-x-1"
            title={t('myScans.downloadPdfReportTitle')}
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            <span className="hidden sm:inline">PDF</span>
          </button>
          <button
            onClick={() => onDelete(scan)}
            className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium flex items-center space-x-1 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors duration-200"
            title={t('myScans.deleteScanTitle')}
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )

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
              {t('myScans.loginRequired')}
            </h1>
            <p className="mt-3 text-gray-500 dark:text-gray-400">
              {t('myScans.signInToView')}
            </p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <PageCard className="mt-8 text-center">
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {t('myScans.historyPrivate')}
              </p>
              <button
                onClick={() => setShowLoginForm(true)}
                className="btn-primary"
              >
                {t('myScans.signInToContinue')}
              </button>
            </PageCard>
          </motion.div>
        </div>
        
        <LoginForm isOpen={showLoginForm} onClose={() => setShowLoginForm(false)} />
      </PageContainer>
    )
  }

  // Show loading spinner while fetching full scan details
  if (loadingFullScan) {
    return (
      <PageContainer title={t('myScans.title')}>
        <div className="flex items-center justify-center min-h-[300px]">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600 dark:text-gray-400">{t('myScans.loadingDetails')}</span>
        </div>
      </PageContainer>
    )
  }

  // Show scan details view
  if (viewingScan && selectedScan) {
    // Handle case where selectedScan IS the scan result (from auto-view) vs when it's a scan object with full_result
    const scanResults = selectedScan.full_result || selectedScan
    const displayUrl = selectedScan.url || selectedScan.file_name || 'PDF Scan'
    
    // Determine which component to use based on scan type
    const ScanResultsComponent = activeTab === 'pdf' ? PDFScanResults : WebScanResults
    
    return (
      <PageContainer>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <ScanResultsComponent 
            results={scanResults} 
            url={displayUrl}
            onBackToScans={handleCloseScanView}
          />
        </motion.div>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title={t('myScans.title')}
      description={t('myScans.description')}
      action={
        <button
          onClick={() => {
            fetchWebScans()
            fetchPdfScans()
          }}
          className="btn-secondary"
          disabled={loading}
        >
          {loading ? t('common.refreshing') : t('common.refresh')}
        </button>
      }
    >
      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-6"
      >
        <div className="inline-flex bg-white dark:bg-gray-800 rounded-xl p-1 shadow-sm border border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('web')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === 'web'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <GlobeAltIcon className="h-4 w-4" />
            <span>{t('myScans.websiteScans')} ({webScans.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('pdf')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === 'pdf'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <DocumentIcon className="h-4 w-4" />
            <span>{t('myScans.pdfScans')} ({pdfScans.length})</span>
          </button>
        </div>
      </motion.div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner className="h-8 w-8" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6"
        >
          <div className="flex gap-3">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {!loading && !error && getCurrentScans().length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
        >
          <PageCard className="text-center py-12">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gray-100 dark:bg-gray-700 mb-4">
              {activeTab === 'web' ? (
                <GlobeAltIcon className="h-8 w-8 text-gray-400" />
              ) : (
                <DocumentIcon className="h-8 w-8 text-gray-400" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {activeTab === 'web' ? t('myScans.noWebScans') : t('myScans.noPdfScans')}
            </h3>
            <p className="mt-2 text-gray-500 dark:text-gray-400 max-w-md mx-auto">
              {activeTab === 'web' ? t('myScans.startWebScan') : t('myScans.startPdfScan')}
            </p>
            <div className="mt-6">
              <button
                onClick={handleStartNewScan}
                className="btn-primary"
              >
                {activeTab === 'web' ? t('myScans.scanWebsite') : t('myScans.scanPdf')}
              </button>
            </div>
          </PageCard>
        </motion.div>
      )}

      {/* Scans List */}
      {!loading && !error && getCurrentScans().length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <PageCard padding="none" className="overflow-hidden">
            <div className="p-4 sm:p-6 space-y-4">
              {getCurrentScans().map((scan, index) => (
                <motion.div
                  key={scan.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <ScanCard 
                    scan={scan} 
                    scanType={activeTab}
                    onView={handleViewScan}
                    onDownload={handleDownloadPDF}
                    onDelete={handleDeleteClick}
                    formatDate={formatDate}
                    getSeverityColor={getSeverityColor}
                  />
                </motion.div>
              ))}
            </div>
          </PageCard>
        </motion.div>
      )}

      {/* Summary Stats */}
      {!loading && !error && getCurrentScans().length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="mt-8"
        >
          <PageCard className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-850">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
              {activeTab === 'web' ? t('myScans.websiteSummary') : t('myScans.pdfSummary')}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl shadow-sm">
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {formatNumber(getCurrentScans().length)}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {t('myScans.totalScans')}
                </p>
              </div>
              <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl shadow-sm">
                <p className="text-3xl font-bold text-red-600">
                  {formatNumber(getCurrentScans().reduce((sum, scan) => {
                    const violations = scan.summary?.total_violations || 0
                    const htmlErrors = scan.summary?.total_html_errors || 0
                    const brokenLinks = scan.summary?.total_broken_links || 0
                    return sum + violations + htmlErrors + brokenLinks
                  }, 0))}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {t('myScans.totalIssues')}
                </p>
              </div>
              <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl shadow-sm">
                <p className="text-3xl font-bold text-green-600">
                  {formatNumber(getCurrentScans().reduce((sum, scan) => {
                    const passes = scan.summary?.total_passes || 0
                    return sum + passes
                  }, 0))}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {t('myScans.testsPassed')}
                </p>
              </div>
            </div>
          </PageCard>
        </motion.div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && scanToDelete && (
        <DeleteConfirmationDialog
          isOpen={showDeleteDialog}
          onClose={handleDeleteDialogClose}
          onConfirm={handleDeleteConfirm}
          itemName={activeTab === 'pdf' ? scanToDelete.file_name : scanToDelete.url}
          itemType={`${activeTab === 'pdf' ? 'PDF' : 'Website'} Scan`}
        />
      )}
    </PageContainer>
  )
}

export default MyScansPage
