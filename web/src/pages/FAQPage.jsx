import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { 
  ChevronDownIcon,
  CreditCardIcon,
  DocumentMagnifyingGlassIcon,
  LinkIcon,
  QuestionMarkCircleIcon,
  EnvelopeIcon
} from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

// Accordion component for FAQ items
const FAQItem = ({ question, answer, isOpen, onToggle }) => {
  return (
    <div className="border-b border-gray-200 dark:border-gray-700 last:border-0">
      <button
        onClick={onToggle}
        className="w-full py-5 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors rounded-lg px-4 -mx-4"
        aria-expanded={isOpen}
      >
        <span className="text-base font-medium text-gray-900 dark:text-white pr-4">
          {question}
        </span>
        <ChevronDownIcon 
          className={`h-5 w-5 text-gray-500 dark:text-gray-400 flex-shrink-0 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <p className="pb-5 px-4 -mx-4 text-gray-600 dark:text-gray-400 leading-relaxed">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Category section component
const FAQCategory = ({ title, icon: Icon, faqs, openIndex, onToggle, categoryIndex }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: categoryIndex * 0.1 }}
      className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700/50 overflow-hidden"
    >
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-750 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-500/10 rounded-lg">
            <Icon className="h-5 w-5 text-primary-500" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h2>
        </div>
      </div>
      <div className="px-6 py-2">
        {faqs.map((faq, index) => (
          <FAQItem
            key={index}
            question={faq.question}
            answer={faq.answer}
            isOpen={openIndex === `${categoryIndex}-${index}`}
            onToggle={() => onToggle(`${categoryIndex}-${index}`)}
          />
        ))}
      </div>
    </motion.div>
  )
}

// Sub-section for integration-specific FAQs
const IntegrationSubSection = ({ title, faqs, openIndex, onToggle, sectionId }) => {
  return (
    <div className="mt-6">
      <h3 className="text-md font-semibold text-gray-800 dark:text-gray-200 mb-3 pl-4 border-l-3 border-primary-500">
        {title}
      </h3>
      <div className="space-y-0">
        {faqs.map((faq, index) => (
          <FAQItem
            key={index}
            question={faq.question}
            answer={faq.answer}
            isOpen={openIndex === `${sectionId}-${index}`}
            onToggle={() => onToggle(`${sectionId}-${index}`)}
          />
        ))}
      </div>
    </div>
  )
}

const FAQPage = () => {
  const { t } = useTranslation()
  const [openIndex, setOpenIndex] = useState(null)

  const handleToggle = (index) => {
    setOpenIndex(openIndex === index ? null : index)
  }

  // Build FAQ data from translations
  const creditsFaqs = [
    {
      question: t('faq.credits.getMore.question'),
      answer: t('faq.credits.getMore.answer')
    },
    {
      question: t('faq.credits.monitor.question'),
      answer: t('faq.credits.monitor.answer')
    },
    {
      question: t('faq.credits.invoice.question'),
      answer: t('faq.credits.invoice.answer')
    }
  ]

  const scansFaqs = [
    {
      question: t('faq.scans.pastScans.question'),
      answer: t('faq.scans.pastScans.answer')
    },
    {
      question: t('faq.scans.exportScan.question'),
      answer: t('faq.scans.exportScan.answer')
    }
  ]

  const integrationsOverviewFaqs = [
    {
      question: t('faq.integrations.overview.question'),
      answer: t('faq.integrations.overview.answer')
    },
    {
      question: t('faq.integrations.access.question'),
      answer: t('faq.integrations.access.answer')
    }
  ]

  const githubFaqs = [
    {
      question: t('faq.integrations.github.connect.question'),
      answer: t('faq.integrations.github.connect.answer')
    },
    {
      question: t('faq.integrations.github.configure.question'),
      answer: t('faq.integrations.github.configure.answer')
    },
    {
      question: t('faq.integrations.github.sections.question'),
      answer: t('faq.integrations.github.sections.answer')
    },
    {
      question: t('faq.integrations.github.disconnect.question'),
      answer: t('faq.integrations.github.disconnect.answer')
    }
  ]

  const notionFaqs = [
    {
      question: t('faq.integrations.notion.connect.question'),
      answer: t('faq.integrations.notion.connect.answer')
    },
    {
      question: t('faq.integrations.notion.configure.question'),
      answer: t('faq.integrations.notion.configure.answer')
    },
    {
      question: t('faq.integrations.notion.parentPage.question'),
      answer: t('faq.integrations.notion.parentPage.answer')
    },
    {
      question: t('faq.integrations.notion.disconnect.question'),
      answer: t('faq.integrations.notion.disconnect.answer')
    }
  ]

  const slackFaqs = [
    {
      question: t('faq.integrations.slack.connect.question'),
      answer: t('faq.integrations.slack.connect.answer')
    },
    {
      question: t('faq.integrations.slack.configure.question'),
      answer: t('faq.integrations.slack.configure.answer')
    },
    {
      question: t('faq.integrations.slack.channel.question'),
      answer: t('faq.integrations.slack.channel.answer')
    },
    {
      question: t('faq.integrations.slack.disconnect.question'),
      answer: t('faq.integrations.slack.disconnect.answer')
    }
  ]

  const commonFaqs = [
    {
      question: t('faq.integrations.common.scanSections.question'),
      answer: t('faq.integrations.common.scanSections.answer')
    },
    {
      question: t('faq.integrations.common.severityFilter.question'),
      answer: t('faq.integrations.common.severityFilter.answer')
    },
    {
      question: t('faq.integrations.common.grouping.question'),
      answer: t('faq.integrations.common.grouping.answer')
    },
    {
      question: t('faq.integrations.common.regroupViolations.question'),
      answer: t('faq.integrations.common.regroupViolations.answer')
    }
  ]

  return (
    <PageContainer
      title={t('faq.title')}
      description={t('faq.description')}
    >
      <div className="space-y-8">
        {/* Credits & Billing */}
        <FAQCategory
          title={t('faq.categories.credits')}
          icon={CreditCardIcon}
          faqs={creditsFaqs}
          openIndex={openIndex}
          onToggle={handleToggle}
          categoryIndex={0}
        />

        {/* Scans & Reports */}
        <FAQCategory
          title={t('faq.categories.scans')}
          icon={DocumentMagnifyingGlassIcon}
          faqs={scansFaqs}
          openIndex={openIndex}
          onToggle={handleToggle}
          categoryIndex={1}
        />

        {/* Integrations - More complex section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700/50 overflow-hidden"
        >
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-750 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-500/10 rounded-lg">
                <LinkIcon className="h-5 w-5 text-primary-500" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('faq.categories.integrations')}
              </h2>
            </div>
          </div>
          <div className="px-6 py-2">
            {/* General Integrations Questions */}
            {integrationsOverviewFaqs.map((faq, index) => (
              <FAQItem
                key={index}
                question={faq.question}
                answer={faq.answer}
                isOpen={openIndex === `int-overview-${index}`}
                onToggle={() => handleToggle(`int-overview-${index}`)}
              />
            ))}

            {/* GitHub Section */}
            <IntegrationSubSection
              title={t('faq.integrations.github.title')}
              faqs={githubFaqs}
              openIndex={openIndex}
              onToggle={handleToggle}
              sectionId="github"
            />

            {/* Notion Section */}
            <IntegrationSubSection
              title={t('faq.integrations.notion.title')}
              faqs={notionFaqs}
              openIndex={openIndex}
              onToggle={handleToggle}
              sectionId="notion"
            />

            {/* Slack Section */}
            <IntegrationSubSection
              title={t('faq.integrations.slack.title')}
              faqs={slackFaqs}
              openIndex={openIndex}
              onToggle={handleToggle}
              sectionId="slack"
            />

            {/* Common Topics */}
            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <h3 className="text-md font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
                <QuestionMarkCircleIcon className="h-5 w-5 text-gray-500" />
                Common Topics
              </h3>
              <div className="space-y-0">
                {commonFaqs.map((faq, index) => (
                  <FAQItem
                    key={index}
                    question={faq.question}
                    answer={faq.answer}
                    isOpen={openIndex === `common-${index}`}
                    onToggle={() => handleToggle(`common-${index}`)}
                  />
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Still Have Questions? */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="bg-gradient-to-br from-primary-500/10 to-primary-600/5 dark:from-primary-500/20 dark:to-primary-600/10 rounded-2xl p-8 text-center border border-primary-200 dark:border-primary-800/30"
        >
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-primary-500/10 rounded-full">
              <EnvelopeIcon className="h-8 w-8 text-primary-500" />
            </div>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {t('faq.stillHaveQuestions.title')}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
            {t('faq.stillHaveQuestions.description')}
          </p>
          <Link
            to="/contact"
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-medium transition-colors shadow-lg hover:shadow-xl"
          >
            <EnvelopeIcon className="h-5 w-5" />
            {t('faq.stillHaveQuestions.contactUs')}
          </Link>
        </motion.div>
      </div>
    </PageContainer>
  )
}

export default FAQPage
