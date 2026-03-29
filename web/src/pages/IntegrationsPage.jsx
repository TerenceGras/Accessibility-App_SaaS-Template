import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LockClosedIcon } from '@heroicons/react/24/outline'
import useAuthStore from '../stores/authStore'
import useIntegrationStore from '../stores/integrationStore'
import useGitHubIntegration from '../hooks/useGitHubIntegration'
import useNotionIntegration from '../hooks/useNotionIntegration'
import useSlackIntegration from '../hooks/useSlackIntegration'
import useOAuthCallback from '../hooks/useOAuthCallback'
import useIntegrationConnections from '../hooks/useIntegrationConnections'
import useDisconnectIntegration from '../hooks/useDisconnectIntegration'
import LoadingSpinner from '../components/integrations/LoadingSpinner'
import AuthenticationRequired from '../components/integrations/AuthenticationRequired'
import IntroductionBanner from '../components/integrations/IntroductionBanner'
import GitHubIntegrationCard from '../components/integrations/GitHubIntegrationCard'
import NotionIntegrationCard from '../components/integrations/NotionIntegrationCard'
import SlackIntegrationCard from '../components/integrations/SlackIntegrationCard'
import GitHubConfigurationPanel from '../components/integrations/GitHubConfigurationPanel'
import NotionConfigurationPanel from '../components/integrations/NotionConfigurationPanel'
import SlackConfigurationPanel from '../components/integrations/SlackConfigurationPanel'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''

const IntegrationsPage = () => {
  const { t } = useTranslation()
  const { user, getIdToken, loading: authLoading } = useAuthStore()
  const { integrations, loading, errors, loadIntegrations, clearError, updateIntegration } = useIntegrationStore()
  
  const [activeTab, setActiveTab] = useState('overview')
  const [subscription, setSubscription] = useState(null)
  const [subscriptionLoading, setSubscriptionLoading] = useState(true)
  const [slackConfig, setSlackConfig] = useState({
    webhook_url: '',
    channel: '',
    wcag_severity_filter: ['High', 'Medium', 'Low'],
    wcag_grouping_option: 'per-error-type',
    wcag_regroup_violations: false
  })

  // Custom hooks
  const {
    githubConfig,
    setGithubConfig,
    githubRepositories,
    loadingRepositories,
    loadGithubRepositories,
    updateGithubConfig,
    updateGithubIntegrationStatus
  } = useGitHubIntegration(user, integrations, loadIntegrations, updateIntegration)

  const {
    notionConfig,
    setNotionConfig,
    updateNotionConfig,
    updateNotionIntegrationStatus
  } = useNotionIntegration(user, integrations, loadIntegrations, updateIntegration)

  const {
    slackConfig: slackIntegrationConfig,
    setSlackConfig: setSlackIntegrationConfig,
    updateSlackConfig,
    updateSlackIntegrationStatus
  } = useSlackIntegration(user, integrations, loadIntegrations, updateIntegration)
  
  useOAuthCallback(user, loadIntegrations)
  
  const { handleConnect, handleSlackConnect } = useIntegrationConnections(clearError, updateIntegration)
  const { disconnectIntegration, isDisconnecting } = useDisconnectIntegration(loadIntegrations)

  // Load integrations when user is available
  useEffect(() => {
    if (user && !authLoading) {
      try {
        loadIntegrations(user)
        loadSubscription()
      } catch (error) {
        logger.error('Error loading integrations:', error)
      }
    }
  }, [user, authLoading, loadIntegrations])

  const loadSubscription = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/subscription`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setSubscription(data.subscription)
      }
    } catch (error) {
      logger.error('Error fetching subscription:', error)
    } finally {
      setSubscriptionLoading(false)
    }
  }

  // Integrations are now available to all logged-in users
  const hasIntegrationsAccess = true  // Was: subscription && subscription.plan !== 'free' && subscription.status === 'active'

  const handleSlackConnectAndClose = async () => {
    const success = await handleSlackConnect(slackConfig)
    if (success) {
      setActiveTab('overview')
      // Reload integrations to get updated state
      if (user) {
        loadIntegrations(user)
      }
    }
  }

  const handleRepositoryChange = (newRepo) => {
    setGithubConfig(prev => ({ ...prev, repository: newRepo }))
  }

  const handleToggleIntegration = (platform, update) => {
    updateIntegration(platform, update)
    // Extract the web_scan_enabled value from the update object
    const isEnabled = update.config?.web_scan_enabled
    if (isEnabled !== undefined) {
      if (platform === 'github') {
        updateGithubIntegrationStatus(isEnabled)
      } else if (platform === 'notion') {
        updateNotionIntegrationStatus(isEnabled)
      } else if (platform === 'slack') {
        updateSlackIntegrationStatus(isEnabled)
      }
    }
  }

  if (authLoading || loading.general || subscriptionLoading) {
    return <LoadingSpinner />
  }

  if (!user) {
    return <AuthenticationRequired />
  }

  return (
    <PageContainer
      title={t('integrations.title')}
      description={t('integrations.description')}
    >
      {/* Free Plan - Full page blur overlay */}
      {!hasIntegrationsAccess ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="relative"
        >
          {/* Blurred background content */}
          <div className="filter blur-sm pointer-events-none select-none opacity-60">
            <IntroductionBanner />
            <div className="space-y-4 mt-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 h-48"></div>
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 h-48"></div>
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 h-48"></div>
            </div>
          </div>
          
          {/* Overlay with lock message */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-8 max-w-md mx-4 text-center">
              <div className="flex justify-center mb-4">
                <div className="p-3 bg-amber-100 dark:bg-amber-900/30 rounded-full">
                  <LockClosedIcon className="h-8 w-8 text-amber-600 dark:text-amber-400" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('integrations.paidRequired.title')}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                {t('integrations.paidRequired.description')}
              </p>
              <Link
                to="/pricing"
                className="inline-flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
              >
                {t('integrations.paidRequired.viewPlans')}
              </Link>
            </div>
          </div>
        </motion.div>
      ) : (
        <>
          {activeTab === 'overview' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-6"
        >
          <IntroductionBanner />

          <div className="space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <GitHubIntegrationCard
                integration={integrations.github}
                error={errors.github}
                loading={loading}
                githubConfig={githubConfig}
                githubRepositories={githubRepositories}
                loadingRepositories={loadingRepositories}
                onConnect={hasIntegrationsAccess ? handleConnect : null}
                onConfigClick={() => setActiveTab('github')}
                onRepositoryChange={handleRepositoryChange}
                onLoadRepositories={loadGithubRepositories}
                onToggleEnabled={handleToggleIntegration}
                updateGithubConfig={updateGithubConfig}
                onDisconnect={disconnectIntegration}
                isDisconnecting={isDisconnecting.github}
                disabled={!hasIntegrationsAccess}
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.2 }}
            >
              <NotionIntegrationCard
                integration={integrations.notion}
                error={errors.notion}
                loading={loading}
                notionConfig={notionConfig}
                onConnect={hasIntegrationsAccess ? handleConnect : null}
                onConfigClick={() => setActiveTab('notion')}
                onPageUrlChange={(newPageUrl) => setNotionConfig(prev => ({ ...prev, page_url: newPageUrl }))}
                onToggleEnabled={handleToggleIntegration}
                updateNotionConfig={updateNotionConfig}
                onDisconnect={disconnectIntegration}
                isDisconnecting={isDisconnecting.notion}
                disabled={!hasIntegrationsAccess}
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
            >
              <SlackIntegrationCard
                integration={integrations.slack}
                error={errors.slack}
                loading={loading}
                slackConfig={slackIntegrationConfig}
                onConnect={hasIntegrationsAccess ? (platform) => {
                  if (platform === 'slack') {
                    setActiveTab('slack')
                  } else {
                    handleConnect(platform)
                  }
                } : null}
                onConfigClick={() => setActiveTab('slack')}
                onToggleEnabled={handleToggleIntegration}
                updateSlackConfig={updateSlackConfig}
                onDisconnect={disconnectIntegration}
                isDisconnecting={isDisconnecting.slack}
                disabled={!hasIntegrationsAccess}
              />
            </motion.div>
          </div>
        </motion.div>
      )}

      {activeTab === 'slack' && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <SlackConfigurationPanel
            integration={integrations.slack}
            slackConfig={integrations.slack?.config?.connected ? slackIntegrationConfig : slackConfig}
            loading={loading}
            onBackToOverview={() => setActiveTab('overview')}
            onConnect={integrations.slack?.config?.connected ? undefined : handleSlackConnectAndClose}
            onConfigChange={integrations.slack?.config?.connected ? setSlackIntegrationConfig : setSlackConfig}
            onToggleEnabled={handleToggleIntegration}
            updateSlackConfig={updateSlackConfig}
            onDisconnect={disconnectIntegration}
            isDisconnecting={isDisconnecting.slack}
          />
        </motion.div>
      )}

      {activeTab === 'github' && integrations.github?.config?.connected && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <GitHubConfigurationPanel
            integration={integrations.github}
            githubConfig={githubConfig}
            githubRepositories={githubRepositories}
            loadingRepositories={loadingRepositories}
            onBackToOverview={() => setActiveTab('overview')}
            onRepositoryChange={handleRepositoryChange}
            onLoadRepositories={loadGithubRepositories}
            onToggleEnabled={handleToggleIntegration}
            updateGithubConfig={updateGithubConfig}
            onDisconnect={disconnectIntegration}
            isDisconnecting={isDisconnecting.github}
          />
        </motion.div>
      )}

      {activeTab === 'notion' && integrations.notion?.config?.connected && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <NotionConfigurationPanel
            integration={integrations.notion}
            notionConfig={notionConfig}
            onBackToOverview={() => setActiveTab('overview')}
            onPageUrlChange={(newPageUrl) => setNotionConfig(prev => ({ ...prev, page_url: newPageUrl }))}
            onToggleEnabled={handleToggleIntegration}
            updateNotionConfig={updateNotionConfig}
            onDisconnect={disconnectIntegration}
            isDisconnecting={isDisconnecting.notion}
          />
        </motion.div>
      )}
        </>
      )}
    </PageContainer>
  )
}

export default IntegrationsPage
