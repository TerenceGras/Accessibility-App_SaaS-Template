import toast from 'react-hot-toast'
import useAuthStore from '../stores/authStore'
import logger from '../utils/logger'

const useIntegrationConnections = (clearError, updateIntegration) => {
  const handleConnect = async (platform) => {
    clearError(platform)
    
    switch (platform) {
      case 'github':
        try {
          const token = await useAuthStore.getState().getIdToken()
          const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/github/oauth/authorize`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const data = await response.json()
            // Redirect to GitHub OAuth
            window.location.href = data.oauth_url
          } else {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to start OAuth flow')
          }
        } catch (error) {
          logger.error('Error starting GitHub OAuth:', error)
          toast.error('Failed to start GitHub connection. Please try again.')
        }
        break
      case 'notion':
        try {
          const token = await useAuthStore.getState().getIdToken()
          const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/notion/oauth/authorize`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const data = await response.json()
            // Redirect to Notion OAuth
            window.location.href = data.oauth_url
          } else {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to start OAuth flow')
          }
        } catch (error) {
          logger.error('Error starting Notion OAuth:', error)
          toast.error('Failed to start Notion connection. Please try again.')
        }
        break
      case 'slack':
        // Handled by parent component - switching to slack tab
        break
      default:
        toast.error(`${platform} integration is not yet supported.`)
    }
  }

  const handleSlackConnect = async (slackConfig) => {
    if (!slackConfig.webhook_url.trim()) {
      toast.error('Please enter a valid webhook URL')
      return false
    }
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/slack/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          webhook_url: slackConfig.webhook_url.trim(),
          channel: slackConfig.channel.trim() || null,
          notification_trigger: slackConfig.notification_trigger
        })
      })

      if (response.ok) {
        // Update the integration store
        updateIntegration('slack', {
          connected: true,
          enabled: true,
          config: {
            channel: slackConfig.channel.trim() || null,
            notification_trigger: slackConfig.notification_trigger
          }
        })
        toast.success('Slack integration connected successfully!')
        return true
      } else {
        const errorData = await response.json()
        toast.error(errorData.detail || 'Failed to connect Slack integration')
        return false
      }
    } catch (error) {
      logger.error('Error connecting Slack:', error)
      toast.error('Failed to connect Slack integration')
      return false
    }
  }

  return {
    handleConnect,
    handleSlackConnect
  }
}

export default useIntegrationConnections
