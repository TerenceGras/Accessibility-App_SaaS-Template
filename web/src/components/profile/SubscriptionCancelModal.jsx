import React, { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useTranslation } from '../../hooks/useTranslation'

const SubscriptionCancelModal = ({ isOpen, onClose, onConfirm, subscription, isDarkMode }) => {
  const { t } = useTranslation()
  
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70" />
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
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ExclamationTriangleIcon className="h-10 w-10 text-red-600 dark:text-red-500" aria-hidden="true" />
                    </div>
                    <Dialog.Title
                      as="h3"
                      className="ml-4 text-xl font-semibold leading-6 text-gray-900 dark:text-white"
                    >
                      {t('profile.cancelModal.title')}
                    </Dialog.Title>
                  </div>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 transition-colors"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="mt-4 space-y-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {t('profile.cancelModal.areYouSure')}
                  </p>

                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-2">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="ml-3 text-sm text-gray-700 dark:text-gray-300">
                        {t('profile.cancelModal.retainAccess', { plan: subscription?.plan || 'current' })}
                      </p>
                    </div>

                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="ml-3 text-sm text-gray-700 dark:text-gray-300">
                        {t('profile.cancelModal.creditsPreserved')}
                      </p>
                    </div>

                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="ml-3 text-sm text-gray-700 dark:text-gray-300">
                        {t('profile.cancelModal.downgradedToFree')}
                      </p>
                    </div>

                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="ml-3 text-sm text-gray-700 dark:text-gray-300">
                        {t('profile.cancelModal.reactivateAnytime')}
                      </p>
                    </div>
                  </div>

                  {subscription?.current_period_end && (
                    <p className="text-sm font-medium text-gray-900 dark:text-white bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                      {t('profile.cancelModal.activeUntil', {
                        date: new Date(subscription.current_period_end).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      })}
                    </p>
                  )}
                </div>

                <div className="mt-6 flex gap-3 justify-end">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-lg bg-blue-600 dark:bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
                    onClick={onClose}
                  >
                    {t('profile.subscription.resume')}
                  </button>
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-lg bg-red-600 dark:bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 dark:hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
                    onClick={() => {
                      onConfirm()
                      onClose()
                    }}
                  >
                    {t('profile.subscription.cancelSubscription')}
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

export default SubscriptionCancelModal
