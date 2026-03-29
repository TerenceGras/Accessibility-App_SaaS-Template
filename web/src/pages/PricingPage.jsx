import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckIcon, XMarkIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { loadStripe } from '@stripe/stripe-js'
import { Elements } from '@stripe/react-stripe-js'
import useAuthStore from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import toast from 'react-hot-toast'
import StripeCheckoutModal from '../components/pricing/StripeCheckoutModal'
import BillingInfoModal from '../components/pricing/BillingInfoModal'
import LoadingSpinner from '../components/LoadingSpinner'
import PageContainer, { PageCard } from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''
const STRIPE_PUBLISHABLE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

const stripePromise = loadStripe(STRIPE_PUBLISHABLE_KEY)

const PricingPage = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, getIdToken } = useAuthStore()
  const { isDarkMode } = useThemeStore()
  const [loading, setLoading] = useState(true)
  const [currentPlan, setCurrentPlan] = useState('free')
  const [billingInterval, setBillingInterval] = useState('monthly') // 'monthly' or 'yearly'
  const [showCheckoutModal, setShowCheckoutModal] = useState(false)
  const [showBillingModal, setShowBillingModal] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [clientSecret, setClientSecret] = useState(null)
  const [pendingAction, setPendingAction] = useState(null)

  const pricingTiers = [
    {
      id: 'free',
      name: t('pricing.plans.free.name'),
      monthlyPrice: 0,
      yearlyPrice: 0,
      description: t('pricing.plans.free.description'),
      features: [
        t('pricing.plans.free.features.webScans'),
        t('pricing.plans.free.features.pdfScans'),
        t('pricing.plans.free.features.storage'),
        t('pricing.plans.free.features.reports'),
        t('pricing.plans.free.features.integrations'),
        t('pricing.plans.free.features.api'),
      ],
      cta: t('pricing.currentPlan'),
      highlighted: false,
    },
    {
      id: 'standard',
      name: t('pricing.plans.standard.name'),
      monthlyPrice: 49,
      yearlyPrice: 539, // 49 * 11 = one month free
      description: t('pricing.plans.standard.description'),
      features: [
        t('pricing.plans.standard.features.webScans'),
        t('pricing.plans.standard.features.pdfScans'),
        t('pricing.plans.standard.features.storage'),
        t('pricing.plans.standard.features.reports'),
        t('pricing.plans.standard.features.integrations'),
        t('pricing.plans.standard.features.api'),
      ],
      cta: t('pricing.subscribe'),
      highlighted: false,
    },
    {
      id: 'business',
      name: t('pricing.plans.business.name'),
      monthlyPrice: 109,
      yearlyPrice: 1199, // 109 * 11 = one month free
      description: t('pricing.plans.business.description'),
      features: [
        t('pricing.plans.business.features.webScans'),
        t('pricing.plans.business.features.pdfScans'),
        t('pricing.plans.business.features.storage'),
        t('pricing.plans.business.features.reports'),
        t('pricing.plans.business.features.integrations'),
        t('pricing.plans.business.features.api'),
      ],
      cta: t('pricing.subscribe'),
      highlighted: false,
    },
    {
      id: 'enterprise',
      name: t('pricing.plans.enterprise.name'),
      monthlyPrice: null,
      yearlyPrice: null,
      description: t('pricing.plans.enterprise.description'),
      features: [
        t('pricing.plans.enterprise.features.webScans'),
        t('pricing.plans.enterprise.features.pdfScans'),
        t('pricing.plans.enterprise.features.storage'),
        t('pricing.plans.enterprise.features.integrations'),
        t('pricing.plans.enterprise.features.reports'),
        t('pricing.plans.enterprise.features.api'),
      ],
      cta: t('pricing.contactUs'),
      highlighted: false,
    },
  ]

  useEffect(() => {
    if (user) {
      fetchCurrentPlan()
    } else {
      setLoading(false)
    }
  }, [user])

  // Handle return from Stripe Checkout (cancelled)
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const subscriptionStatus = searchParams.get('subscription')
    
    if (subscriptionStatus === 'cancelled') {
      toast(t('pricing.subscriptionCancelled') || 'Subscription process was cancelled', { icon: 'ℹ️' })
      // Clean up URL
      navigate('/pricing', { replace: true })
    }
  }, [location.search])

  const fetchCurrentPlan = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/subscription`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        const subscription = data.subscription
        // CRITICAL: Only treat as a paid plan if status is 'active'
        // Incomplete/incomplete_expired/past_due subscriptions should show as 'free'
        const status = subscription?.status || 'active'
        const plan = subscription?.plan || 'free'
        
        if (status === 'active' && plan !== 'free') {
          setCurrentPlan(plan)
        } else {
          setCurrentPlan('free')
        }
      }
    } catch (error) {
      logger.error('Error fetching current plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkBillingInfo = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/billing-info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        const billingInfo = data.billing_info
        
        // Check if billing info is complete
        if (billingInfo && billingInfo.company_name && billingInfo.address?.line1 && 
            billingInfo.address?.city && billingInfo.address?.postal_code && 
            billingInfo.address?.country) {
          return true
        }
      }
      return false
    } catch (error) {
      logger.error('Error checking billing info:', error)
      return false
    }
  }

  const handleSubscribe = async (planId) => {
    if (!user) {
      toast.error(t('pricing.errors.signInRequired'))
      return
    }

    if (planId === 'enterprise') {
      navigate('/contact')
      return
    }

    if (planId === currentPlan) {
      toast(t('pricing.errors.alreadyOnPlan'), { icon: 'ℹ️' })
      return
    }

    // Handle downgrade to free plan
    if (planId === 'free' && currentPlan !== 'free') {
      navigate('/profile', { state: { highlightCancel: true } })
      return
    }

    // Check if billing info is complete
    const hasBillingInfo = await checkBillingInfo()
    if (!hasBillingInfo) {
      setPendingAction({ type: 'subscribe', planId, interval: billingInterval })
      setShowBillingModal(true)
      return
    }

    await proceedWithSubscription(planId, billingInterval)
  }

  const proceedWithSubscription = async (planId, interval = 'monthly') => {
    try {
      setLoading(true)
      const token = await getIdToken()
      
      const response = await fetch(`${PRICING_API_URL}/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          plan: planId,
          interval: interval,
          email: user.email,
          name: user.displayName,
        }),
      })

      const data = await response.json()

      if (response.ok && data.success) {
        // New Checkout Session flow - redirect to Stripe hosted checkout
        if (data.checkout_url) {
          window.location.href = data.checkout_url
          return
        }
        
        // Fallback for old flow with client_secret (if still supported)
        if (data.subscription?.client_secret) {
          setSelectedPlan(planId)
          setClientSecret(data.subscription.client_secret)
          setShowCheckoutModal(true)
          return
        }
        
        throw new Error('No checkout URL or client secret returned')
      } else {
        logger.error('Subscription creation failed:', data.message)
        throw new Error('subscription_failed')
      }
    } catch (error) {
      logger.error('Error creating subscription:', error)
      toast.error(t('pricing.errors.subscriptionFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handlePaymentSuccess = async () => {
    setShowCheckoutModal(false)
    setClientSecret(null)
    setSelectedPlan(null)
    
    // Sync subscription status from Stripe to Firestore
    // This ensures the status is 'active' before we check it elsewhere
    try {
      const token = await getIdToken()
      await fetch(`${PRICING_API_URL}/subscription/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
    } catch (error) {
      logger.error('Error syncing subscription status:', error)
      // Continue anyway - webhook should eventually sync the status
    }
    
    toast.success(t('pricing.paymentSuccess'))
    fetchCurrentPlan()
    // Dispatch custom event to notify Sidebar to refresh credits
    window.dispatchEvent(new CustomEvent('subscription-updated'))
  }

  const handlePaymentCancel = async () => {
    setShowCheckoutModal(false)
    setClientSecret(null)
    setSelectedPlan(null)
    
    // Cleanup the incomplete subscription in the backend
    // This ensures no 'incomplete' subscription data remains that could cause UI issues
    try {
      const token = await getIdToken()
      await fetch(`${PRICING_API_URL}/subscription/cleanup-incomplete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      // Refresh the current plan to reflect the cleanup
      fetchCurrentPlan()
    } catch (error) {
      logger.error('Error cleaning up incomplete subscription:', error)
      // Don't show error to user - this is a background cleanup
    }
  }

  // Helper function to get button text based on current plan
  const getButtonText = (tierId) => {
    if (tierId === 'enterprise') {
      return t('pricing.contactUs')
    }
    if (tierId === currentPlan) {
      return t('pricing.currentPlan')
    }
    
    const tierOrder = ['free', 'standard', 'business', 'enterprise']
    const currentIndex = tierOrder.indexOf(currentPlan)
    const tierIndex = tierOrder.indexOf(tierId)
    
    if (tierIndex > currentIndex) {
      return t('pricing.upgrade')
    } else if (tierIndex < currentIndex) {
      return t('pricing.downgrade')
    }
    return t('pricing.subscribe')
  }

  if (loading && user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner className="h-12 w-12" />
      </div>
    )
  }

  return (
    <PageContainer
      title={t('pricing.title')}
      description={t('pricing.description')}
      centered
    >
      {/* Billing Interval Toggle */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex justify-center mb-8"
      >
        <div className="inline-flex items-center bg-white dark:bg-gray-800 rounded-xl p-1 shadow-sm border border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setBillingInterval('monthly')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              billingInterval === 'monthly'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {t('pricing.monthly')}
          </button>
          <button
            onClick={() => setBillingInterval('yearly')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
              billingInterval === 'yearly'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {t('pricing.yearly')}
            <span className={`text-xs px-1.5 py-0.5 rounded-full ${
              billingInterval === 'yearly'
                ? 'bg-white/20 text-white'
                : 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400'
            }`}>
              {t('pricing.oneMonthFree')}
            </span>
          </button>
        </div>
      </motion.div>

      {/* Pricing Tiers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-12 px-2 sm:px-0">
        {pricingTiers.map((tier, index) => {
          const displayPrice = tier.monthlyPrice === null 
            ? t('pricing.custom')
            : billingInterval === 'yearly' 
              ? `€${tier.yearlyPrice}` 
              : `€${tier.monthlyPrice}`
          const periodText = tier.monthlyPrice === null 
            ? '' 
            : billingInterval === 'yearly' 
              ? t('pricing.perYear')
              : t('pricing.perMonth')
          const monthlyEquivalent = tier.monthlyPrice !== null && billingInterval === 'yearly' && tier.yearlyPrice > 0
            ? Math.round(tier.yearlyPrice / 12)
            : null

          return (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
              className={`relative rounded-xl sm:rounded-2xl flex flex-col overflow-hidden ${
                tier.id === currentPlan
                  ? 'ring-2 ring-green-500 shadow-xl'
                  : 'border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600'
              } bg-white dark:bg-gray-800 transition-all duration-300 hover:shadow-lg`}
            >
              {tier.id === currentPlan && (
                <div className="absolute -top-px left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600"></div>
              )}
              
              <div className="p-4 sm:p-6 flex flex-col h-full">
                {tier.id === currentPlan && (
                  <div className="mb-3 sm:mb-4">
                    <span className="inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      <CheckIcon className="h-3.5 w-3.5 mr-1" />
                      {t('pricing.activePlan')}
                    </span>
                  </div>
                )}

                <div className="mb-4 sm:mb-6">
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white mb-1 sm:mb-2">
                    {tier.name}
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm">
                    {tier.description}
                  </p>
                </div>

                <div className="mb-4 sm:mb-6">
                  <div className="flex items-baseline">
                    <span className="text-2xl sm:text-4xl font-bold text-gray-900 dark:text-white">
                      {displayPrice}
                    </span>
                    {periodText && (
                      <span className="ml-1 sm:ml-2 text-gray-500 dark:text-gray-400 text-xs sm:text-sm">
                        {periodText}
                      </span>
                    )}
                  </div>
                  {monthlyEquivalent && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      ~€{monthlyEquivalent}/month
                    </p>
                  )}
                </div>

                <ul className="space-y-2 sm:space-y-3 mb-6 sm:mb-8 flex-grow">
                {tier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start text-xs sm:text-sm">
                    <CheckIcon className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 mr-1.5 sm:mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-600 dark:text-gray-300 text-sm">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSubscribe(tier.id)}
                disabled={tier.id === currentPlan && tier.id !== 'free'}
                className={`w-full py-3 px-6 rounded-xl font-medium transition-all duration-200 mt-auto ${
                  tier.id === currentPlan
                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    : 'bg-primary-500 text-white hover:bg-primary-600 shadow-sm hover:shadow-md active:scale-[0.98]'
                }`}
              >
                {getButtonText(tier.id)}
              </button>
            </div>
          </motion.div>
          )
        })}
      </div>

      {/* FAQ or Additional Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.5 }}
      >
        <PageCard className="bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 max-w-4xl mx-auto">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <SparklesIcon className="h-5 w-5 text-primary-500" />
            {t('pricing.importantInfo.title')}
          </h3>
          <ul className="space-y-3 text-gray-600 dark:text-gray-300">
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.creditsReset')}</span>
            </li>
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.creditsExpire')}</span>
            </li>
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.freeCredits')}</span>
            </li>
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.webScanCost')}</span>
            </li>
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.pdfScanCost')}</span>
            </li>
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.changePlan')}</span>
            </li>
            <li className="flex items-start">
              <span className="mr-3 text-primary-500 font-medium">•</span>
              <span>{t('pricing.importantInfo.needMore')}</span>
            </li>
          </ul>
        </PageCard>
      </motion.div>

      {/* Billing Info Modal */}
      {showBillingModal && (
        <BillingInfoModal
          isOpen={showBillingModal}
          onClose={() => setShowBillingModal(false)}
          onComplete={async () => {
            setShowBillingModal(false)
            // Proceed with the pending action
            if (pendingAction) {
              if (pendingAction.type === 'subscribe') {
                await proceedWithSubscription(pendingAction.planId, pendingAction.interval)
              }
              setPendingAction(null)
            }
          }}
          isDarkMode={isDarkMode}
        />
      )}

      {/* Stripe Checkout Modal */}
      {showCheckoutModal && clientSecret && (
        <Elements stripe={stripePromise} options={{ clientSecret }}>
          <StripeCheckoutModal
            isOpen={showCheckoutModal}
            onClose={handlePaymentCancel}
            onSuccess={handlePaymentSuccess}
            planName={selectedPlan ? pricingTiers.find(t => t.id === selectedPlan)?.name : null}
          />
        </Elements>
      )}
    </PageContainer>
  )
}

export default PricingPage
