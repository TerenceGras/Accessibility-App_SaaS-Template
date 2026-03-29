import React from 'react'
import { useTranslation } from '../hooks/useTranslation'

const LoadingSpinner = ({ className = 'h-8 w-8' }) => {
  const { t } = useTranslation()
  
  return (
    <div
      className={`animate-spin rounded-full border-2 border-gray-300 border-t-primary-400 ${className}`}
      role="status"
      aria-label={t('accessibility.loading')}
    >
      <span className="sr-only">{t('common.loading')}</span>
    </div>
  )
}

export default LoadingSpinner
