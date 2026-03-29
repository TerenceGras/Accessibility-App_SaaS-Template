import React from 'react'
import { motion } from 'framer-motion'

/**
 * PageContainer - A consistent wrapper for all page content
 * Provides consistent spacing, max-width, and optional page header
 */
const PageContainer = ({ 
  children, 
  title, 
  description, 
  action,
  fullWidth = false,
  noPadding = false,
  className = ''
}) => {
  return (
    <div 
      className={`
        min-h-screen bg-gray-50 dark:bg-gray-900
        ${noPadding ? '' : 'py-6 sm:py-8 lg:py-10'}
      `}
    >
      <div 
        className={`
          ${fullWidth ? 'w-full' : 'max-w-7xl mx-auto'}
          ${noPadding ? '' : 'px-4 sm:px-6 lg:px-8'}
          ${className}
        `}
      >
        {/* Page Header */}
        {(title || description || action) && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="mb-8"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                {title && (
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
                    {title}
                  </h1>
                )}
                {description && (
                  <p className="mt-1.5 text-base text-gray-500 dark:text-gray-400 max-w-2xl">
                    {description}
                  </p>
                )}
              </div>
              {action && (
                <div className="flex-shrink-0">
                  {action}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Page Content */}
        {children}
      </div>
    </div>
  )
}

/**
 * PageSection - A styled section within a page
 */
export const PageSection = ({ 
  children, 
  title, 
  description,
  className = '',
  cardStyle = true 
}) => {
  const Wrapper = cardStyle ? 'div' : React.Fragment
  const wrapperProps = cardStyle ? {
    className: `bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700/50 overflow-hidden ${className}`
  } : {}

  return (
    <Wrapper {...wrapperProps}>
      {(title || description) && (
        <div className={cardStyle ? 'px-6 py-5 border-b border-gray-200 dark:border-gray-700/50' : 'mb-4'}>
          {title && (
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {title}
            </h2>
          )}
          {description && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {description}
            </p>
          )}
        </div>
      )}
      <div className={cardStyle ? 'p-6' : ''}>
        {children}
      </div>
    </Wrapper>
  )
}

/**
 * PageCard - A premium styled card component
 */
export const PageCard = ({ 
  children, 
  className = '', 
  hover = false,
  onClick,
  padding = 'normal'
}) => {
  const paddingClasses = {
    none: '',
    small: 'p-4',
    normal: 'p-6',
    large: 'p-8'
  }

  const Component = onClick ? 'button' : 'div'

  return (
    <Component
      onClick={onClick}
      className={`
        bg-white dark:bg-gray-800 rounded-2xl 
        shadow-sm border border-gray-200 dark:border-gray-700/50
        ${hover ? 'hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 hover:-translate-y-0.5 cursor-pointer' : ''}
        transition-all duration-200 ease-out
        ${paddingClasses[padding]}
        ${onClick ? 'w-full text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900' : ''}
        ${className}
      `}
    >
      {children}
    </Component>
  )
}

/**
 * PageGrid - Responsive grid layout
 */
export const PageGrid = ({ 
  children, 
  cols = 3,
  gap = 'normal',
  className = '' 
}) => {
  const colClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
  }

  const gapClasses = {
    small: 'gap-4',
    normal: 'gap-6',
    large: 'gap-8'
  }

  return (
    <div className={`grid ${colClasses[cols]} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  )
}

export default PageContainer
