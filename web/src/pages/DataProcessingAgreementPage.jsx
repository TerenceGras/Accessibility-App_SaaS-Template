import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { DocumentCheckIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const DataProcessingAgreementPage = () => {
  const { t, tRaw } = useTranslation()
  const lastUpdated = '15 December 2025'

  const sections = [
    {
      title: t('legalPages.dpa.sections.definitions.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.dpa.sections.definitions.intro')}</p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.dpa.sections.definitions.items').map((item, i) => {
              const match = item.match(/^"([^"]+)"(.*)$/)
              return match ? (
                <li key={i}><strong>"{match[1]}"</strong>{match[2]}</li>
              ) : (
                <li key={i}>{item}</li>
              )
            })}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.scope.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.scope.intro')}
          </p>
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.scope.subjectMatter.title')}</h4>
          <p className="mb-4">
            {t('legalPages.dpa.sections.scope.subjectMatter.content')}
          </p>
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.scope.nature.title')}</h4>
          <p className="mb-4">{t('legalPages.dpa.sections.scope.nature.intro')}</p>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.scope.nature.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.scope.categories.title')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.scope.categories.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.scope.types.title')}</h4>
          <ul className="list-disc list-inside space-y-1">
            {tRaw('legalPages.dpa.sections.scope.types.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.obligations.title'),
      content: (
        <>
          <p className="mb-4">{t('legalPages.dpa.sections.obligations.intro')}</p>
          
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.obligations.lawful.title')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.obligations.lawful.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.obligations.confidentiality.title')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.obligations.confidentiality.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.obligations.security.title')}</h4>
          <p className="mb-2">{t('legalPages.dpa.sections.obligations.security.intro')}</p>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.obligations.security.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.obligations.subprocessors.title')}</h4>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.obligations.subprocessors.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.obligations.assistance.title')}</h4>
          <ul className="list-disc list-inside space-y-1">
            {tRaw('legalPages.dpa.sections.obligations.assistance.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.rights.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.rights.intro')}
          </p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.dpa.sections.rights.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return rest.length > 0 ? (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              ) : (
                <li key={i}>{item}</li>
              )
            })}
          </ul>
          <p className="mt-4">
            {t('legalPages.dpa.sections.rights.response').split('hello@your-domain.com')[0]}
            <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a>
            {t('legalPages.dpa.sections.rights.response').split('hello@your-domain.com')[1]}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.subprocessorsList.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.subprocessorsList.intro')}
          </p>
          <div className="overflow-x-auto mb-4">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-gray-300 dark:border-gray-700">
                  {tRaw('legalPages.dpa.sections.subprocessorsList.tableHeaders').map((header, i) => (
                    <th key={i} className="text-left py-2 pr-4 font-semibold">{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tRaw('legalPages.dpa.sections.subprocessorsList.rows').map((row, i) => (
                  <tr key={i} className="border-b border-gray-200 dark:border-gray-800">
                    <td className="py-2 pr-4">{row[0]}</td>
                    <td className="py-2 pr-4">{row[1]}</td>
                    <td className="py-2">{row[2]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('legalPages.dpa.sections.subprocessorsList.notification')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.transfers.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.transfers.intro')}
          </p>
          <ul className="list-disc list-inside space-y-2">
            {tRaw('legalPages.dpa.sections.transfers.items').map((item, i) => {
              const [bold, ...rest] = item.split(':')
              return rest.length > 0 ? (
                <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
              ) : (
                <li key={i}>{item}</li>
              )
            })}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.incidents.title'),
      content: (
        <>
          <h4 className="font-semibold mb-2">{t('legalPages.dpa.sections.incidents.notification.title')}</h4>
          <p className="mb-4">
            {t('legalPages.dpa.sections.incidents.notification.content')}
          </p>
          
          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.incidents.content.title')}</h4>
          <p className="mb-2">{t('legalPages.dpa.sections.incidents.content.intro')}</p>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.incidents.content.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.incidents.cooperation.title')}</h4>
          <p>
            {t('legalPages.dpa.sections.incidents.cooperation.content')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.audit.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.audit.intro')}
          </p>
          <p className="mb-4">{t('legalPages.dpa.sections.audit.conditions')}</p>
          <ul className="list-disc list-inside space-y-1">
            {tRaw('legalPages.dpa.sections.audit.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.retention.title'),
      content: (
        <>
          <h4 className="font-semibold mb-2">{t('legalPages.dpa.sections.retention.retentionPeriod.title')}</h4>
          <p className="mb-4">
            {t('legalPages.dpa.sections.retention.retentionPeriod.content').split('Privacy Policy')[0]}
            <Link to="/privacy" className="text-primary-500 hover:underline">{t('common.privacyPolicy')}</Link>
            {t('legalPages.dpa.sections.retention.retentionPeriod.content').split('Privacy Policy')[1]}
          </p>

          <h4 className="font-semibold mt-4 mb-2">{t('legalPages.dpa.sections.retention.deletion.title')}</h4>
          <p className="mb-4">
            {t('legalPages.dpa.sections.retention.deletion.intro')}
          </p>
          <ul className="list-disc list-inside space-y-1 mb-4">
            {tRaw('legalPages.dpa.sections.retention.deletion.items').map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <p>
            {t('legalPages.dpa.sections.retention.deletion.note')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.liability.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.liability.content1').split('Terms of Service')[0]}
            <Link to="/terms" className="text-primary-500 hover:underline">{t('common.termsOfService')}</Link>
            {t('legalPages.dpa.sections.liability.content1').split('Terms of Service')[1]}
          </p>
          <p>
            {t('legalPages.dpa.sections.liability.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.term.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.term.content1')}
          </p>
          <p>
            {t('legalPages.dpa.sections.term.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.governing.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.governing.content1')}
          </p>
          <p>
            {t('legalPages.dpa.sections.governing.content2')}
          </p>
        </>
      )
    },
    {
      title: t('legalPages.dpa.sections.contact.title'),
      content: (
        <>
          <p className="mb-4">
            {t('legalPages.dpa.sections.contact.intro')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
            <p><strong>{t('legalPages.dpa.sections.contact.dataProtectionContact')}</strong></p>
            <p>YOUR_COMPANY_NAME (LumTrails)</p>
            <p>YOUR_STREET_ADDRESS</p>
            <p>YOUR_CITY_ZIP, YOUR_COUNTRY</p>
            <p>{t('legalPages.privacy.sections.dataController.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
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
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-purple-400 to-indigo-600 text-white shadow-lg shadow-purple-500/25 mb-6">
            <DocumentCheckIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('legalPages.dpa.title')}
          </h1>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            {t('legalPages.dpa.subtitle')}
          </p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
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
            {t('legalPages.dpa.intro')}
          </p>
        </motion.div>

        {/* Download Option */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-6 mb-8"
        >
          <div className="flex items-start gap-4">
            <ArrowDownTrayIcon className="h-6 w-6 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">{t('legalPages.dpa.signedCopy.title')}</h3>
              <p className="text-blue-800 dark:text-blue-200 text-sm mt-1 mb-3">
                {t('legalPages.dpa.signedCopy.description')}
              </p>
              <Link 
                to="/contact" 
                className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
              >
                {t('legalPages.dpa.signedCopy.requestLink')}
              </Link>
            </div>
          </div>
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

export default DataProcessingAgreementPage
