#!/usr/bin/env python3
"""
LumTrails Mailing Service - Verification Service
Handles verification code generation, storage, and validation using Firebase
"""
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore


# Initialize Firebase (will use Application Default Credentials on Cloud Run)
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app()
    except Exception:
        # For local development, use default credentials
        firebase_admin.initialize_app()

db = firestore.client()


class VerificationService:
    """Service for managing email verification codes"""
    
    COLLECTION_NAME = "verification_codes"
    CODE_LENGTH = 6
    EXPIRY_MINUTES = 15
    MAX_ATTEMPTS = 5
    
    @classmethod
    def generate_code(cls) -> str:
        """Generate a random 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(cls.CODE_LENGTH))
    
    @classmethod
    async def create_verification(cls, email: str, user_id: Optional[str] = None) -> str:
        """
        Create a new verification code for an email address
        
        Args:
            email: Email address to verify
            user_id: Optional user ID if already created
        
        Returns:
            The generated verification code
        """
        code = cls.generate_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=cls.EXPIRY_MINUTES)
        
        doc_ref = db.collection(cls.COLLECTION_NAME).document(email.lower())
        doc_ref.set({
            "email": email.lower(),
            "code": code,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "attempts": 0,
            "verified": False
        })
        
        return code
    
    @classmethod
    async def verify_code(cls, email: str, code: str) -> dict:
        """
        Verify a code for an email address
        
        Args:
            email: Email address
            code: Verification code to check
        
        Returns:
            Dict with success status and message
        """
        doc_ref = db.collection(cls.COLLECTION_NAME).document(email.lower())
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "success": False,
                "error": "verification_not_found",
                "message": "No verification pending for this email"
            }
        
        data = doc.to_dict()
        
        # Check if already verified
        if data.get("verified"):
            return {
                "success": False,
                "error": "already_verified",
                "message": "Email already verified"
            }
        
        # Check expiry
        expires_at = data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, datetime):
                if expires_at < datetime.now(timezone.utc):
                    return {
                        "success": False,
                        "error": "code_expired",
                        "message": "Verification code has expired"
                    }
        
        # Check attempts
        attempts = data.get("attempts", 0)
        if attempts >= cls.MAX_ATTEMPTS:
            return {
                "success": False,
                "error": "max_attempts",
                "message": "Maximum verification attempts exceeded"
            }
        
        # Increment attempts
        doc_ref.update({"attempts": attempts + 1})
        
        # Verify code
        if data.get("code") != code:
            remaining = cls.MAX_ATTEMPTS - attempts - 1
            return {
                "success": False,
                "error": "invalid_code",
                "message": f"Invalid verification code. {remaining} attempts remaining."
            }
        
        # Mark as verified
        doc_ref.update({
            "verified": True,
            "verified_at": datetime.now(timezone.utc)
        })
        
        return {
            "success": True,
            "user_id": data.get("user_id"),
            "message": "Email verified successfully"
        }
    
    @classmethod
    async def resend_code(cls, email: str) -> dict:
        """
        Generate a new verification code for an email
        
        Args:
            email: Email address
        
        Returns:
            Dict with new code or error
        """
        doc_ref = db.collection(cls.COLLECTION_NAME).document(email.lower())
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "success": False,
                "error": "verification_not_found",
                "message": "No verification pending for this email"
            }
        
        data = doc.to_dict()
        
        if data.get("verified"):
            return {
                "success": False,
                "error": "already_verified",
                "message": "Email already verified"
            }
        
        # Generate new code
        new_code = cls.generate_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=cls.EXPIRY_MINUTES)
        
        doc_ref.update({
            "code": new_code,
            "expires_at": expires_at,
            "attempts": 0,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "success": True,
            "code": new_code,
            "message": "New verification code generated"
        }
    
    @classmethod
    async def cleanup_expired(cls) -> int:
        """
        Delete expired verification codes (for cron job)
        
        Returns:
            Number of deleted documents
        """
        expired_docs = (
            db.collection(cls.COLLECTION_NAME)
            .where("expires_at", "<", datetime.now(timezone.utc))
            .where("verified", "==", False)
            .stream()
        )
        
        deleted_count = 0
        for doc in expired_docs:
            doc.reference.delete()
            deleted_count += 1
        
        return deleted_count
    
    @classmethod
    async def is_verified(cls, email: str) -> bool:
        """
        Check if an email is verified
        
        Args:
            email: Email address to check
        
        Returns:
            True if verified, False otherwise
        """
        doc = db.collection(cls.COLLECTION_NAME).document(email.lower()).get()
        
        if not doc.exists:
            return False
        
        return doc.to_dict().get("verified", False)
    
    @classmethod
    async def get_user_id(cls, email: str) -> Optional[str]:
        """
        Get user ID associated with a verified email
        
        Args:
            email: Email address
        
        Returns:
            User ID if found, None otherwise
        """
        doc = db.collection(cls.COLLECTION_NAME).document(email.lower()).get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        if not data.get("verified"):
            return None
        
        return data.get("user_id")
