import { create } from 'zustand';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
  updateProfile
} from 'firebase/auth';
import { auth } from '../config/firebase';
import { isEmailAuthorized, isDevEnvironment } from '../config/authConfig';
import axios from 'axios';
import logger from '../utils/logger';

const API_URL = import.meta.env.VITE_API_URL || '';
const MAILING_URL = import.meta.env.VITE_MAILING_URL || '';

const useAuthStore = create((set, get) => ({
  user: null,
  firebaseUser: null, // Store Firebase user for token access
  loading: true,
  error: null,
  
  // Get current Firebase ID token
  getIdToken: async () => {
    const firebaseUser = get().firebaseUser;
    if (!firebaseUser) {
      throw new Error('No authenticated user');
    }
    return await firebaseUser.getIdToken();
  },
  
  // Initialize auth state listener
  initializeAuth: () => {
    onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          // Check if email is authorized (DEV environment whitelist)
          if (!isEmailAuthorized(firebaseUser.email)) {
            logger.warn('Unauthorized email attempted login:', firebaseUser.email);
            await firebaseSignOut(auth);
            set({ 
              user: null, 
              firebaseUser: null, 
              loading: false, 
              error: isDevEnvironment() 
                ? 'Access restricted to authorized accounts in DEV environment' 
                : 'Access denied'
            });
            return;
          }

          // Get ID token and verify with backend
          const idToken = await firebaseUser.getIdToken();
          
          const response = await axios.post(`${API_URL}/auth/verify-token`, {
            token: idToken
          });
          
          if (response.data.success) {
            set({ 
              user: response.data.user,
              firebaseUser: firebaseUser, // Store Firebase user
              loading: false,
              error: null
            });
          } else {
            set({ user: null, firebaseUser: null, loading: false, error: 'Token verification failed' });
          }
        } catch (error) {
          logger.error('Auth verification error:', error);
          set({ user: null, firebaseUser: null, loading: false, error: error.response?.data?.detail || 'Authentication failed' });
        }
      } else {
        set({ user: null, firebaseUser: null, loading: false, error: null });
      }
    });
  },

  // Sign in with Google
  signInWithGoogle: async () => {
    set({ loading: true, error: null });
    try {
      const provider = new GoogleAuthProvider();
      provider.addScope('email');
      provider.addScope('profile');
      // Force account selection prompt every time
      provider.setCustomParameters({
        prompt: 'select_account'
      });
      
      const result = await signInWithPopup(auth, provider);
      
      // Check if email is authorized (DEV environment whitelist)
      if (!isEmailAuthorized(result.user.email)) {
        await firebaseSignOut(auth);
        const errorMessage = isDevEnvironment() 
          ? 'Access restricted to authorized accounts in DEV environment' 
          : 'Access denied';
        set({ loading: false, error: errorMessage });
        return { success: false, error: errorMessage };
      }
      
      const idToken = await result.user.getIdToken();
      
      // Verify with backend
      const response = await axios.post(`${API_URL}/auth/verify-token`, {
        token: idToken
      });
      
      if (response.data.success) {
        set({ 
          user: response.data.user,
          firebaseUser: result.user, // Store Firebase user
          loading: false,
          error: null
        });
        return { success: true };
      } else {
        throw new Error('Backend verification failed');
      }
    } catch (error) {
      let errorMessage;
      
      if (error.code === 'auth/popup-closed-by-user') {
        errorMessage = 'Sign-in cancelled';
      } else if (error.code === 'auth/popup-blocked') {
        errorMessage = 'Please allow popups for this site';
      } else if (error.code === 'auth/account-exists-with-different-credential') {
        errorMessage = 'An account already exists with this email using a different sign-in method';
      } else {
        errorMessage = error.message || 'Google sign-in failed';
      }
      
      set({ loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  // Sign in with email and password
  signIn: async (email, password) => {
    set({ loading: true, error: null });
    
    // Check if email is authorized before attempting login (DEV environment whitelist)
    if (!isEmailAuthorized(email)) {
      const errorMessage = isDevEnvironment() 
        ? 'Access restricted to authorized accounts in DEV environment' 
        : 'Access denied';
      set({ loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
    
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await userCredential.user.getIdToken();
      
      // Verify with backend
      const response = await axios.post(`${API_URL}/auth/verify-token`, {
        token: idToken
      });
      
      if (response.data.success) {
        set({ 
          user: response.data.user,
          firebaseUser: userCredential.user, // Store Firebase user
          loading: false,
          error: null
        });
        return { success: true };
      } else {
        throw new Error('Backend verification failed');
      }
    } catch (error) {
      const errorMessage = error.code === 'auth/user-not-found' ? 'No account found with this email'
        : error.code === 'auth/wrong-password' ? 'Incorrect password'
        : error.code === 'auth/invalid-email' ? 'Invalid email address'
        : error.code === 'auth/too-many-requests' ? 'Too many failed attempts. Try again later.'
        : error.message || 'Sign in failed';
      
      set({ loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  // Validate password strength
  validatePassword: (password) => {
    const errors = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Sign up with email and password
  signUp: async (email, password, name, language = 'en') => {
    logger.log('signUp called with email:', email, 'name:', name, 'language:', language);
    set({ loading: true, error: null });
    
    // Check if email is authorized before attempting signup (DEV environment whitelist)
    if (!isEmailAuthorized(email)) {
      const errorMessage = isDevEnvironment() 
        ? 'Access restricted to authorized accounts in DEV environment' 
        : 'Access denied';
      logger.warn('Email not authorized:', email);
      set({ loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
    
    // Validate password strength
    const passwordValidation = get().validatePassword(password);
    if (!passwordValidation.isValid) {
      const errorMessage = passwordValidation.errors.join('. ');
      logger.warn('Password validation failed:', passwordValidation.errors);
      set({ loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
    
    try {
      logger.log('Creating user with Firebase...');
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      logger.log('User created in Firebase:', userCredential.user.uid);
      
      // Update user profile with name
      if (name) {
        await updateProfile(userCredential.user, { displayName: name });
      }
      
      const idToken = await userCredential.user.getIdToken();
      logger.log('Got ID token, verifying with backend...');
      
      // Verify with backend (this creates the user record with email_verified: false)
      const response = await axios.post(`${API_URL}/auth/verify-token`, {
        token: idToken
      });
      logger.log('Backend verification response:', response.data);
      
      if (response.data.success) {
        // Send verification email via mailing service
        try {
          logger.log('Sending verification email...');
          await axios.post(`${MAILING_URL}/verification/send`, {
            email: email,
            name: name || '',
            user_id: userCredential.user.uid,
            language: language
          });
          logger.log('Verification email sent successfully');
        } catch (mailError) {
          logger.warn('Failed to send verification email:', mailError);
          // Don't fail the signup if email sending fails
        }
        
        logger.log('Setting user state and returning success...');
        set({ 
          user: { ...response.data.user, email_verified: false },
          firebaseUser: userCredential.user,
          loading: false,
          error: null
        });
        
        // Return success with requiresVerification flag
        logger.log('Returning success with requiresVerification: true');
        return { 
          success: true, 
          requiresVerification: true,
          email: email
        };
      } else {
        logger.error('Backend verification failed - response.data.success is false');
        throw new Error('Backend verification failed');
      }
    } catch (error) {
      logger.error('Sign up error:', error);
      const errorMessage = error.code === 'auth/email-already-in-use' ? 'An account with this email already exists'
        : error.code === 'auth/weak-password' ? 'Password should be at least 6 characters'
        : error.code === 'auth/invalid-email' ? 'Invalid email address'
        : error.message || 'Sign up failed';
      
      set({ loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },

  // Sign out
  signOut: async () => {
    set({ loading: true, error: null });
    try {
      const { user, firebaseUser } = get();
      
      // Sign out from backend if user exists
      if (user?.uid && firebaseUser) {
        try {
          const idToken = await firebaseUser.getIdToken();
          await axios.post(`${API_URL}/auth/signout`, { uid: user.uid }, {
            headers: {
              'Authorization': `Bearer ${idToken}`
            }
          });
        } catch (error) {
          logger.warn('Backend signout failed:', error);
        }
      }
      
      // Sign out from Firebase
      await firebaseSignOut(auth);
      
      set({ user: null, firebaseUser: null, loading: false, error: null });
      return { success: true };
    } catch (error) {
      set({ loading: false, error: 'Sign out failed' });
      return { success: false, error: 'Sign out failed' };
    }
  },

  // Reset password
  resetPassword: async (email) => {
    try {
      await sendPasswordResetEmail(auth, email);
      return { success: true };
    } catch (error) {
      const errorMessage = error.code === 'auth/user-not-found' ? 'No account found with this email'
        : error.code === 'auth/invalid-email' ? 'Invalid email address'
        : 'Failed to send reset email';
      
      return { success: false, error: errorMessage };
    }
  },

  // Mark email as verified in the store
  setEmailVerified: () => {
    const currentUser = get().user;
    if (currentUser) {
      set({ 
        user: { ...currentUser, email_verified: true }
      });
    }
  },

  // Refresh user data from backend (useful after email verification to ensure sync)
  refreshUserFromBackend: async () => {
    const firebaseUser = get().firebaseUser;
    if (!firebaseUser) {
      logger.warn('Cannot refresh user - no Firebase user');
      return null;
    }
    
    try {
      // Force token refresh to ensure we have a fresh token
      const idToken = await firebaseUser.getIdToken(true);
      
      const response = await axios.post(`${API_URL}/auth/verify-token`, {
        token: idToken
      });
      
      if (response.data.success) {
        set({ 
          user: response.data.user,
          error: null
        });
        logger.log('User data refreshed from backend successfully');
        return response.data.user;
      }
      return null;
    } catch (error) {
      logger.error('Failed to refresh user from backend:', error);
      return null;
    }
  },

  // Get user profile from backend
  getUserProfile: async () => {
    try {
      const firebaseUser = auth.currentUser;
      if (!firebaseUser) return null;
      
      const idToken = await firebaseUser.getIdToken();
      const response = await axios.get(`${API_URL}/auth/profile`, {
        headers: {
          Authorization: `Bearer ${idToken}`
        }
      });
      
      if (response.data.success) {
        set({ user: response.data.user });
        return response.data.user;
      }
      return null;
    } catch (error) {
      logger.error('Failed to get user profile:', error);
      return null;
    }
  },

  // Clear error
  clearError: () => set({ error: null })
}));

export default useAuthStore;
