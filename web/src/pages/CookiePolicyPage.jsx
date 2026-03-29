import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { CogIcon } from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const CookiePolicyPage = () => {
  const { t, tRaw } = useTranslation()
  const lastUpdated = '15 December 2025'

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
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/25 mb-6">
            <CogIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('legalPages.cookies.title')}
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
            {t('legalPages.cookies.intro').split('your-domain.com')[0]}
            <a href="https://your-domain.com" className="text-primary-500 hover:underline">your-domain.com</a>
            {t('legalPages.cookies.intro').split('your-domain.com')[1]}
          </p>
        </motion.div>

        {/* What Are Cookies */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.whatAreCookies.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.whatAreCookies.content1')}
            </p>
            <p>
              {t('legalPages.cookies.whatAreCookies.content2')}
            </p>
          </div>
        </motion.div>

        {/* Cookies We Use */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.cookiesWeUse.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.cookiesWeUse.intro')}
            </p>
            
            <h3 className="font-semibold text-gray-900 dark:text-white mt-6 mb-3">{t('legalPages.cookies.cookiesWeUse.strictlyNecessary.title')}</h3>
            <p className="mb-4">
              {t('legalPages.cookies.cookiesWeUse.strictlyNecessary.description')}
            </p>
            
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-gray-300 dark:border-gray-700">
                    {tRaw('legalPages.cookies.cookiesWeUse.strictlyNecessary.tableHeaders').map((header, i) => (
                      <th key={i} className="text-left py-3 pr-4 font-semibold">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tRaw('legalPages.cookies.cookiesWeUse.strictlyNecessary.rows').map((row, i) => (
                    <tr key={i} className="border-b border-gray-200 dark:border-gray-800">
                      <td className="py-3 pr-4 font-mono text-xs">{row[0]}</td>
                      <td className="py-3 pr-4">{row[1]}</td>
                      <td className="py-3 pr-4">{row[2]}</td>
                      <td className="py-3">{row[3]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>

        {/* Third-Party Cookies */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.thirdParty.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.thirdParty.content1')}
            </p>
            <p className="mb-4">
              {t('legalPages.cookies.thirdParty.content2')}
            </p>
            <p>
              <strong>{t('legalPages.cookies.thirdParty.weDoNotUse')}</strong>
            </p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              {tRaw('legalPages.cookies.thirdParty.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* Consent */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.consent.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.consent.content1')}
            </p>
            <p>
              {t('legalPages.cookies.consent.content2')}
            </p>
          </div>
        </motion.div>

        {/* Managing Cookies */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.managing.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.managing.intro')}
            </p>
            <ul className="list-disc list-inside space-y-2 mb-4">
              {tRaw('legalPages.cookies.managing.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <p className="mb-4">
              {t('legalPages.cookies.managing.browserLinks')}
            </p>
            <ul className="space-y-2">
              <li>
                <a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">
                  {tRaw('legalPages.cookies.managing.browsers')[0]}
                </a>
              </li>
              <li>
                <a href="https://support.mozilla.org/en-US/kb/enhanced-tracking-protection-firefox-desktop" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">
                  {tRaw('legalPages.cookies.managing.browsers')[1]}
                </a>
              </li>
              <li>
                <a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">
                  {tRaw('legalPages.cookies.managing.browsers')[2]}
                </a>
              </li>
              <li>
                <a href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">
                  {tRaw('legalPages.cookies.managing.browsers')[3]}
                </a>
              </li>
            </ul>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              {t('legalPages.cookies.managing.note')}
            </p>
          </div>
        </motion.div>

        {/* Local Storage */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.localStorage.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.localStorage.intro')}
            </p>
            <ul className="list-disc list-inside space-y-1">
              {tRaw('legalPages.cookies.localStorage.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <p className="mt-4">
              {t('legalPages.cookies.localStorage.note')}
            </p>
          </div>
        </motion.div>

        {/* Updates */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.45 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.updates.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p>
              {t('legalPages.cookies.updates.content')}
            </p>
          </div>
        </motion.div>

        {/* Contact */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.cookies.contact.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.cookies.contact.intro')}
            </p>
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
              <p>{t('legalPages.privacy.sections.dataController.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
              <p>{t('legalPages.privacy.sections.contact.addressLabel')} YOUR_STREET_ADDRESS, YOUR_CITY_ZIP, YOUR_COUNTRY</p>
            </div>
          </div>
        </motion.div>

        {/* Back to Home */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.55 }}
          className="text-center"
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

export default CookiePolicyPage
