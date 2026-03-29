import React from 'react'
import { useTranslation } from '../../hooks/useTranslation'

const IntroductionBanner = () => {
  const { t } = useTranslation()
  
  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
      <h2 className="text-xl font-semibold text-blue-900 dark:text-blue-100 mb-4">{t('integrations.intro.title')}</h2>
      <p className="text-blue-700 dark:text-blue-300">
        {t('integrations.intro.description')}
      </p>
    </div>
  )
}

export default IntroductionBanner
