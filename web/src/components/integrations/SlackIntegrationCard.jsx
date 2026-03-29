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
import slackIcon from '../../images/slack.svg'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const SlackIntegrationCard = ({
  integration,
  error,
  loading,
  slackConfig,
  onConnect,
  onConfigClick,
  onToggleEnabled,
  updateSlackConfig,
  onDisconnect,
  isDisconnecting,
  disabled = false
}) => {
  const { t } = useTranslation()
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  
  const handleDisconnect = async () => {
    setShowDisconnectDialog(false)
    if (onDisconnect) {
      await onDisconnect('slack')
    }
  }
  const updateSlackIntegrationStatus = async (isEnabled) => {
    const { user } = useAuthStore.getState()
    if (!user) return
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/slack/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_enabled: isEnabled })
      })
      
      if (response.ok) {
        toast.success(t('integrations.common.enabledSuccess', { platform: 'Slack' }).replace('enabled', isEnabled ? 'enabled' : 'disabled'))
      } else {
        const errorData = await response.json()
        logger.error('Slack integration update failed:', errorData.detail)
        toast.error(t('integrations.common.updateFailed', { platform: 'Slack' }))
        // Revert the UI state on error
        onToggleEnabled('slack', { config: { web_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating Slack integration status:', error)
      toast.error(t('integrations.common.updateFailed', { platform: 'Slack' }))
      // Revert the UI state on error
      onToggleEnabled('slack', { config: { web_scan_enabled: !isEnabled } })
    }
  }

  const handleToggleEnabled = () => {
    const newIsEnabled = !integration.config?.web_scan_enabled
    onToggleEnabled('slack', { config: { web_scan_enabled: newIsEnabled } })
    updateSlackIntegrationStatus(newIsEnabled)
  }

  const handleTogglePdfEnabled = () => {
    const newPdfEnabled = !integration.config?.pdf_scan_enabled
    onToggleEnabled('slack', { config: { pdf_scan_enabled: newPdfEnabled } })
    updateSlackPdfStatus(newPdfEnabled)
  }

  const updateSlackPdfStatus = async (isEnabled) => {
    const { user } = useAuthStore.getState()
    if (!user) return
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/slack/pdf-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_enabled: isEnabled })
      })
      
      if (response.ok) {
        toast.success(t('integrations.common.enabledSuccess', { platform: 'Slack PDF' }).replace('enabled', isEnabled ? 'enabled' : 'disabled'))
      } else {
        const errorData = await response.json()
        logger.error('Slack PDF integration update failed:', errorData.detail)
        toast.error(t('integrations.common.updateFailed', { platform: 'Slack PDF' }))
        // Revert the UI state on error
        onToggleEnabled('slack', { config: { pdf_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating Slack PDF integration status:', error)
      toast.error(t('integrations.common.updateFailed', { platform: 'Slack PDF' }))
      // Revert the UI state on error
      onToggleEnabled('slack', { config: { pdf_scan_enabled: !isEnabled } })
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-start space-x-4">
        <div className="p-3 rounded-lg bg-white dark:bg-gray-200 border border-gray-200 dark:border-gray-300">
          <img src={slackIcon} alt="Slack" className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{t('integrations.slack.name')}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {t('integrations.slack.description')}
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
                onClick={() => onConnect('slack')}
                disabled={loading.general || loading.slack}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50"
              >
                {loading.slack ? t('integrations.common.connecting') : t('integrations.common.connect')}
              </button>
            )
          ) : (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                <CheckCircleIcon className="h-4 w-4" />
                <span className="text-sm font-medium">{t('integrations.slack.connected')}</span>
              </div>
              
              {/* Configuration Controls */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('integrations.common.pushWebScan', { platform: 'Slack' })}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('integrations.slack.webScanDesc')}
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
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('integrations.common.pushPdfScan', { platform: 'Slack' })}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('integrations.slack.pdfScanDesc')}
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

              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={onConfigClick}
                  className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors duration-200"
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
        title={t('integrations.slack.disconnectTitle')}
        message={t('integrations.slack.disconnectMessage')}
        confirmText={t('integrations.common.disconnect')}
        cancelText={t('common.cancel')}
        isDangerous={true}
      />
    </div>
  )
}

export default SlackIntegrationCard
