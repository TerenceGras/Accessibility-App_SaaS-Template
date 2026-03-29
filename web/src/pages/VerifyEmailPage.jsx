import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { EnvelopeIcon, ArrowPathIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import useAuthStore from '../stores/authStore';
import { useTranslation } from '../hooks/useTranslation';
import LoadingSpinner from '../components/LoadingSpinner';
import logger from '../utils/logger';

const API_URL = import.meta.env.VITE_API_URL || '';
const MAILING_URL = import.meta.env.VITE_MAILING_URL || '';

const VerifyEmailPage = () => {
  const { t, language } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const email = searchParams.get('email') || '';
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  
  const inputRefs = useRef([]);
  const { user, setEmailVerified } = useAuthStore();
  
  // Redirect if already verified
  useEffect(() => {
    if (user?.email_verified) {
      navigate('/');
    }
  }, [user, navigate]);
  
  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);
  
  // Handle code input
  const handleCodeChange = (index, value) => {
    if (value.length > 1) {
      // Handle paste
      const pastedCode = value.slice(0, 6).split('');
      const newCode = [...code];
      pastedCode.forEach((char, i) => {
        if (index + i < 6 && /^\d$/.test(char)) {
          newCode[index + i] = char;
        }
      });
      setCode(newCode);
      
      // Focus on next empty or last input
      const nextEmptyIndex = newCode.findIndex(c => c === '');
      if (nextEmptyIndex !== -1) {
        inputRefs.current[nextEmptyIndex]?.focus();
      } else {
        inputRefs.current[5]?.focus();
      }
      return;
    }
    
    if (!/^\d*$/.test(value)) return;
    
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    
    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };
  
  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };
  
  const handleVerify = async () => {
    const fullCode = code.join('');
    if (fullCode.length !== 6) {
      setError(t('auth.verification.invalidCode'));
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${MAILING_URL}/verification/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code: fullCode })
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setSuccess(true);
        // Update the user's email_verified status in the store
        setEmailVerified();
        
        // Force re-verification with backend to ensure the updated email_verified status is fetched
        // This prevents the race condition where the local store has email_verified=true
        // but the next auth check might return false if timing is off
        try {
          const { refreshUserFromBackend } = useAuthStore.getState();
          if (refreshUserFromBackend) {
            await refreshUserFromBackend();
          }
        } catch (refreshError) {
          logger.warn('Failed to refresh user from backend after verification:', refreshError);
          // Don't fail - the local store update should be enough for navigation
        }
        
        // Wait a moment then redirect to home
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        setError(t('auth.verification.verificationFailed'));
      }
    } catch (err) {
      logger.error('Verification error:', err);
      setError(t('auth.verification.networkError'));
    } finally {
      setLoading(false);
    }
  };
  
  const handleResend = async () => {
    if (resendCooldown > 0) return;
    
    setResending(true);
    setError('');
    
    try {
      const response = await fetch(`${MAILING_URL}/verification/resend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, language })
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setResendCooldown(60); // 60 second cooldown
        setCode(['', '', '', '', '', '']);
      } else {
        setError(t('auth.verification.resendFailed'));
      }
    } catch (err) {
      logger.error('Resend error:', err);
      setError(t('auth.verification.networkError'));
    } finally {
      setResending(false);
    }
  };
  
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {t('auth.verification.success')}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            {t('auth.verification.redirecting')}
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-sky-100 dark:bg-sky-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <EnvelopeIcon className="w-8 h-8 text-sky-600 dark:text-sky-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {t('auth.verification.title')}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            {t('auth.verification.subtitle')}
          </p>
          <p className="text-sky-600 dark:text-sky-400 font-medium mt-1">{email}</p>
        </div>
        
        {/* Code Input */}
        <div className="flex justify-center gap-2 mb-6">
          {code.map((digit, index) => (
            <input
              key={index}
              ref={el => inputRefs.current[index] = el}
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={digit}
              onChange={(e) => handleCodeChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className={`w-12 h-14 text-center text-2xl font-bold border-2 rounded-lg
                bg-white dark:bg-slate-700 text-gray-900 dark:text-white
                focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500
                ${error ? 'border-red-300 dark:border-red-500' : 'border-gray-300 dark:border-slate-600'}
              `}
              disabled={loading}
            />
          ))}
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg mb-4">
            <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}
        
        {/* Verify Button */}
        <button
          onClick={handleVerify}
          disabled={loading || code.join('').length !== 6}
          className="w-full py-3 px-4 bg-sky-500 hover:bg-sky-600 text-white font-semibold
            rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              {t('auth.verification.verifying')}
            </>
          ) : (
            t('auth.verification.verify')
          )}
        </button>
        
        {/* Resend Link */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">
            {t('auth.verification.noCode')}
          </p>
          <button
            onClick={handleResend}
            disabled={resending || resendCooldown > 0}
            className="text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 font-medium text-sm
              disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1 mx-auto"
          >
            {resending ? (
              <>
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
                {t('auth.verification.sending')}
              </>
            ) : resendCooldown > 0 ? (
              `${t('auth.verification.resendIn')} ${resendCooldown}s`
            ) : (
              <>
                <ArrowPathIcon className="w-4 h-4" />
                {t('auth.verification.resend')}
              </>
            )}
          </button>
        </div>
        
        {/* Expiry Note */}
        <p className="text-gray-400 dark:text-gray-500 text-xs text-center mt-6">
          {t('auth.verification.expiry')}
        </p>
      </div>
    </div>
  );
};

export default VerifyEmailPage;
