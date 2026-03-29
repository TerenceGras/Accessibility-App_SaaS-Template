import React, { useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { CreditCardIcon, BanknotesIcon, ClockIcon } from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'

const SubscriptionCreditSection = ({ subscription, onCancel, onResume, onUpgrade, highlightCancel }) => {
  const { t } = useTranslation()
  const cancelButtonRef = useRef(null)
  const location = useLocation()

  useEffect(() => {
    if (location.state?.highlightCancel && cancelButtonRef.current) {
      cancelButtonRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
      cancelButtonRef.current.classList.add('animate-pulse')
      setTimeout(() => {
        cancelButtonRef.current?.classList.remove('animate-pulse')
      }, 3000)
    }
  }, [location.state])

  if (!subscription) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
        </div>
      </div>
    )
  }

  // CRITICAL: Treat incomplete/incomplete_expired subscriptions as free
  // This prevents UI issues where users appear to be on a paid plan after failed payment
  const isActiveSubscription = subscription.status === 'active' && subscription.plan !== 'free'
  const effectivePlan = isActiveSubscription ? subscription.plan : 'free'

  const planNames = {
    free: 'Free',
    standard: 'Standard',
    business: 'Business',
    enterprise: 'Enterprise',
  }

  const planName = planNames[effectivePlan] || effectivePlan

  const webCredits = subscription.web_scan_credits || 0
  const pdfCredits = subscription.pdf_scan_credits || 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Credit Balance - Left Column */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
            <BanknotesIcon className="h-6 w-6 mr-2" />
            {t('profile.credits.title')}
          </h2>

          <div className="space-y-4">
            {/* Web Scan Credits */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200">
                  {t('profile.credits.webCredits')}
                </h3>
                <span className="text-xs text-blue-600 dark:text-blue-400">
                  {t('webScan.creditsPerModule')}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-700 dark:text-blue-300">{t('common.available')}:</span>
                <span className="text-xl font-bold text-blue-900 dark:text-blue-100">{webCredits.toLocaleString()}</span>
              </div>
            </div>

            {/* PDF Scan Credits */}
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-purple-900 dark:text-purple-200">
                  {t('profile.credits.pdfCredits')}
                </h3>
                <span className="text-xs text-purple-600 dark:text-purple-400">
                  {t('pdfScan.creditsPerPage')}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700 dark:text-purple-300">{t('common.available')}:</span>
                <span className="text-xl font-bold text-purple-900 dark:text-purple-100">{pdfCredits.toLocaleString()}</span>
              </div>
            </div>

            {subscription.credits_expire_at && (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center">
                  <ClockIcon className="h-4 w-4 mr-2" />
                  {t('profile.credits.renewOn')}: {new Date(subscription.credits_expire_at).toLocaleDateString()}
                </p>
              </div>
            )}

            <div className="text-xs text-gray-500 dark:text-gray-400">
              {effectivePlan === 'free' ? (
                <p>{t('profile.credits.freeCreditsInfo')}</p>
              ) : (
                <p>• {t('profile.credits.creditsResetMonthly')}</p>
              )}
            </div>
          </div>
        </div>

        {/* Subscription Management - Right Column */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
            <CreditCardIcon className="h-6 w-6 mr-2" />
            {t('profile.subscription.title')}
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('profile.subscription.currentPlan')}
              </label>
              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                {planName}
              </span>
            </div>

            {isActiveSubscription && subscription.current_period_end && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {subscription.cancel_at_period_end ? t('profile.subscription.accessUntil') : t('profile.subscription.renewsOn')}
                </label>
                <p className="text-gray-900 dark:text-white font-medium">
                  {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              </div>
            )}

            {subscription.cancel_at_period_end && (
              <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center">
                  <ClockIcon className="h-5 w-5 mr-2" />
                  {t('profile.subscription.endsOn')} {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              </div>
            )}

            <div className="space-y-3 pt-4">
              {effectivePlan === 'free' ? (
                <button
                  onClick={onUpgrade}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  {t('profile.subscription.upgrade')}
                </button>
              ) : (
                <>
                  {subscription.cancel_at_period_end ? (
                    <button
                      onClick={onResume}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                      {t('profile.subscription.resume')}
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={onUpgrade}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                      >
                        {t('profile.subscription.changePlan')}
                      </button>
                      <button
                        ref={cancelButtonRef}
                        onClick={onCancel}
                        className="w-full px-4 py-2 bg-red-600 text-white border border-red-700 rounded-lg hover:bg-red-700 dark:hover:bg-red-700 transition-colors font-medium"
                      >
                        {t('profile.subscription.cancel')}
                      </button>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SubscriptionCreditSection
