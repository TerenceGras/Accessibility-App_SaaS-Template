import React, { useState, useEffect } from 'react'
import {
  ChatBubbleLeftEllipsisIcon,
  LinkSlashIcon
} from '@heroicons/react/24/outline'
import ConfirmationDialog from './ConfirmationDialog'
import { useTranslation } from '../../hooks/useTranslation'

const SlackConfigurationPanel = ({
  integration,
  slackConfig,
  loading,
  onBackToOverview,
  onConnect,
  onConfigChange,
  onToggleEnabled,
  updateSlackConfig,
  onDisconnect,
  isDisconnecting
}) => {
  const { t } = useTranslation()
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  const [activeConfigTab, setActiveConfigTab] = useState('web-scan')
  const [showTruncationWarning, setShowTruncationWarning] = useState(false)
  
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
      const success = await onDisconnect('slack')
      if (success) {
        onBackToOverview()
      }
    }
  }
  const handleInputChange = (field, value) => {
    onConfigChange({ ...slackConfig, [field]: value })
  }

  const handleToggleEnabled = () => {
    const newIsEnabled = !integration.config?.web_scan_enabled
    onToggleEnabled('slack', { config: { web_scan_enabled: newIsEnabled } })
  }

  const handleTogglePdfEnabled = () => {
    const newPdfEnabled = !integration.config?.pdf_scan_enabled
    onToggleEnabled('slack', { config: { pdf_scan_enabled: newPdfEnabled } })
  }

  const handleSeverityChange = (severity, checked) => {
    let newFilter
    if (checked) {
      newFilter = [...slackConfig.wcag_severity_filter, severity]
    } else {
      newFilter = slackConfig.wcag_severity_filter.filter(s => s !== severity)
    }
    onConfigChange({ ...slackConfig, wcag_severity_filter: newFilter })
    updateSlackConfig({ wcag_severity_filter: newFilter })
  }

  const handleMessageGroupingChange = (e) => {
    const value = e.target.value
    onConfigChange({ ...slackConfig, wcag_grouping_option: value })
    updateSlackConfig({ wcag_grouping_option: value })
  }

  const handlePdfGroupingChange = (e) => {
    const value = e.target.value
    updateSlackConfig({ pdf_grouping_option: value })
    setShowTruncationWarning(value === 'single-issue')
  }

  const handleHtmlGroupingChange = (e) => {
    updateSlackConfig({ html_grouping_option: e.target.value })
  }

  const handleLinksGroupingChange = (e) => {
    updateSlackConfig({ links_grouping_option: e.target.value })
  }

  const handleLayoutGroupingChange = (e) => {
    updateSlackConfig({ layout_grouping_option: e.target.value })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-purple-600">
            <ChatBubbleLeftEllipsisIcon className="h-5 w-5 text-white" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('integrations.slack.configuration')}</h3>
        </div>
        <button
          onClick={onBackToOverview}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
        >
          ×
        </button>
      </div>

      <div className="space-y-6">
        {!integration?.config?.connected ? (
          <>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">{t('integrations.slack.howToGetWebhook')}</h4>
              <ol className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <li>1. {t('integrations.slack.webhookStep1')}</li>
                <li>2. {t('integrations.slack.webhookStep2')}</li>
                <li>3. {t('integrations.slack.webhookStep3')}</li>
                <li>4. {t('integrations.slack.webhookStep4')}</li>
                <li>5. {t('integrations.slack.webhookStep5')}</li>
              </ol>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('integrations.config.webhookUrlRequired')}
              </label>
              <input
                type="url"
                value={slackConfig.webhook_url}
                onChange={(e) => handleInputChange('webhook_url', e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('integrations.config.webhookUrlHelp')}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('integrations.config.channelOverride')}
              </label>
              <input
                type="text"
                value={slackConfig.channel}
                onChange={(e) => handleInputChange('channel', e.target.value)}
                placeholder={t('integrations.config.channelOverridePlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('integrations.config.channelOverrideHelp')}
              </p>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={onConnect}
                disabled={loading.slack || loading.general}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50"
              >
                {loading.slack ? t('integrations.slack.connecting') : t('integrations.slack.connectSlack')}
              </button>
              <button
                onClick={onBackToOverview}
                className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-md font-medium transition-colors duration-200"
              >
                {t('integrations.slack.cancel')}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">{t('integrations.config.howItWorks')}</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                {t('integrations.slack.howItWorksDesc')}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('integrations.config.pushWebScanResults', { platform: 'Slack' })}
              </label>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {t('integrations.config.enableAutoIntegrationWeb', { platform: 'Slack' })}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.whenDisabledNoMessages')}
                  </p>
                </div>
                <button
                  onClick={handleToggleEnabled}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    integration.config?.web_scan_enabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      integration.config?.web_scan_enabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Push PDF Scan Results to Slack Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('integrations.config.pushPdfScanResults', { platform: 'Slack' })}
              </label>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {t('integrations.config.enableAutoIntegrationPdf', { platform: 'Slack' })}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.whenDisabledNoPdfMessages')}
                  </p>
                </div>
                <button
                  onClick={handleTogglePdfEnabled}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    integration.config?.pdf_scan_enabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      integration.config?.pdf_scan_enabled ? 'translate-x-5' : 'translate-x-0'
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
            {activeConfigTab === 'web-scan' && (
              <div className="space-y-6 transition-opacity duration-200">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('integrations.config.webhookUrl')}
                  </label>
                  <input
                    type="url"
                    value={slackConfig.webhook_url || ''}
                    onChange={(e) => {
                      const newValue = e.target.value
                      onConfigChange({ ...slackConfig, webhook_url: newValue })
                      updateSlackConfig({ webhook_url: newValue })
                    }}
                    placeholder="https://hooks.slack.com/services/..."
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.slackChannelSettings.webhookUrlHelp')}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('integrations.config.slackChannelSettings.channelOverrideLabel')}
                  </label>
                  <input
                    type="text"
                    value={slackConfig.channel || ''}
                    onChange={(e) => {
                      const newValue = e.target.value
                      onConfigChange({ ...slackConfig, channel: newValue })
                      updateSlackConfig({ channel: newValue })
                    }}
                    placeholder="e.g., #accessibility or @username"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.config.slackChannelSettings.channelOverrideHelp')}
                  </p>
                </div>

                {/* WCAG Compliance Testing Section */}
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-md font-semibold text-gray-900 dark:text-white">{t('integrations.config.sectionTitles.wcagComplianceTesting')}</h4>
                    <button
                      onClick={() => {
                        const newValue = !wcagEnabled
                        setWcagEnabled(newValue)
                        updateSlackConfig({ 
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
                          {t('integrations.config.slackSeverityFilter.label')}
                        </label>
                        <div className="space-y-2">
                          {['High', 'Medium', 'Low'].map(severity => (
                            <label key={severity} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={slackConfig.wcag_severity_filter.includes(severity)}
                                onChange={(e) => handleSeverityChange(severity, e.target.checked)}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              />
                              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                                {t(`integrations.config.slackSeverityFilter.${severity.toLowerCase()}SeverityIssues`)}
                              </span>
                            </label>
                          ))}
                        </div>
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {t('integrations.config.slackSeverityFilter.help')}
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          {t('integrations.config.slackMessageGrouping')}
                        </label>
                        <select
                          value={slackConfig.wcag_grouping_option}
                          onChange={handleMessageGroupingChange}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                          <option value="per-error-type">{t('integrations.config.slackWcagGroupingOptions.perErrorType')}</option>
                          <option value="single-issue">{t('integrations.config.slackWcagGroupingOptions.singleIssue')}</option>
                        </select>
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {slackConfig.wcag_grouping_option === 'single-issue'
                            ? t('integrations.config.slackWcagGroupingOptions.singleIssueHelp')
                            : t('integrations.config.slackWcagGroupingOptions.perErrorTypeHelp')
                          }
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          {t('integrations.config.slackViolationGrouping.label')}
                        </label>
                        <div className="space-y-3">
                          <div className="flex items-start">
                            <input
                              type="checkbox"
                              id="regroup-violations"
                              checked={slackConfig.wcag_regroup_violations}
                              onChange={(e) => {
                                onConfigChange({ ...slackConfig, wcag_regroup_violations: e.target.checked })
                                updateSlackConfig({ wcag_regroup_violations: e.target.checked })
                              }}
                              disabled={slackConfig.wcag_grouping_option === 'single-issue'}
                              className={`mt-0.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 ${slackConfig.wcag_grouping_option === 'single-issue' ? 'opacity-50 cursor-not-allowed' : ''}`}
                            />
                            <div className="ml-3">
                              <label htmlFor="regroup-violations" className={`text-sm font-medium ${slackConfig.wcag_grouping_option === 'single-issue' ? 'text-gray-400 dark:text-gray-500' : 'text-gray-700 dark:text-gray-300'}`}>
                                {t('integrations.config.slackViolationGrouping.groupByRuleType')}
                              </label>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {slackConfig.wcag_grouping_option === 'single-issue' 
                                  ? t('integrations.config.slackViolationGrouping.disabledWhenSingleIssue')
                                  : t('integrations.config.slackViolationGrouping.groupByRuleTypeHelp')}
                              </p>
                            </div>
                          </div>
                          {slackConfig.wcag_regroup_violations && slackConfig.wcag_grouping_option !== 'single-issue' && (
                            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                              <div className="flex items-start">
                                <div className="flex-shrink-0">
                                  <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                  </svg>
                                </div>
                                <div className="ml-2">
                                  <p className="text-xs text-yellow-700 dark:text-yellow-300">
                                    {t('integrations.config.slackViolationGrouping.truncationWarning')}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {slackConfig.wcag_grouping_option === 'single-issue' && (
                        <div className="mt-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div className="ml-2">
                              <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                                {t('integrations.config.slackWarnings.messageSizeLimit')}
                              </h4>
                              <p className="mt-1 text-xs text-yellow-700 dark:text-yellow-300">
                                {t('integrations.config.slackWarnings.truncationMessage')}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
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
                        updateSlackConfig({ 
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
                        {t('integrations.config.slackMessageGrouping')}
                      </label>
                      <select
                        value={slackConfig.html_grouping_option || 'per-error-type'}
                        onChange={handleHtmlGroupingChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="per-error-type">{t('integrations.config.slackHtmlGroupingOptions.perErrorType')}</option>
                        <option value="single-issue">{t('integrations.config.slackHtmlGroupingOptions.singleIssue')}</option>
                      </select>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {t('integrations.config.slackHtmlGroupingOptions.help')}
                      </p>
                      {slackConfig.html_grouping_option === 'single-issue' && (
                        <div className="mt-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div className="ml-2">
                              <p className="text-xs text-yellow-700 dark:text-yellow-300">
                                {t('integrations.config.slackWarnings.truncationShort')}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
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
                        updateSlackConfig({ 
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
                        {t('integrations.config.slackMessageGrouping')}
                      </label>
                      <select
                        value={slackConfig.links_grouping_option || 'per-error-type'}
                        onChange={handleLinksGroupingChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="per-error-type">{t('integrations.config.slackLinksGroupingOptions.perErrorType')}</option>
                        <option value="single-issue">{t('integrations.config.slackLinksGroupingOptions.singleIssue')}</option>
                      </select>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {t('integrations.config.slackLinksGroupingOptions.help')}
                      </p>
                      {slackConfig.links_grouping_option === 'single-issue' && (
                        <div className="mt-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div className="ml-2">
                              <p className="text-xs text-yellow-700 dark:text-yellow-300">
                                {t('integrations.config.slackWarnings.truncationShort')}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
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
                        updateSlackConfig({ 
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
                      When enabled, the accessibility tree structure will be included in Slack messages.
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
                        updateSlackConfig({ 
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
                        {t('integrations.config.slackMessageGrouping')}
                      </label>
                      <select
                        value={slackConfig.layout_grouping_option || 'per-error-type'}
                        onChange={handleLayoutGroupingChange}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="per-error-type">{t('integrations.config.slackLayoutGroupingOptions.perErrorType')}</option>
                        <option value="single-issue">{t('integrations.config.slackLayoutGroupingOptions.singleIssue')}</option>
                      </select>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {t('integrations.config.slackLayoutGroupingOptions.help')}
                      </p>
                      {slackConfig.layout_grouping_option === 'single-issue' && (
                        <div className="mt-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div className="ml-2">
                              <p className="text-xs text-yellow-700 dark:text-yellow-300">
                                {t('integrations.config.slackWarnings.truncationShort')}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
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
                value={slackConfig.pdf_grouping_option || 'per-page'}
                onChange={handlePdfGroupingChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="per-page">{t('integrations.config.slackPdfGroupingOptions.perPage')}</option>
                <option value="single-issue">{t('integrations.config.slackPdfGroupingOptions.singleIssue')}</option>
              </select>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('integrations.config.slackPdfGroupingOptions.help')}
              </p>
              {showTruncationWarning && (
                <div className="mt-3 flex items-start space-x-2 text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3">
                  <svg className="h-5 w-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div className="text-sm">
                    <p className="font-medium">{t('integrations.config.warnings.potentialTruncation')}</p>
                    <p className="mt-1">{t('integrations.config.slackWarnings.pdfTruncationMessage')}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeConfigTab === 'statistics' && (
          <div className="space-y-6 transition-opacity duration-200">
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <h4 className="font-medium text-green-900 dark:text-green-100 mb-2">{t('integrations.config.statisticsTab.title')}</h4>
              <div className="text-sm text-green-700 dark:text-green-300 space-y-1">
                <p>{t('integrations.config.statisticsTab.messagesSent')} {integration?.stats?.messages_posted || 0}</p>
                {integration?.stats?.last_message_posted && (
                  <p>{t('integrations.config.statisticsTab.lastMessageSent')} {new Date(integration.stats.last_message_posted).toLocaleDateString()}</p>
                )}
              </div>
            </div>
          </div>
        )}
          </>
        )}

        <div className="flex items-center justify-between">
          <button
            onClick={onBackToOverview}
            className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-md font-medium transition-colors duration-200"
          >
            {t('integrations.config.buttons.backToOverview')}
          </button>
          
          {integration?.config?.connected && (
            <button
              onClick={() => setShowDisconnectDialog(true)}
              disabled={isDisconnecting}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50 flex items-center space-x-2"
            >
              <LinkSlashIcon className="h-4 w-4" />
              <span>{isDisconnecting ? t('integrations.config.buttons.disconnecting') : t('integrations.config.buttons.disconnect')}</span>
            </button>
          )}
        </div>
      </div>
      
      <ConfirmationDialog
        isOpen={showDisconnectDialog}
        onClose={() => setShowDisconnectDialog(false)}
        onConfirm={handleDisconnect}
        title={t('integrations.slack.disconnectTitle')}
        message={t('integrations.slack.disconnectMessage')}
        confirmText={t('integrations.common.disconnect')}
        cancelText={t('common.cancel')}
        isDangerous={true}
      />
    </div>
  )
}

export default SlackConfigurationPanel
