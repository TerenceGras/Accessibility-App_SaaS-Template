import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import useAuthStore from '../stores/authStore'
import logger from '../utils/logger'

const useNotionIntegration = (user, integrations, loadIntegrations, updateIntegration) => {
  const [notionConfig, setNotionConfig] = useState({
    page_url: '',
    parent_page_id: '',
    wcag_severity_filter: ['High', 'Medium', 'Low'],
    wcag_grouping_option: 'per-error-type',
    wcag_regroup_violations: true,  // Default true per recommended settings for Notion
    // Module-specific grouping options
    html_grouping_option: 'per-error-type',
    links_grouping_option: 'per-error-type',
    layout_grouping_option: 'per-error-type',
    // PDF grouping option
    pdf_grouping_option: 'per-page'
  })

  // Update Notion config when integrations change
  useEffect(() => {
    try {
      if (integrations?.notion) {
        logger.log('Updating Notion config from integrations:', integrations.notion)
        // Read from web_scan_sections - strict schema, no fallbacks
        const webScanSections = integrations.notion.web_scan_sections || {}
        const pdfScanSections = integrations.notion.pdf_scan_sections || {}
        const config = integrations.notion.config || {}
        
        setNotionConfig(prev => ({
          ...prev,
          page_url: config.page_url || '',
          parent_page_id: config.parent_page_id || '',
          // Strict schema - only read from web_scan_sections with wcag_ prefix
          wcag_severity_filter: webScanSections.wcag_severity_filter || ['High', 'Medium', 'Low'],
          wcag_grouping_option: webScanSections.wcag_grouping_option || 'per-error-type',
          wcag_regroup_violations: webScanSections.wcag_regroup_violations !== undefined ? 
            webScanSections.wcag_regroup_violations : true,
          // Module-specific grouping options from web_scan_sections
          html_grouping_option: webScanSections.html_grouping_option || 'per-error-type',
          links_grouping_option: webScanSections.links_grouping_option || 'per-error-type',
          layout_grouping_option: webScanSections.layout_grouping_option || 'per-error-type',
          // PDF grouping option from pdf_scan_sections
          pdf_grouping_option: pdfScanSections.pdf_grouping_option || 'per-page'
        }))
      }
    } catch (error) {
      logger.error('Error updating Notion config state:', error)
    }
  }, [integrations?.notion])

  const updateNotionConfig = async (configUpdate) => {
    if (!user) return
    
    logger.log('Updating Notion config with:', configUpdate)
    
    try {
      const token = await useAuthStore.getState().getIdToken()
      const requestBody = JSON.stringify(configUpdate)
      logger.log('Request body:', requestBody)
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/notion/config`, {
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
        setNotionConfig(prev => ({ ...prev, ...configUpdate }))
        // Update integration store
        updateIntegration('notion', data.config)
        toast.success('Notion configuration updated successfully!')
      } else {
        let errorMessage = 'Failed to update Notion configuration'
        try {
          const errorData = await response.json()
          logger.error('Notion config update error:', errorData)
          
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
          errorMessage = 'Failed to update Notion configuration'
        }
        
        toast.error(errorMessage)
      }
    } catch (error) {
      logger.error('Error updating Notion config:', error)
      let errorMessage = 'Failed to update Notion configuration'
      
      // Ensure we never pass objects to toast
      if (error && typeof error.message === 'string') {
        errorMessage = error.message
      }
      
      toast.error(errorMessage)
    }
  }

  const updateNotionIntegrationStatus = async (isEnabled) => {
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
        toast.success(`Notion integration ${isEnabled ? 'enabled' : 'disabled'} successfully!`)
      } else {
        const errorData = await response.json()
        toast.error(errorData.detail || 'Failed to update Notion integration status')
        // Revert the UI state on error - update config.web_scan_enabled
        updateIntegration('notion', { config: { web_scan_enabled: !isEnabled } })
      }
    } catch (error) {
      logger.error('Error updating Notion integration status:', error)
      toast.error('Failed to update Notion integration status')
      // Revert the UI state on error - update config.web_scan_enabled
      updateIntegration('notion', { config: { web_scan_enabled: !isEnabled } })
    }
  }

  return {
    notionConfig,
    setNotionConfig,
    updateNotionConfig,
    updateNotionIntegrationStatus
  }
}

export default useNotionIntegration
