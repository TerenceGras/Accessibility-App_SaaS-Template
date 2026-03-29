import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import useAuthStore from './authStore'

const useIntegrationStore = create(
  persist(
    (set, get) => ({
      // Integration states
      integrations: {
        github: {
          config: {
            repository: null,
            label: 'accessibility',
            connected: false,
            web_scan_enabled: false,
            pdf_scan_enabled: false,
            last_updated: null
          },
          web_scan_sections: {
            wcag_enabled: true,
            wcag_severity_filter: ['High', 'Medium', 'Low'],
            wcag_grouping_option: 'per-error-type',
            wcag_regroup_violations: false,
            html_enabled: true,
            links_enabled: true,
            axtree_enabled: false,
            layout_enabled: true
          },
          pdf_scan_sections: {
            pdf_grouping_option: 'per-page'
          },
          stats: {
            issues_created: 0,
            last_issue_created: null
          }
        },
        notion: {
          config: {
            parent_page_id: null,
            page_url: null,
            connected: false,
            web_scan_enabled: false,
            pdf_scan_enabled: false,
            last_updated: null
          },
          web_scan_sections: {
            wcag_enabled: true,
            wcag_severity_filter: ['High', 'Medium', 'Low'],
            wcag_grouping_option: 'per-error-type',
            wcag_regroup_violations: true,
            html_enabled: true,
            links_enabled: true,
            axtree_enabled: false,
            layout_enabled: true
          },
          pdf_scan_sections: {
            pdf_grouping_option: 'per-page'
          },
          stats: {
            pages_created: 0,
            last_page_created: null
          }
        },
        slack: {
          config: {
            channel: null,
            connected: false,
            web_scan_enabled: false,
            pdf_scan_enabled: false,
            last_updated: null
          },
          web_scan_sections: {
            wcag_enabled: true,
            wcag_severity_filter: ['High', 'Medium', 'Low'],
            wcag_grouping_option: 'per-error-type',
            wcag_regroup_violations: false,
            html_enabled: true,
            links_enabled: true,
            axtree_enabled: false,
            layout_enabled: true
          },
          pdf_scan_sections: {
            pdf_grouping_option: 'per-page'
          },
          stats: {
            messages_posted: 0,
            last_message_posted: null
          }
        }
      },

      // Loading states
      loading: {
        github: false,
        notion: false,
        slack: false,
        general: false,
      },

      // Error states
      errors: {
        github: null,
        notion: null,
        slack: null,
        general: null,
      },

      // Actions
      setLoading: (platform, isLoading) => 
        set((state) => ({
          loading: { ...state.loading, [platform]: isLoading }
        })),

      setError: (platform, error) =>
        set((state) => ({
          errors: { ...state.errors, [platform]: error }
        })),

      clearError: (platform) =>
        set((state) => ({
          errors: { ...state.errors, [platform]: null }
        })),

      updateIntegration: (platform, updates) =>
        set((state) => {
          const currentPlatform = state.integrations[platform] || {}
          const currentConfig = currentPlatform.config || {}
          const currentWebScanSections = currentPlatform.web_scan_sections || {}
          const currentPdfScanSections = currentPlatform.pdf_scan_sections || {}
          const currentStats = currentPlatform.stats || {}
          
          // Deep merge for nested objects to prevent losing existing values
          const newConfig = updates.config 
            ? { ...currentConfig, ...updates.config }
            : currentConfig
          
          const newWebScanSections = updates.web_scan_sections
            ? { ...currentWebScanSections, ...updates.web_scan_sections }
            : currentWebScanSections
          
          const newPdfScanSections = updates.pdf_scan_sections
            ? { ...currentPdfScanSections, ...updates.pdf_scan_sections }
            : currentPdfScanSections
          
          const newStats = updates.stats
            ? { ...currentStats, ...updates.stats }
            : currentStats
          
          return {
            integrations: {
              ...state.integrations,
              [platform]: {
                ...currentPlatform,
                config: newConfig,
                web_scan_sections: newWebScanSections,
                pdf_scan_sections: newPdfScanSections,
                stats: newStats,
              }
            }
          }
        }),

      updateConfig: (platform, config) =>
        set((state) => ({
          integrations: {
            ...state.integrations,
            [platform]: {
              ...state.integrations[platform],
              config: {
                ...state.integrations[platform].config,
                ...config,
              }
            }
          }
        })),

      connectIntegration: (platform, configUpdate = {}) =>
        set((state) => ({
          integrations: {
            ...state.integrations,
            [platform]: {
              ...state.integrations[platform],
              config: {
                ...state.integrations[platform].config,
                ...configUpdate,
                connected: true,
                web_scan_enabled: true,
                last_updated: new Date().toISOString(),
              }
            }
          }
        })),

      disconnectIntegration: (platform) =>
        set((state) => ({
          integrations: {
            ...state.integrations,
            [platform]: {
              ...state.integrations[platform],
              config: {
                ...state.integrations[platform].config,
                connected: false,
                web_scan_enabled: false,
                pdf_scan_enabled: false,
                // Clear sensitive data but keep other preferences
                ...(platform === 'github' && { repository: null }),
                ...(platform === 'notion' && { page_url: null, parent_page_id: null }),
              }
            }
          }
        })),

      updateStats: (platform, stats) =>
        set((state) => ({
          integrations: {
            ...state.integrations,
            [platform]: {
              ...state.integrations[platform],
              stats: {
                ...state.integrations[platform].stats,
                ...stats,
              }
            }
          }
        })),

      // Load integrations from server
      loadIntegrations: async (user) => {
        if (!user) return

        set({ loading: { ...get().loading, general: true } })
        
        try {
          const token = await useAuthStore.getState().getIdToken()
          const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const data = await response.json()
            if (data.integrations) {
              set({ integrations: data.integrations })
            }
          } else {
            throw new Error('Failed to load integrations')
          }
        } catch (error) {
          set((state) => ({
            errors: { ...state.errors, general: error.message }
          }))
        } finally {
          set((state) => ({
            loading: { ...state.loading, general: false }
          }))
        }
      },

      // Save integration configuration
      saveIntegrationConfig: async (user, platform, config) => {
        if (!user) return false

        set((state) => ({
          loading: { ...state.loading, [platform]: true }
        }))
        
        try {
          const token = await useAuthStore.getState().getIdToken()
          const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/${platform}/config`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ config })
          })
          
          if (response.ok) {
            set((state) => ({
              integrations: {
                ...state.integrations,
                [platform]: {
                  ...state.integrations[platform],
                  config: {
                    ...state.integrations[platform].config,
                    ...config,
                  }
                }
              }
            }))
            return true
          } else {
            throw new Error('Failed to save configuration')
          }
        } catch (error) {
          set((state) => ({
            errors: { ...state.errors, [platform]: error.message }
          }))
          return false
        } finally {
          set((state) => ({
            loading: { ...state.loading, [platform]: false }
          }))
        }
      },

      // Disconnect integration
      disconnectIntegrationAsync: async (user, platform) => {
        if (!user) return false

        set((state) => ({
          loading: { ...state.loading, [platform]: true }
        }))
        
        try {
          const token = await useAuthStore.getState().getIdToken()
          const response = await fetch(`${import.meta.env.VITE_API_URL}/integrations/${platform}/disconnect`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            get().disconnectIntegration(platform)
            return true
          } else {
            throw new Error('Failed to disconnect integration')
          }
        } catch (error) {
          set((state) => ({
            errors: { ...state.errors, [platform]: error.message }
          }))
          return false
        } finally {
          set((state) => ({
            loading: { ...state.loading, [platform]: false }
          }))
        }
      },

      // Reset all integrations (useful for logout)
      resetIntegrations: () => {
        set({
          integrations: get().integrations,
          loading: {
            github: false,
            notion: false,
            slack: false,
            general: false,
          },
          errors: {
            github: null,
            notion: null,
            slack: null,
            general: null,
          }
        })
      },

      // Get integration statistics
      getIntegrationStats: () => {
        const integrations = get().integrations
        return {
          totalConnected: Object.values(integrations).filter(i => i.connected).length,
          totalEnabled: Object.values(integrations).filter(i => i.enabled).length,
          totalIssuesCreated: integrations.github.stats.issuesCreated,
          totalPagesCreated: integrations.notion.stats.pagesCreated,
          totalMessagesPosted: integrations.slack.stats.messagesPosted,
        }
      },
    }),
    {
      name: 'lumtrails-integrations',
      partialize: (state) => ({
        integrations: state.integrations,
      }),
    }
  )
)

export default useIntegrationStore