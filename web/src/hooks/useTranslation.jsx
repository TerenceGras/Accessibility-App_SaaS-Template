import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { doc, getDoc, updateDoc, setDoc } from 'firebase/firestore';
import { db } from '../config/firebase';
import useAuthStore from '../stores/authStore';
import logger from '../utils/logger';

// Import language files
import en from '../languages/en.json';
import fr from '../languages/fr.json';
import de from '../languages/de.json';
import it from '../languages/it.json';
import es from '../languages/es.json';
import pt from '../languages/pt.json';

// Available languages with metadata
export const SUPPORTED_LANGUAGES = {
  en: { name: 'English', nativeName: 'English', flag: '🇬🇧', translations: en },
  fr: { name: 'French', nativeName: 'Français', flag: '🇫🇷', translations: fr },
  de: { name: 'German', nativeName: 'Deutsch', flag: '🇩🇪', translations: de },
  it: { name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹', translations: it },
  es: { name: 'Spanish', nativeName: 'Español', flag: '🇪🇸', translations: es },
  pt: { name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹', translations: pt },
};

// Get browser language and match to supported languages
const getBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage || 'en';
  // Extract the language code (e.g., 'en-US' -> 'en')
  const langCode = browserLang.split('-')[0].toLowerCase();
  
  // Check if we support this language
  if (SUPPORTED_LANGUAGES[langCode]) {
    return langCode;
  }
  
  // Default to English
  return 'en';
};

// Create the context
const LanguageContext = createContext();

// Language Provider component
export const LanguageProvider = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [translations, setTranslations] = useState(en);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuthStore();

  // Load language preference
  useEffect(() => {
    const loadLanguagePreference = async () => {
      setIsLoading(true);
      
      if (user?.uid) {
        // User is logged in - try to load from Firebase
        try {
          const userDocRef = doc(db, 'users', user.uid);
          const userDoc = await getDoc(userDocRef);
          
          if (userDoc.exists() && userDoc.data().preferredLanguage) {
            const savedLang = userDoc.data().preferredLanguage;
            if (SUPPORTED_LANGUAGES[savedLang]) {
              setCurrentLanguage(savedLang);
              setTranslations(SUPPORTED_LANGUAGES[savedLang].translations);
              localStorage.setItem('lumtrails-language', savedLang);
              setIsLoading(false);
              return;
            }
          }
        } catch (error) {
          logger.error('Error loading language preference from Firebase:', error);
        }
      }
      
      // Fallback: Check localStorage
      const savedLanguage = localStorage.getItem('lumtrails-language');
      if (savedLanguage && SUPPORTED_LANGUAGES[savedLanguage]) {
        setCurrentLanguage(savedLanguage);
        setTranslations(SUPPORTED_LANGUAGES[savedLanguage].translations);
        setIsLoading(false);
        return;
      }
      
      // Final fallback: Detect browser language
      const browserLang = getBrowserLanguage();
      setCurrentLanguage(browserLang);
      setTranslations(SUPPORTED_LANGUAGES[browserLang].translations);
      localStorage.setItem('lumtrails-language', browserLang);
      
      setIsLoading(false);
    };

    loadLanguagePreference();
  }, [user?.uid]);

  // Change language function
  const changeLanguage = useCallback(async (langCode) => {
    if (!SUPPORTED_LANGUAGES[langCode]) {
      logger.warn(`Language ${langCode} is not supported`);
      return;
    }

    setCurrentLanguage(langCode);
    setTranslations(SUPPORTED_LANGUAGES[langCode].translations);
    localStorage.setItem('lumtrails-language', langCode);

    // If user is logged in, save to Firebase
    if (user?.uid) {
      try {
        const userDocRef = doc(db, 'users', user.uid);
        const userDoc = await getDoc(userDocRef);
        
        if (userDoc.exists()) {
          await updateDoc(userDocRef, {
            preferredLanguage: langCode,
            updatedAt: new Date().toISOString()
          });
        } else {
          // Create the document if it doesn't exist
          await setDoc(userDocRef, {
            preferredLanguage: langCode,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }, { merge: true });
        }
      } catch (error) {
        logger.error('Error saving language preference to Firebase:', error);
      }
    }
  }, [user?.uid]);

  // Helper function to get raw value by key path
  const getRawValue = (key) => {
    const keys = key.split('.');
    let value = translations;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        // Key not found, return undefined
        logger.warn(`Translation key not found: ${key}`);
        return undefined;
      }
    }
    
    return value;
  };

  // Translation function - supports nested keys like "home.hero.title"
  const t = (key, replacements = {}) => {
    const value = getRawValue(key);
    
    if (value === undefined) {
      return key;
    }
    
    // If the value is not a string, return the key
    if (typeof value !== 'string') {
      logger.warn(`Translation value is not a string for key: ${key}`);
      return key;
    }
    
    // Replace placeholders like {{name}} with actual values
    let result = value;
    Object.keys(replacements).forEach((placeholder) => {
      const regex = new RegExp(`\\{\\{${placeholder}\\}\\}`, 'g');
      result = result.replace(regex, replacements[placeholder]);
    });
    
    return result;
  };

  // Raw translation function - returns arrays or objects as-is, useful for lists
  const tRaw = (key) => {
    const value = getRawValue(key);
    
    if (value === undefined) {
      return [];
    }
    
    return value;
  };

  return (
    <LanguageContext.Provider value={{ 
      currentLanguage, 
      changeLanguage, 
      t,
      tRaw,
      isLoading,
      availableLanguages: Object.keys(SUPPORTED_LANGUAGES),
      supportedLanguages: SUPPORTED_LANGUAGES
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

// Custom hook to use translations
export const useTranslation = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider');
  }
  return context;
};

export default LanguageContext;
