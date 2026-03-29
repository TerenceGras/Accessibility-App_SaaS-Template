/**
 * Centralized logger utility for production-safe logging
 * Prevents sensitive information from leaking to browser console in production
 * All console output is completely silenced in production environment
 */

const isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';

const logger = {
  /**
   * Log debug information (development only)
   */
  debug: (...args) => {
    if (isDevelopment) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Log general information (development only)
   */
  info: (...args) => {
    if (isDevelopment) {
      console.info('[INFO]', ...args);
    }
  },

  /**
   * Log warnings (development only)
   */
  warn: (...args) => {
    if (isDevelopment) {
      console.warn('[WARN]', ...args);
    }
    // Silent in production - no console output
  },

  /**
   * Log errors (development only)
   */
  error: (...args) => {
    if (isDevelopment) {
      console.error('[ERROR]', ...args);
    }
    // Silent in production - no console output
  },

  /**
   * Log with custom level (development only)
   */
  log: (...args) => {
    if (isDevelopment) {
      console.log(...args);
    }
  }
};

export default logger;
