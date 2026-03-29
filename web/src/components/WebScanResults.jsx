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
  DocumentTextIcon,
  CodeBracketIcon,
  ShieldCheckIcon,
  WindowIcon,
  LinkIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

// API Configuration
const REPORT_GENERATOR_URL = import.meta.env.VITE_REPORT_GENERATOR_URL || ''

const WebScanResults = ({ results, url, onNewScan, onBackToScans }) => {
  const { t } = useTranslation()
  const [expandedSections, setExpandedSections] = useState({
    wcag: true,
    html: true,
    tree: false,
    layout: false,
    links: true
  })
  const [downloading, setDownloading] = useState(false)

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const handleDownloadReport = async () => {
    if (downloading) return
    
    setDownloading(true)
    const loadingToast = toast.loading(t('webScan.generatingPdf'))
    
    try {
      const payload = {
        url: url || results.url,
        unified_results: results.unified_results,
        timestamp: results.timestamp || new Date().toISOString(),
        testEngine: results.testEngine,
        taskId: results.id || results.task_id,
        accessibility_score: results.accessibility_score
      }

      const response = await fetch(`${REPORT_GENERATOR_URL}/generate/web-scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || 'Failed to generate PDF report')
      }

      // Get the PDF blob
      const blob = await response.blob()

      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl

      // Generate filename
      const date = new Date().toISOString().split('T')[0]
      const safeUrl = (url || results.url).replace(/https?:\/\//, '').replace(/[^a-z0-9]/gi, '-').substring(0, 50)
      link.download = `web-accessibility-report-${safeUrl}-${date}.pdf`

      // Trigger download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      toast.success(t('webScan.pdfDownloadSuccess'), { id: loadingToast })
    } catch (error) {
      logger.error('Error downloading report:', error)
      toast.error(t('webScan.pdfDownloadError'), { id: loadingToast })
    } finally {
      setDownloading(false)
    }
  }

  // Handle case where results is undefined or null
  if (!results) {
    return (
      <div className="bg-white dark:bg-gray-900 min-h-screen">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">{t('webScan.noResultsAvailable')}</p>
            {onBackToScans && (
              <button
                onClick={onBackToScans}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                {t('webScan.backToScans')}
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  const unified = results.unified_results || {}
  const axeData = unified.axe || {}
  const nuData = unified.nu || {}
  const axTreeData = unified.axTree || {}
  const galenData = unified.galen || {}
  const linksData = unified.links || {}
  const meta = unified.meta || results.meta || {}

  const violations = axeData.violations || []
  const passes = axeData.passes || []
  const incomplete = axeData.incomplete || []

  // Count TOTAL violations (sum of all nodes across all violation categories)
  const totalViolationNodes = violations.reduce((sum, violation) => {
    return sum + (violation.nodes ? violation.nodes.length : 0)
  }, 0)
  
  // Count TOTAL passes (sum of all nodes across all passing rules)
  const totalPassNodes = passes.reduce((sum, pass) => {
    return sum + (pass.nodes ? pass.nodes.length : 0)
  }, 0)
  
  const htmlErrors = nuData.errors || []
  const htmlWarnings = nuData.warnings || []
  
  // New link states: valid, invalid, timeout, unreachable (backward compatible)
  const invalidLinks = linksData.invalid_links || linksData.broken_links || []
  const timeoutLinks = linksData.timeout_links || []
  const unreachableLinks = linksData.unreachable_links || []
  const validLinks = linksData.valid_links || []
  // For backward compatibility, also support old field names - error_links may include timeout + unreachable
  const errorLinks = linksData.error_links || [...timeoutLinks, ...unreachableLinks]
  // Combine timeout and unreachable for display purposes (both are "could not reach" issues)
  const connectionIssueLinks = [...timeoutLinks, ...unreachableLinks]

  const severityColors = {
    critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    serious: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    moderate: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    minor: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
  }

  const StatCard = ({ icon: Icon, label, count, color = 'text-gray-600' }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 p-6 text-center">
      <Icon className={`mx-auto h-8 w-8 ${color} mb-3`} />
      <div className="text-2xl font-bold text-gray-900 dark:text-white">{count}</div>
      <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  )

  const SectionHeader = ({ title, subtitle, icon: Icon, count, expanded, onToggle, color = "blue" }) => (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 hover:from-gray-100 hover:to-gray-200 dark:hover:from-gray-700 dark:hover:to-gray-600 rounded-xl border border-gray-200 dark:border-gray-600 transition-all"
    >
      <div className="flex items-center space-x-4">
        <div className={`p-3 bg-${color}-100 dark:bg-${color}-900/30 rounded-lg`}>
          <Icon className={`h-6 w-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
        <div className="text-left">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
        </div>
      </div>
      <div className="flex items-center space-x-3">
        {count !== undefined && (
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            count > 0 ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
          }`}>
            {count} {count === 1 ? 'issue' : 'issues'}
          </span>
        )}
        {expanded ? (
          <ChevronUpIcon className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDownIcon className="h-5 w-5 text-gray-400" />
        )}
      </div>
    </button>
  )

  const ViolationCard = ({ violation }) => {
    const severity = violation.impact || 'moderate'
    const nodes = violation.nodes || []

    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-5 mb-4">
        <div className="flex items-start justify-between mb-3">
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white flex-1">
            {violation.help || violation.title}
          </h4>
          <span className={`ml-3 px-2.5 py-0.5 rounded-full text-xs font-medium ${severityColors[severity]}`}>
            {severity.charAt(0).toUpperCase() + severity.slice(1)}
          </span>
        </div>
        <p className="text-gray-600 dark:text-gray-300 mb-4">{violation.description}</p>
        
        {violation.helpUrl && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mb-4">
            <a
              href={violation.helpUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              → Learn how to fix this issue
            </a>
          </div>
        )}
        
        {nodes.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              Found on {nodes.length} element{nodes.length !== 1 ? 's' : ''}:
            </p>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {nodes.map((node, i) => (
                <div key={i} className="bg-gray-100 dark:bg-gray-900 rounded p-3 text-xs">
                  {node.target && (
                    <code className="text-blue-600 dark:text-blue-400 block mb-1">
                      {Array.isArray(node.target) ? node.target[0] : node.target}
                    </code>
                  )}
                  {node.html && (
                    <code className="text-gray-600 dark:text-gray-400 block">
                      {node.html.substring(0, 100)}...
                    </code>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {onBackToScans && (
            <button onClick={onBackToScans} className="btn-secondary flex items-center space-x-2">
              <ArrowLeftIcon className="h-4 w-4" />
              <span>{t('webScan.results.backToMyScans')}</span>
            </button>
          )}
          <button 
            onClick={handleDownloadReport} 
            disabled={downloading}
            className="btn-secondary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <DocumentArrowDownIcon className="h-4 w-4" />
            <span>{downloading ? t('webScan.results.generating') : t('webScan.results.downloadReport')}</span>
          </button>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          {t('webScan.results.title')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          <span className="font-medium">{url || results.url}</span>
        </p>
        {results.timestamp && (
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
            {t('webScan.results.scannedOn', { date: new Date(results.timestamp).toLocaleString() })}
          </p>
        )}
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={ExclamationTriangleIcon}
          label="WCAG Violations"
          count={totalViolationNodes}
          color={totalViolationNodes > 0 ? 'text-red-500' : 'text-green-500'}
        />
        <StatCard 
          icon={CodeBracketIcon}
          label="HTML Errors"
          count={htmlErrors.length}
          color={htmlErrors.length > 0 ? 'text-orange-500' : 'text-green-500'}
        />
        <StatCard 
          icon={LinkIcon}
          label="Invalid Links"
          count={invalidLinks.length}
          color={invalidLinks.length > 0 ? 'text-red-500' : 'text-green-500'}
        />
        <StatCard 
          icon={CheckCircleIcon}
          label="Tests Passed"
          count={totalPassNodes}
          color="text-green-500"
        />
      </div>

      {/* Module Results */}
      <div className="space-y-6">
        {/* WCAG Violations (axe-core) */}
        <div>
          <SectionHeader
            title={t('webScan.results.sections.wcag.title')}
            subtitle={t('webScan.results.sections.wcag.subtitle')}
            icon={ShieldCheckIcon}
            count={violations.length}
            expanded={expandedSections.wcag}
            onToggle={() => toggleSection('wcag')}
            color="red"
          />
          {expandedSections.wcag && (
            <div className="mt-4 space-y-4">
              {violations.length === 0 ? (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
                  <CheckCircleIcon className="mx-auto h-12 w-12 text-green-500 mb-3" />
                  <p className="text-green-800 dark:text-green-300 font-medium">
                    {t('webScan.results.sections.wcag.noViolations')}
                  </p>
                </div>
              ) : (
                violations.map((violation, i) => <ViolationCard key={i} violation={violation} />)
              )}
            </div>
          )}
        </div>

        {/* HTML Validation */}
        <div>
          <SectionHeader
            title={t('webScan.results.sections.html.title')}
            subtitle={t('webScan.results.sections.html.subtitle')}
            icon={CodeBracketIcon}
            count={htmlErrors.length}
            expanded={expandedSections.html}
            onToggle={() => toggleSection('html')}
            color="orange"
          />
          {expandedSections.html && (
            <div className="mt-4">
              {htmlErrors.length === 0 ? (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
                  <CheckCircleIcon className="mx-auto h-12 w-12 text-green-500 mb-3" />
                  <p className="text-green-800 dark:text-green-300 font-medium">
                    {t('webScan.results.sections.html.noErrors')}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {htmlErrors.map((error, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4 overflow-hidden">
                      <div className="flex items-start space-x-3">
                        <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-900 dark:text-white font-medium break-words">{error.message}</p>
                          {error.extract && (
                            <code className="block mt-2 p-2 bg-gray-100 dark:bg-gray-900 rounded text-xs text-gray-700 dark:text-gray-300 overflow-x-auto max-h-32 whitespace-pre-wrap break-all">
                              {error.extract.length > 500 ? error.extract.substring(0, 500) + '...' : error.extract}
                            </code>
                          )}
                          {error.line && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                              {t('webScan.results.lineColumn', { line: error.line, column: error.column })}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Link Health */}
        <div>
          <SectionHeader
            title={t('webScan.results.sections.links.title')}
            subtitle={t('webScan.results.sections.links.subtitle')}
            icon={LinkIcon}
            expanded={expandedSections.links}
            onToggle={() => toggleSection('links')}
            color="yellow"
          />
          {expandedSections.links && (
            <div className="mt-4">
              {invalidLinks.length === 0 && connectionIssueLinks.length === 0 ? (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 text-center">
                  <CheckCircleIcon className="mx-auto h-12 w-12 text-green-500 mb-3" />
                  <p className="text-green-800 dark:text-green-300 font-medium">
                    {t('webScan.results.sections.links.allWorking')}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    {t('webScan.results.linksChecked', { count: linksData.checked_links || 0 })}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Summary line */}
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {t('webScan.results.linksChecked', { count: linksData.checked_links || 0 })}
                    {validLinks.length > 0 && ` • ${validLinks.length} valid`}
                    {invalidLinks.length > 0 && ` • ${invalidLinks.length} broken`}
                    {connectionIssueLinks.length > 0 && ` • ${connectionIssueLinks.length} unreachable`}
                  </p>
                  
                  {/* Broken Links (HTTP errors) */}
                  {invalidLinks.length > 0 && (
                    <div className="space-y-2">
                      {invalidLinks.map((link, i) => (
                        <div key={`invalid-${i}`} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-red-200 dark:border-red-800 p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-mono text-blue-600 dark:text-blue-400 break-all">
                                {link.url}
                              </p>
                              {link.text && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {t('webScan.results.linkText', { text: link.text })}
                                </p>
                              )}
                              {link.error_reason && (
                                <p className="text-xs text-red-500 dark:text-red-400 mt-1">
                                  {link.error_reason}
                                </p>
                              )}
                            </div>
                            <span className="ml-3 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
                              {link.status > 0 ? t('webScan.results.httpStatus', { status: link.status }) : 'Broken'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Connection Issue Links (Timeout + Unreachable) */}
                  {connectionIssueLinks.length > 0 && (
                    <div className="space-y-2">
                      {connectionIssueLinks.map((link, i) => (
                        <div key={`connection-${i}`} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-mono text-blue-600 dark:text-blue-400 break-all">
                                {link.url}
                              </p>
                              {link.text && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {t('webScan.results.linkText', { text: link.text })}
                                </p>
                              )}
                              {link.error_reason && (
                                <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                                  {link.error_reason}
                                </p>
                              )}
                            </div>
                            <span className="ml-3 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
                              {link.state === 'timeout' ? 'Timeout' : 'Unreachable'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Accessibility Tree */}
        {axTreeData.tree && (
          <div>
            <SectionHeader
              title={t('webScan.results.sections.tree.title')}
              subtitle={t('webScan.results.sections.tree.subtitle')}
              icon={WindowIcon}
              expanded={expandedSections.tree}
              onToggle={() => toggleSection('tree')}
              color="indigo"
            />
            {expandedSections.tree && (
              <div className="mt-4 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {t('webScan.results.accessibilityTreeDescription')}
                </p>
                <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 max-h-96 overflow-auto">
                  <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {JSON.stringify(axTreeData.tree, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Layout Testing */}
        {galenData.viewport_results && galenData.viewport_results.length > 0 && (
          <div>
            <SectionHeader
              title={t('webScan.results.sections.layout.title')}
              subtitle={t('webScan.results.sections.layout.subtitle')}
              icon={WindowIcon}
              expanded={expandedSections.layout}
              onToggle={() => toggleSection('layout')}
              color="green"
            />
            {expandedSections.layout && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                {galenData.viewport_results.map((result, i) => (
                  <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                      {result.viewport.width} × {result.viewport.height}
                    </h4>
                    <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                      <p>{t('webScan.results.horizontalScroll')} {result.metrics.hasHorizontalScroll ? t('webScan.results.yes') : t('webScan.results.no')}</p>
                      <p>{t('webScan.results.visibleElements')} {result.metrics.elements.visible}</p>
                      <p>{t('webScan.results.hiddenElements')} {result.metrics.elements.hidden}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-8 text-center">
        <button onClick={onNewScan} className="btn-primary inline-flex items-center">
          <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
          {t('webScan.results.runAnotherScan')}
        </button>
      </div>
    </div>
  )
}

export default WebScanResults
