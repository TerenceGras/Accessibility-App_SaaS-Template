import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  CheckCircleIcon, 
  SparklesIcon,
  ArrowRightIcon,
  DocumentIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  BoltIcon,
  ArrowTrendingUpIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline'
import euFlag from '../images/eu_flag.png'
import githubIcon from '../images/github.svg'
import notionIcon from '../images/notion.svg'
import slackIcon from '../images/slack.svg'
import { useTranslation } from '../hooks/useTranslation'

const HomePage = () => {
  const { t } = useTranslation();
  // Animation variants
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

  const features = [
    {
      name: t('home.features.webScanning.title'),
      description: t('home.features.webScanning.description'),
      icon: GlobeAltIcon,
    },
    {
      name: t('home.features.pdfAnalysis.title'),
      description: t('home.features.pdfAnalysis.description'),
      icon: DocumentIcon,
    },
    {
      name: t('home.features.api.title'),
      description: t('home.features.api.description'),
      icon: BoltIcon,
    },
    {
      name: t('home.features.integrations.title'),
      description: t('home.features.integrations.description'),
      icon: SparklesIcon,
    },
    {
      name: t('home.features.euCompliance.title'),
      description: t('home.features.euCompliance.description'),
      icon: ShieldCheckIcon,
    },
    {
      name: t('home.features.progressTracking.title'),
      description: t('home.features.progressTracking.description'),
      icon: ChartBarIcon,
    },
  ]

  const legalCards = [
    {
      title: t('home.legal.cards.eaa2025.title'),
      description: t('home.legal.cards.eaa2025.description')
    },
    {
      title: t('home.legal.cards.improvement.title'),
      description: t('home.legal.cards.improvement.description')
    },
    {
      title: t('home.legal.cards.wcag.title'),
      description: t('home.legal.cards.wcag.description')
    },
    {
      title: t('home.legal.cards.developer.title'),
      description: t('home.legal.cards.developer.description')
    }
  ]

  const integrations = [
    {
      name: 'GitHub',
      icon: githubIcon,
      description: t('home.integrations.github.description'),
      features: [t('home.integrations.github.feature1'), t('home.integrations.github.feature2'), t('home.integrations.github.feature3')]
    },
    {
      name: 'Slack',
      icon: slackIcon,
      description: t('home.integrations.slack.description'),
      features: [t('home.integrations.slack.feature1'), t('home.integrations.slack.feature2'), t('home.integrations.slack.feature3')]
    },
    {
      name: 'Notion',
      icon: notionIcon,
      description: t('home.integrations.notion.description'),
      features: [t('home.integrations.notion.feature1'), t('home.integrations.notion.feature2'), t('home.integrations.notion.feature3')]
    }
  ]

  return (
    <div className="bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <section className="relative min-h-[calc(100vh-4rem)] lg:min-h-screen flex items-center overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-hero" />
        
        {/* Decorative elements */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary-400/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-primary-300/10 rounded-full blur-3xl" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="text-center"
          >
            {/* EU Flag Badge */}
            <motion.div variants={itemVariants} className="mb-8 flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-primary-400/20 rounded-full blur-xl scale-150" />
                <img
                  className="relative h-24 w-24 sm:h-28 sm:w-28 rounded-full border-4 border-white dark:border-gray-800 shadow-2xl object-cover"
                  src={euFlag}
                  alt="European Union flag representing EU accessibility compliance"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
              </div>
            </motion.div>

            {/* Main Headline */}
            <motion.h1 
              variants={itemVariants}
              className="text-3xl xs:text-4xl sm:text-5xl lg:text-6xl xl:text-7xl tracking-tight font-extrabold text-gray-900 dark:text-white px-2"
            >
              <span className="block">{t('home.hero.title')}</span>
              <span className="block mt-2 pb-2 bg-gradient-to-r from-primary-500 to-primary-400 bg-clip-text text-transparent leading-tight">
                {t('home.hero.titleHighlight')}
              </span>
            </motion.h1>

            {/* Subtitle */}
            <motion.p 
              variants={itemVariants}
              className="mt-4 sm:mt-6 text-base sm:text-lg md:text-xl lg:text-2xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto leading-relaxed px-4"
            >
              {t('home.hero.subtitle')}{' '}
              <span className="font-semibold text-primary-600 dark:text-primary-400">
                {t('home.hero.subtitleHighlight1')}
              </span>
              , {t('home.hero.subtitlePart2')}{' '}
              <span className="font-semibold text-primary-600 dark:text-primary-400">
                {t('home.hero.subtitleHighlight2')}
              </span>{' '}
              {t('home.hero.subtitlePart3')}
            </motion.p>

            {/* CTA Buttons */}
            <motion.div 
              variants={itemVariants}
              className="mt-8 sm:mt-10 flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4"
            >
              <Link
                to="/scan"
                className="group btn-primary text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-4"
                aria-describedby="web-scan-description"
              >
                <GlobeAltIcon className="h-5 w-5" aria-hidden="true" />
                <span>{t('home.hero.ctaScanWebsite')}</span>
                <ArrowRightIcon className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
              </Link>
              <Link
                to="/pdf-scan"
                className="group btn-secondary text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-4"
                aria-describedby="pdf-scan-description"
              >
                <DocumentIcon className="h-5 w-5" aria-hidden="true" />
                <span>{t('home.hero.ctaScanPDF')}</span>
                <ArrowRightIcon className="h-5 w-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
              </Link>
            </motion.div>

            {/* Hidden descriptions for screen readers */}
            <p id="web-scan-description" className="sr-only">
              {t('home.hero.srWebScan')}
            </p>
            <p id="pdf-scan-description" className="sr-only">
              {t('home.hero.srPDFScan')}
            </p>

            {/* Trust indicators */}
            <motion.div 
              variants={itemVariants}
              className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500 dark:text-gray-400"
            >
              <div className="flex items-center gap-2">
                <ShieldCheckIcon className="h-5 w-5 text-green-500" />
                <span>{t('home.hero.wcagCompliant')}</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-primary-500" />
                <span>{t('home.hero.euReady')}</span>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* SEO & Traffic Section */}
      <section className="section bg-white dark:bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-3xl mx-auto"
          >
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
              <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
              {t('home.seo.badge')}
            </span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight">
              {t('home.seo.title')}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              {t('home.seo.description')}
            </p>
          </motion.div>

          <div className="mt-12 grid gap-8 md:grid-cols-2">
            {/* Study 1: SEMrush/Accessibility.Works */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-2xl p-6 border border-green-200 dark:border-green-700/50"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-xl bg-green-500 text-white">
                  <ArrowTrendingUpIcon className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-3xl font-bold text-green-600 dark:text-green-400">{t('home.seo.study1.stat')}</span>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{t('home.seo.study1.statLabel')}</p>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('home.seo.study1.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-4">
                {t('home.seo.study1.description', { traffic: '23%', keywords: '12%' })}
              </p>
              <a 
                href="https://www.accessibility.works/blog/web-accessibility-roi-seo-traffic-ai-bot-agent-optimization/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 font-medium transition-colors"
              >
                {t('home.seo.study1.link')}
                <ArrowRightIcon className="h-4 w-4 ml-1" />
              </a>
            </motion.div>

            {/* Study 2: Google's 2025 Algorithm */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-700/50"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-xl bg-blue-500 text-white">
                  <MagnifyingGlassIcon className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">{t('home.seo.study2.stat')}</span>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{t('home.seo.study2.statLabel')}</p>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('home.seo.study2.title')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-4">
                {t('home.seo.study2.description', { traffic: '37%' })}
              </p>
              <a 
                href="https://accessibility-test.org/blog/compliance/global-standards/accessibility-boosts-seo-googles-2025-algorithm-update/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
              >
                {t('home.seo.study2.link')}
                <ArrowRightIcon className="h-4 w-4 ml-1" />
              </a>
            </motion.div>
          </div>

          {/* Key Insights */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-8 grid gap-4 sm:grid-cols-3"
          >
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700/50 shadow-soft">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{t('home.seo.insights.coreWebVitals.title')}</h4>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-xs">
                {t('home.seo.insights.coreWebVitals.description')}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700/50 shadow-soft">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{t('home.seo.insights.aiSearch.title')}</h4>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-xs">
                {t('home.seo.insights.aiSearch.description')}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700/50 shadow-soft">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{t('home.seo.insights.bounceRates.title')}</h4>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-xs">
                {t('home.seo.insights.bounceRates.description')}
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section bg-white dark:bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-3xl mx-auto"
          >
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
              {t('home.features.badge')}
            </span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight">
              {t('home.features.title')}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              {t('home.features.description')}
            </p>
          </motion.div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div
                key={feature.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft hover:shadow-soft-lg transition-all duration-300 hover:-translate-y-1 border border-gray-100 dark:border-gray-700/50"
              >
                <div className={`inline-flex items-center justify-center h-12 w-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-lg`}>
                  <feature.icon className="h-6 w-6" aria-hidden="true" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">
                  {feature.name}
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Legal Information Section */}
      <section className="section bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-3xl mx-auto"
          >
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
              {t('home.legal.badge')}
            </span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight">
              {t('home.legal.title')}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              {t('home.legal.description')}
            </p>
          </motion.div>

          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {legalCards.map((card, index) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft border border-gray-100 dark:border-gray-700/50"
              >
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {card.title}
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                  {card.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className="section bg-white dark:bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center max-w-3xl mx-auto"
          >
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
              <BoltIcon className="h-4 w-4 mr-1" />
              {t('home.integrations.badge')}
            </span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight">
              {t('home.integrations.title')}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              {t('home.integrations.description')}
            </p>
          </motion.div>

          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {integrations.map((integration, index) => (
              <motion.div
                key={integration.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-soft border border-gray-100 dark:border-gray-700/50 hover:shadow-soft-lg transition-all duration-300 hover:-translate-y-1"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-white dark:bg-gray-200 border border-gray-200 dark:border-gray-300">
                    <img src={integration.icon} alt={integration.name} className="h-8 w-8" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {integration.name}
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed mb-4">
                  {integration.description}
                </p>
                <ul className="space-y-2">
                  {integration.features.map((feature) => (
                    <li key={feature} className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mt-10 text-center"
          >
            <Link
              to="/integrations"
              className="group inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 font-medium hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
            >
              <span>{t('home.integrations.configureLink')}</span>
              <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Get Started Section */}
      <section className="section bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Developer CTA Box */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/20 dark:to-primary-800/20 border border-primary-200 dark:border-primary-700/50 rounded-2xl p-8 shadow-soft"
          >
            <div className="flex flex-col md:flex-row items-center gap-6">
              <div className="flex-shrink-0 h-16 w-16 rounded-2xl bg-primary-500 flex items-center justify-center">
                <BoltIcon className="h-8 w-8 text-white" aria-hidden="true" />
              </div>
              <div className="flex-1 text-center md:text-left">
                <h4 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {t('home.cta.title')}
                </h4>
                <p className="mt-2 text-gray-600 dark:text-gray-300">
                  {t('home.cta.description')}
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link
                  to="/scan"
                  className="btn-primary px-6 py-3"
                >
                  <span>{t('home.cta.tryFreeScan')}</span>
                  <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
                </Link>
                <Link
                  to="/api"
                  className="btn-secondary px-6 py-3"
                >
                  <span>{t('home.cta.viewApiDocs')}</span>
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

export default HomePage
