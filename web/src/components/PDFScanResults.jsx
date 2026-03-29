import React, { useState } from 'react'
import { toast } from 'react-hot-toast'
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  MinusCircleIcon,
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

// API Configuration
const REPORT_GENERATOR_URL = import.meta.env.VITE_REPORT_GENERATOR_URL || ''

const PDFScanResults = ({ results, url, onNewScan, onBackToScans }) => {
  const { t } = useTranslation()
  // Helper function to download PDF report
  const handleDownloadPDFReport = async () => {
    try {
      toast.loading(t('pdfScan.generatingReport'))
      
      // Get accessibility_report from multiple possible locations
      const accessibilityReport = 
        results.accessibility_report || 
        results.unified_results?.accessibility_report
      
      const endpoint = `${REPORT_GENERATOR_URL}/generate/pdf-scan`
      const payload = {
        file_name: results.file_name || 'document.pdf',
        accessibility_report: accessibilityReport,
        unified_results: results.unified_results,
        timestamp: results.timestamp,
        analysis_type: results.analysis_type
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
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      
      // Generate filename
      const date = new Date().toISOString().split('T')[0]
      const filename = `pdf-accessibility-report-${(results.file_name || 'document').replace('.pdf', '')}-${date}.pdf`
      
      link.download = filename
      document.body.appendChild(link)
      link.click()
      
      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
      
      toast.dismiss()
      toast.success(t('pdfScan.downloadSuccess'))
      
    } catch (error) {
      logger.error('Error downloading PDF report:', error)
      toast.dismiss()
      toast.error(t('pdfScan.downloadError'))
    }
  }

  // Handle case where results is undefined or null
  if (!results) {
    return (
      <div className="bg-white dark:bg-gray-900 min-h-screen">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">{t('pdfScan.results.noResultsAvailable')}</p>
            {onBackToScans && (
              <button
                onClick={onBackToScans}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                {t('pdfScan.results.backToScans')}
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  const {
    unified_results = null,
    timestamp,
    status,
    message,
    file_name,
    scan_type
  } = results

  // If this is a queued task, show a different interface
  if (status === 'queued' || status === 'processing') {
    return (
      <div className="bg-white dark:bg-gray-900 min-h-screen">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            {/* Enhanced loading animation */}
            <div className="relative mb-8">
              <div className="mx-auto w-16 h-16 relative">
                {/* Outer spinning ring */}
                <div className="absolute inset-0 rounded-full border-4 border-blue-200 dark:border-blue-800"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-500 animate-spin"></div>
                {/* Inner pulsing circle */}
                <div className="absolute inset-2 bg-blue-100 dark:bg-blue-900 rounded-full animate-pulse flex items-center justify-center">
                  <MagnifyingGlassIcon className="h-6 w-6 text-blue-500" />
                </div>
              </div>
            </div>
            
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-4">
              PDF Accessibility Scan in Progress
            </h1>
            <p className="text-lg text-gray-500 dark:text-gray-300 mb-8">
              {message || 'Analyzing your PDF document for accessibility issues. This may take a few minutes. Results will appear here automatically.'}
            </p>
            
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 p-8 mb-6">
              <div className="grid grid-cols-1 gap-6 text-left">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    PDF Document Being Scanned
                  </h3>
                  <p className="text-blue-600 dark:text-blue-400 break-all font-medium">
                    {file_name || url}
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    What we're checking in your PDF:
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Document structure & headings
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Alternative text for images
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Form field accessibility
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Reading order & navigation
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Color contrast & accessibility
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Language specification
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      PDF/A compliance
                    </div>
                    <div className="flex items-center text-gray-600 dark:text-gray-300">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      {scan_type === 'vision' ? 'AI visual analysis' : 'Technical validation'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="text-center">
              <button
                onClick={onNewScan}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
              >
                <ArrowLeftIcon className="-ml-1 mr-2 h-4 w-4" aria-hidden="true" />
                Start a New Scan
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Check if this is a PDF scan with free-text format
  const accessibilityReport = results.accessibility_report || unified_results?.accessibility_report || 'No accessibility report available.'

  // For PDF scans with free-text format, render the analysis report
  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {onBackToScans && (
            <button
              onClick={onBackToScans}
              className="btn-secondary flex items-center space-x-2"
            >
              <span>{t('pdfScan.results.backToMyScans')}</span>
            </button>
          )}
          <button
            onClick={handleDownloadPDFReport}
            className="btn-secondary flex items-center space-x-2"
          >
            <DocumentArrowDownIcon className="h-4 w-4" aria-hidden="true" />
            <span>{t('pdfScan.results.downloadPdfReport')}</span>
          </button>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {t('pdfScan.results.title')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          {t('pdfScan.results.analyzedFor')} <span className="font-medium">{file_name || url}</span>
        </p>
        {timestamp && (
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
            {t('pdfScan.results.analyzedOn', { date: new Date(timestamp).toLocaleString() })}
          </p>
        )}
      </div>

      {/* PDF Accessibility Report */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
            <DocumentTextIcon className="h-6 w-6 text-blue-600 mr-2" />
            {t('pdfScan.results.gptAnalysisTitle')}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive visual accessibility assessment powered by AI
          </p>
        </div>
        
        <div className="p-6">
          <div 
            className="prose prose-sm dark:prose-invert max-w-none"
            style={{ 
              whiteSpace: 'pre-wrap',
              fontFamily: 'inherit',
              lineHeight: '1.6'
            }}
          >
            {accessibilityReport}
          </div>
        </div>
        
        {/* Tool Information */}
        {(results.tool_info || unified_results?.tool_info) && (
          <div className="bg-gray-50 dark:bg-gray-900/50 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">
                Analysis powered by: {(results.tool_info || unified_results?.tool_info)?.name || 'GPT-5 Vision Scanner'}
              </span>
              <span className="text-gray-500 dark:text-gray-500">
                Version: {(results.tool_info || unified_results?.tool_info)?.version || '2.0.0'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-8 text-center">
        <button
          onClick={onNewScan}
          className="btn-primary inline-flex items-center"
        >
          <DocumentTextIcon className="h-4 w-4 mr-2" />
          Scan Another PDF
        </button>
      </div>
    </div>
  )
}

export default PDFScanResults
