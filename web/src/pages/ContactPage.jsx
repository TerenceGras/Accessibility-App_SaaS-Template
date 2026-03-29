import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { 
  EnvelopeIcon, 
  MapPinIcon, 
  BuildingOfficeIcon,
  PaperAirplaneIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import LoadingSpinner from '../components/LoadingSpinner'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

// Use main API for contact form (secure service-to-service communication)
const API_URL = import.meta.env.VITE_API_URL || '';

const ContactPage = () => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [errors, setErrors] = useState({})

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.name.trim()) {
      newErrors.name = t('contact.form.errors.nameRequired')
    }
    
    if (!formData.email.trim()) {
      newErrors.email = t('contact.form.errors.emailRequired')
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = t('contact.form.errors.emailInvalid')
    }
    
    if (!formData.subject.trim()) {
      newErrors.subject = t('contact.form.errors.subjectRequired')
    }
    
    if (!formData.message.trim()) {
      newErrors.message = t('contact.form.errors.messageRequired')
    } else if (formData.message.trim().length < 10) {
      newErrors.message = t('contact.form.errors.messageMinLength')
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      toast.error(t('contact.form.errors.fillRequired'))
      return
    }
    
    setIsSubmitting(true)
    
    try {
      // Use main API for contact form (secure service-to-service to mailing service)
      const response = await fetch(`${API_URL}/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          subject: formData.subject,
          message: formData.message
        })
      })
      
      if (response.ok) {
        setIsSubmitted(true)
        setFormData({ name: '', email: '', subject: '', message: '' })
        toast.success(t('contact.form.successMessage'))
      } else {
        throw new Error('Failed to send message')
      }
    } catch (error) {
      logger.error('Contact form error:', error)
      toast.error(t('contact.form.errorMessage'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const subjectOptions = [
    { value: 'General Inquiry', label: t('contact.form.subjects.generalInquiry') },
    { value: 'Technical Support', label: t('contact.form.subjects.technicalSupport') },
    { value: 'Billing Question', label: t('contact.form.subjects.billingQuestion') },
    { value: 'Accessibility Feedback', label: t('contact.form.subjects.accessibilityFeedback') },
    { value: 'Feature Request', label: t('contact.form.subjects.featureRequest') },
    { value: 'Partnership Inquiry', label: t('contact.form.subjects.partnershipInquiry') },
    { value: 'Press Inquiry', label: t('contact.form.subjects.pressInquiry') },
    { value: 'Other', label: t('contact.form.subjects.other') }
  ]

  return (
    <PageContainer>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 text-white shadow-lg shadow-primary-500/25 mb-6">
            <EnvelopeIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('contact.title')}
          </h1>
          <p className="mt-4 text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            {t('contact.subtitle')}
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Contact Information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-1 space-y-6"
          >
            {/* Direct Contact */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {t('contact.getInTouch')}
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <EnvelopeIcon className="h-5 w-5 text-primary-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{t('contact.email')}</p>
                    <a 
                      href="mailto:hello@your-domain.com" 
                      className="text-sm text-primary-500 hover:underline"
                    >
                      hello@your-domain.com
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* Response Time */}
            <div className="bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border border-primary-200 dark:border-primary-800 rounded-2xl p-6">
              <h3 className="font-semibold text-primary-900 dark:text-primary-100 mb-2">
                {t('contact.responseTime')}
              </h3>
              <p className="text-sm text-primary-800 dark:text-primary-200">
                {t('contact.responseTimeDesc')}
              </p>
            </div>

            {/* Quick Links */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                {t('contact.helpfulLinks')}
              </h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/privacy" className="text-primary-500 hover:underline">
                    {t('nav.privacy')}
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="text-primary-500 hover:underline">
                    {t('nav.terms')}
                  </Link>
                </li>
                <li>
                  <Link to="/accessibility" className="text-primary-500 hover:underline">
                    {t('nav.accessibility')}
                  </Link>
                </li>
                <li>
                  <Link to="/api" className="text-primary-500 hover:underline">
                    {t('nav.api')}
                  </Link>
                </li>
              </ul>
            </div>
          </motion.div>

          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 sm:p-8">
              {isSubmitted ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center py-12"
                >
                  <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-6">
                    <CheckCircleIcon className="h-8 w-8 text-green-500" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    {t('contact.form.messageSentTitle')}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                    {t('contact.form.messageSentDesc')}
                  </p>
                  <button
                    onClick={() => setIsSubmitted(false)}
                    className="btn-secondary"
                  >
                    {t('contact.form.sendAnother')}
                  </button>
                </motion.div>
              ) : (
                <>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                    {t('contact.form.sendMessage')}
                  </h2>
                  
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid sm:grid-cols-2 gap-6">
                      {/* Name */}
                      <div>
                        <label 
                          htmlFor="name" 
                          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                          {t('contact.form.name')} <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          id="name"
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          className={`w-full px-4 py-2.5 rounded-lg border ${
                            errors.name 
                              ? 'border-red-500 focus:ring-red-500' 
                              : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
                          } bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:border-transparent transition-colors`}
                          placeholder={t('contact.form.namePlaceholder')}
                          aria-describedby={errors.name ? 'name-error' : undefined}
                          aria-invalid={errors.name ? 'true' : 'false'}
                        />
                        {errors.name && (
                          <p id="name-error" className="mt-1 text-sm text-red-500" role="alert">
                            {errors.name}
                          </p>
                        )}
                      </div>

                      {/* Email */}
                      <div>
                        <label 
                          htmlFor="email" 
                          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                        >
                          {t('contact.form.email')} <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="email"
                          id="email"
                          name="email"
                          value={formData.email}
                          onChange={handleChange}
                          className={`w-full px-4 py-2.5 rounded-lg border ${
                            errors.email 
                              ? 'border-red-500 focus:ring-red-500' 
                              : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
                          } bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:border-transparent transition-colors`}
                          placeholder={t('contact.form.emailPlaceholder')}
                          aria-describedby={errors.email ? 'email-error' : undefined}
                          aria-invalid={errors.email ? 'true' : 'false'}
                        />
                        {errors.email && (
                          <p id="email-error" className="mt-1 text-sm text-red-500" role="alert">
                            {errors.email}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Subject */}
                    <div>
                      <label 
                        htmlFor="subject" 
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        {t('contact.form.subject')} <span className="text-red-500">*</span>
                      </label>
                      <select
                        id="subject"
                        name="subject"
                        value={formData.subject}
                        onChange={handleChange}
                        className={`w-full px-4 py-2.5 rounded-lg border ${
                          errors.subject 
                            ? 'border-red-500 focus:ring-red-500' 
                            : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
                        } bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:border-transparent transition-colors`}
                        aria-describedby={errors.subject ? 'subject-error' : undefined}
                        aria-invalid={errors.subject ? 'true' : 'false'}
                      >
                        <option value="">{t('contact.form.selectSubject')}</option>
                        {subjectOptions.map(option => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                      {errors.subject && (
                        <p id="subject-error" className="mt-1 text-sm text-red-500" role="alert">
                          {errors.subject}
                        </p>
                      )}
                    </div>

                    {/* Message */}
                    <div>
                      <label 
                        htmlFor="message" 
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        {t('contact.form.message')} <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        id="message"
                        name="message"
                        value={formData.message}
                        onChange={handleChange}
                        rows={6}
                        className={`w-full px-4 py-2.5 rounded-lg border ${
                          errors.message 
                            ? 'border-red-500 focus:ring-red-500' 
                            : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500'
                        } bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:border-transparent transition-colors resize-y`}
                        placeholder={t('contact.form.messagePlaceholder')}
                        aria-describedby={errors.message ? 'message-error' : 'message-hint'}
                        aria-invalid={errors.message ? 'true' : 'false'}
                      />
                      {errors.message ? (
                        <p id="message-error" className="mt-1 text-sm text-red-500" role="alert">
                          {errors.message}
                        </p>
                      ) : (
                        <p id="message-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          {t('contact.form.messageHint')}
                        </p>
                      )}
                    </div>

                    {/* Privacy Notice */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm text-gray-600 dark:text-gray-400">
                      <p>
                        {t('contact.form.privacyNotice')}{' '}
                        <Link to="/privacy" className="text-primary-500 hover:underline">{t('nav.privacy')}</Link>. 
                        {t('contact.form.privacyNotice2')}
                      </p>
                    </div>

                    {/* Submit Button */}
                    <div>
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full sm:w-auto btn-primary flex items-center justify-center gap-2 px-8 py-3"
                      >
                        {isSubmitting ? (
                          <>
                            <LoadingSpinner className="h-5 w-5" />
                            <span>{t('contact.form.sending')}</span>
                          </>
                        ) : (
                          <>
                            <PaperAirplaneIcon className="h-5 w-5" />
                            <span>{t('contact.form.submit')}</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </>
              )}
            </div>
          </motion.div>
        </div>

        {/* Back to Home */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-12 text-center"
        >
          <Link
            to="/"
            className="text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 font-medium"
          >
            ← {t('common.backToHome')}
          </Link>
        </motion.div>
      </div>
    </PageContainer>
  )
}

export default ContactPage
