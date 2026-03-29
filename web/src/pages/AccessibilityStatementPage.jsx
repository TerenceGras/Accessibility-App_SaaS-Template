import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { EyeIcon, CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const AccessibilityStatementPage = () => {
  const { t, tRaw } = useTranslation()
  const lastUpdated = '15 December 2025'
  const lastReviewed = '15 December 2025'

  // WCAG criteria data - these are technical standards, not translated
  const conformanceLevels = [
    {
      category: t('legalPages.accessibilityStatement.wcagDetails.categories.perceivable'),
      criteria: [
        { id: '1.1.1', name: 'Non-text Content', level: 'A', status: 'pass', notes: 'All images have appropriate alt text. Decorative images are marked as such.' },
        { id: '1.2.1', name: 'Audio-only and Video-only', level: 'A', status: 'na', notes: 'No audio-only or video-only content on the site.' },
        { id: '1.3.1', name: 'Info and Relationships', level: 'A', status: 'pass', notes: 'Semantic HTML structure with proper headings, lists, and landmarks.' },
        { id: '1.3.2', name: 'Meaningful Sequence', level: 'A', status: 'pass', notes: 'Content order is logical in DOM and visually.' },
        { id: '1.3.3', name: 'Sensory Characteristics', level: 'A', status: 'pass', notes: 'Instructions do not rely solely on sensory characteristics.' },
        { id: '1.4.1', name: 'Use of Color', level: 'A', status: 'pass', notes: 'Color is not the only means of conveying information.' },
        { id: '1.4.2', name: 'Audio Control', level: 'A', status: 'na', notes: 'No auto-playing audio on the site.' },
        { id: '1.4.3', name: 'Contrast (Minimum)', level: 'AA', status: 'pass', notes: 'Text meets 4.5:1 contrast ratio requirements.' },
        { id: '1.4.4', name: 'Resize Text', level: 'AA', status: 'pass', notes: 'Text can be resized up to 200% without loss of functionality.' },
        { id: '1.4.5', name: 'Images of Text', level: 'AA', status: 'pass', notes: 'Text is used instead of images of text.' },
        { id: '1.4.10', name: 'Reflow', level: 'AA', status: 'pass', notes: 'Content reflows properly at 400% zoom.' },
        { id: '1.4.11', name: 'Non-text Contrast', level: 'AA', status: 'pass', notes: 'UI components and graphics have sufficient contrast.' },
        { id: '1.4.12', name: 'Text Spacing', level: 'AA', status: 'pass', notes: 'Text spacing can be adjusted without loss of content.' },
        { id: '1.4.13', name: 'Content on Hover or Focus', level: 'AA', status: 'pass', notes: 'Tooltips and popovers are dismissible and hoverable.' },
      ]
    },
    {
      category: t('legalPages.accessibilityStatement.wcagDetails.categories.operable'),
      criteria: [
        { id: '2.1.1', name: 'Keyboard', level: 'A', status: 'pass', notes: 'All functionality available via keyboard.' },
        { id: '2.1.2', name: 'No Keyboard Trap', level: 'A', status: 'pass', notes: 'Focus can move away from all components.' },
        { id: '2.1.4', name: 'Character Key Shortcuts', level: 'A', status: 'na', notes: 'No single-character keyboard shortcuts used.' },
        { id: '2.2.1', name: 'Timing Adjustable', level: 'A', status: 'pass', notes: 'No time limits on content (session tokens refresh automatically).' },
        { id: '2.2.2', name: 'Pause, Stop, Hide', level: 'A', status: 'pass', notes: 'Loading spinners are the only moving content and are essential.' },
        { id: '2.3.1', name: 'Three Flashes or Below', level: 'A', status: 'pass', notes: 'No content flashes more than 3 times per second.' },
        { id: '2.4.1', name: 'Bypass Blocks', level: 'A', status: 'pass', notes: 'Skip to main content link provided.' },
        { id: '2.4.2', name: 'Page Titled', level: 'A', status: 'pass', notes: 'All pages have descriptive titles.' },
        { id: '2.4.3', name: 'Focus Order', level: 'A', status: 'pass', notes: 'Focus order follows logical reading sequence.' },
        { id: '2.4.4', name: 'Link Purpose (In Context)', level: 'A', status: 'pass', notes: 'Link text is descriptive of destination.' },
        { id: '2.4.5', name: 'Multiple Ways', level: 'AA', status: 'pass', notes: 'Navigation menu and direct links provide multiple paths.' },
        { id: '2.4.6', name: 'Headings and Labels', level: 'AA', status: 'pass', notes: 'Headings and labels describe content accurately.' },
        { id: '2.4.7', name: 'Focus Visible', level: 'AA', status: 'pass', notes: 'Custom focus indicators are clearly visible.' },
        { id: '2.5.1', name: 'Pointer Gestures', level: 'A', status: 'pass', notes: 'No multipoint or path-based gestures required.' },
        { id: '2.5.2', name: 'Pointer Cancellation', level: 'A', status: 'pass', notes: 'Click/tap actions use up-event for activation.' },
        { id: '2.5.3', name: 'Label in Name', level: 'A', status: 'pass', notes: 'Visible labels match accessible names.' },
        { id: '2.5.4', name: 'Motion Actuation', level: 'A', status: 'na', notes: 'No motion-based interactions.' },
      ]
    },
    {
      category: t('legalPages.accessibilityStatement.wcagDetails.categories.understandable'),
      criteria: [
        { id: '3.1.1', name: 'Language of Page', level: 'A', status: 'pass', notes: 'HTML lang attribute set to "en".' },
        { id: '3.1.2', name: 'Language of Parts', level: 'AA', status: 'pass', notes: 'Language changes marked where applicable.' },
        { id: '3.2.1', name: 'On Focus', level: 'A', status: 'pass', notes: 'Focus does not trigger unexpected context changes.' },
        { id: '3.2.2', name: 'On Input', level: 'A', status: 'pass', notes: 'Form inputs do not auto-submit.' },
        { id: '3.2.3', name: 'Consistent Navigation', level: 'AA', status: 'pass', notes: 'Navigation is consistent across pages.' },
        { id: '3.2.4', name: 'Consistent Identification', level: 'AA', status: 'pass', notes: 'Components with same function have consistent labels.' },
        { id: '3.3.1', name: 'Error Identification', level: 'A', status: 'pass', notes: 'Form errors are clearly identified and described.' },
        { id: '3.3.2', name: 'Labels or Instructions', level: 'A', status: 'pass', notes: 'Form fields have associated labels.' },
        { id: '3.3.3', name: 'Error Suggestion', level: 'AA', status: 'pass', notes: 'Error messages include suggestions for correction.' },
        { id: '3.3.4', name: 'Error Prevention (Legal, Financial, Data)', level: 'AA', status: 'pass', notes: 'Subscription changes can be reviewed and confirmed.' },
      ]
    },
    {
      category: t('legalPages.accessibilityStatement.wcagDetails.categories.robust'),
      criteria: [
        { id: '4.1.1', name: 'Parsing', level: 'A', status: 'pass', notes: 'HTML validated with Nu HTML Checker.' },
        { id: '4.1.2', name: 'Name, Role, Value', level: 'A', status: 'pass', notes: 'Custom components have appropriate ARIA attributes.' },
        { id: '4.1.3', name: 'Status Messages', level: 'AA', status: 'pass', notes: 'Toast notifications use ARIA live regions.' },
      ]
    }
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pass':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'partial':
        return <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />
      case 'na':
        return <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{t('legalPages.accessibilityStatement.wcagDetails.status.na')}</span>
      default:
        return null
    }
  }

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
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-green-400 to-emerald-600 text-white shadow-lg shadow-green-500/25 mb-6">
            <EyeIcon className="h-8 w-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            {t('legalPages.accessibilityStatement.title')}
          </h1>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            {t('legalPages.accessibilityStatement.subtitle')}
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
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
            {t('legalPages.accessibilityStatement.intro')}
          </p>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            {t('legalPages.accessibilityStatement.introApplies').split('your-domain.com')[0]}
            <a href="https://your-domain.com" className="text-primary-500 hover:underline">your-domain.com</a>
            {t('legalPages.accessibilityStatement.introApplies').split('your-domain.com')[1]}
          </p>
        </motion.div>

        {/* Conformance Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.conformance.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <div className="flex items-center gap-3 mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <CheckCircleIcon className="h-8 w-8 text-green-500 flex-shrink-0" />
              <div>
                <p className="font-semibold text-green-800 dark:text-green-200">{t('legalPages.accessibilityStatement.conformance.badge')}</p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  {t('legalPages.accessibilityStatement.conformance.badgeDescription')}
                </p>
              </div>
            </div>
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.conformance.content1')}
            </p>
            <p>
              {t('legalPages.accessibilityStatement.conformance.content2')}
            </p>
          </div>
        </motion.div>

        {/* Testing Methodology */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.testing.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.testing.intro')}
            </p>
            
            <h3 className="font-semibold mt-4 mb-2">{t('legalPages.accessibilityStatement.testing.automated.title')}</h3>
            <ul className="list-disc list-inside space-y-2 mb-4">
              {tRaw('legalPages.accessibilityStatement.testing.automated.items').map((item, i) => {
                const [bold, ...rest] = item.split(':')
                return rest.length > 0 ? (
                  <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
                ) : (
                  <li key={i}>{item}</li>
                )
              })}
            </ul>

            <h3 className="font-semibold mt-4 mb-2">{t('legalPages.accessibilityStatement.testing.manual.title')}</h3>
            <ul className="list-disc list-inside space-y-2 mb-4">
              {tRaw('legalPages.accessibilityStatement.testing.manual.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>

            <h3 className="font-semibold mt-4 mb-2">{t('legalPages.accessibilityStatement.testing.browsers.title')}</h3>
            <ul className="list-disc list-inside space-y-2">
              {tRaw('legalPages.accessibilityStatement.testing.browsers.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* Technical Specifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.technical.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.technical.intro')}
            </p>
            <ul className="list-disc list-inside space-y-2">
              {tRaw('legalPages.accessibilityStatement.technical.items').map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <p className="mt-4">
              {t('legalPages.accessibilityStatement.technical.note')}
            </p>
          </div>
        </motion.div>

        {/* Accessibility Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.features.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.features.intro')}
            </p>
            <ul className="list-disc list-inside space-y-2">
              {tRaw('legalPages.accessibilityStatement.features.items').map((item, i) => {
                const [bold, ...rest] = item.split(':')
                return rest.length > 0 ? (
                  <li key={i}><strong>{bold}:</strong>{rest.join(':')}</li>
                ) : (
                  <li key={i}>{item}</li>
                )
              })}
            </ul>
          </div>
        </motion.div>

        {/* WCAG Criteria Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.wcagDetails.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-6 text-sm">
              {t('legalPages.accessibilityStatement.wcagDetails.intro')}
            </p>
            
            {conformanceLevels.map((category) => (
              <div key={category.category} className="mb-8">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3">
                  {category.category}
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-gray-300 dark:border-gray-700">
                        {tRaw('legalPages.accessibilityStatement.wcagDetails.tableHeaders').map((header, i) => (
                          <th key={i} className={`text-left py-2 pr-3 font-semibold ${i === 0 ? 'w-16' : i === 2 || i === 3 ? 'text-center w-16' : ''}`}>
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {category.criteria.map((criterion) => (
                        <tr key={criterion.id} className="border-b border-gray-200 dark:border-gray-800">
                          <td className="py-2 pr-3 font-mono text-xs">{criterion.id}</td>
                          <td className="py-2 pr-3">{criterion.name}</td>
                          <td className="py-2 pr-3 text-center">
                            <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                              criterion.level === 'A' 
                                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                            }`}>
                              {criterion.level}
                            </span>
                          </td>
                          <td className="py-2 pr-3 text-center">
                            {getStatusIcon(criterion.status)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Known Limitations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.knownIssues.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p>
              {t('legalPages.accessibilityStatement.knownIssues.content')}
            </p>
          </div>
        </motion.div>

        {/* Feedback */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.45 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.feedback.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.feedback.intro')}
            </p>
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 mb-4">
              <p>{t('legalPages.privacy.sections.dataController.emailLabel')} <a href="mailto:hello@your-domain.com" className="text-primary-500 hover:underline">hello@your-domain.com</a></p>
              <p>{t('legalPages.privacy.sections.contact.addressLabel')} YOUR_STREET_ADDRESS, YOUR_CITY_ZIP, YOUR_COUNTRY</p>
            </div>
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.feedback.responseTime')}
            </p>
            <p>
              {t('legalPages.legalNotice.sections.contact.contactFormLink').split('Contact Form')[0]}
              <Link to="/contact" className="text-primary-500 hover:underline">{t('common.contactForm')}</Link>
              {t('legalPages.legalNotice.sections.contact.contactFormLink').split('Contact Form')[1]}
            </p>
          </div>
        </motion.div>

        {/* Enforcement */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {t('legalPages.accessibilityStatement.enforcement.title')}
          </h2>
          <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
            <p className="mb-4">
              {t('legalPages.accessibilityStatement.enforcement.content1')}
            </p>
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
              <p className="font-semibold">{t('legalPages.accessibilityStatement.enforcement.authority')}</p>
              <p>7 rue Saint-Florentin</p>
              <p>75409 Paris Cedex 08</p>
              <p>Website: <a href={`https://${t('legalPages.accessibilityStatement.enforcement.website')}`} target="_blank" rel="noopener noreferrer" className="text-primary-500 hover:underline">{t('legalPages.accessibilityStatement.enforcement.website')}</a></p>
            </div>
          </div>
        </motion.div>

        {/* Assessment Date */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.55 }}
          className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-6 mb-8"
        >
          <div className="flex items-start gap-4">
            <InformationCircleIcon className="h-6 w-6 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-blue-800 dark:text-blue-200">
                <strong>{t('accessibility.lastReviewed')}:</strong> {lastReviewed}
              </p>
              <p className="text-blue-700 dark:text-blue-300 text-sm mt-1">
                {t('accessibility.reviewNote')}
              </p>
            </div>
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

export default AccessibilityStatementPage
