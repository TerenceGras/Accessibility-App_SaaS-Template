import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { BuildingOfficeIcon } from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const LegalNoticePage = () => {
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
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-600 text-white shadow-lg shadow-indigo-500/25 mb-6">
            <BuildingOfficeIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('legalPages.legalNotice.title')}
          </h1>
          <p className="mt-4 text-sm text-gray-500 dark:text-gray-500">
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
            {t('legalPages.legalNotice.intro').split('your-domain.com')[0]}
            <a href="https://your-domain.com" className="text-primary-500 hover:underline">your-domain.com</a>
            {t('legalPages.legalNotice.intro').split('your-domain.com')[1]}
          </p>
        </motion.div>

        {/* Website Publisher */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.publisher.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
              <table className="w-full text-sm">
                <tbody>
                  {tRaw('legalPages.legalNotice.sections.publisher.rows').map((row, i) => (
                    <tr key={i}>
                      <td className="py-2 pr-4 font-semibold whitespace-nowrap">{row[0]}</td>
                      <td className="py-2">
                        {row[0] === 'Email:' ? (
                          <a href={`mailto:${row[1]}`} className="text-primary-500 hover:underline">{row[1]}</a>
                        ) : row[1]}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>

        {/* Hosting */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.hosting.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
              <p className="font-semibold">{t('legalPages.legalNotice.sections.hosting.provider')}</p>
              <p>{t('legalPages.legalNotice.sections.hosting.company')}</p>
              <p>{t('legalPages.legalNotice.sections.hosting.address1')}</p>
              <p>{t('legalPages.legalNotice.sections.hosting.address2')}</p>
              <p className="mt-2">
                Website: <a href={`https://${t('legalPages.legalNotice.sections.hosting.website')}`} target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">{t('legalPages.legalNotice.sections.hosting.website')}</a>
              </p>
            </div>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              {t('legalPages.legalNotice.sections.hosting.serverLocation')}
            </p>
          </div>
        </motion.div>

        {/* Website Purpose */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.purpose.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.legalNotice.sections.purpose.intro')}
            </p>
            <ul className="list-disc list-inside space-y-2">
              {tRaw('legalPages.legalNotice.sections.purpose.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <p className="text-amber-800 dark:text-amber-200 text-sm">
                {t('legalPages.legalNotice.sections.purpose.disclaimer')}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Intellectual Property */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.ip.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.legalNotice.sections.ip.content1')}
            </p>
            <p className="mb-4">
              {t('legalPages.legalNotice.sections.ip.content2')}
            </p>
            <p>
              {t('legalPages.legalNotice.sections.ip.content3')}
            </p>
          </div>
        </motion.div>

        {/* Personal Data */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.personalData.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.legalNotice.sections.personalData.content1')}
            </p>
            <p>
              {t('legalPages.legalNotice.sections.personalData.content2').split('Privacy Policy')[0]}
              <Link to="/privacy" className="text-primary-500 hover:underline">{t('common.privacyPolicy')}</Link>
              {t('legalPages.legalNotice.sections.personalData.content2').split('Privacy Policy')[1]}
            </p>
          </div>
        </motion.div>

        {/* Cookies */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.45 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.cookiesSection.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p>
              {t('legalPages.legalNotice.sections.cookiesSection.content').split('Cookie Policy')[0]}
              <Link to="/cookies" className="text-primary-500 hover:underline">{t('common.cookiePolicy')}</Link>
              {t('legalPages.legalNotice.sections.cookiesSection.content').split('Cookie Policy')[1]}
            </p>
          </div>
        </motion.div>

        {/* Applicable Law */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.applicableLaw.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.legalNotice.sections.applicableLaw.content1')}
            </p>
            <p>
              {t('legalPages.legalNotice.sections.applicableLaw.content2')}{' '}
              <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">
                https://ec.europa.eu/consumers/odr
              </a>
            </p>
          </div>
        </motion.div>

        {/* Contact */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.55 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.legalNotice.sections.contact.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.legalNotice.sections.contact.intro')}
            </p>
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
              <p>{t('legalPages.privacy.sections.dataController.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
              <p>{t('legalPages.privacy.sections.contact.addressLabel')} YOUR_STREET_ADDRESS, YOUR_CITY_ZIP, YOUR_COUNTRY</p>
            </div>
            <p className="mt-4">
              {t('legalPages.legalNotice.sections.contact.contactFormLink').split('Contact Form')[0]}
              <Link to="/contact" className="text-primary-500 hover:underline">{t('common.contactForm')}</Link>
              {t('legalPages.legalNotice.sections.contact.contactFormLink').split('Contact Form')[1]}
            </p>
          </div>
        </motion.div>

        {/* Back to Home */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
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

export default LegalNoticePage
