import React, { useState, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { 
  BuildingOfficeIcon,
  MapPinIcon,
  IdentificationIcon
} from '@heroicons/react/24/outline'
import useAuthStore from '../../stores/authStore'
import { useTranslation } from '../../hooks/useTranslation'
import logger from '../../utils/logger'

const BillingInfoForm = ({ isDarkMode, userId, apiUrl, onUpdate }) => {
  const { t } = useTranslation()
  const { getIdToken } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [billingInfo, setBillingInfo] = useState({
    company_name: '',
    vat_number: '',
    address: {
      line1: '',
      line2: '',
      city: '',
      postal_code: '',
      country: ''
    }
  })

  useEffect(() => {
    fetchBillingInfo()
  }, [userId])

  const fetchBillingInfo = async () => {
    if (!userId) return

    try {
      setLoading(true)
      const token = await getIdToken()
      const response = await fetch(`${apiUrl}/billing-info`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data && data.billing_info) {
          // Ensure address exists
          const fetchedInfo = data.billing_info
          setBillingInfo({
            company_name: fetchedInfo.company_name || '',
            vat_number: fetchedInfo.vat_number || '',
            address: {
              line1: fetchedInfo.address?.line1 || '',
              line2: fetchedInfo.address?.line2 || '',
              city: fetchedInfo.address?.city || '',
              postal_code: fetchedInfo.address?.postal_code || '',
              country: fetchedInfo.address?.country || ''
            }
          })
        }
      }
    } catch (error) {
      logger.error('Error fetching billing info:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)

    try {
      const token = await getIdToken()
      const response = await fetch(`${apiUrl}/billing-info`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(billingInfo)
      })

      if (!response.ok) {
        throw new Error('Failed to update billing information')
      }

      toast.success(t('profile.billingInfo.toasts.updateSuccess'))
      if (onUpdate) onUpdate()
    } catch (error) {
      logger.error('Error updating billing info:', error)
      toast.error(t('profile.billingInfo.toasts.updateFailed'))
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

  if (loading) {
    return (
      <div className={`${
        isDarkMode ? 'bg-gray-800' : 'bg-white'
      } rounded-lg shadow-lg p-6 border ${
        isDarkMode ? 'border-gray-700' : 'border-gray-200'
      }`}>
        <div className="animate-pulse space-y-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className={`h-12 ${
                isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
              } rounded`}
            ></div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className={`${
      isDarkMode ? 'bg-gray-800' : 'bg-white'
    } rounded-lg shadow-lg p-6 border ${
      isDarkMode ? 'border-gray-700' : 'border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className={`text-lg font-semibold ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          {t('profile.billingInfo.title')}
        </h3>
        <BuildingOfficeIcon className="h-6 w-6 text-blue-500" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Company Name */}
        <div>
          <label className={`block text-sm font-medium mb-1 ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Company Name
          </label>
          <input
            type="text"
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

        {/* VAT Number */}
        <div>
          <label className={`block text-sm font-medium mb-1 ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            VAT Number (optional)
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <IdentificationIcon className={`h-5 w-5 ${
                isDarkMode ? 'text-gray-500' : 'text-gray-400'
              }`} />
            </div>
            <input
              type="text"
              value={billingInfo.vat_number}
              onChange={(e) => handleChange('vat_number', e.target.value)}
              placeholder="EU123456789"
              className={`w-full pl-10 pr-3 py-2 rounded-md border ${
                isDarkMode
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } focus:outline-none focus:ring-2 focus:ring-blue-500`}
            />
          </div>
        </div>

        {/* Address Line 1 */}
        <div>
          <label className={`block text-sm font-medium mb-1 ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Address Line 1
          </label>
          <input
            type="text"
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

        {/* Address Line 2 */}
        <div>
          <label className={`block text-sm font-medium mb-1 ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Address Line 2 (optional)
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

        {/* City, Postal Code, Country */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className={`block text-sm font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              City
            </label>
            <input
              type="text"
              value={billingInfo.address.city}
              onChange={(e) => handleChange('address.city', e.target.value)}
              placeholder="Brussels"
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
              Postal Code
            </label>
            <input
              type="text"
              value={billingInfo.address.postal_code}
              onChange={(e) => handleChange('address.postal_code', e.target.value)}
              placeholder="1000"
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
              Country
            </label>
            <input
              type="text"
              value={billingInfo.address.country}
              onChange={(e) => handleChange('address.country', e.target.value)}
              placeholder="Belgium"
              className={`w-full px-3 py-2 rounded-md border ${
                isDarkMode
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              } focus:outline-none focus:ring-2 focus:ring-blue-500`}
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4">
          <button
            type="submit"
            disabled={saving}
            className={`w-full px-4 py-2 rounded-md font-medium transition-colors ${
              saving
                ? isDarkMode
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {saving ? 'Saving...' : 'Save Billing Information'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default BillingInfoForm
