// Authentication Configuration for LumTrails
// Environment-specific settings

// Allowed emails for DEV environment only
// In production, all authenticated users are allowed
// Configure via DEV_WHITELIST_EMAILS env var or edit this list
const ALLOWED_DEV_EMAILS = (import.meta.env.VITE_DEV_WHITELIST_EMAILS || "").split(",").filter(Boolean).map(e => e.trim().toLowerCase());

// Check if we're in DEV environment
const isDev = import.meta.env.MODE === 'development' || import.meta.env.VITE_ENVIRONMENT === 'development';

/**
 * Check if a user email is authorized to access the application
 * @param {string} email - The user's email address
 * @returns {boolean} - True if authorized, false otherwise
 */
export const isEmailAuthorized = (email) => {
  // In production, everyone is allowed
  if (!isDev) {
    return true;
  }
  
  // In DEV, only whitelisted emails are allowed
  return ALLOWED_DEV_EMAILS.includes(email?.toLowerCase());
};

/**
 * Get the list of allowed emails (for display purposes in error messages)
 * @returns {string[]} - Array of allowed email addresses
 */
export const getAllowedEmails = () => {
  return ALLOWED_DEV_EMAILS;
};

/**
 * Check if we're running in DEV environment
 * @returns {boolean}
 */
export const isDevEnvironment = () => {
  return isDev;
};

export default {
  isEmailAuthorized,
  getAllowedEmails,
  isDevEnvironment,
};
