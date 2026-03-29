import React, { Fragment, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Dialog, Transition } from '@headlessui/react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import useAuthStore from '../stores/authStore';
import LoadingSpinner from './LoadingSpinner';
import { useTranslation } from '../hooks/useTranslation';
import logger from '../utils/logger';

// Password validation rules
const validatePassword = (password) => {
  const rules = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSymbol: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
  };
  
  const isValid = Object.values(rules).every(Boolean);
  return { isValid, rules };
};

const LoginForm = ({ isOpen = true, onClose }) => {
  const { t, language } = useTranslation();
  const navigate = useNavigate();
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: ''
  });

  const { signIn, signUp, signInWithGoogle, resetPassword, loading, error, clearError } = useAuthStore();

  const handlePasswordChange = (password) => {
    setFormData(prev => ({ ...prev, password }));
    if (isSignUp) {
      setPasswordValidation(validatePassword(password));
    }
  };

  const handleGoogleSignIn = async () => {
    clearError();
    const result = await signInWithGoogle();
    if (result.success && onClose) {
      onClose();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    logger.log('handleSubmit called, isSignUp:', isSignUp);
    clearError();

    if (isSignUp) {
      // Validate password
      logger.log('Validating password...');
      const passwordCheck = validatePassword(formData.password);
      if (!passwordCheck.isValid) {
        logger.log('Password validation failed:', passwordCheck.rules);
        // Show which requirements are not met
        setPasswordValidation(passwordCheck);
        return;
      }
      
      if (formData.password !== formData.confirmPassword) {
        logger.log('Passwords do not match');
        // Password mismatch is already shown inline, but ensure form doesn't submit
        return;
      }
      
      logger.log('Calling signUp...');
      const result = await signUp(formData.email, formData.password, formData.name, language);
      logger.log('signUp result:', result);
      if (result.success) {
        if (result.requiresVerification) {
          logger.log('Redirecting to verification page...');
          // Close the modal first, then navigate
          if (onClose) onClose();
          navigate(`/verify-email?email=${encodeURIComponent(formData.email)}`);
        } else {
          // Account created without verification (shouldn't happen normally)
          if (onClose) onClose();
        }
      }
    } else {
      const result = await signIn(formData.email, formData.password);
      if (result.success && onClose) {
        onClose();
      }
    }
  };

  const handleForgotPassword = async () => {
    if (!formData.email) {
      return;
    }
    
    const result = await resetPassword(formData.email);
    if (result.success) {
      toast.success(t('auth.passwordResetSent'));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'password') {
      handlePasswordChange(value);
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    if (error) clearError();
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose || (() => {})}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-2 xs:p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 p-4 xs:p-6 shadow-xl transition-all max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-4 xs:mb-6">
                  <Dialog.Title as="h2" className="text-xl xs:text-2xl font-bold text-gray-900 dark:text-white">
                    {isSignUp ? t('auth.createAccount') : t('auth.signIn')}
                  </Dialog.Title>
                  {onClose && (
                    <button
                      onClick={onClose}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <span className="sr-only">{t('common.close')}</span>
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignUp && (
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('auth.fullName')}
              </label>
              <input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder={t('auth.enterYourFullName')}
                required={isSignUp}
              />
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('auth.emailAddress')}
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder={t('auth.enterYourEmail')}
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('auth.password')}
            </label>
            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                value={formData.password}
                onChange={handleChange}
                className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder={t('auth.enterYourPassword')}
                required
                minLength="8"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
            
            {/* Password Validation (only show during signup) */}
            {isSignUp && passwordValidation && (
              <div className="mt-2 text-xs space-y-1">
                <div className={`flex items-center space-x-1 ${passwordValidation.rules.minLength ? 'text-green-600' : 'text-red-600'}`}>
                  <span>{passwordValidation.rules.minLength ? '✓' : '✗'}</span>
                  <span>{t('auth.passwordRequirements.minLength')}</span>
                </div>
                <div className={`flex items-center space-x-1 ${passwordValidation.rules.hasUppercase ? 'text-green-600' : 'text-red-600'}`}>
                  <span>{passwordValidation.rules.hasUppercase ? '✓' : '✗'}</span>
                  <span>{t('auth.passwordRequirements.uppercase')}</span>
                </div>
                <div className={`flex items-center space-x-1 ${passwordValidation.rules.hasLowercase ? 'text-green-600' : 'text-red-600'}`}>
                  <span>{passwordValidation.rules.hasLowercase ? '✓' : '✗'}</span>
                  <span>{t('auth.passwordRequirements.lowercase')}</span>
                </div>
                <div className={`flex items-center space-x-1 ${passwordValidation.rules.hasNumber ? 'text-green-600' : 'text-red-600'}`}>
                  <span>{passwordValidation.rules.hasNumber ? '✓' : '✗'}</span>
                  <span>{t('auth.passwordRequirements.number')}</span>
                </div>
                <div className={`flex items-center space-x-1 ${passwordValidation.rules.hasSymbol ? 'text-green-600' : 'text-red-600'}`}>
                  <span>{passwordValidation.rules.hasSymbol ? '✓' : '✗'}</span>
                  <span>{t('auth.passwordRequirements.symbol')}</span>
                </div>
              </div>
            )}
          </div>

          {isSignUp && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('auth.confirmPassword')}
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder={t('auth.confirmYourPassword')}
                required={isSignUp}
              />
              {isSignUp && formData.password !== formData.confirmPassword && formData.confirmPassword && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {t('auth.passwordsDoNotMatch')}
                </p>
              )}
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
              <p className="text-sm text-red-800 dark:text-red-400">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || (isSignUp && formData.password !== formData.confirmPassword)}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            {loading ? (
              <LoadingSpinner size="sm" />
            ) : (
              isSignUp ? t('auth.createAccount') : t('auth.signIn')
            )}
          </button>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">{t('auth.or')}</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex justify-center items-center py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                {t('auth.continueWithGoogle')}
              </>
            )}
          </button>

          {!isSignUp && (
            <button
              type="button"
              onClick={handleForgotPassword}
              disabled={!formData.email}
              className="w-full text-center text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('auth.forgotPassword')}
            </button>
          )}

          <div className="text-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isSignUp ? t('auth.alreadyHaveAccount') : t('auth.dontHaveAccount')}
            </span>
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                clearError();
                setFormData({
                  email: '',
                  password: '',
                  confirmPassword: '',
                  name: ''
                });
              }}
              className="ml-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            >
              {isSignUp ? t('auth.signIn') : t('auth.createAccount')}
            </button>
          </div>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            {t('auth.termsAgreement')}{' '}
            <Link to="/terms" onClick={onClose} className="text-primary-500 hover:underline">{t('auth.termsOfService')}</Link>
            {' '}{t('common.and')}{' '}
            <Link to="/privacy" onClick={onClose} className="text-primary-500 hover:underline">{t('auth.privacyPolicy')}</Link>.
          </p>
        </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default LoginForm;
