import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/authStore';

/**
 * RequireVerifiedEmail - A guard component that ensures users have verified their email
 * 
 * This component wraps protected routes and redirects unverified users to the
 * email verification page. It allows:
 * - Unauthenticated users (they'll be prompted to sign in when needed)
 * - Users who signed in with Google (email is automatically verified)
 * - Users with verified email addresses
 * 
 * Blocks:
 * - Users who signed up with email/password but haven't verified their email
 */
const RequireVerifiedEmail = ({ children }) => {
  const { user, loading } = useAuthStore();
  const location = useLocation();

  // Still loading auth state - don't redirect yet
  if (loading) {
    return null;
  }

  // No user logged in - allow access (they'll be prompted to sign in when needed)
  if (!user) {
    return children;
  }

  // User is logged in - check if email is verified
  // email_verified comes from the backend response
  if (user.email_verified === false) {
    // Redirect to verification page with email
    const verifyUrl = `/verify-email?email=${encodeURIComponent(user.email || '')}`;
    
    // Don't redirect if already on verification page
    if (location.pathname === '/verify-email') {
      return children;
    }
    
    return <Navigate to={verifyUrl} replace />;
  }

  // Email is verified or user signed in with Google - allow access
  return children;
};

export default RequireVerifiedEmail;
