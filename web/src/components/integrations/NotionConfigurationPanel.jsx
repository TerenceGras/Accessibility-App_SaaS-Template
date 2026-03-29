import React, { useState, useEffect } from 'react'
import {
  DocumentTextIcon,
  LinkSlashIcon
} from '@heroicons/react/24/outline'
import ConfirmationDialog from './ConfirmationDialog'
import { useTranslation } from '../../hooks/useTranslation'

const NotionConfigurationPanel = ({
  integration,
  notionConfig,
  onBackToOverview,
  onPageUrlChange,
  onToggleEnabled,
  updateNotionConfig,
  onDisconnect,
  isDisconnecting
}) => {
  const { t } = useTranslation()
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  const [activeConfigTab, setActiveConfigTab] = useState('web-scan')
  
  // Web scan section toggles - initialized from integration data
  const [wcagEnabled, setWcagEnabled] = useState(true)
  const [htmlEnabled, setHtmlEnabled] = useState(true)
  const [linksEnabled, setLinksEnabled] = useState(true)
  const [axTreeEnabled, setAxTreeEnabled] = useState(false)
  const [layoutEnabled, setLayoutEnabled] = useState(true)
  
  // Load web_scan_sections values from integration when it changes
  useEffect(() => {
    if (integration?.web_scan_sections) {
      const sections = integration.web_scan_sections
      setWcagEnabled(sections.wcag_enabled !== undefined ? sections.wcag_enabled : true)
      setHtmlEnabled(sections.html_enabled !== undefined ? sections.html_enabled : true)
      setLinksEnabled(sections.links_enabled !== undefined ? sections.links_enabled : true)
      setAxTreeEnabled(sections.axtree_enabled !== undefined ? sections.axtree_enabled : false)
      setLayoutEnabled(sections.layout_enabled !== undefined ? sections.layout_enabled : true)
    }
  }, [integration?.web_scan_sections])
  
  const handleDisconnect = async () => {
    setShowDisconnectDialog(false)
    if (onDisconnect) {
      const success = await onDisconnect('notion')
      if (success) {
        onBackToOverview()
      }
    }
  }
  const handlePageUrlChange = (e) => {
    const newPageUrl = e.target.value
    onPageUrlChange(newPageUrl)
    updateNotionConfig({ page_url: newPageUrl })
  }

  const handleToggleEnabled = () => {
    const newIsEnabled = !integration.config?.web_scan_enabled
    onToggleEnabled('notion', { config: { web_scan_enabled: newIsEnabled } })
    // Backend update is handled in parent component
  }

  const handleSeverityChange = (severity, checked) => {
    let newFilter
    if (checked) {
      newFilter = [...notionConfig.wcag_severity_filter, severity]
    } else {
      newFilter = notionConfig.wcag_severity_filter.filter(s => s !== severity)
    }
    updateNotionConfig({ wcag_severity_filter: newFilter })
  }

  const handleRegroupChange = (checked) => {
    updateNotionConfig({ wcag_regroup_violations: checked })
  }

  const handleGroupingOptionChange = (e) => {
    updateNotionConfig({ wcag_grouping_option: e.target.value })
  }

  const handleTogglePdfEnabled = () => {
    const newPdfEnabled = !integration.config?.pdf_scan_enabled
    onToggleEnabled('notion', { config: { pdf_scan_enabled: newPdfEnabled } })
  }

  const handlePdfGroupingChange = (e) => {
    const value = e.target.value
    updateNotionConfig({ pdf_grouping_option: value })
    // No truncation warning for Notion - it has no character limits
  }

  const handleHtmlGroupingChange = (e) => {
    updateNotionConfig({ html_grouping_option: e.target.value })
  }

  const handleLinksGroupingChange = (e) => {
    updateNotionConfig({ links_grouping_option: e.target.value })
  }

  const handleLayoutGroupingChange = (e) => {
    updateNotionConfig({ layout_grouping_option: e.target.value })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-black">
            <DocumentTextIcon className="h-5 w-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('integrations.notion.configuration')}</h3>
        </div>
        <button
          onClick={onBackToOverview}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
        >
          ×
        </button>
      </div>

      <div className="space-y-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">{t('integrations.config.howItWorks')}</h4>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {t('integrations.notion.howItWorksDesc')}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('integrations.config.parentPageUrlRequired')}
          </label>
          <input
            type="url"
            value={notionConfig.page_url || ''}
            onChange={handlePageUrlChange}
            placeholder={t('integrations.notion.parentPagePlaceholder')}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {t('integrations.config.parentPageHelp')}
          </p>
        </div>

        {/* Push Web Scan Results to Notion Toggle */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('integrations.config.pushWebScanResults', { platform: 'Notion' })}
          </label>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {t('integrations.config.enableAutoIntegrationWeb', { platform: 'Notion' })}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('integrations.config.whenDisabledNoPages')}
              </p>
            </div>
            <button
              onClick={handleToggleEnabled}
              disabled={!notionConfig.page_url}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 ${
                integration.config?.web_scan_enabled && notionConfig.page_url ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  integration.config?.web_scan_enabled && notionConfig.page_url ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Push PDF Scan Results to Notion Toggle */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('integrations.config.pushPdfScanResults', { platform: 'Notion' })}
          </label>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {t('integrations.config.enableAutoIntegrationPdf', { platform: 'Notion' })}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('integrations.config.whenDisabledNoPdfPages')}
              </p>
            </div>
            <button
              onClick={handleTogglePdfEnabled}
              disabled={!notionConfig.page_url}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 ${
                integration.config?.pdf_scan_enabled && notionConfig.page_url ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  integration.config?.pdf_scan_enabled && notionConfig.page_url ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveConfigTab('web-scan')}
              className={`${
                activeConfigTab === 'web-scan'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200`}
            >
              {t('integrations.config.webScanConfiguration')}
            </button>
            <button
              onClick={() => setActiveConfigTab('pdf-scan')}
              className={`${
                activeConfigTab === 'pdf-scan'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200`}
            >
              {t('integrations.config.pdfScanConfiguration')}
            </button>
            <button
              onClick={() => setActiveConfigTab('statistics')}
              className={`${
                activeConfigTab === 'statistics'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200`}
            >
              {t('integrations.config.statistics')}
            </button>
          </nav>
        </div>

        {/* Web Scan Configuration Tab */}
        {/* Web Scan Configuration Tab */}
        {activeConfigTab === 'web-scan' && (
          <div className="space-y-6 transition-opacity duration-200">
            {/* WCAG Compliance Testing Section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900 dark:text-white">{t('integrations.config.wcagComplianceTesting')}</h4>
                <button
                  onClick={() => {
                    const newValue = !wcagEnabled
                    setWcagEnabled(newValue)
                    updateNotionConfig({ 
                      web_scan_sections: {
                        wcag_enabled: newValue
                      }
                    })
                  }}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    wcagEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      wcagEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {wcagEnabled && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('integrations.config.severityFilter')}
                    </label>
                    <div className="space-y-2">
                      {['High', 'Medium', 'Low'].map(severity => (
                        <label key={severity} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={notionConfig.wcag_severity_filter.includes(severity)}
                            onChange={(e) => handleSeverityChange(severity, e.target.checked)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            {t(`integrations.config.severity.${severity.toLowerCase()}SeverityIssues`)}
                          </span>
                        </label>
                      ))}
                    </div>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {t('integrations.config.notionSeverityFilter.help')}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('integrations.config.notionViolationGrouping.label')}
                    </label>
                    <div className="space-y-3">
                      <div className="flex items-start">
                        <input
                          type="checkbox"
                          id="regroup-violations"
                          checked={notionConfig.wcag_regroup_violations}
                          onChange={(e) => handleRegroupChange(e.target.checked)}
                          disabled={notionConfig.wcag_grouping_option === 'single-issue'}
                          className={`mt-0.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 ${notionConfig.wcag_grouping_option === 'single-issue' ? 'opacity-50 cursor-not-allowed' : ''}`}
                        />
                        <div className="ml-3">
                          <label htmlFor="regroup-violations" className={`text-sm ${notionConfig.wcag_grouping_option === 'single-issue' ? 'text-gray-400 dark:text-gray-500' : 'text-gray-700 dark:text-gray-300'}`}>
                            {t('integrations.config.notionViolationGrouping.groupByRuleType')}
                          </label>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {notionConfig.wcag_grouping_option === 'single-issue'
                              ? t('integrations.config.notionViolationGrouping.disabledWhenSingleIssue')
                              : t('integrations.config.notionViolationGrouping.groupByRuleTypeHelp')}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('integrations.config.pageGrouping')}
                    </label>
                    <select
                      value={notionConfig.wcag_grouping_option}
                      onChange={handleGroupingOptionChange}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="per-error-type">{t('integrations.config.notionWcagGroupingOptions.perErrorType')}</option>
                      <option value="single-issue">{t('integrations.config.notionWcagGroupingOptions.singleIssue')}</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {notionConfig.wcag_grouping_option === 'single-issue'
                        ? t('integrations.config.notionWcagGroupingOptions.singleIssueHelp')
                        : t('integrations.config.notionWcagGroupingOptions.perErrorTypeHelp')}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* HTML Markup Validation Section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900 dark:text-white">{t('integrations.config.sectionTitles.htmlMarkupValidation')}</h4>
                <button
                  onClick={() => {
                    const newValue = !htmlEnabled
                    setHtmlEnabled(newValue)
                    updateNotionConfig({ 
                      web_scan_sections: {
                        html_enabled: newValue
                      }
                    })
                  }}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    htmlEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      htmlEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {htmlEnabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('integrations.config.pageGrouping')}
                  </label>
                  <select
                    value={notionConfig.html_grouping_option || 'per-error-type'}
                    onChange={handleHtmlGroupingChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="per-error-type">{t('integrations.config.notionHtmlGroupingOptions.perErrorType')}</option>
                    <option value="single-issue">{t('integrations.config.notionHtmlGroupingOptions.singleIssue')}</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.notionHtmlGroupingOptions.help')}
                  </p>
                </div>
              )}
            </div>

            {/* Link Health Check Section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900 dark:text-white">{t('integrations.config.sectionTitles.linkHealthCheck')}</h4>
                <button
                  onClick={() => {
                    const newValue = !linksEnabled
                    setLinksEnabled(newValue)
                    updateNotionConfig({ 
                      web_scan_sections: {
                        links_enabled: newValue
                      }
                    })
                  }}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    linksEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      linksEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {linksEnabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('integrations.config.pageGrouping')}
                  </label>
                  <select
                    value={notionConfig.links_grouping_option || 'per-error-type'}
                    onChange={handleLinksGroupingChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="per-error-type">{t('integrations.config.notionLinksGroupingOptions.perErrorType')}</option>
                    <option value="single-issue">{t('integrations.config.notionLinksGroupingOptions.singleIssue')}</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.notionLinksGroupingOptions.help')}
                  </p>
                </div>
              )}
            </div>

            {/* Accessibility Tree Structure Section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900 dark:text-white">{t('integrations.config.sectionTitles.accessibilityTreeStructure')}</h4>
                <button
                  onClick={() => {
                    const newValue = !axTreeEnabled
                    setAxTreeEnabled(newValue)
                    updateNotionConfig({ 
                      web_scan_sections: {
                        axtree_enabled: newValue
                      }
                    })
                  }}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    axTreeEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      axTreeEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {axTreeEnabled && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  When enabled, the accessibility tree structure will be included in Notion pages.
                </p>
              )}
            </div>

            {/* Responsive Layout Testing Section */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-900 dark:text-white">{t('integrations.config.sectionTitles.responsiveLayoutTesting')}</h4>
                <button
                  onClick={() => {
                    const newValue = !layoutEnabled
                    setLayoutEnabled(newValue)
                    updateNotionConfig({ 
                      web_scan_sections: {
                        layout_enabled: newValue
                      }
                    })
                  }}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    layoutEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      layoutEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {layoutEnabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('integrations.config.pageGrouping')}
                  </label>
                  <select
                    value={notionConfig.layout_grouping_option || 'per-error-type'}
                    onChange={handleLayoutGroupingChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="per-error-type">{t('integrations.config.notionLayoutGroupingOptions.perErrorType')}</option>
                    <option value="single-issue">{t('integrations.config.notionLayoutGroupingOptions.singleIssue')}</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.notionLayoutGroupingOptions.help')}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* PDF Scan Configuration Tab */}
        {activeConfigTab === 'pdf-scan' && (
          <div className="space-y-6 transition-opacity duration-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('integrations.config.reportGrouping')}
              </label>
              <select
                value={notionConfig.pdf_grouping_option || 'per-page'}
                onChange={handlePdfGroupingChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="per-page">{t('integrations.config.notionPdfGroupingOptions.perPage')}</option>
                <option value="single-issue">{t('integrations.config.notionPdfGroupingOptions.singleIssue')}</option>
              </select>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('integrations.config.notionPdfGroupingOptions.help')}
              </p>
            </div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeConfigTab === 'statistics' && (
          <div className="space-y-6 transition-opacity duration-200">
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <h4 className="font-medium text-green-900 dark:text-green-100 mb-2">{t('integrations.config.statisticsTab.title')}</h4>
              <div className="text-sm text-green-700 dark:text-green-300 space-y-1">
                <p>{t('integrations.config.statisticsTab.pagesCreated')} {integration?.stats?.pages_created || 0}</p>
                {integration?.stats?.last_page_created && (
                  <p>{t('integrations.config.statisticsTab.lastPageCreated')} {new Date(integration.stats.last_page_created).toLocaleDateString()}</p>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">{t('integrations.config.pageAccessManagement.title')}</h4>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {t('integrations.config.pageAccessManagement.description')}
          </p>
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={onBackToOverview}
            className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-md font-medium transition-colors duration-200"
          >
            {t('integrations.config.buttons.backToOverview')}
          </button>
          
          <button
            onClick={() => setShowDisconnectDialog(true)}
            disabled={isDisconnecting}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50 flex items-center space-x-2"
          >
            <LinkSlashIcon className="h-4 w-4" />
            <span>{isDisconnecting ? t('integrations.config.buttons.disconnecting') : t('integrations.config.buttons.disconnect')}</span>
          </button>
        </div>
      </div>
      
      <ConfirmationDialog
        isOpen={showDisconnectDialog}
        onClose={() => setShowDisconnectDialog(false)}
        onConfirm={handleDisconnect}
        title={t('integrations.notion.disconnectTitle')}
        message={t('integrations.notion.disconnectMessage')}
        confirmText={t('integrations.common.disconnect')}
        cancelText={t('common.cancel')}
        isDangerous={true}
      />
    </div>
  )
}

export default NotionConfigurationPanel
