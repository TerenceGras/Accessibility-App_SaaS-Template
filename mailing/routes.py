#!/usr/bin/env python3
"""
LumTrails Mailing Service - API Routes

Security: This service is internal-only. All endpoints require authenticated
service-to-service calls via OIDC tokens (Cloud Run IAM).
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends, Request
import firebase_admin
from firebase_admin import auth, firestore
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from models import (
    VerificationRequest, VerificationResendRequest, VerificationConfirmRequest, VerificationResponse,
    WelcomeEmailRequest, SubscriptionEmailRequest, DeletionEmailRequest,
    NewsletterRequest, ProductUpdateRequest, ContactFormRequest,
    EmailResponse, BulkEmailResponse,
    Language, SubscriptionTier
)
from brevo_service import BrevoService
from verification_service import VerificationService
from newsletter_service import NewsletterService
from templates import (
    get_verification_email,
    get_welcome_email,
    get_subscription_upgrade_email,
    get_deletion_request_email,
    get_account_deleted_email
)
from config import SUPPORTED_LANGUAGES, CONTACT_EMAIL

logger = logging.getLogger(__name__)

router = APIRouter()

# Project configuration for OIDC verification
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER", "")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
ALLOWED_SERVICE_ACCOUNTS = [
    f"{PROJECT_NUMBER}-compute@developer.gserviceaccount.com",
    f"{PROJECT_ID}@appspot.gserviceaccount.com",
]

# Initialize Firebase
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app()
    except Exception:
        firebase_admin.initialize_app()

db = firestore.client()


async def get_user_language(user_id: str) -> str:
    """Get user's preferred language from Firestore"""
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict().get("language", "en")
    except Exception:
        pass
    return "en"


async def get_user_info(user_id: str) -> dict:
    """Get user info from Firestore"""
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            return {
                "email": data.get("email"),
                "name": data.get("display_name") or data.get("name") or "",
                "language": data.get("language", "en")
            }
    except Exception:
        pass
    return None


async def verify_internal_token(authorization: Optional[str] = Header(None, alias="Authorization")) -> bool:
    """
    Verify OIDC token for service-to-service calls.
    Only allows calls from authorized GCP service accounts.
    """
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or invalid authorization header")
        raise HTTPException(status_code=403, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    
    try:
        # Verify the OIDC token
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=None  # We verify the service account email instead
        )
        
        # Verify the token is from an allowed service account
        email = claims.get("email", "")
        if email not in ALLOWED_SERVICE_ACCOUNTS:
            logger.warning(f"Unauthorized service account attempted access: {email}")
            raise HTTPException(status_code=403, detail="Unauthorized service account")
        
        logger.info(f"Verified OIDC token from service account: {email}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC token verification failed: {e}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")


# =============================================================================
# Verification Endpoints
# =============================================================================

@router.post("/verification/send", response_model=VerificationResponse)
async def send_verification_code(request: VerificationRequest):
    """
    Send email verification code to a new user
    
    This is called when a user signs up with email/password (non-Google auth)
    """
    brevo = BrevoService()
    
    # Determine language (from request or default)
    language = request.language or "en"
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    
    # Generate verification code
    code = await VerificationService.create_verification(
        email=request.email,
        user_id=request.user_id
    )
    
    # Generate email content
    email_content = get_verification_email(code=code, name=request.name or "", language=language)
    
    # Send email
    result = brevo.send_email(
        to_email=request.email,
        to_name=request.name or "",
        subject=email_content["subject"],
        html_content=email_content["html_content"]
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    return VerificationResponse(
        success=True,
        message="Verification code sent",
        email=request.email
    )


@router.post("/verification/confirm", response_model=VerificationResponse)
async def confirm_verification(request: VerificationConfirmRequest):
    """
    Confirm verification code and mark email as verified.
    After successful verification, sends a welcome email to the user.
    
    CRITICAL: This endpoint MUST update the email_verified field in Firestore
    to prevent users from being stuck in a verification loop.
    """
    result = await VerificationService.verify_code(
        email=request.email,
        code=request.code
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.get("error"),
                "message": result.get("message")
            }
        )
    
    # Update user's email_verified status in Firestore and get user info
    user_id = result.get("user_id")
    user_name = ""
    user_language = "en"
    email_updated = False
    
    # If we don't have user_id from verification record, look up by email
    if not user_id:
        try:
            # Find user by email in Firestore
            users_query = db.collection("users").where("email", "==", request.email.lower()).limit(1).stream()
            for user_doc in users_query:
                user_id = user_doc.id
                logger.info(f"Found user_id {user_id} by email lookup for {request.email}")
                break
        except Exception as e:
            logger.error(f"Failed to look up user by email {request.email}: {e}")
    
    if user_id:
        try:
            # Get user info before updating
            user_doc = db.collection("users").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_name = user_data.get("display_name") or user_data.get("name") or ""
                user_language = user_data.get("language", "en")
            
            # Update verification status - THIS IS CRITICAL
            db.collection("users").document(user_id).update({
                "email_verified": True,
                "email_verified_at": firestore.SERVER_TIMESTAMP
            })
            email_updated = True
            logger.info(f"Updated email_verified=True for user {user_id} ({request.email})")
        except Exception as e:
            # Log error but don't fail - verification was successful
            logger.error(f"CRITICAL: Failed to update email_verified for user {user_id}: {e}")
    else:
        logger.warning(f"Could not find user_id for email {request.email} - email_verified status not updated in Firestore")
    
    # Send welcome email after successful verification
    try:
        brevo = BrevoService()
        email_content = get_welcome_email(name=user_name, language=user_language)
        
        welcome_result = brevo.send_email(
            to_email=request.email,
            to_name=user_name,
            subject=email_content["subject"],
            html_content=email_content["html_content"]
        )
        
        if welcome_result.get("success"):
            logger.info(f"Welcome email sent to {request.email}")
        else:
            logger.warning(f"Failed to send welcome email to {request.email}")
    except Exception as e:
        # Log but don't fail - verification was still successful
        logger.warning(f"Failed to send welcome email: {e}")
    
    return VerificationResponse(
        success=True,
        message="Email verified successfully",
        email=request.email
    )


@router.post("/verification/resend", response_model=VerificationResponse)
async def resend_verification(request: VerificationResendRequest):
    """
    Resend verification code to an email
    """
    brevo = BrevoService()
    
    # Get new code
    result = await VerificationService.resend_code(email=request.email)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.get("error"),
                "message": result.get("message")
            }
        )
    
    # Determine language
    language = request.language or "en"
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    
    # Generate and send new email
    email_content = get_verification_email(code=result["code"], language=language)
    
    send_result = brevo.send_email(
        to_email=request.email,
        to_name=request.name or "",
        subject=email_content["subject"],
        html_content=email_content["html_content"]
    )
    
    if not send_result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    return VerificationResponse(
        success=True,
        message="New verification code sent",
        email=request.email
    )


# =============================================================================
# Welcome Email Endpoint
# =============================================================================

@router.post("/welcome", response_model=EmailResponse)
async def send_welcome_email(request: WelcomeEmailRequest):
    """
    Send welcome email after user verifies their email
    """
    brevo = BrevoService()
    
    # Get language from request or user preferences
    language = request.language
    if not language and request.user_id:
        language = await get_user_language(request.user_id)
    language = language or "en"
    
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    
    # Generate email content
    email_content = get_welcome_email(name=request.name or "", language=language)
    
    # Send email
    result = brevo.send_email(
        to_email=request.email,
        to_name=request.name or "",
        subject=email_content["subject"],
        html_content=email_content["html_content"]
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send welcome email")
    
    return EmailResponse(
        success=True,
        message="Welcome email sent",
        message_id=result.get("message_id")
    )


# =============================================================================
# Subscription Email Endpoint
# =============================================================================

@router.post("/subscription/upgrade", response_model=EmailResponse)
async def send_subscription_upgrade_email(request: SubscriptionEmailRequest):
    """
    Send subscription upgrade confirmation email
    
    Called by pricing service after successful subscription upgrade
    """
    brevo = BrevoService()
    
    # Get user info for language preference
    language = "en"
    name = request.name or ""
    
    if request.user_id:
        user_info = await get_user_info(request.user_id)
        if user_info:
            language = user_info.get("language", "en")
            name = name or user_info.get("name", "")
    
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    
    # Generate email content
    email_content = get_subscription_upgrade_email(
        name=name,
        old_tier=request.old_tier,
        new_tier=request.new_tier,
        interval=request.interval or "monthly",
        language=language
    )
    
    # Send email
    result = brevo.send_email(
        to_email=request.email,
        to_name=name,
        subject=email_content["subject"],
        html_content=email_content["html_content"]
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send subscription email")
    
    return EmailResponse(
        success=True,
        message="Subscription upgrade email sent",
        message_id=result.get("message_id")
    )


# =============================================================================
# Deletion Email Endpoints
# =============================================================================

@router.post("/deletion/request", response_model=EmailResponse)
async def send_deletion_request_email(request: DeletionEmailRequest):
    """
    Send account deletion request confirmation email
    
    Called when user initiates account deletion
    """
    brevo = BrevoService()
    
    # Get language preference
    language = "en"
    name = request.name or ""
    
    if request.user_id:
        user_info = await get_user_info(request.user_id)
        if user_info:
            language = user_info.get("language", "en")
            name = name or user_info.get("name", "")
    
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    
    # Generate email content
    email_content = get_deletion_request_email(name=name, language=language)
    
    # Send email
    result = brevo.send_email(
        to_email=request.email,
        to_name=name,
        subject=email_content["subject"],
        html_content=email_content["html_content"]
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send deletion request email")
    
    return EmailResponse(
        success=True,
        message="Deletion request email sent",
        message_id=result.get("message_id")
    )


@router.post("/deletion/complete", response_model=EmailResponse)
async def send_account_deleted_email(request: DeletionEmailRequest):
    """
    Send account deleted confirmation email
    
    Called after account deletion is complete
    """
    brevo = BrevoService()
    
    # Note: We can't get user info from Firestore as user is deleted
    # Use data from request
    language = request.language or "en"
    name = request.name or ""
    
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    
    # Generate email content
    email_content = get_account_deleted_email(name=name, language=language)
    
    # Send email
    result = brevo.send_email(
        to_email=request.email,
        to_name=name,
        subject=email_content["subject"],
        html_content=email_content["html_content"]
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to send account deleted email")
    
    return EmailResponse(
        success=True,
        message="Account deleted email sent",
        message_id=result.get("message_id")
    )


# =============================================================================
# Newsletter Endpoints
# =============================================================================

@router.post("/newsletter/send", response_model=BulkEmailResponse)
async def send_newsletter(request: NewsletterRequest):
    """
    Send newsletter to users by subscription tier
    
    Requires admin authentication (to be implemented)
    """
    result = await NewsletterService.send_newsletter(
        tier=request.tier,
        subject=request.subject,
        content_html=request.content_html,
        test_email=request.test_email
    )
    
    return BulkEmailResponse(
        success=True,
        total_sent=result.get("success_count", 0),
        total_failed=result.get("failure_count", 0),
        message=f"Newsletter sent to {result.get('success_count', 0)} recipients"
    )


@router.post("/newsletter/product-update", response_model=BulkEmailResponse)
async def send_product_update(request: ProductUpdateRequest):
    """
    Send product update announcement to users
    
    Requires admin authentication (to be implemented)
    """
    result = await NewsletterService.send_product_update(
        tier=request.tier,
        title=request.title,
        features=request.features,
        test_email=request.test_email
    )
    
    return BulkEmailResponse(
        success=True,
        total_sent=result.get("success_count", 0),
        total_failed=result.get("failure_count", 0),
        message=f"Product update sent to {result.get('success_count', 0)} recipients"
    )


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.post("/cleanup/verification-codes")
async def cleanup_expired_codes():
    """
    Cleanup expired verification codes
    
    Can be called by Cloud Scheduler cron job
    """
    deleted_count = await VerificationService.cleanup_expired()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Cleaned up {deleted_count} expired verification codes"
    }


# =============================================================================
# Contact Form Endpoint (Authenticated service-to-service)
# =============================================================================

@router.post("/contact", response_model=EmailResponse)
async def submit_contact_form(
    request: ContactFormRequest,
    _: bool = Depends(verify_internal_token)
):
    """
    Handle contact form submissions
    
    Sends the message to the configured contact email with the user's details
    """
    brevo = BrevoService()
    
    if not brevo.is_configured():
        raise HTTPException(
            status_code=503, 
            detail="Email service not configured"
        )
    
    # Build the email content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Contact Form Submission</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #1a56db; margin-top: 0;">New Contact Form Submission</h2>
        </div>
        
        <div style="background-color: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 10px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>From:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{request.name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><a href="mailto:{request.email}">{request.email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;"><strong>Subject:</strong></td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb;">{request.subject}</td>
                </tr>
            </table>
            
            <h3 style="margin-top: 20px; color: #374151;">Message:</h3>
            <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px; white-space: pre-wrap;">{request.message}</div>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #e0f2fe; border-radius: 8px;">
            <p style="margin: 0; font-size: 14px; color: #0369a1;">
                <strong>Reply directly to this email to respond to {request.name}.</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        result = await brevo.send_email_async(
            to_email=CONTACT_EMAIL,
            to_name="LumTrails Support",
            subject=f"[Contact Form] {request.subject}",
            html_content=html_content,
            reply_to_email=request.email,
            reply_to_name=request.name,
            tags=["contact-form"]
        )
        
        if result.get("success"):
            return EmailResponse(
                success=True,
                message="Your message has been sent successfully. We'll get back to you soon!",
                message_id=result.get("message_id")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send message. Please try again later."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )
