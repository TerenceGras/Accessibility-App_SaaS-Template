#!/usr/bin/env python3
"""
LumTrails Mailing Service - Pydantic Models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum


class Language(str, Enum):
    EN = "en"
    FR = "fr"
    DE = "de"
    ES = "es"
    IT = "it"
    PT = "pt"


class SubscriptionTier(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    ALL = "all"  # For newsletter targeting


class EmailType(str, Enum):
    VERIFICATION = "verification"
    WELCOME = "welcome"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    ACCOUNT_DELETION_REQUEST = "account_deletion_request"
    ACCOUNT_DELETED = "account_deleted"
    NEWSLETTER = "newsletter"
    CONTACT_FORM = "contact_form"


# Request Models
class ContactFormRequest(BaseModel):
    """Request model for contact form submissions"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class VerificationRequest(BaseModel):
    """Request model for sending verification emails"""
    email: EmailStr
    user_id: str
    name: Optional[str] = None
    language: Optional[str] = "en"


class VerificationResendRequest(BaseModel):
    """Request model for resending verification emails (user_id not required)"""
    email: EmailStr
    name: Optional[str] = None
    language: Optional[str] = "en"


class VerificationConfirmRequest(BaseModel):
    """Request model for confirming email verification"""
    email: EmailStr
    code: str


class WelcomeEmailRequest(BaseModel):
    """Request model for sending welcome emails"""
    email: EmailStr
    user_id: str
    name: Optional[str] = None
    language: Optional[str] = "en"


class SubscriptionEmailRequest(BaseModel):
    """Request model for subscription-related emails"""
    email: EmailStr
    user_id: Optional[str] = None
    name: Optional[str] = None
    language: Optional[str] = "en"
    old_tier: Optional[str] = "free"
    new_tier: str
    interval: Optional[str] = "monthly"  # "monthly" or "yearly"
    web_credits: Optional[int] = 0
    pdf_credits: Optional[int] = 0


class DeletionEmailRequest(BaseModel):
    """Request model for account deletion emails"""
    email: EmailStr
    user_id: Optional[str] = None
    name: Optional[str] = None
    language: Optional[str] = "en"
    scheduled_deletion_date: Optional[str] = None


class NewsletterRequest(BaseModel):
    """Request model for newsletter emails"""
    tier: SubscriptionTier = SubscriptionTier.ALL
    subject: str
    content_html: str
    test_email: Optional[EmailStr] = None


class ProductUpdateRequest(BaseModel):
    """Request model for product update emails"""
    tier: SubscriptionTier = SubscriptionTier.ALL
    title: str
    features: List[str]
    test_email: Optional[EmailStr] = None


# Response Models
class EmailResponse(BaseModel):
    """Response model for single email operations"""
    success: bool
    message: str
    message_id: Optional[str] = None


class VerificationResponse(BaseModel):
    """Response model for verification operations"""
    success: bool
    message: str
    email: Optional[str] = None
    verified: bool = False


class BulkEmailResponse(BaseModel):
    """Response model for bulk email operations"""
    success: bool
    message: str
    total_sent: int = 0
    total_failed: int = 0
