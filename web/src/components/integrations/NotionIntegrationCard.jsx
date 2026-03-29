import React, { useState } from 'react'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon,
  LinkSlashIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import useAuthStore from '../../stores/authStore'
import ConfirmationDialog from './ConfirmationDialog'
import notionIcon from '../../images/notion.svg'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const NotionIntegrationCard = ({
  integration,
  error,
  loading,
  notionConfig,
  onConnect,
  onConfigClick,
  onPageUrlChange,
  onToggleEnabled,
  updateNotionConfig,
  onDisconnect,
  isDisconnecting,
  disabled = false
}) => {
  const { t } = useTranslation()
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  
  const handleDisconnect = async () => {
    setShowDisconnectDialog(false)
    if (onDisconnect) {
      await onDisconnect('notion')
    }
  }
  const updateNotionIntegrationStatus = async (isEnabled) => {
    const { user } = useAuthStore.getState()
    if (!user) return
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/notion/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_enabled: isEnabled })
      })
      
      if (response.ok) {
        toast.success(t('integrations.common.enabledSuccess', { platform: 'Notion' }).replace('enabled', isEnabled ? 'enabled' : 'disabled'))
      } else {
        const errorData = await response.json()
        logger.error('Notion integration update failed:', errorData.detail)
        toast.error(t('integrations.common.updateFailed', { platform: 'Notion' }))
        // Revert the UI state on error
        onToggleEnabled('notion', { config: { web_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating Notion integration status:', error)
      toast.error(t('integrations.common.updateFailed', { platform: 'Notion' }))
      // Revert the UI state on error
      onToggleEnabled('notion', { config: { web_scan_enabled: !isEnabled } })
    }
  }

  const handleToggleEnabled = () => {
    const newIsEnabled = !integration.config?.web_scan_enabled
    onToggleEnabled('notion', { config: { web_scan_enabled: newIsEnabled } })
    // Also update the backend
    updateNotionIntegrationStatus(newIsEnabled)
  }

  const handleTogglePdfEnabled = () => {
    const newPdfEnabled = !integration.config?.pdf_scan_enabled
    onToggleEnabled('notion', { config: { pdf_scan_enabled: newPdfEnabled } })
    // Also update the backend for PDF scans
    updateNotionPdfStatus(newPdfEnabled)
  }

  const updateNotionPdfStatus = async (isEnabled) => {
    const { user } = useAuthStore.getState()
    if (!user) return
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/notion/pdf-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_enabled: isEnabled })
      })
      
      if (response.ok) {
        toast.success(t('integrations.common.enabledSuccess', { platform: 'Notion PDF' }).replace('enabled', isEnabled ? 'enabled' : 'disabled'))
      } else {
        const errorData = await response.json()
        logger.error('Notion PDF integration update failed:', errorData.detail)
        toast.error(t('integrations.common.updateFailed', { platform: 'Notion PDF' }))
        // Revert the UI state on error
        onToggleEnabled('notion', { config: { pdf_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating Notion PDF integration status:', error)
      toast.error(t('integrations.common.updateFailed', { platform: 'Notion PDF' }))
      // Revert the UI state on error
      onToggleEnabled('notion', { config: { pdf_scan_enabled: !isEnabled } })
    }
  }

  const handlePageUrlChange = (e) => {
    const newPageUrl = e.target.value
    onPageUrlChange(newPageUrl)
    updateNotionConfig({ page_url: newPageUrl })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-start space-x-4">
        <div className="p-3 rounded-lg bg-white dark:bg-gray-200 border border-gray-200 dark:border-gray-300">
          <img src={notionIcon} alt="Notion" className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{t('integrations.notion.name')}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {t('integrations.notion.description')}
          </p>
          
          {error && (
            <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 mb-4">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <span className="text-sm">{typeof error === 'string' ? error : t('integrations.common.errorOccurred')}</span>
            </div>
          )}
          
          {!integration?.config?.connected ? (
            disabled ? (
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm">
                <LockClosedIcon className="h-4 w-4" />
                <span>{t('integrations.common.upgradeToConnect')}</span>
              </div>
            ) : (
              <button
                onClick={() => onConnect('notion')}
                disabled={loading.general || loading.notion}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50"
              >
                {loading.notion ? t('integrations.common.connecting') : t('integrations.common.connect')}
              </button>
            )
          ) : (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                <CheckCircleIcon className="h-4 w-4" />
                <span className="text-sm font-medium">{t('integrations.notion.connected', { workspace: integration.config?.workspace_name || t('integrations.notion.connectedDefault').replace('Connected to ', '') })}</span>
              </div>
              
              {/* Parent Page URL Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('integrations.notion.parentPageUrl')}
                </label>
                <input
                  type="url"
                  value={notionConfig.page_url || ''}
                  onChange={handlePageUrlChange}
                  placeholder={t('integrations.notion.parentPagePlaceholder')}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('integrations.notion.parentPageHelp')}
                </p>
              </div>
              
              {/* Push Web Scan Results to Notion Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('integrations.common.pushWebScan', { platform: 'Notion' })}
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.notion.webScanDesc')}
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
              
              {/* Push PDF Scan Results to Notion Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('integrations.common.pushPdfScan', { platform: 'Notion' })}
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.notion.pdfScanDesc')}
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
              
              {/* Configuration and Disconnect Buttons */}
              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => onConfigClick('notion')}
                  className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors duration-200"
                >
                  <Cog6ToothIcon className="h-4 w-4" />
                  <span className="text-sm">{t('integrations.common.configure')}</span>
                </button>
                
                <button
                  onClick={() => setShowDisconnectDialog(true)}
                  disabled={isDisconnecting}
                  className="flex items-center space-x-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors duration-200 disabled:opacity-50"
                >
                  <LinkSlashIcon className="h-4 w-4" />
                  <span className="text-sm">{isDisconnecting ? t('integrations.common.disconnecting') : t('integrations.common.disconnect')}</span>
                </button>
              </div>
            </div>
          )}
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

export default NotionIntegrationCard
