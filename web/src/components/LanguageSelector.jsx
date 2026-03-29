import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronUpIcon } from '@heroicons/react/24/outline'
import { useTranslation, SUPPORTED_LANGUAGES } from '../hooks/useTranslation'

// Flag components using SVG for crisp rendering with proper accessibility
const FlagIcon = ({ countryCode, className = "w-5 h-5", lang }) => {
  const flagData = {
    en: { name: 'United Kingdom', svg: (
      <svg viewBox="0 0 60 30" className={className} role="img" aria-label="United Kingdom flag">
        <title>United Kingdom flag</title>
        <clipPath id="s-en">
          <path d="M0,0 v30 h60 v-30 z"/>
        </clipPath>
        <clipPath id="t-en">
          <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/>
        </clipPath>
        <g clipPath="url(#s-en)">
          <path d="M0,0 v30 h60 v-30 z" fill="#012169"/>
          <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6"/>
          <path d="M0,0 L60,30 M60,0 L0,30" clipPath="url(#t-en)" stroke="#C8102E" strokeWidth="4"/>
          <path d="M30,0 v30 M0,15 h60" stroke="#fff" strokeWidth="10"/>
          <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" strokeWidth="6"/>
        </g>
      </svg>
    )},
    fr: { name: 'France', svg: (
      <svg viewBox="0 0 3 2" className={className} role="img" aria-label="France flag">
        <title>France flag</title>
        <rect width="3" height="2" fill="#ED2939"/>
        <rect width="2" height="2" fill="#fff"/>
        <rect width="1" height="2" fill="#002395"/>
      </svg>
    )},
    de: { name: 'Germany', svg: (
      <svg viewBox="0 0 5 3" className={className} role="img" aria-label="Germany flag">
        <title>Germany flag</title>
        <rect width="5" height="3" fill="#FFCC00"/>
        <rect width="5" height="2" fill="#DD0000"/>
        <rect width="5" height="1" fill="#000"/>
      </svg>
    )},
    it: { name: 'Italy', svg: (
      <svg viewBox="0 0 3 2" className={className} role="img" aria-label="Italy flag">
        <title>Italy flag</title>
        <rect width="3" height="2" fill="#CE2B37"/>
        <rect width="2" height="2" fill="#fff"/>
        <rect width="1" height="2" fill="#009246"/>
      </svg>
    )},
    es: { name: 'Spain', svg: (
      <svg viewBox="0 0 750 500" className={className} role="img" aria-label="Spain flag">
        <title>Spain flag</title>
        <rect width="750" height="500" fill="#c60b1e"/>
        <rect width="750" height="250" y="125" fill="#ffc400"/>
      </svg>
    )},
    pt: { name: 'Portugal', svg: (
      <svg viewBox="0 0 600 400" className={className} role="img" aria-label="Portugal flag">
        <title>Portugal flag</title>
        <rect width="600" height="400" fill="#FF0000"/>
        <rect width="240" height="400" fill="#006600"/>
        <circle cx="240" cy="200" r="64" fill="#FFCC00"/>
      </svg>
    )}
  }

  const flag = flagData[countryCode] || flagData.en

  return (
    <div 
      className={`${className} rounded-sm overflow-hidden shadow-sm ring-1 ring-black/10 flex-shrink-0`}
      role="img"
      aria-label={`${flag.name} flag`}
    >
      {flag.svg}
    </div>
  )
}

const LanguageSelector = ({ compact = false }) => {
  const { currentLanguage, changeLanguage, t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const dropdownRef = useRef(null)
  const buttonRef = useRef(null)
  const menuRef = useRef(null)

  const languageCodes = Object.keys(SUPPORTED_LANGUAGES)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
        setFocusedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Keyboard navigation
  const handleKeyDown = useCallback((event) => {
    // Don't intercept keyboard events when user is typing in an input or textarea
    const activeElement = document.activeElement
    const isTypingInInput = activeElement && (
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.isContentEditable
    )
    
    if (isTypingInInput) {
      return // Let the input handle the keypress
    }
    
    if (!isOpen) {
      if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        event.preventDefault()
        setIsOpen(true)
        setFocusedIndex(languageCodes.indexOf(currentLanguage))
      }
      return
    }

    switch (event.key) {
      case 'Escape':
        event.preventDefault()
        setIsOpen(false)
        setFocusedIndex(-1)
        buttonRef.current?.focus()
        break
      case 'ArrowUp':
        event.preventDefault()
        setFocusedIndex(prev => (prev <= 0 ? languageCodes.length - 1 : prev - 1))
        break
      case 'ArrowDown':
        event.preventDefault()
        setFocusedIndex(prev => (prev >= languageCodes.length - 1 ? 0 : prev + 1))
        break
      case 'Enter':
      case ' ':
        event.preventDefault()
        if (focusedIndex >= 0) {
          handleLanguageChange(languageCodes[focusedIndex])
        }
        break
      case 'Tab':
        setIsOpen(false)
        setFocusedIndex(-1)
        break
      case 'Home':
        event.preventDefault()
        setFocusedIndex(0)
        break
      case 'End':
        event.preventDefault()
        setFocusedIndex(languageCodes.length - 1)
        break
      default:
        break
    }
  }, [isOpen, focusedIndex, languageCodes, currentLanguage])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Focus management for menu items
  useEffect(() => {
    if (isOpen && focusedIndex >= 0 && menuRef.current) {
      const buttons = menuRef.current.querySelectorAll('button[role="option"]')
      buttons[focusedIndex]?.focus()
    }
  }, [focusedIndex, isOpen])

  const handleLanguageChange = (langCode) => {
    changeLanguage(langCode)
    setIsOpen(false)
    setFocusedIndex(-1)
    buttonRef.current?.focus()
  }

  const currentLang = SUPPORTED_LANGUAGES[currentLanguage]

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        ref={buttonRef}
        onClick={() => {
          setIsOpen(!isOpen)
          if (!isOpen) {
            setFocusedIndex(languageCodes.indexOf(currentLanguage))
          }
        }}
        className={`
          flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full
          text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white 
          hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 
          dark:focus:ring-offset-gray-900
        `}
        aria-label={`${t('language.select')}: ${currentLang?.nativeName || 'English'}`}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls="language-menu"
        id="language-selector-button"
      >
        <FlagIcon countryCode={currentLanguage} className="w-5 h-5" />
        {!compact && (
          <>
            <span className="flex-1 text-left truncate">{currentLang?.nativeName || 'English'}</span>
            <ChevronUpIcon 
              className={`h-4 w-4 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
              aria-hidden="true"
            />
          </>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={menuRef}
            id="language-menu"
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className={`
              absolute z-50 bottom-full mb-2 py-2 rounded-xl shadow-lg
              bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
              max-h-[60vh] overflow-y-auto
              ${compact ? 'left-0 w-48' : 'left-0 right-0 min-w-[200px]'}
            `}
            role="listbox"
            aria-labelledby="language-selector-button"
            aria-activedescendant={focusedIndex >= 0 ? `language-option-${languageCodes[focusedIndex]}` : undefined}
          >
            {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang], index) => (
              <button
                key={code}
                id={`language-option-${code}`}
                onClick={() => handleLanguageChange(code)}
                onMouseEnter={() => setFocusedIndex(index)}
                className={`
                  w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors
                  focus:outline-none
                  ${currentLanguage === code 
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400' 
                    : focusedIndex === index
                      ? 'bg-gray-100 dark:bg-gray-700/50 text-gray-900 dark:text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                  }
                `}
                role="option"
                aria-selected={currentLanguage === code}
                tabIndex={-1}
              >
                <FlagIcon countryCode={code} className="w-5 h-5" />
                <span className="flex-1 text-left font-medium">{lang.nativeName}</span>
                {currentLanguage === code && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0"
                    aria-hidden="true"
                  />
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default LanguageSelector
