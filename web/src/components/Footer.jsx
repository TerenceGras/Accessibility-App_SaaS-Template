import React from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from '../hooks/useTranslation'
import lumtrailsLogo from '../images/lumtrails_logo.png'

const Footer = () => {
  const { t } = useTranslation()
  
  const legalLinks = [
    { name: t('footer.privacyPolicy'), href: '/privacy' },
    { name: t('footer.termsOfService'), href: '/terms' },
    { name: t('footer.cookiePolicy'), href: '/cookies' },
    { name: t('footer.legalNotice'), href: '/legal' },
    { name: t('footer.accessibility'), href: '/accessibility' },
    { name: t('footer.dpa'), href: '/dpa' },
  ]

  const companyLinks = [
    { name: t('nav.contact'), href: '/contact' },
    { name: t('nav.pricing'), href: '/pricing' },
    { name: t('nav.api'), href: '/api' },
    { name: t('nav.faq'), href: '/faq' },
    { name: t('footer.affiliates'), href: '/affiliates' },
  ]

  return (
    <footer className="bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link to="/" className="flex items-center space-x-3 mb-4" aria-label={t('accessibility.homepage')}>
              <img
                className="h-8 w-8"
                src={lumtrailsLogo}
                alt=""
                onError={(e) => {
                  e.target.style.display = 'none'
                }}
              />
              <span className="text-lg font-bold text-gray-900 dark:text-white">LumTrails</span>
            </Link>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              {t('footer.description')}
            </p>
            <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
              <span className="inline-flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-1.5"></span>
                {t('footer.wcagCompliant')}
              </span>
            </div>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              {t('footer.legal')}
            </h3>
            <ul className="space-y-3">
              {legalLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              {t('footer.company')}
            </h3>
            <ul className="space-y-3">
              {companyLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              {t('footer.contact')}
            </h3>
            <ul className="space-y-3 text-sm text-gray-500 dark:text-gray-400">
              <li>
                <a 
                  href="mailto:hello@your-domain.com" 
                  className="hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
                >
                  hello@your-domain.com
                </a>
              </li>
              <li>
                YOUR_STREET_ADDRESS<br />
                YOUR_CITY_ZIP, YOUR_COUNTRY
              </li>
              <li className="text-xs">
                SIRET: YOUR_SIRET_NUMBER
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              © {new Date().getFullYear()} LumTrails. {t('footer.allRightsReserved')}
            </p>
            
            <div className="flex items-center space-x-6 text-xs text-gray-500 dark:text-gray-400">
              <span>{t('footer.euReady')}</span>
              <span>•</span>
              <span>{t('footer.madeInFrance')} 🇫🇷</span>
            </div>
          </div>
          
          <p className="mt-4 text-xs text-gray-600 dark:text-gray-400 text-center">
            {t('footer.disclaimer')}
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
