import React from 'react'
import { motion } from 'framer-motion'
import { useLocation } from 'react-router-dom'

/**
 * PageTransition - Wraps page content with smooth enter/exit animations
 * Respects prefers-reduced-motion for accessibility
 */
const PageTransition = ({ children }) => {
  const location = useLocation()
  
  // Check for reduced motion preference
  const prefersReducedMotion = 
    typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (prefersReducedMotion) {
    return <>{children}</>
  }

  return (
    <motion.div
      key={location.pathname}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{
        type: 'tween',
        ease: 'easeOut',
        duration: 0.2
      }}
    >
      {children}
    </motion.div>
  )
}

/**
 * FadeIn - Simple fade in animation wrapper
 */
export const FadeIn = ({ 
  children, 
  delay = 0, 
  duration = 0.4,
  className = '' 
}) => {
  const prefersReducedMotion = 
    typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay, duration, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * SlideUp - Slide up animation wrapper
 */
export const SlideUp = ({ 
  children, 
  delay = 0, 
  duration = 0.4,
  distance = 20,
  className = '' 
}) => {
  const prefersReducedMotion = 
    typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: distance }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * StaggerContainer - Container for staggered children animations
 */
export const StaggerContainer = ({ 
  children, 
  staggerDelay = 0.1,
  className = '' 
}) => {
  const prefersReducedMotion = 
    typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay
          }
        }
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * StaggerItem - Item to be used inside StaggerContainer
 */
export const StaggerItem = ({ children, className = '' }) => {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { 
          opacity: 1, 
          y: 0,
          transition: { duration: 0.4, ease: 'easeOut' }
        }
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * ScaleIn - Scale in animation wrapper
 */
export const ScaleIn = ({ 
  children, 
  delay = 0, 
  duration = 0.3,
  className = '' 
}) => {
  const prefersReducedMotion = 
    typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export default PageTransition
