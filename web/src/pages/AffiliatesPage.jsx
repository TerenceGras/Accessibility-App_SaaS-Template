import React from 'react'
import { motion } from 'framer-motion'
import { 
  AcademicCapIcon,
  BanknotesIcon,
  UserGroupIcon,
  ClockIcon,
  RocketLaunchIcon,
  HeartIcon,
  GlobeEuropeAfricaIcon,
  SparklesIcon,
  EnvelopeIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import PageContainer from '../components/PageContainer'
import { useTranslation } from '../hooks/useTranslation'

const AffiliatesPage = () => {
  const { t } = useTranslation()

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: 'easeOut' }
    }
  }

  const benefits = [
    {
      icon: RocketLaunchIcon,
      title: t('affiliates.benefits.experience.title'),
      description: t('affiliates.benefits.experience.description')
    },
    {
      icon: AcademicCapIcon,
      title: t('affiliates.benefits.skills.title'),
      description: t('affiliates.benefits.skills.description')
    },
    {
      icon: UserGroupIcon,
      title: t('affiliates.benefits.network.title'),
      description: t('affiliates.benefits.network.description')
    },
    {
      icon: ClockIcon,
      title: t('affiliates.benefits.flexibility.title'),
      description: t('affiliates.benefits.flexibility.description')
    },
    {
      icon: BanknotesIcon,
      title: t('affiliates.benefits.income.title'),
      description: t('affiliates.benefits.income.description')
    },
    {
      icon: HeartIcon,
      title: t('affiliates.benefits.impact.title'),
      description: t('affiliates.benefits.impact.description')
    }
  ]

  const productHighlights = [
    t('affiliates.product.highlights.ethical'),
    t('affiliates.product.highlights.eu'),
    t('affiliates.product.highlights.ai'),
    t('affiliates.product.highlights.modern')
  ]

  return (
    <PageContainer>
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="space-y-16"
        >
          {/* Hero Section */}
          <motion.div variants={itemVariants} className="text-center">
            <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-medium bg-primary-100 text-primary-800 dark:bg-primary-900/30 dark:text-primary-300 mb-6">
              <SparklesIcon className="h-4 w-4 mr-2" />
              {t('affiliates.badge')}
            </span>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
              {t('affiliates.title')}
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {t('affiliates.subtitle')}
            </p>
          </motion.div>

          {/* Intro Section */}
          <motion.div 
            variants={itemVariants}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm border border-gray-200 dark:border-gray-700"
          >
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              {t('affiliates.intro.title')}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
              {t('affiliates.intro.description')}
            </p>
          </motion.div>

          {/* Open Positions */}
          <motion.div variants={itemVariants}>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {t('affiliates.positions.title')}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {t('affiliates.positions.description')}
            </p>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  {/* German Flag - SVG for consistent cross-platform display */}
                  <svg className="w-8 h-6 rounded shadow-sm" viewBox="0 0 5 3" xmlns="http://www.w3.org/2000/svg">
                    <rect width="5" height="1" y="0" fill="#000"/>
                    <rect width="5" height="1" y="1" fill="#DD0000"/>
                    <rect width="5" height="1" y="2" fill="#FFCE00"/>
                  </svg>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {t('affiliates.positions.germany.title')}
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400">
                  {t('affiliates.positions.germany.description')}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  {/* French Flag - SVG for consistent cross-platform display */}
                  <svg className="w-8 h-6 rounded shadow-sm" viewBox="0 0 3 2" xmlns="http://www.w3.org/2000/svg">
                    <rect width="1" height="2" x="0" fill="#002395"/>
                    <rect width="1" height="2" x="1" fill="#FFFFFF"/>
                    <rect width="1" height="2" x="2" fill="#ED2939"/>
                  </svg>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {t('affiliates.positions.france.title')}
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400">
                  {t('affiliates.positions.france.description')}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Mission */}
          <motion.div 
            variants={itemVariants}
            className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 rounded-2xl p-8 border border-primary-200 dark:border-primary-700/50"
          >
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              {t('affiliates.mission.title')}
            </h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              {t('affiliates.mission.description')}
            </p>
          </motion.div>

          {/* Compensation */}
          <motion.div variants={itemVariants}>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {t('affiliates.compensation.title')}
            </h2>
            <p className="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-6">
              {t('affiliates.compensation.subtitle')}
            </p>
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm border border-gray-200 dark:border-gray-700 space-y-6">
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {t('affiliates.compensation.description')}
              </p>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                    {t('affiliates.compensation.duration')}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {t('affiliates.compensation.durationDescription')}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                    {t('affiliates.compensation.structure')}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {t('affiliates.compensation.structureDescription')}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Mentoring */}
          <motion.div 
            variants={itemVariants}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-xl">
                <AcademicCapIcon className="h-8 w-8 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {t('affiliates.mentoring.title')}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {t('affiliates.mentoring.description')}
                </p>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <p className="font-semibold text-gray-900 dark:text-white mb-1">
                    {t('affiliates.mentoring.sessions')}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {t('affiliates.mentoring.sessionsDescription')}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Benefits Grid */}
          <motion.div variants={itemVariants}>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
              {t('affiliates.benefits.title')}
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {benefits.map((benefit, index) => (
                <motion.div
                  key={index}
                  variants={itemVariants}
                  className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
                >
                  <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg w-fit mb-4">
                    <benefit.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                  </div>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                    {benefit.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {benefit.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* About Product */}
          <motion.div 
            variants={itemVariants}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                <GlobeEuropeAfricaIcon className="h-8 w-8 text-primary-600 dark:text-primary-400" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {t('affiliates.product.title')}
              </h2>
            </div>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-6">
              {t('affiliates.product.description')}
            </p>
            <div className="grid sm:grid-cols-2 gap-3">
              {productHighlights.map((highlight, index) => (
                <div key={index} className="flex items-center gap-2">
                  <CheckCircleIcon className="h-5 w-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{highlight}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div 
            variants={itemVariants}
            className="bg-gray-50 dark:bg-gray-800 rounded-2xl p-8 text-center border border-gray-200 dark:border-gray-700"
          >
            <h2 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">
              {t('affiliates.apply.title')}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-lg mx-auto">
              {t('affiliates.apply.description')}
            </p>
            <div className="space-y-2">
              <a
                href={`mailto:${t('affiliates.apply.email')}?subject=Affiliate Program Application`}
                className="text-lg font-semibold text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
              >
                {t('affiliates.apply.email')}
              </a>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                {t('affiliates.apply.note')}
              </p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </PageContainer>
  )
}

export default AffiliatesPage
