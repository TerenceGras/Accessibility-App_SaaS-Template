import { useEffect } from 'react'
import toast from 'react-hot-toast'

const useOAuthCallback = (user, loadIntegrations) => {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const githubStatus = urlParams.get('github')
    const githubUser = urlParams.get('user')
    const notionStatus = urlParams.get('notion')
    const notionWorkspace = urlParams.get('workspace')
    const errorMessage = urlParams.get('message')
    
    if (githubStatus === 'success' && githubUser) {
      toast.success(`GitHub connected successfully for ${githubUser}!`)
      // Reload integrations to show connected state
      if (user) {
        loadIntegrations(user)
      }
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (githubStatus === 'error') {
      toast.error(`GitHub connection failed: ${errorMessage || 'Unknown error'}`)
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (notionStatus === 'success' && notionWorkspace) {
      toast.success(`Notion connected successfully for ${notionWorkspace}!`)
      // Reload integrations to show connected state
      if (user) {
        loadIntegrations(user)
      }
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (notionStatus === 'error') {
      toast.error(`Notion connection failed: ${errorMessage || 'Unknown error'}`)
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [user, loadIntegrations])
}

export default useOAuthCallback
