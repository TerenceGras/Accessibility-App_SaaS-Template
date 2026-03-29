import React, { Fragment, useState, useEffect } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import LoadingSpinner from '../LoadingSpinner'
import logger from '../../utils/logger'

const StripeCheckoutModal = ({ isOpen, onClose, onSuccess, planName, packageName }) => {
  const stripe = useStripe()
  const elements = useElements()
  const [isProcessing, setIsProcessing] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)

  const handleClose = () => {
    if (!isProcessing) {
      onClose()
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!stripe || !elements) {
      return
    }

    setIsProcessing(true)
    setErrorMessage(null)

    try {
      const { error } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/profile?payment=success`,
        },
        redirect: 'if_required',
      })

      if (error) {
        setErrorMessage(error.message)
        setIsProcessing(false)
      } else {
        // Payment succeeded
        onSuccess()
      }
    } catch (error) {
      logger.error('Payment error:', error)
      setErrorMessage('An unexpected error occurred. Please try again.')
      setIsProcessing(false)
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
          <div className="fixed inset-0 bg-gray-500 dark:bg-gray-900 bg-opacity-75 dark:bg-opacity-75" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left shadow-xl transition-all sm:my-8 sm:max-w-lg sm:w-full">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <Dialog.Title as="h3" className="text-lg font-medium text-gray-900 dark:text-white">
                    Complete Your Purchase
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    disabled={isProcessing}
                    className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {/* Content */}
                <div className="px-6 py-4">
                  {planName && (
                    <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                        Subscribing to: <span className="font-bold">{planName} Plan</span>
                      </p>
                    </div>
                  )}

                  {packageName && (
                    <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                        Purchasing: <span className="font-bold">{packageName}</span>
                      </p>
                    </div>
                  )}

                  <form onSubmit={handleSubmit}>
                    {/* Stripe Payment Element */}
                    <div className="mb-6">
                      <PaymentElement 
                        options={{
                          layout: 'tabs',
                        }}
                      />
                    </div>

                    {/* Error message */}
                    {errorMessage && (
                      <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                        <p className="text-sm text-red-800 dark:text-red-200">
                          {errorMessage}
                        </p>
                      </div>
                    )}

                    {/* Buttons */}
                    <div className="flex space-x-3">
                      <button
                        type="button"
                        onClick={handleClose}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={!stripe || isProcessing}
                        className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                      >
                        {isProcessing ? (
                          <>
                            <LoadingSpinner className="h-4 w-4 mr-2" />
                            Processing...
                          </>
                        ) : (
                          'Pay Now'
                        )}
                      </button>
                    </div>
                  </form>

                  {/* Security notice */}
                  <div className="mt-4 text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      🔒 Secure payment powered by Stripe
                    </p>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default StripeCheckoutModal
