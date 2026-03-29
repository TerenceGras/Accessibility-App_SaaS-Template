import React, { Fragment, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Dialog, Transition } from '@headlessui/react'
import { 
  TrashIcon, 
  ExclamationTriangleIcon,
  XMarkIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''

const AccountDeletionModal = ({ isOpen, onClose, onConfirm, deletionInfo, isLoading, t }) => {
  const [confirmText, setConfirmText] = useState('')
  
  const confirmPhrase = t('profile.deleteAccount.confirmPhrase')
  const canConfirm = confirmText.toLowerCase() === confirmPhrase.toLowerCase()

  const handleClose = () => {
    if (!isLoading) {
      setConfirmText('')
      onClose()
    }
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 shadow-xl transition-all text-left">
                {/* Header */}
                <div className="bg-red-50 dark:bg-red-900/20 px-6 py-4 border-b border-red-100 dark:border-red-900/50">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center">
                      <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <Dialog.Title as="h3" className="text-lg font-semibold text-red-900 dark:text-red-100">
                        {t('profile.deleteAccount.title')}
                      </Dialog.Title>
                      <p className="text-sm text-red-700 dark:text-red-300">
                        {t('profile.deleteAccount.cannotUndo')}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="px-6 py-5 space-y-4">
                  {deletionInfo?.subscription_ends ? (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                      <div className="flex gap-3">
                        <ClockIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                            {t('profile.deleteAccount.subscriptionActive')}
                          </p>
                          <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                            {t('profile.deleteAccount.scheduledDeletion', { 
                              date: new Date(deletionInfo.subscription_ends).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                              })
                            })}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">
                      {t('profile.deleteAccount.immediateWarning')}
                    </p>
                  )}

                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('profile.deleteAccount.dataToDelete')}
                    </p>
                    <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
                      <li>{t('profile.deleteAccount.dataList.profile')}</li>
                      <li>{t('profile.deleteAccount.dataList.webScans')}</li>
                      <li>{t('profile.deleteAccount.dataList.pdfScans')}</li>
                      <li>{t('profile.deleteAccount.dataList.apiKeys')}</li>
                      <li>{t('profile.deleteAccount.dataList.usage')}</li>
                    </ul>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('profile.deleteAccount.typeToConfirmPrefix')}{' '}
                      <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{confirmPhrase}</span>{' '}
                      {t('profile.deleteAccount.typeToConfirmSuffix')}
                    </label>
                    <input
                      type="text"
                      value={confirmText}
                      onChange={(e) => setConfirmText(e.target.value)}
                      placeholder={confirmPhrase}
                      disabled={isLoading}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-red-500 focus:border-transparent disabled:opacity-50"
                    />
                  </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 flex gap-3 justify-end">
                  <button
                    onClick={handleClose}
                    disabled={isLoading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    onClick={onConfirm}
                    disabled={!canConfirm || isLoading}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        {t('common.processing')}
                      </>
                    ) : (
                      <>
                        <TrashIcon className="h-4 w-4" />
                        {deletionInfo?.subscription_ends ? t('profile.deleteAccount.scheduleDeletion') : t('profile.deleteAccount.deleteAccount')}
                      </>
                    )}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

const AccountDeletionSection = ({ subscription, getIdToken, onAccountDeleted }) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [showModal, setShowModal] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [deletionInfo, setDeletionInfo] = useState(null)
  const [loadingStatus, setLoadingStatus] = useState(true)

  // Fetch deletion status on mount
  useEffect(() => {
    fetchDeletionStatus()
  }, [])

  const fetchDeletionStatus = async () => {
    try {
      setLoadingStatus(true)
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/account/deletion-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setDeletionInfo(data)
      }
    } catch (error) {
      logger.error('Error fetching deletion status:', error)
    } finally {
      setLoadingStatus(false)
    }
  }

  const handleRequestDeletion = async () => {
    try {
      setIsLoading(true)
      const token = await getIdToken()
      
      const response = await fetch(`${PRICING_API_URL}/account/request-deletion`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process deletion request')
      }

      if (data.immediate) {
        // Account was deleted immediately
        toast.success(t('profile.deleteAccount.accountDeleted'))
        if (onAccountDeleted) {
          onAccountDeleted()
        } else {
          // Sign out and redirect
          navigate('/')
          window.location.reload()
        }
      } else {
        // Deletion was scheduled
        toast.success(t('profile.deleteAccount.deletionScheduledFor', { date: new Date(data.deletion_date).toLocaleDateString() }))
        setShowModal(false)
        fetchDeletionStatus()
      }
    } catch (error) {
      logger.error('Error requesting deletion:', error)
      toast.error(t('profile.deleteAccount.deletionFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancelDeletion = async () => {
    try {
      setIsLoading(true)
      const token = await getIdToken()
      
      const response = await fetch(`${PRICING_API_URL}/account/cancel-deletion`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) {
        const data = await response.json()
        logger.error('Cancel deletion failed:', data.detail)
        throw new Error('cancel_deletion_failed')
      }

      toast.success(t('profile.deleteAccount.deletionCancelled'))
      fetchDeletionStatus()
    } catch (error) {
      logger.error('Error cancelling deletion:', error)
      toast.error(t('profile.deleteAccount.cancelFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  const openDeletionModal = () => {
    // Check if user needs to cancel subscription first
    if (subscription && subscription.plan !== 'free' && !subscription.cancel_at_period_end) {
      toast.error(t('profile.deleteAccount.cancelSubscriptionFirst'))
      return
    }
    setShowModal(true)
  }

  if (loadingStatus) {
    return null // Don't show anything while loading - it's subtle anyway
  }

  return (
    <>
      {deletionInfo?.scheduled ? (
        // Account is scheduled for deletion - show prominent warning
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mt-6">
          <div className="flex gap-3">
            <ClockIcon className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800 dark:text-red-200">
                {t('profile.deleteAccount.deletionScheduled')}
              </p>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {t('profile.deleteAccount.scheduledFor', {
                  date: new Date(deletionInfo.deletion_date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })
                })}
              </p>
              <button
                onClick={handleCancelDeletion}
                disabled={isLoading}
                className="mt-2 text-sm text-red-700 dark:text-red-300 hover:text-red-900 dark:hover:text-red-100 underline disabled:opacity-50"
              >
                {isLoading ? t('profile.deleteAccount.cancelling') : t('profile.deleteAccount.cancelDeletion')}
              </button>
            </div>
          </div>
        </div>
      ) : (
        // Normal state - show subtle delete option
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {t('profile.deleteAccount.wantToRemove')}
            </div>
            <button
              onClick={openDeletionModal}
              disabled={subscription && subscription.plan !== 'free' && !subscription.cancel_at_period_end}
              className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('profile.deleteAccount.deleteAccount')}
            </button>
          </div>
          {subscription && subscription.plan !== 'free' && !subscription.cancel_at_period_end && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              {t('profile.deleteAccount.cancelSubFirst')}
            </p>
          )}
        </div>
      )}

      <AccountDeletionModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConfirm={handleRequestDeletion}
        deletionInfo={deletionInfo}
        isLoading={isLoading}
        t={t}
      />
    </>
  )
}

export default AccountDeletionSection
