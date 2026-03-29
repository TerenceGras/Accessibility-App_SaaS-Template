import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  HomeIcon,
  GlobeAltIcon,
  DocumentIcon,
  FolderIcon,
  LinkIcon,
  CreditCardIcon,
  KeyIcon,
  UserCircleIcon,
  SunIcon,
  MoonIcon,
  ChevronDownIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowRightOnRectangleIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline'
import { useThemeStore } from '../stores/themeStore'
import useAuthStore from '../stores/authStore'
import lumtrailsLogo from '../images/lumtrails_logo.png'
import LoginForm from './LoginForm'
import LanguageSelector from './LanguageSelector'
import { useTranslation } from '../hooks/useTranslation'
import logger from '../utils/logger'

const PRICING_API_URL = import.meta.env.VITE_PRICING_API_URL || ''

const Sidebar = ({ isMobileOpen, setIsMobileOpen }) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { isDarkMode, toggleTheme } = useThemeStore()
  const { user, getIdToken, signOut } = useAuthStore()
  const { t } = useTranslation()
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [scanMenuOpen, setScanMenuOpen] = useState(true)
  const [credits, setCredits] = useState({ web: null, pdf: null })

  // Handle sign out
  const handleSignOut = async () => {
    try {
      await signOut()
      setIsMobileOpen(false)
      navigate('/')
    } catch (error) {
      logger.error('Error signing out:', error)
    }
  }

  // Fetch user credits
  useEffect(() => {
    if (user) {
      fetchCredits()
    } else {
      setCredits({ web: null, pdf: null })
    }
  }, [user])

  // Listen for subscription updates to refresh credits
  useEffect(() => {
    const handleSubscriptionUpdate = () => {
      if (user) {
        fetchCredits()
      }
    }
    
    window.addEventListener('subscription-updated', handleSubscriptionUpdate)
    return () => window.removeEventListener('subscription-updated', handleSubscriptionUpdate)
  }, [user])

  // Listen for credits updates (after scans complete)
  useEffect(() => {
    const handleCreditsUpdate = () => {
      if (user) {
        fetchCredits()
      }
    }
    
    window.addEventListener('credits-updated', handleCreditsUpdate)
    return () => window.removeEventListener('credits-updated', handleCreditsUpdate)
  }, [user])

  const fetchCredits = async () => {
    try {
      const token = await getIdToken()
      const response = await fetch(`${PRICING_API_URL}/subscription`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setCredits({
          web: data.subscription?.web_scan_credits ?? 0,
          pdf: data.subscription?.pdf_scan_credits ?? 0
        })
      }
    } catch (error) {
      logger.error('Error fetching credits:', error)
    }
  }

  // Navigation items organized into groups
  const mainNavItems = [
    { name: t('sidebar.home'), href: '/', icon: HomeIcon }
  ]

  const scanNavItems = [
    { name: t('sidebar.scanWebsite'), href: '/scan', icon: GlobeAltIcon },
    { name: t('sidebar.scanPDF'), href: '/pdf-scan', icon: DocumentIcon },
    ...(user ? [{ name: t('sidebar.myScans'), href: '/my-scans', icon: FolderIcon }] : [])
  ]

  const toolsNavItems = [
    { name: t('sidebar.api'), href: '/api', icon: KeyIcon },
    ...(user ? [{ name: t('sidebar.integrations'), href: '/integrations', icon: LinkIcon }] : [])
  ]

  const accountNavItems = [
    { name: t('sidebar.pricing'), href: '/pricing', icon: CreditCardIcon },
    { name: t('sidebar.faq'), href: '/faq', icon: QuestionMarkCircleIcon },
    ...(user ? [{ name: t('sidebar.profile'), href: '/profile', icon: UserCircleIcon }] : [])
  ]

  const isActive = (href) => location.pathname === href
  const isScanActive = scanNavItems.some(item => location.pathname === item.href)

  const NavLink = ({ item, compact = false }) => (
    <Link
      to={item.href}
      onClick={() => setIsMobileOpen(false)}
      className={`
        group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
        transition-all duration-200 ease-out
        ${isActive(item.href)
          ? 'bg-primary-400/10 text-primary-500 dark:text-primary-400 shadow-sm'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800/50'
        }
      `}
      aria-current={isActive(item.href) ? 'page' : undefined}
    >
      <item.icon 
        className={`
          h-5 w-5 flex-shrink-0 transition-colors duration-200
          ${isActive(item.href) 
            ? 'text-primary-500 dark:text-primary-400' 
            : 'text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300'
          }
        `} 
        aria-hidden="true" 
      />
      {!compact && <span>{item.name}</span>}
    </Link>
  )

  const NavGroup = ({ title, items, collapsible = false, isOpen = true, onToggle }) => {
    if (items.length === 0) return null
    
    return (
      <div className="space-y-1">
        {title && (
          <button
            onClick={collapsible ? onToggle : undefined}
            className={`
              w-full flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wider
              text-gray-400 dark:text-gray-500
              ${collapsible ? 'hover:text-gray-600 dark:hover:text-gray-400 cursor-pointer' : 'cursor-default'}
            `}
          >
            <span>{title}</span>
            {collapsible && (
              <ChevronDownIcon 
                className={`h-4 w-4 transition-transform duration-200 ${isOpen ? 'rotate-0' : '-rotate-90'}`} 
              />
            )}
          </button>
        )}
        <AnimatePresence initial={false}>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: 'easeInOut' }}
              className="overflow-hidden"
            >
              <div className="space-y-1">
                {items.map((item) => (
                  <NavLink key={item.href} item={item} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-200 dark:border-gray-700/50">
        <Link
          to="/"
          onClick={() => setIsMobileOpen(false)}
          className="flex items-center gap-3 focus:outline-none focus:ring-2 focus:ring-primary-400 rounded-lg"
          aria-label={t('accessibility.homepage')}
        >
          <div className="relative">
            <img
              className="h-9 w-9"
              src={lumtrailsLogo}
              alt=""
              onError={(e) => {
                e.target.style.display = 'none'
              }}
            />
            <div className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-green-400 rounded-full border-2 border-white dark:border-gray-900" />
          </div>
          <div>
            <span className="text-lg font-bold text-gray-900 dark:text-white">LumTrails</span>
            <p className="text-[10px] text-gray-400 dark:text-gray-500 -mt-0.5">{t('sidebar.accessibilityPlatform')}</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6" aria-label={t('accessibility.mainNavigation')}>
        <NavGroup items={mainNavItems} />
        
        <NavGroup 
          title={t('sidebar.scans')} 
          items={scanNavItems}
          collapsible={true}
          isOpen={scanMenuOpen || isScanActive}
          onToggle={() => setScanMenuOpen(!scanMenuOpen)}
        />
        
        {toolsNavItems.length > 0 && (
          <NavGroup title={t('sidebar.tools')} items={toolsNavItems} />
        )}
        
        <NavGroup title={t('sidebar.account')} items={accountNavItems} />
      </nav>

      {/* Bottom section - Theme & User */}
      <div className="border-t border-gray-200 dark:border-gray-700/50 p-4 space-y-3">
        {/* Language Selector */}
        <LanguageSelector />

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
            text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white 
            hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-all duration-200"
          aria-label={isDarkMode ? t('sidebar.switchToLightMode') : t('sidebar.switchToDarkMode')}
        >
          {isDarkMode ? (
            <>
              <SunIcon className="h-5 w-5 text-amber-400" aria-hidden="true" />
              <span>{t('sidebar.lightMode')}</span>
            </>
          ) : (
            <>
              <MoonIcon className="h-5 w-5 text-indigo-400" aria-hidden="true" />
              <span>{t('sidebar.darkMode')}</span>
            </>
          )}
        </button>

        {/* Credits Display */}
        {user && credits.web !== null && (
          <div className="px-3 py-2.5">
            <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <GlobeAltIcon className="h-4 w-4 text-blue-500" aria-hidden="true" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">{t('sidebar.webCredits')}</span>
                </div>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {credits.web?.toLocaleString() ?? 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DocumentIcon className="h-4 w-4 text-purple-500" aria-hidden="true" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">{t('sidebar.pdfCredits')}</span>
                </div>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {credits.pdf?.toLocaleString() ?? 0}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* User Section */}
        {user ? (
          <div className="space-y-2">
            <Link
              to="/profile"
              onClick={() => setIsMobileOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl
                hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-all duration-200"
            >
              <div className="flex-shrink-0">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={`${user.name || user.email}'s profile`}
                    className="h-9 w-9 rounded-full ring-2 ring-gray-200 dark:ring-gray-700"
                  />
                ) : (
                  <div className="h-9 w-9 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-sm font-semibold ring-2 ring-gray-200 dark:ring-gray-700">
                    {user.name?.charAt(0) || user.email?.charAt(0).toUpperCase() || 'U'}
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user.name || 'User'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user.email}
                </p>
              </div>
            </Link>
            
            {/* Sign Out Button */}
            <button
              onClick={handleSignOut}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
                text-white bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700
                transition-all duration-200 shadow-sm"
              aria-label={t('common.signOut')}
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" aria-hidden="true" />
              <span>{t('common.signOut')}</span>
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowLoginForm(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 
              bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700
              text-white text-sm font-semibold rounded-xl shadow-lg shadow-primary-500/25
              transition-all duration-200 hover:shadow-xl hover:shadow-primary-500/30 hover:-translate-y-0.5"
          >
            <UserCircleIcon className="h-5 w-5" aria-hidden="true" />
            <span>{t('auth.signIn')}</span>
          </button>
        )}
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop Sidebar */}
      <aside 
        className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 
          bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
          shadow-sm z-30"
        aria-label={t('accessibility.sidebarNavigation')}
      >
        <SidebarContent />
      </aside>

      {/* Mobile Header Bar */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-40 
        bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl 
        border-b border-gray-200 dark:border-gray-800 h-16"
        aria-label={t('accessibility.mobileNavigation')}>
        <div className="flex items-center justify-between h-full px-4">
          <Link
            to="/"
            className="flex items-center gap-2"
            aria-label={t('accessibility.homepage')}
          >
            <img className="h-8 w-8" src={lumtrailsLogo} alt="" />
            <span className="text-lg font-bold text-gray-900 dark:text-white">LumTrails</span>
          </Link>
          
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 
                dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label={isDarkMode ? t('sidebar.switchToLightMode') : t('sidebar.switchToDarkMode')}
            >
              {isDarkMode ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>
            
            <button
              onClick={() => setIsMobileOpen(true)}
              className="p-2 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 
                dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label={t('sidebar.openMenu')}
              aria-expanded={isMobileOpen}
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-40 lg:hidden"
              onClick={() => setIsMobileOpen(false)}
              aria-hidden="true"
            />
            
            {/* Drawer */}
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-80 max-w-[85vw] z-50 lg:hidden
                bg-white dark:bg-gray-900 shadow-2xl"
              aria-label={t('accessibility.mobileNavigation')}
            >
              {/* Close Button */}
              <button
                onClick={() => setIsMobileOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-lg text-gray-400 
                  hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 
                  dark:hover:bg-gray-800 transition-colors z-10"
                aria-label={t('sidebar.closeMenu')}
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
              
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Login Modal - Rendered outside sidebar containers to avoid z-index/containment issues */}
      <LoginForm isOpen={showLoginForm} onClose={() => setShowLoginForm(false)} />
    </>
  )
}

export default Sidebar
