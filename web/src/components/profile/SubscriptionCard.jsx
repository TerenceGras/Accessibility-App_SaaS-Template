import React from 'react'
import { CreditCardIcon, CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'

const SubscriptionCard = ({ subscription, onCancel, onResume, onUpgrade }) => {
  const { t } = useTranslation()
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

  const planNames = {
    free: t('pricing.plans.free.name'),
    standard: t('pricing.plans.standard.name'),
    business: t('pricing.plans.business.name'),
    enterprise: t('pricing.plans.enterprise.name'),
  }

  const statusColors = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    canceled: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    past_due: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    trialing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  }

  const planName = planNames[subscription.plan] || subscription.plan
  const statusClass = statusColors[subscription.status] || statusColors.active

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
        <CreditCardIcon className="h-6 w-6 mr-2" />
        {t('profile.subscription.title')}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('profile.subscription.currentPlan')}
          </label>
          <div className="flex items-center">
            <span className="text-2xl font-bold text-gray-900 dark:text-white mr-3">
              {planName}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusClass}`}>
              {subscription.status}
            </span>
          </div>
        </div>

        {subscription.plan !== 'free' && subscription.current_period_end && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {subscription.cancel_at_period_end ? t('profile.subscription.accessUntil') : t('profile.subscription.renewsOn')}
            </label>
            <p className="text-gray-900 dark:text-white font-medium">
              {new Date(subscription.current_period_end).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>

      {subscription.cancel_at_period_end && (
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center">
            <ClockIcon className="h-5 w-5 mr-2" />
            {t('profile.subscription.subscriptionEndsOn', { date: new Date(subscription.current_period_end).toLocaleDateString() })}
          </p>
        </div>
      )}

      <div className="mt-6 flex space-x-3">
        {subscription.plan === 'free' ? (
          <button
            onClick={onUpgrade}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            {t('profile.subscription.upgradePlan')}
          </button>
        ) : (
          <>
            {subscription.cancel_at_period_end ? (
              <button
                onClick={onResume}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                {t('profile.subscription.resumeSubscription')}
              </button>
            ) : (
              <>
                <button
                  onClick={onUpgrade}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  {t('profile.subscription.changePlan')}
                </button>
                <button
                  onClick={onCancel}
                  className="flex-1 px-4 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  {t('profile.subscription.cancelSubscription')}
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default SubscriptionCard
