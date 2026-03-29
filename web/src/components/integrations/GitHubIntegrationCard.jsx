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
import githubIcon from '../../images/github.svg'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const GitHubIntegrationCard = ({
  integration,
  error,
  loading,
  githubConfig,
  githubRepositories,
  loadingRepositories,
  onConnect,
  onConfigClick,
  onRepositoryChange,
  onLoadRepositories,
  onToggleEnabled,
  updateGithubConfig,
  onDisconnect,
  isDisconnecting,
  disabled = false
}) => {
  const { t } = useTranslation()
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false)
  const handleDisconnect = async () => {
    setShowDisconnectDialog(false)
    if (onDisconnect) {
      await onDisconnect('github')
    }
  }

  const updateGithubIntegrationStatus = async (isEnabled) => {
    const { user } = useAuthStore.getState()
    if (!user) return
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/github/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_enabled: isEnabled })
      })
      
      if (response.ok) {
        toast.success(t('integrations.common.toasts.enabled', { platform: 'GitHub' }).replace('enabled', isEnabled ? 'enabled' : 'disabled'))
      } else {
        const errorData = await response.json()
        logger.error('GitHub integration update failed:', errorData.detail)
        toast.error(t('integrations.common.toasts.updateFailed', { platform: 'GitHub' }))
        // Revert the UI state on error
        onToggleEnabled('github', { config: { web_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating GitHub integration status:', error)
      toast.error(t('integrations.common.toasts.updateFailed', { platform: 'GitHub' }))
      // Revert the UI state on error
      onToggleEnabled('github', { config: { web_scan_enabled: !isEnabled } })
    }
  }

  const handleToggleEnabled = () => {
    const newIsEnabled = !integration.config?.web_scan_enabled
    onToggleEnabled('github', { config: { web_scan_enabled: newIsEnabled } })
    // Also update the backend
    updateGithubIntegrationStatus(newIsEnabled)
  }

  const handleTogglePdfEnabled = () => {
    const newPdfEnabled = !integration.config?.pdf_scan_enabled
    onToggleEnabled('github', { config: { pdf_scan_enabled: newPdfEnabled } })
    // Also update the backend for PDF scans
    updateGithubPdfStatus(newPdfEnabled)
  }

  const updateGithubPdfStatus = async (isEnabled) => {
    const { user } = useAuthStore.getState()
    if (!user) return
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/github/pdf-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_enabled: isEnabled })
      })
      
      if (response.ok) {
        toast.success(isEnabled ? t('integrations.common.toasts.enabled', { platform: 'GitHub PDF' }) : t('integrations.common.toasts.disabled', { platform: 'GitHub PDF' }))
      } else {
        const errorData = await response.json()
        logger.error('GitHub PDF integration update failed:', errorData.detail)
        toast.error(t('integrations.common.toasts.updateFailed', { platform: 'GitHub PDF' }))
        // Revert the UI state on error
        onToggleEnabled('github', { config: { pdf_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating GitHub PDF integration status:', error)
      toast.error(t('integrations.common.toasts.updateFailed', { platform: 'GitHub PDF' }))
      // Revert the UI state on error
      onToggleEnabled('github', { config: { pdf_scan_enabled: !isEnabled } })
    }
  }

  const handleRepositoryChange = (e) => {
    const newRepo = e.target.value
    onRepositoryChange(newRepo)
    updateGithubConfig({ repository: newRepo })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-start space-x-4">
        <div className="p-3 rounded-lg bg-white dark:bg-gray-200 border border-gray-200 dark:border-gray-300">
          <img src={githubIcon} alt="GitHub" className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{t('integrations.github.name')}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {t('integrations.github.description')}
          </p>
          
          {error && (
            <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 mb-4">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <span className="text-sm">{typeof error === 'string' ? error : 'An error occurred'}</span>
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
                onClick={() => onConnect('github')}
                disabled={loading.general || loading.github}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 disabled:opacity-50"
              >
                {loading.github ? t('integrations.common.connecting') : t('integrations.common.connect')}
              </button>
            )
          ) : (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                <CheckCircleIcon className="h-4 w-4" />
                <span className="text-sm font-medium">{t('integrations.github.connected')} {integration.config?.github_user}</span>
              </div>
              
              {/* Repository Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('integrations.github.repository')}
                </label>
                <div className="flex space-x-2">
                  <select
                    value={githubConfig.repository}
                    onChange={handleRepositoryChange}
                    onClick={() => {
                      if (githubRepositories.length === 0) {
                        onLoadRepositories()
                      }
                    }}
                    className="flex-1 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">{t('integrations.github.selectRepository')}</option>
                    {githubRepositories.map(repo => (
                      <option key={repo.full_name} value={repo.full_name}>
                        {repo.full_name} {repo.private ? '(Private)' : '(Public)'}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={onLoadRepositories}
                    disabled={loadingRepositories}
                    className="bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300 px-3 py-2 rounded-md transition-colors duration-200 disabled:opacity-50"
                  >
                    {loadingRepositories ? '...' : '↻'}
                  </button>
                </div>
              </div>
              
              {/* Push Web Scan Results to GitHub Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('integrations.common.webScanEnabled')}
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.github.webScanDesc')}
                  </p>
                </div>
                <button
                  onClick={handleToggleEnabled}
                  disabled={!githubConfig.repository}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 ${
                    integration.config?.web_scan_enabled && githubConfig.repository ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      integration.config?.web_scan_enabled && githubConfig.repository ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
              
              {/* Push PDF Scan Results to GitHub Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('integrations.common.pdfScanEnabled')}
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('integrations.github.pdfScanDesc')}
                  </p>
                </div>
                <button
                  onClick={handleTogglePdfEnabled}
                  disabled={!githubConfig.repository}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 ${
                    integration.config?.pdf_scan_enabled && githubConfig.repository ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      integration.config?.pdf_scan_enabled && githubConfig.repository ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
              
              {/* Configuration and Disconnect Buttons */}
              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => onConfigClick('github')}
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
        title={t('integrations.github.disconnectTitle')}
        message={t('integrations.github.disconnectMessage')}
        confirmText={t('integrations.common.disconnect')}
        cancelText={t('common.cancel')}
        isDangerous={true}
      />
    </div>
  )
}

export default GitHubIntegrationCard
