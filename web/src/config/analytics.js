/**
 * Google Analytics 4 Configuration for LumTrails
 * 
 * Uses essential cookies only (no consent banner required):
 * - IP anonymization enabled
 * - No advertising features
 * - No user-ID tracking across devices
 * - Analytics storage set to 'denied' by default (uses sessionStorage)
 * 
 * This configuration is GDPR-compliant for essential analytics.
 */

// GA4 Measurement ID - Only used in production
const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;

// Check if we're in production
const isProduction = import.meta.env.VITE_ENVIRONMENT === 'production';

/**
 * Initialize Google Analytics
 * Only runs in production environment
 */
export function initializeAnalytics() {
  if (!isProduction || !GA_MEASUREMENT_ID) {
    console.log('[Analytics] Skipping - not in production or no measurement ID');
    return;
  }

  // Load gtag.js script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  // Initialize dataLayer and gtag function
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;

  // Configure for essential cookies only (no consent required)
  gtag('consent', 'default', {
    'analytics_storage': 'denied',  // Don't store analytics cookies
    'ad_storage': 'denied',         // No advertising cookies
    'wait_for_update': 500
  });

  gtag('js', new Date());

  // Configure GA4 with privacy-focused settings
  gtag('config', GA_MEASUREMENT_ID, {
    'anonymize_ip': true,           // Anonymize IP addresses
    'allow_google_signals': false,  // No Google signals
    'allow_ad_personalization_signals': false,  // No ad personalization
    'send_page_view': true,
    // Use session storage instead of cookies for client ID
    'client_storage': 'none',
    // Cookie settings for essential-only mode
    'cookie_flags': 'SameSite=Strict;Secure',
    'cookie_expires': 0  // Session cookie only
  });

  console.log('[Analytics] Google Analytics initialized (essential cookies only)');
}

/**
 * Track a page view
 * @param {string} pagePath - The page path to track
 * @param {string} pageTitle - The page title
 */
export function trackPageView(pagePath, pageTitle) {
  if (!isProduction || !window.gtag) return;
  
  window.gtag('event', 'page_view', {
    page_path: pagePath,
    page_title: pageTitle
  });
}

/**
 * Track a custom event
 * @param {string} eventName - The event name
 * @param {object} parameters - Event parameters
 */
export function trackEvent(eventName, parameters = {}) {
  if (!isProduction || !window.gtag) return;
  
  window.gtag('event', eventName, parameters);
}

export default {
  initializeAnalytics,
  trackPageView,
  trackEvent
};
