import { useState, useEffect, useCallback, useRef } from 'react'
import toast from 'react-hot-toast'
import useAuthStore from '../stores/authStore'
import logger from '../utils/logger'

const useGitHubIntegration = (user, integrations, loadIntegrations, updateIntegration) => {
  const [githubConfig, setGithubConfig] = useState({
    repository: '',
    wcag_severity_filter: ['High', 'Medium', 'Low'],
    wcag_grouping_option: 'per-error-type',
    wcag_regroup_violations: false,  // Default false per recommended settings
    // Module-specific grouping options
    html_grouping_option: 'per-error-type',
    links_grouping_option: 'per-error-type',
    layout_grouping_option: 'per-error-type',
    // PDF grouping option
    pdf_grouping_option: 'per-page'
  })
  
  const [githubRepositories, setGithubRepositories] = useState([])
  const [loadingRepositories, setLoadingRepositories] = useState(false)
  const hasAttemptedLoad = useRef(false)  // Track if we've attempted to load repos

  // Update GitHub config when integrations change
  useEffect(() => {
    try {
      if (integrations?.github) {
        logger.log('Updating GitHub config from integrations:', integrations.github)
        // Read from web_scan_sections - strict schema, no fallbacks
        const webScanSections = integrations.github.web_scan_sections || {}
        const pdfScanSections = integrations.github.pdf_scan_sections || {}
        const config = integrations.github.config || {}
        
        setGithubConfig(prev => ({
          ...prev,
          repository: config.repository || '',
          // Strict schema - only read from web_scan_sections with wcag_ prefix
          wcag_severity_filter: webScanSections.wcag_severity_filter || ['High', 'Medium', 'Low'],
          wcag_grouping_option: webScanSections.wcag_grouping_option || 'per-error-type',
          wcag_regroup_violations: webScanSections.wcag_regroup_violations !== undefined ? 
            webScanSections.wcag_regroup_violations : false,
          // Module-specific grouping options from web_scan_sections
          html_grouping_option: webScanSections.html_grouping_option || 'per-error-type',
          links_grouping_option: webScanSections.links_grouping_option || 'per-error-type',
          layout_grouping_option: webScanSections.layout_grouping_option || 'per-error-type',
          // PDF grouping option from pdf_scan_sections
          pdf_grouping_option: pdfScanSections.pdf_grouping_option || 'per-page'
        }))
        
        // Auto-load repositories if GitHub is connected (check config.connected)
        // Only attempt once to prevent infinite loops
        if (config.connected && githubRepositories.length === 0 && !loadingRepositories && !hasAttemptedLoad.current) {
          logger.log('GitHub is connected, auto-loading repositories...')
          hasAttemptedLoad.current = true
          loadGithubRepositories()
        }
      }
    } catch (error) {
      logger.error('Error updating GitHub config state:', error)
    }
  }, [integrations?.github, githubRepositories.length, loadingRepositories])

  const loadGithubRepositories = useCallback(async () => {
    if (!user) return
    
    setLoadingRepositories(true)
    try {
      const token = await useAuthStore.getState().getIdToken()
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/github/repositories`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setGithubRepositories(data.repositories || [])
      } else if (response.status === 401) {
        // Token expired, reconnection needed
        toast.error('GitHub connection expired. Please reconnect.')
        // Reload integrations to update connected state
        loadIntegrations(user)
      } else if (response.status === 404) {
        // GitHub not connected - prevent infinite loop by NOT retrying
        let errorData = {}
        try {
          errorData = await response.json()
        } catch (e) {
          // ignore
        }
        logger.log('GitHub not connected:', errorData)
        // Set empty repositories to prevent retry loop
        setGithubRepositories([])
        // Only show toast if it's a connection issue, not a real 404
        if (errorData.detail === 'GitHub not connected' || errorData.error === 'GitHub not connected') {
          toast.error('GitHub connection not found. Please reconnect.')
          // Optionally reload integrations to sync state
          loadIntegrations(user)
        }
      } else {
        let errorMessage = 'Failed to load repositories'
        try {
          const errorData = await response.json()
          logger.error('GitHub repositories error:', errorData)
          
          // Handle different error structures
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail
          } else if (typeof errorData.message === 'string') {
            errorMessage = errorData.message
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors
            errorMessage = errorData.detail.map(err => err.msg || 'Invalid data').join(', ')
          }
        } catch (e) {
          logger.warn('Could not parse error response:', e)
        }
        
        // Ensure errorMessage is always a string
        if (typeof errorMessage !== 'string') {
          errorMessage = 'Failed to load repositories'
        }
        
        toast.error(errorMessage)
      }
    } catch (error) {
      logger.error('Error loading GitHub repositories:', error)
      let errorMessage = 'Failed to load repositories'
      
      // Ensure we never pass objects to toast
      if (error && typeof error.message === 'string') {
        errorMessage = error.message
      }
      
      toast.error(errorMessage)
    } finally {
      setLoadingRepositories(false)
    }
  }, [user, loadIntegrations])

  const updateGithubConfig = async (configUpdate) => {
    if (!user) return
    
    logger.log('Updating GitHub config with:', configUpdate)
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const requestBody = JSON.stringify(configUpdate)
      logger.log('Request body:', requestBody)
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/github/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: requestBody
      })
      
      if (response.ok) {
        const data = await response.json()
        // Update local state
        setGithubConfig(prev => ({ ...prev, ...configUpdate }))
        // Update integration store
        updateIntegration('github', data.config)
        toast.success('GitHub configuration updated successfully!')
      } else {
        let errorMessage = 'Failed to update GitHub configuration'
        try {
          const errorData = await response.json()
          logger.error('GitHub config update error:', errorData)
          
          // Handle different error structures
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail
          } else if (typeof errorData.message === 'string') {
            errorMessage = errorData.message
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors - extract messages from array
            const validationErrors = errorData.detail.map(err => {
              if (typeof err === 'string') return err
              if (err && typeof err.msg === 'string') return err.msg
              if (err && typeof err.message === 'string') return err.message
              return 'Validation error'
            })
            errorMessage = validationErrors.join(', ')
            logger.error('Pydantic validation errors:', errorData.detail)
          } else if (errorData.detail && typeof errorData.detail === 'object') {
            errorMessage = 'Invalid configuration data provided'
          }
        } catch (e) {
          logger.warn('Could not parse error response:', e)
        }
        
        // Ensure errorMessage is always a string and not empty
        if (typeof errorMessage !== 'string' || errorMessage.trim() === '') {
          errorMessage = 'Failed to update GitHub configuration'
        }
        
        toast.error(errorMessage)
      }
    } catch (error) {
      logger.error('Error updating GitHub config:', error)
      let errorMessage = 'Failed to update GitHub configuration'
      
      // Ensure we never pass objects to toast
      if (error && typeof error.message === 'string') {
        errorMessage = error.message
      }
      
      toast.error(errorMessage)
    }
  }

  const updateGithubIntegrationStatus = async (isEnabled) => {
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
        toast.success(`GitHub integration ${isEnabled ? 'enabled' : 'disabled'} successfully!`)
      } else {
        const errorData = await response.json()
        toast.error(errorData.detail || 'Failed to update GitHub integration status')
        // Revert the UI state on error - update config.web_scan_enabled
        updateIntegration('github', { config: { web_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating GitHub integration status:', error)
      toast.error('Failed to update GitHub integration status')
      // Revert the UI state on error - update config.web_scan_enabled
      updateIntegration('github', { config: { web_scan_enabled: !isEnabled } })
    }
  }

  return {
    githubConfig,
    setGithubConfig,
    githubRepositories,
    loadingRepositories,
    loadGithubRepositories,
    updateGithubConfig,
    updateGithubIntegrationStatus
  }
}

export default useGitHubIntegration
