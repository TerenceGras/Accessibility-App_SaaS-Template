import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { SunIcon, MoonIcon, UserIcon, ChevronDownIcon } from '@heroicons/react/24/outline'
import { useThemeStore } from '../stores/themeStore'
import useAuthStore from '../stores/authStore'
import lumtrailsLogo from '../images/lumtrails_logo.png'
import LoginForm from './LoginForm'
import UserProfile from './UserProfile'
import { useTranslation } from '../hooks/useTranslation'

const Header = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const { isDarkMode, toggleTheme } = useThemeStore()
  const { user } = useAuthStore()
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [showScanDropdown, setShowScanDropdown] = useState(false)

  const navigation = [
    { name: t('sidebar.home'), href: '/', current: location.pathname === '/' },
    // API is accessible to all users (docs are public, key creation requires login)
    { name: t('sidebar.api'), href: '/api', current: location.pathname === '/api' },
    // Only show Integrations if user is logged in
    ...(user ? [
      { name: t('sidebar.integrations'), href: '/integrations', current: location.pathname === '/integrations' }
    ] : []),
    { name: t('sidebar.pricing'), href: '/pricing', current: location.pathname === '/pricing' }
  ]

  const scanMenuItems = [
    { name: t('sidebar.scanWebsite'), href: '/scan', current: location.pathname === '/scan' },
    { name: t('sidebar.scanPDF'), href: '/pdf-scan', current: location.pathname === '/pdf-scan' },
    // Only show My Scans if user is logged in
    ...(user ? [
      { name: t('sidebar.myScans'), href: '/my-scans', current: location.pathname === '/my-scans' }
    ] : [])
  ]

  const isScanActive = scanMenuItems.some(item => item.current)

  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label={t('accessibility.mainNavigation')}>
        <div className="flex items-center h-16">
          {/* Logo - positioned more to the left */}
          <div className="flex items-center mr-8">
            <Link
              to="/"
              className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 rounded-lg p-1"
              aria-label={t('accessibility.homepage')}
            >
              <img
                className="h-8 w-8"
                src={lumtrailsLogo}
                alt=""
                onError={(e) => {
                  // If logo fails to load, show a fallback
                  e.target.style.display = 'none'
                  e.target.nextSibling.style.marginLeft = '0'
                }}
              />
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                LumTrails
              </span>
            </Link>
          </div>

          {/* Spacer to push navigation to the right */}
          <div className="flex-grow"></div>

          {/* Navigation Links - positioned more to the right */}
          <div className="flex items-center space-x-8">
            <div className="hidden md:block">
              <div className="flex items-center space-x-4">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 ${
                      item.current
                        ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700'
                    }`}
                    aria-current={item.current ? 'page' : undefined}
                  >
                    {item.name}
                  </Link>
                ))}
                
                {/* Scan Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setShowScanDropdown(!showScanDropdown)}
                    onBlur={() => setTimeout(() => setShowScanDropdown(false), 200)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 inline-flex items-center ${
                      isScanActive
                        ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700'
                    }`}
                  >
                    Scan
                    <ChevronDownIcon className="ml-1 h-4 w-4" aria-hidden="true" />
                  </button>
                  
                  {showScanDropdown && (
                    <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 z-50">
                      <div className="py-1" role="menu">
                        {scanMenuItems.map((item) => (
                          <Link
                            key={item.name}
                            to={item.href}
                            className={`block px-4 py-2 text-sm transition-colors duration-200 ${
                              item.current
                                ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                                : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                            }`}
                            role="menuitem"
                          >
                            {item.name}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 transition-colors duration-200"
              aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? (
                <SunIcon className="h-5 w-5" aria-hidden="true" />
              ) : (
                <MoonIcon className="h-5 w-5" aria-hidden="true" />
              )}
            </button>

            {/* Authentication */}
            {user ? (
              <UserProfile />
            ) : (
              <button
                onClick={() => setShowLoginForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
              >
                <UserIcon className="h-4 w-4 mr-2" aria-hidden="true" />
                {t('auth.signIn')}
              </button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <div className="flex items-center space-x-2">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-400 ${
                    item.current
                      ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                      : 'text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
                  }`}
                  aria-current={item.current ? 'page' : undefined}
                >
                  {item.name}
                </Link>
              ))}
              
              {/* Mobile Scan Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowScanDropdown(!showScanDropdown)}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-400 inline-flex items-center ${
                    isScanActive
                      ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                      : 'text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
                  }`}
                >
                  Scan
                  <ChevronDownIcon className="ml-1 h-3 w-3" aria-hidden="true" />
                </button>
                
                {showScanDropdown && (
                  <div className="absolute right-0 mt-2 w-40 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 z-50">
                    <div className="py-1" role="menu">
                      {scanMenuItems.map((item) => (
                        <Link
                          key={item.name}
                          to={item.href}
                          className={`block px-3 py-2 text-xs transition-colors duration-200 ${
                            item.current
                              ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300'
                              : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                          }`}
                          role="menuitem"
                        >
                          {item.name === 'Scan Website' ? 'Website' : item.name === 'Scan PDF' ? 'PDF' : item.name}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Login Form Modal */}
      <LoginForm isOpen={showLoginForm} onClose={() => setShowLoginForm(false)} />
    </header>
  )
}

export default Header
