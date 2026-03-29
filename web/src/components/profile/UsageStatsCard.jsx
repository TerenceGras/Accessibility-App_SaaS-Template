import React from 'react'
import { ChartBarIcon, GlobeAltIcon, DocumentTextIcon, KeyIcon, LinkIcon } from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'

const UsageStatsCard = ({ stats, isDarkMode }) => {
  const { t } = useTranslation()
  
  return (
    <div className={`${
      isDarkMode ? 'bg-gray-800' : 'bg-white'
    } rounded-lg shadow-lg p-6 border ${
      isDarkMode ? 'border-gray-700' : 'border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-semibold ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          {t('profile.usage.title')}
        </h3>
        <ChartBarIcon className="h-6 w-6 text-blue-500" />
      </div>

      <div className="space-y-4">
        {/* Total Scans */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${
              isDarkMode ? 'bg-blue-900/20' : 'bg-blue-50'
            }`}>
              <GlobeAltIcon className="h-5 w-5 text-blue-500" />
            </div>
            <div className="ml-3">
              <p className={`text-sm font-medium ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {t('profile.usage.totalWebScans')}
              </p>
            </div>
          </div>
          <p className={`text-2xl font-bold ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            {stats?.all_time?.web_scans || 0}
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${
              isDarkMode ? 'bg-purple-900/20' : 'bg-purple-50'
            }`}>
              <DocumentTextIcon className="h-5 w-5 text-purple-500" />
            </div>
            <div className="ml-3">
              <p className={`text-sm font-medium ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {t('profile.usage.totalPdfScans')}
              </p>
            </div>
          </div>
          <p className={`text-2xl font-bold ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            {stats?.all_time?.pdf_scans || 0}
          </p>
        </div>

        {/* API Keys Count */}
        <div className={`border-t ${
          isDarkMode ? 'border-gray-700' : 'border-gray-200'
        } pt-4 mt-4`}></div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${
              isDarkMode ? 'bg-green-900/20' : 'bg-green-50'
            }`}>
              <KeyIcon className="h-5 w-5 text-green-500" />
            </div>
            <div className="ml-3">
              <p className={`text-sm font-medium ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {t('profile.usage.activeApiKeys')}
              </p>
            </div>
          </div>
          <p className={`text-2xl font-bold ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            {stats?.api_keys_count || 0}
          </p>
        </div>

        {/* Integrations */}
        {stats?.integrations && (
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className={`p-2 rounded-lg ${
                  isDarkMode ? 'bg-amber-900/20' : 'bg-amber-50'
                }`}>
                  <LinkIcon className="h-5 w-5 text-amber-500" />
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    {t('profile.usage.activeIntegrations')}
                  </p>
                </div>
              </div>
              <p className={`text-2xl font-bold ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {(stats.integrations.github || 0) + (stats.integrations.slack || 0) + (stats.integrations.notion || 0)}
              </p>
            </div>

            {/* Integration Breakdown */}
            <div className={`pl-12 space-y-2 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              {stats.integrations.github > 0 && (
                <p className="text-sm">
                  • GitHub: {stats.integrations.github}
                </p>
              )}
              {stats.integrations.slack > 0 && (
                <p className="text-sm">
                  • Slack: {stats.integrations.slack}
                </p>
              )}
              {stats.integrations.notion > 0 && (
                <p className="text-sm">
                  • Notion: {stats.integrations.notion}
                </p>
              )}
              {(stats.integrations.github === 0 && stats.integrations.slack === 0 && stats.integrations.notion === 0) && (
                <p className="text-sm italic">
                  {t('profile.usage.noIntegrations')}
                </p>
              )}
            </div>
          </>
        )}

        {/* Current Period Usage */}
        {stats?.current_month && (
          <>
            <div className={`border-t ${
              isDarkMode ? 'border-gray-700' : 'border-gray-200'
            } pt-4 mt-4`}>
              <p className={`text-xs font-medium mb-3 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              } uppercase tracking-wider`}>
                {t('profile.usage.thisMonth')}
              </p>
            </div>

            <div className="flex items-center justify-between">
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {t('profile.usage.webScansUsed')}
              </p>
              <p className={`text-lg font-semibold ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {stats.current_month.web_scans || 0}
              </p>
            </div>

            <div className="flex items-center justify-between">
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {t('profile.usage.pdfScansUsed')}
              </p>
              <p className={`text-lg font-semibold ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {stats.current_month.pdf_scans || 0}
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default UsageStatsCard
