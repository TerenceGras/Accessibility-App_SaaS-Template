import React from 'react'
import { BanknotesIcon, ClockIcon } from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'

const CreditBalanceCard = ({ subscription }) => {
  const { t } = useTranslation()
  
  if (!subscription) {
    return null
  }

  const webCredits = subscription.web_scan_credits || 0
  const pdfCredits = subscription.pdf_scan_credits || 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
        <BanknotesIcon className="h-6 w-6 mr-2" />
        {t('profile.credits.title')}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Web Scan Credits */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200">
              {t('profile.credits.webCredits')}
            </h3>
            <span className="text-xs text-blue-600 dark:text-blue-400">
              {t('profile.credits.perModule')}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-blue-700 dark:text-blue-300">{t('common.available')}:</span>
            <span className="text-2xl font-bold text-blue-900 dark:text-blue-100">{webCredits.toLocaleString()}</span>
          </div>
        </div>

        {/* PDF Scan Credits */}
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-purple-900 dark:text-purple-200">
              {t('profile.credits.pdfCredits')}
            </h3>
            <span className="text-xs text-purple-600 dark:text-purple-400">
              {t('profile.credits.perPage')}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-purple-700 dark:text-purple-300">{t('common.available')}:</span>
            <span className="text-2xl font-bold text-purple-900 dark:text-purple-100">{pdfCredits.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {subscription.credits_expire_at && (
        <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center">
            <ClockIcon className="h-4 w-4 mr-2" />
            {t('profile.credits.expireOn', { date: new Date(subscription.credits_expire_at).toLocaleDateString() })}
          </p>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
        {subscription.plan === 'free' ? (
          <span>{t('profile.credits.freeCreditsInfo')}</span>
        ) : (
          <span>* {t('profile.credits.creditsResetMonthly')}</span>
        )}
      </div>
    </div>
  )
}

export default CreditBalanceCard
