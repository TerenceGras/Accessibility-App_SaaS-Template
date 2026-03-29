import React, { useState, useEffect, Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, BuildingOfficeIcon, UserIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import useAuthStore from '../../stores/authStore'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const BillingInfoModal = ({ isOpen, onClose, onComplete, isDarkMode }) => {
  const { t } = useTranslation()
  const { getIdToken } = useAuthStore()
  const [isB2B, setIsB2B] = useState(true)
  const [saving, setSaving] = useState(false)
  const [billingInfo, setBillingInfo] = useState({
    company_name: '',
    vat_number: '',
    full_name: '',
    address: {
      line1: '',
      line2: '',
      city: '',
      postal_code: '',
      country: ''
    }
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate required fields
    if (isB2B && !billingInfo.company_name) {
      toast.error(t('billing.modal.companyRequired'))
      return
    }
    if (!isB2B && !billingInfo.full_name) {
      toast.error(t('billing.modal.nameRequired'))
      return
    }
    if (!billingInfo.address.line1 || !billingInfo.address.city || 
        !billingInfo.address.postal_code || !billingInfo.address.country) {
      toast.error(t('billing.modal.addressRequired'))
      return
    }

    setSaving(true)
    try {
      const token = await getIdToken()
      const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''
      
      const payload = {
        company_name: isB2B ? billingInfo.company_name : billingInfo.full_name,
        vat_number: isB2B ? billingInfo.vat_number : null,
        address: billingInfo.address
      }

      const response = await fetch(`${PRICING_API_URL}/billing-info`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error('Failed to save billing information')
      }

      toast.success(t('billing.modal.saveSuccess'))
      onComplete()
    } catch (error) {
      logger.error('Error saving billing info:', error)
      toast.error(t('billing.modal.saveFailed'))
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (field, value) => {
    if (field.startsWith('address.')) {
      const addressField = field.split('.')[1]
      setBillingInfo(prev => ({
        ...prev,
        address: {
          ...prev.address,
          [addressField]: value
        }
      }))
    } else {
      setBillingInfo(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

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
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75" />
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
              <Dialog.Panel className={`w-full max-w-2xl transform overflow-hidden rounded-lg ${
                isDarkMode ? 'bg-gray-800' : 'bg-white'
              } px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:p-6`}>
                <div className="absolute top-0 right-0 pt-4 pr-4">
                  <button
                    onClick={onClose}
                    className={`${
                      isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-400 hover:text-gray-500'
                    } focus:outline-none`}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="w-full">
                  <Dialog.Title as="h3" className={`text-lg font-medium leading-6 ${
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  } mb-4`}>
                    {t('billing.modal.title')}
                  </Dialog.Title>
                  <p className={`text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              } mb-6`}>
                {t('billing.modal.description')}
              </p>

              {/* B2B/B2C Toggle */}
              <div className="mb-6">
                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => setIsB2B(true)}
                    className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                      isB2B
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : isDarkMode
                        ? 'border-gray-600 hover:border-gray-500'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <BuildingOfficeIcon className={`h-6 w-6 mx-auto mb-2 ${
                      isB2B ? 'text-blue-500' : isDarkMode ? 'text-gray-400' : 'text-gray-500'
                    }`} />
                    <span className={`text-sm font-medium ${
                      isDarkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      {t('billing.modal.business')}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsB2B(false)}
                    className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                      !isB2B
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : isDarkMode
                        ? 'border-gray-600 hover:border-gray-500'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <UserIcon className={`h-6 w-6 mx-auto mb-2 ${
                      !isB2B ? 'text-blue-500' : isDarkMode ? 'text-gray-400' : 'text-gray-500'
                    }`} />
                    <span className={`text-sm font-medium ${
                      isDarkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      {t('billing.modal.individual')}
                    </span>
                  </button>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {isB2B ? (
                  <>
                    <div>
                      <label className={`block text-sm font-medium mb-1 ${
                        isDarkMode ? 'text-gray-300' : 'text-gray-700'
                      }`}>
                        {t('billing.modal.companyName')} *
                      </label>
                      <input
                        type="text"
                        required
                        value={billingInfo.company_name}
                        onChange={(e) => handleChange('company_name', e.target.value)}
                        placeholder="Acme Corporation"
                        className={`w-full px-3 py-2 rounded-md border ${
                          isDarkMode
                            ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                            : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                        } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                      />
                    </div>
                    <div>
                      <label className={`block text-sm font-medium mb-1 ${
                        isDarkMode ? 'text-gray-300' : 'text-gray-700'
                      }`}>
                        {t('billing.modal.vatNumber')}
                      </label>
                      <input
                        type="text"
                        value={billingInfo.vat_number}
                        onChange={(e) => handleChange('vat_number', e.target.value)}
                        placeholder="EU123456789"
                        className={`w-full px-3 py-2 rounded-md border ${
                          isDarkMode
                            ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                            : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                        } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                      />
                    </div>
                  </>
                ) : (
                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      isDarkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      {t('billing.modal.fullName')} *
                    </label>
                    <input
                      type="text"
                      required
                      value={billingInfo.full_name}
                      onChange={(e) => handleChange('full_name', e.target.value)}
                      placeholder="John Doe"
                      className={`w-full px-3 py-2 rounded-md border ${
                        isDarkMode
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>
                )}

                <div>
                  <label className={`block text-sm font-medium mb-1 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    {t('billing.modal.addressLine1')} *
                  </label>
                  <input
                    type="text"
                    required
                    value={billingInfo.address.line1}
                    onChange={(e) => handleChange('address.line1', e.target.value)}
                    placeholder="123 Main Street"
                    className={`w-full px-3 py-2 rounded-md border ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    {t('billing.modal.addressLine2')}
                  </label>
                  <input
                    type="text"
                    value={billingInfo.address.line2}
                    onChange={(e) => handleChange('address.line2', e.target.value)}
                    placeholder="Apartment, suite, etc."
                    className={`w-full px-3 py-2 rounded-md border ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      isDarkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      {t('billing.modal.city')} *
                    </label>
                    <input
                      type="text"
                      required
                      value={billingInfo.address.city}
                      onChange={(e) => handleChange('address.city', e.target.value)}
                      placeholder="Paris"
                      className={`w-full px-3 py-2 rounded-md border ${
                        isDarkMode
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium mb-1 ${
                      isDarkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      {t('billing.modal.postalCode')} *
                    </label>
                    <input
                      type="text"
                      required
                      value={billingInfo.address.postal_code}
                      onChange={(e) => handleChange('address.postal_code', e.target.value)}
                      placeholder="75001"
                      className={`w-full px-3 py-2 rounded-md border ${
                        isDarkMode
                          ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-1 ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    {t('billing.modal.country')} *
                  </label>
                  <input
                    type="text"
                    required
                    value={billingInfo.address.country}
                    onChange={(e) => handleChange('address.country', e.target.value)}
                    placeholder="France"
                    className={`w-full px-3 py-2 rounded-md border ${
                      isDarkMode
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                <div className="mt-6 flex space-x-3">
                  <button
                    type="button"
                    onClick={onClose}
                    className={`flex-1 px-4 py-2 rounded-md border ${
                      isDarkMode
                        ? 'border-gray-600 text-gray-300 hover:bg-gray-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    } font-medium`}
                  >
                    {t('billing.modal.cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? t('billing.modal.saving') : t('billing.modal.continue')}
                  </button>
                </div>
              </form>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default BillingInfoModal
