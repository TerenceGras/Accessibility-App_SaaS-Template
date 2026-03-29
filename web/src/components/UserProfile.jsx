import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { UserCircleIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import useAuthStore from '../stores/authStore';
import { useTranslation } from '../hooks/useTranslation';

const UserProfile = () => {
  const { t } = useTranslation();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const { user, signOut, loading } = useAuthStore();

  if (!user) return null;

  const handleSignOut = async () => {
    setIsDropdownOpen(false);
    await signOut();
  };

  const getInitials = (name) => {
    if (!name) return user.email?.charAt(0).toUpperCase() || 'U';
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatJoinDate = (dateString) => {
    if (!dateString) return null;
    try {
      return new Date(dateString).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    } catch {
      return null;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center space-x-3 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="flex-shrink-0">
          {user.picture ? (
            <img
              src={user.picture}
              alt={`${user.name || user.email}'s profile picture`}
              className="h-8 w-8 rounded-full"
            />
          ) : (
            <div className="h-8 w-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
              {getInitials(user.name)}
            </div>
          )}
        </div>
        
        <div className="flex-1 min-w-0 text-left">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {user.name || 'User'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
            {user.email}
          </p>
        </div>
        
        <ChevronDownIcon 
          className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${
            isDropdownOpen ? 'rotate-180' : ''
          }`} 
        />
      </button>

      {isDropdownOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={`${user.name || user.email}'s profile picture`}
                    className="h-12 w-12 rounded-full"
                  />
                ) : (
                  <div className="h-12 w-12 bg-blue-500 rounded-full flex items-center justify-center text-white text-lg font-medium">
                    {getInitials(user.name)}
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-medium text-gray-900 dark:text-white truncate">
                  {user.name || 'User'}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                  {user.email}
                </p>
                <div className="flex items-center mt-1">
                  <div className={`h-2 w-2 rounded-full mr-2 ${
                    user.email_verified ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {user.email_verified ? t('auth.verified') : t('auth.unverified')}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-4 space-y-3">
            {user.created_at && (
              <div className="text-xs text-gray-500 dark:text-gray-400 pb-3 border-b border-gray-200 dark:border-gray-700">
                <p><span className="font-medium">{t('auth.memberSince')}</span> {formatJoinDate(user.created_at)}</p>
              </div>
            )}
            
            <div className="space-y-1">
              <Link
                to="/profile"
                onClick={() => setIsDropdownOpen(false)}
                className="block w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md"
              >
                {t('auth.viewProfile')}
              </Link>
              <button
                onClick={handleSignOut}
                disabled={loading}
                className="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md disabled:opacity-50"
              >
                {loading ? t('auth.signingOut') : t('auth.signOut')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backdrop to close dropdown */}
      {isDropdownOpen && (
        <div 
          className="fixed inset-0 z-40"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  );
};

export default UserProfile;
