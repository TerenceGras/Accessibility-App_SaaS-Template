import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from '../../hooks/useTranslation'

const AuthenticationRequired = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('auth.authenticationRequired')}</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">{t('integrations.signInToAccess')}</p>
        <button
          onClick={() => navigate('/login')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium"
        >
          {t('common.signIn')}
        </button>
      </div>
    </div>
  )
}

export default AuthenticationRequired
