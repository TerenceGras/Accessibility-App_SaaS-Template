import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { DocumentTextIcon } from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const TermsOfServicePage = () => {
  const { t, tRaw } = useTranslation()
  const lastUpdated = '15 December 2025'
  const effectiveDate = '15 December 2025'

  const sections = [
    {
      title: t('legalPages.terms.sections.acceptance.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.acceptance.content1').split('your-domain.com')[0]}
            <a href="https://your-domain.com" className="text-primary-500 hover:underline">your-domain.com</a>
            {t('legalPages.terms.sections.acceptance.content1').split('your-domain.com')[1]}
          </p>
          <p>
            {t('legalPages.terms.sections.acceptance.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.description.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.description.intro')}
          </p>
          <ul className="list-disc list-inside space-y-2 mb-4">
            {tRaw('legalPages.terms.sections.description.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              )
            })}
          </ul>
          <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <p className="text-amber-800 dark:text-amber-200 text-sm">
              {t('legalPages.terms.sections.description.disclaimer')}
            </p>
          </div>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.registration.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.terms.sections.registration.intro')}</p>
          <ul className="list-disc list-inside space-y-2 mb-4">
            {tRaw('legalPages.terms.sections.registration.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <p>
            {t('legalPages.terms.sections.registration.suspension')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.credits.title'),
      content: (
        <>
          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.credits.creditSystem.title')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.credits.creditSystem.intro')}
          </p>
          <ul className="list-disc list-inside space-y-2 mb-4">
            {tRaw('legalPages.terms.sections.credits.creditSystem.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              )
            })}
          </ul>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.credits.plans.title')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.credits.plans.content').split('Pricing page')[0]}
            <Link to="/pricing" className="text-primary-500 hover:underline">{t('common.pricingPage')}</Link>
            {t('legalPages.terms.sections.credits.plans.content').split('Pricing page')[1]}
          </p>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.credits.renewal.title')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.credits.renewal.content')}
          </p>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.credits.billing.title')}</h4>
          <p>
            {t('legalPages.terms.sections.credits.billing.content')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.cancellation.title'),
      content: (
        <>
          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.cancellation.cancellationTitle')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.cancellation.cancellationContent')}
          </p>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.cancellation.refundTitle')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.cancellation.refundIntro')}
          </p>
          <ul className="list-disc list-inside space-y-2 mb-4">
            {tRaw('legalPages.terms.sections.cancellation.refundItems').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <p>
            {t('legalPages.terms.sections.cancellation.refundContact').split('hello@your-domain.com')[0]}
            <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a>
            {t('legalPages.terms.sections.cancellation.refundContact').split('hello@your-domain.com')[1]}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.acceptableUse.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.terms.sections.acceptableUse.intro')}</p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.terms.sections.acceptableUse.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.ip.title'),
      content: (
        <>
          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.ip.ourIp.title')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.ip.ourIp.content')}
          </p>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.ip.yourContent.title')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.ip.yourContent.content')}
          </p>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.ip.scanResults.title')}</h4>
          <p>
            {t('legalPages.terms.sections.ip.scanResults.content')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.availability.title'),
      content: (
        <>
          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.availability.availabilityTitle')}</h4>
          <p className="mb-4">
            {t('legalPages.terms.sections.availability.availabilityContent')}
          </p>

          <h4 className="font-semibold mb-2">{t('legalPages.terms.sections.availability.modificationsTitle')}</h4>
          <p>
            {t('legalPages.terms.sections.availability.modificationsContent')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.liability.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.liability.intro')}
          </p>
          <ul className="list-disc list-inside space-y-2 mb-4">
            {tRaw('legalPages.terms.sections.liability.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <p>
            {t('legalPages.terms.sections.liability.note')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.indemnification.title'),
      content: (
        <>
          <p>
            {t('legalPages.terms.sections.indemnification.content')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.privacy.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.privacy.content1').split('Privacy Policy')[0]}
            <Link to="/privacy" className="text-primary-500 hover:underline">{t('common.privacyPolicy')}</Link>
            {t('legalPages.terms.sections.privacy.content1').split('Privacy Policy')[1]}
          </p>
          <p>
            {t('legalPages.terms.sections.privacy.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.thirdParty.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.thirdParty.content')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.termination.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.termination.content1')}
          </p>
          <p>
            {t('legalPages.terms.sections.termination.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.changes.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.changes.content1')}
          </p>
          <p>
            {t('legalPages.terms.sections.changes.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.governing.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.governing.content1')}
          </p>
          <p className="mb-4">
            {t('legalPages.terms.sections.governing.content2')}
          </p>
          <p>
            {t('legalPages.terms.sections.governing.content3')}{' '}
            <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">
              https://ec.europa.eu/consumers/odr
            </a>
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.severability.title'),
      content: (
        <>
          <p>
            {t('legalPages.terms.sections.severability.content')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.terms.sections.contact.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.terms.sections.contact.intro')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
            <p><strong>YOUR_COMPANY_NAME (LumTrails)</strong></p>
            <p>YOUR_STREET_ADDRESS</p>
            <p>YOUR_CITY_ZIP, YOUR_COUNTRY</p>
            <p>{t('legalPages.privacy.sections.dataController.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
            <p>{t('legalPages.privacy.sections.dataController.siret')}</p>
          </div>
        </>
      )
    }
  ]

  return (
    <PageContainer>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-400 to-blue-600 text-white shadow-lg shadow-blue-500/25 mb-6">
            <DocumentTextIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('legalPages.terms.title')}
          </h1>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            {t('legalPages.lastUpdated')} {lastUpdated}
          </p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
            {t('legalPages.effectiveDate')} {effectiveDate}
          </p>
        </motion.div>

        {/* Sections */}
        <div className="space-y-6">
          {sections.map((section, index) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 + index * 0.03 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
            >
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                {section.title}
              </h2>
              <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {section.content}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Back to Home */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-12 text-center"
        >
          <Link
            to="/"
            className="text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 font-medium"
          >
            {t('legalPages.backToHome')}
          </Link>
        </motion.div>
      </div>
    </PageContainer>
  )
}

export default TermsOfServicePage
