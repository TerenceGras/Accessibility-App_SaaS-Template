import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ShieldCheckIcon } from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const PrivacyPolicyPage = () => {
  const { t, tRaw } = useTranslation()
  const lastUpdated = '15 December 2025'

  const sections = [
    {
      title: t('legalPages.privacy.sections.dataController.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.privacy.sections.dataController.intro')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 mb-4">
            <p className="font-semibold">{t('legalPages.privacy.sections.dataController.companyName')}</p>
            <p>{t('legalPages.privacy.sections.dataController.address')}</p>
            <p>{t('legalPages.privacy.sections.dataController.city')}</p>
            <p>{t('legalPages.privacy.sections.dataController.siret')}</p>
            <p>{t('legalPages.privacy.sections.dataController.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
          </div>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.personalData.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.personalData.intro')}</p>
          
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.privacy.sections.personalData.accountInfo')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.privacy.sections.personalData.accountItems').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.privacy.sections.personalData.usageData')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.privacy.sections.personalData.usageItems').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.privacy.sections.personalData.technicalData')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.privacy.sections.personalData.technicalItems').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.privacy.sections.personalData.integrationData')}</h4>
          <ul className="list-disc list-inside space-y-1">
            {tRaw('legalPages.privacy.sections.personalData.integrationItems').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.legalBasis.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.legalBasis.intro')}</p>
          <table className="w-full border-collapse mb-4">
            <thead>
              <tr className="border-b border-gray-300 dark:border-gray-700">
                <th className="text-left py-2 pr-4">{tRaw('legalPages.privacy.sections.legalBasis.tableHeaders')[0]}</th>
                <th className="text-left py-2">{tRaw('legalPages.privacy.sections.legalBasis.tableHeaders')[1]}</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {tRaw('legalPages.privacy.sections.legalBasis.rows').map((row, i) => (
                <tr key={i} className="border-b border-gray-200 dark:border-gray-800">
                  <td className="py-2 pr-4">{row[0]}</td>
                  <td className="py-2">{row[1]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.purposes.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.purposes.intro')}</p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.privacy.sections.purposes.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              )
            })}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.retention.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.retention.intro')}</p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.privacy.sections.retention.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              )
            })}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.processors.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.processors.intro')}</p>
          <table className="w-full border-collapse mb-4">
            <thead>
              <tr className="border-b border-gray-300 dark:border-gray-700">
                <th className="text-left py-2 pr-4">{tRaw('legalPages.privacy.sections.processors.tableHeaders')[0]}</th>
                <th className="text-left py-2 pr-4">{tRaw('legalPages.privacy.sections.processors.tableHeaders')[1]}</th>
                <th className="text-left py-2">{tRaw('legalPages.privacy.sections.processors.tableHeaders')[2]}</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {tRaw('legalPages.privacy.sections.processors.rows').map((row, i) => (
                <tr key={i} className="border-b border-gray-200 dark:border-gray-800">
                  <td className="py-2 pr-4">{row[0]}</td>
                  <td className="py-2 pr-4">{row[1]}</td>
                  <td className="py-2">{row[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('legalPages.privacy.sections.processors.note')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.transfers.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.privacy.sections.transfers.intro')}
          </p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.privacy.sections.transfers.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              )
            })}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.rights.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.rights.intro')}</p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.privacy.sections.rights.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              )
            })}
          </ul>
          <p className="mt-4">
            {t('legalPages.privacy.sections.rights.exerciseRights').split('hello@your-domain.com')[0]}
            <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a>
            {t('legalPages.privacy.sections.rights.exerciseRights').split('hello@your-domain.com')[1]}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.security.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.privacy.sections.security.intro')}</p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.privacy.sections.security.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.cookies.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.privacy.sections.cookies.content').split('Cookie Policy')[0]}
            <Link to="/cookies" className="text-primary-500 hover:underline">{t('common.cookiePolicy')}</Link>
            {t('legalPages.privacy.sections.cookies.content').split('Cookie Policy')[1]}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.complaints.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.privacy.sections.complaints.intro')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
            <p className="font-semibold">{t('legalPages.privacy.sections.complaints.authority')}</p>
            <p>{t('legalPages.privacy.sections.complaints.address1')}</p>
            <p>{t('legalPages.privacy.sections.complaints.address2')}</p>
            <p>{t('legalPages.privacy.sections.complaints.address3')}</p>
            <p>{t('legalPages.privacy.sections.complaints.website').split('www.cnil.fr')[0]}<a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">www.cnil.fr</a></p>
          </div>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.changes.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.privacy.sections.changes.content1')}
          </p>
          <p>
            {t('legalPages.privacy.sections.changes.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.privacy.sections.contact.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.privacy.sections.contact.intro')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
            <p>{t('legalPages.privacy.sections.contact.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
            <p>{t('legalPages.privacy.sections.contact.addressLabel')} YOUR_STREET_ADDRESS, YOUR_CITY_ZIP, YOUR_COUNTRY</p>
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
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 text-white shadow-lg shadow-primary-500/25 mb-6">
            <ShieldCheckIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('legalPages.privacy.title')}
          </h1>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            {t('legalPages.lastUpdated')} {lastUpdated}
          </p>
        </motion.div>

        {/* Introduction */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8"
        >
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            {t('legalPages.privacy.intro').split('your-domain.com')[0]}
            <a href="https://your-domain.com" className="text-primary-500 hover:underline">your-domain.com</a>
            {t('legalPages.privacy.intro').split('your-domain.com')[1]}
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
            {t('legalPages.privacy.introGdpr')}
          </p>
        </motion.div>

        {/* Sections */}
        <div className="space-y-6">
          {sections.map((section, index) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 + index * 0.05 }}
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
          transition={{ duration: 0.5, delay: 0.5 }}
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

export default PrivacyPolicyPage
