import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import useAuthStore from '../stores/authStore'
import logger from '../utils/logger'

const useSlackIntegration = (user, integrations, loadIntegrations, updateIntegration) => {
  const [slackConfig, setSlackConfig] = useState({
    webhook_url: '',
    channel: '',
    notification_trigger: 'all-scans',
    wcag_severity_filter: ['High', 'Medium', 'Low'],
    wcag_grouping_option: 'per-error-type',
    wcag_regroup_violations: false,
    // Module-specific grouping options
    html_grouping_option: 'per-error-type',
    links_grouping_option: 'per-error-type',
    layout_grouping_option: 'per-error-type',
    // PDF grouping option
    pdf_grouping_option: 'per-page'
  })

  // Update Slack config when integrations change
  useEffect(() => {
    try {
      if (integrations?.slack) {
        logger.log('Updating Slack config from integrations:', integrations.slack)
        // Read from web_scan_sections - strict schema, no fallbacks
        const webScanSections = integrations.slack.web_scan_sections || {}
        const pdfScanSections = integrations.slack.pdf_scan_sections || {}
        const config = integrations.slack.config || {}
        
        setSlackConfig(prev => ({
          ...prev,
          channel: config.channel || '',
          notification_trigger: config.notification_trigger || 'all-scans',
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
      }
    } catch (error) {
      logger.error('Error updating Slack config state:', error)
    }
  }, [integrations?.slack])

  const updateSlackConfig = async (configUpdate) => {
    if (!user) return
    
    logger.log('Updating Slack config with:', configUpdate)
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const requestBody = JSON.stringify(configUpdate)
      logger.log('Request body:', requestBody)
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/slack/config`, {
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
        setSlackConfig(prev => ({ ...prev, ...configUpdate }))
        // Update integration store
        updateIntegration('slack', data.config)
        toast.success('Slack configuration updated successfully!')
      } else {
        let errorMessage = 'Failed to update Slack configuration'
        try {
          const errorData = await response.json()
          logger.error('Slack config update error:', errorData)
          
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
          errorMessage = 'Failed to update Slack configuration'
        }
        
        toast.error(errorMessage)
      }
    } catch (error) {
      logger.error('Error updating Slack config:', error)
      let errorMessage = 'Failed to update Slack configuration'
      
      // Ensure we never pass objects to toast
      if (error && typeof error.message === 'string') {
        errorMessage = error.message
      }
      
      toast.error(errorMessage)
    }
  }

  const updateSlackIntegrationStatus = async (isEnabled) => {
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
        toast.success(`Slack integration ${isEnabled ? 'enabled' : 'disabled'} successfully!`)
      } else {
        const errorData = await response.json()
        toast.error(errorData.detail || 'Failed to update Slack integration status')
        // Revert the UI state on error - update config.web_scan_enabled
        updateIntegration('slack', { config: { web_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating Slack integration status:', error)
      toast.error('Failed to update Slack integration status')
      // Revert the UI state on error - update config.web_scan_enabled
      updateIntegration('slack', { config: { web_scan_enabled: !isEnabled } })
    }
  }

  return {
    slackConfig,
    setSlackConfig,
    updateSlackConfig,
    updateSlackIntegrationStatus
  }
}

export default useSlackIntegration
