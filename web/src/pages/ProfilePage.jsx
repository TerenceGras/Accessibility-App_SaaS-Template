import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  UserCircleIcon,
  CreditCardIcon,
  ChartBarIcon,
  ClockIcon,
  BuildingOfficeIcon,
  DocumentTextIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'
import useAuthStore from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { useTranslation } from '../hooks/useTranslation'
import LoadingSpinner from '../components/LoadingSpinner'
import SubscriptionCreditSection from '../components/profile/SubscriptionCreditSection'
import UsageStatsCard from '../components/profile/UsageStatsCard'
import UsageSeparateCharts from '../components/profile/UsageSeparateCharts'
import BillingInfoForm from '../components/profile/BillingInfoForm'
import SubscriptionCancelModal from '../components/profile/SubscriptionCancelModal'
import AccountDeletionSection from '../components/profile/AccountDeletionSection'
import PageContainer, { PageCard } from '../components/PageContainer'
import toast from 'react-hot-toast'
import logger from '../utils/logger'

const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''

const ProfilePage = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, loading: authLoading, getIdToken, signOut } = useAuthStore()
  const { isDarkMode } = useThemeStore()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [subscription, setSubscription] = useState(null)
  const [usageStats, setUsageStats] = useState(null)
  const [invoices, setInvoices] = useState([])
  const [showCancelModal, setShowCancelModal] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/') // Redirect to home if not authenticated
    } else if (user) {
      fetchProfileData()
    }
  }, [user, authLoading, navigate])

  // Handle return from Stripe Checkout (success)
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const subscriptionStatus = searchParams.get('subscription')
    
    if (subscriptionStatus === 'success') {
      toast.success(t('profile.toasts.subscriptionSuccess') || 'Subscription successful! Welcome aboard!')
      // Refresh subscription data to get latest status
      if (user) {
        fetchProfileData()
        // Dispatch event to update sidebar credits
        window.dispatchEvent(new CustomEvent('subscription-updated'))
      }
      // Clean up URL
      navigate('/profile', { replace: true })
    }
  }, [location.search, user])

  const fetchProfileData = async () => {
    try {
      setLoading(true)
      const token = await getIdToken()

      // Fetch subscription
      const subResponse = await fetch(`${PRICING_API_URL}/subscription`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (subResponse.ok) {
        const subData = await subResponse.json()
        setSubscription(subData.subscription)
      }

      // Fetch usage stats
      const statsResponse = await fetch(`${PRICING_API_URL}/usage-stats`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setUsageStats(statsData.stats)
      }

      // Fetch invoices (purchases + subscriptions)
      const invoicesResponse = await fetch(`${PRICING_API_URL}/invoices`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (invoicesResponse.ok) {
        const invoicesData = await invoicesResponse.json()
        setInvoices(invoicesData.invoices || [])
      }
    } catch (error) {
      logger.error('Error fetching profile data:', error)
      toast.error(t('profile.toasts.loadFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleOpenCancelModal = () => {
    setShowCancelModal(true)
  }

  const handleCancelSubscription = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/cancel-subscription`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success(t('profile.toasts.subscriptionCancelled'))
        setShowCancelModal(false)
        fetchProfileData()
      } else {
        throw new Error('Failed to cancel subscription')
      }
    } catch (error) {
      logger.error('Error cancelling subscription:', error)
      toast.error(t('profile.toasts.cancelFailed'))
    }
  }

  const handleResumeSubscription = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/resume-subscription`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        toast.success(t('profile.toasts.subscriptionResumed'))
        fetchProfileData()
      } else {
        throw new Error('Failed to resume subscription')
      }
    } catch (error) {
      logger.error('Error resuming subscription:', error)
      toast.error(t('profile.toasts.resumeFailed'))
    }
  }

  const tabs = [
    { id: 'overview', name: t('profile.tabs.overview'), icon: UserCircleIcon },
    { id: 'usage', name: t('profile.tabs.usageHistory'), icon: ChartBarIcon },
    { id: 'invoices', name: t('profile.tabs.invoices'), icon: DocumentTextIcon },
  ]

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner className="h-12 w-12" />
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <PageContainer
      title={t('profile.title')}
      description={t('profile.description')}
    >
      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-6 sm:mb-8"
      >
        <div className="flex flex-wrap gap-1 xs:gap-0 xs:inline-flex bg-white dark:bg-gray-800 rounded-xl p-1 shadow-sm border border-gray-200 dark:border-gray-700">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 xs:gap-2 px-2.5 xs:px-3 sm:px-4 py-2 rounded-lg text-xs xs:text-sm font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span className="hidden xs:inline">{tab.name}</span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-6"
        >
          {/* Billing Information - Moved to top */}
          <PageCard>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <BuildingOfficeIcon className="h-6 w-6 mr-2 text-primary-500" />
              {t('profile.billingInfo.title')}
            </h2>
            <BillingInfoForm
              onUpdate={fetchProfileData}
              isDarkMode={isDarkMode}
              userId={user.uid}
              apiUrl={PRICING_API_URL}
            />
            
            {/* Email Display with Sign Out */}
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('common.email')}
                  </label>
                  <p className="text-gray-900 dark:text-white">{user.email}</p>
                </div>
                <button
                  onClick={async () => {
                    await signOut()
                    navigate('/')
                  }}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                    text-white bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700
                    transition-all duration-200 shadow-sm flex-shrink-0"
                  aria-label={t('common.signOut')}
                >
                  <ArrowRightOnRectangleIcon className="h-5 w-5" aria-hidden="true" />
                  <span>{t('common.signOut')}</span>
                </button>
              </div>
            </div>

            {/* Account Deletion - Subtle link at bottom */}
            <AccountDeletionSection 
              subscription={subscription}
              getIdToken={getIdToken}
              onAccountDeleted={async () => {
                await signOut()
                navigate('/')
              }}
            />
          </PageCard>

          {/* Subscription and Credit Balance - Combined */}
          <SubscriptionCreditSection
            subscription={subscription}
            onCancel={handleOpenCancelModal}
            onResume={handleResumeSubscription}
            onUpgrade={() => navigate('/pricing')}
            highlightCancel={location.state?.highlightCancel}
          />

          {/* Usage Stats */}
          {usageStats && <UsageStatsCard stats={usageStats} isDarkMode={isDarkMode} />}
        </motion.div>
      )}

      {activeTab === 'usage' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <UsageSeparateCharts 
            userId={user.uid}
            apiUrl={PRICING_API_URL}
            isDarkMode={isDarkMode}
          />
        </motion.div>
      )}

      {activeTab === 'invoices' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <PageCard>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <DocumentTextIcon className="h-6 w-6 mr-2 text-primary-500" />
                {t('profile.invoices.title')}
              </h2>
            </div>

            {invoices.length === 0 ? (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gray-100 dark:bg-gray-700 mb-4">
                  <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('profile.invoices.empty.title')}</h3>
                <p className="mt-2 text-gray-500 dark:text-gray-400">
                  {t('profile.invoices.empty.description')}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {invoices.map((invoice, index) => (
                  <motion.div
                    key={invoice.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className="border border-gray-200 dark:border-gray-700 rounded-xl p-3 xs:p-4 hover:border-primary-300 dark:hover:border-primary-600 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-all"
                  >
                    <div className="flex flex-col xs:flex-row xs:items-center xs:justify-between gap-2 xs:gap-0">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white text-sm xs:text-base">
                          {invoice.description}
                        </h3>
                        <p className="text-xs xs:text-sm text-gray-500 dark:text-gray-400">
                          {new Date(invoice.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </p>
                      </div>
                      <div className="xs:text-right flex xs:flex-col items-center xs:items-end gap-2 xs:gap-0">
                        <p className="font-semibold text-gray-900 dark:text-white text-sm xs:text-base">
                          €{invoice.amount.toFixed(2)}
                        </p>
                        <button
                          onClick={() => window.open(invoice.invoice_url, '_blank')}
                          className="text-xs xs:text-sm text-primary-600 dark:text-primary-400 hover:underline"
                        >
                          {t('profile.invoices.download')}
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </PageCard>
        </motion.div>
      )}

      {/* Subscription Cancel Modal */}
      <SubscriptionCancelModal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        onConfirm={handleCancelSubscription}
        subscription={subscription}
        isDarkMode={isDarkMode}
      />
    </PageContainer>
  )
}

export default ProfilePage
