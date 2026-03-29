import { useState } from 'react'
import toast from 'react-hot-toast'
import useAuthStore from '../stores/authStore'
import logger from '../utils/logger'

const useDisconnectIntegration = (loadIntegrations) => {
  const [isDisconnecting, setIsDisconnecting] = useState({
    github: false,
    notion: false,
    slack: false
  })

  const disconnectIntegration = async (platform) => {
    const { user } = useAuthStore.getState()
    if (!user) {
      toast.error('You must be logged in to disconnect integrations')
      return false
    }

    setIsDisconnecting(prev => ({ ...prev, [platform]: true }))
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/${platform}/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        toast.success(`${platform.charAt(0).toUpperCase() + platform.slice(1)} disconnected successfully!`)
        // Reload integrations to reflect the disconnected state
        if (loadIntegrations) {
          await loadIntegrations(user)
        }
        return true
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to disconnect ${platform}`)
      }
    } catch (error) {
      logger.error(`Error disconnecting ${platform}:`, error)
      toast.error(`Failed to disconnect ${platform}. Please try again.`)
      return false
    } finally {
      setIsDisconnecting(prev => ({ ...prev, [platform]: false }))
    }
  }

  return {
    disconnectIntegration,
    isDisconnecting
  }
}

export default useDisconnectIntegration
