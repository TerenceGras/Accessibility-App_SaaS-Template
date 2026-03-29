#!/usr/bin/env python3
"""
LumTrails Mailing Service - Newsletter Service
Handles bulk email sending to users by subscription tier
"""
from typing import Optional
import firebase_admin
from firebase_admin import firestore

from brevo_service import BrevoService
from templates import get_newsletter_email, get_product_update_email
from models import SubscriptionTier


# Ensure Firebase is initialized
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app()
    except Exception:
        firebase_admin.initialize_app()

db = firestore.client()


class NewsletterService:
    """Service for sending newsletters to users by subscription tier"""
    
    @classmethod
    async def get_users_by_tier(
        cls,
        tier: SubscriptionTier,
        newsletter_subscribed: bool = True
    ) -> list[dict]:
        """
        Get list of users by subscription tier
        
        Args:
            tier: Subscription tier to filter by (or 'all' for all users)
            newsletter_subscribed: Only include users subscribed to newsletter
        
        Returns:
            List of user dicts with email, name, and language
        """
        users_ref = db.collection("users")
        
        # Build query based on tier
        if tier == SubscriptionTier.ALL:
            query = users_ref
        else:
            query = users_ref.where("subscription_tier", "==", tier.value)
        
        # Only include newsletter subscribers if specified
        if newsletter_subscribed:
            query = query.where("newsletter_subscribed", "==", True)
        
        users = []
        for doc in query.stream():
            data = doc.to_dict()
            # Only include verified users with emails
            if data.get("email") and data.get("email_verified", True):
                users.append({
                    "email": data["email"],
                    "name": data.get("display_name") or data.get("name") or "",
                    "language": data.get("language", "en")
                })
        
        return users
    
    @classmethod
    async def send_newsletter(
        cls,
        tier: SubscriptionTier,
        subject: str,
        content_html: str,
        test_email: Optional[str] = None
    ) -> dict:
        """
        Send newsletter to users of a specific tier
        
        Args:
            tier: Subscription tier to target (free, standard, business, all)
            subject: Email subject line
            content_html: HTML content for the newsletter body
            test_email: If provided, send only to this email (for testing)
        
        Returns:
            Dict with success count, failure count, and details
        """
        brevo = BrevoService()
        
        if test_email:
            # Test mode - send only to specified email
            email_content = get_newsletter_email(
                subject=subject,
                content_html=content_html,
                name="Test User",
                language="en"
            )
            
            result = brevo.send_email(
                to_email=test_email,
                to_name="Test User",
                subject=email_content["subject"],
                html_content=email_content["html_content"]
            )
            
            return {
                "mode": "test",
                "success_count": 1 if result.get("success") else 0,
                "failure_count": 0 if result.get("success") else 1,
                "details": [result]
            }
        
        # Get users for the specified tier
        users = await cls.get_users_by_tier(tier, newsletter_subscribed=True)
        
        if not users:
            return {
                "mode": "production",
                "tier": tier.value,
                "success_count": 0,
                "failure_count": 0,
                "message": "No users found for the specified tier"
            }
        
        # Prepare emails for batch sending
        emails_to_send = []
        for user in users:
            email_content = get_newsletter_email(
                subject=subject,
                content_html=content_html,
                name=user["name"],
                language=user["language"]
            )
            emails_to_send.append({
                "to_email": user["email"],
                "to_name": user["name"],
                "subject": email_content["subject"],
                "html_content": email_content["html_content"]
            })
        
        # Send in batches
        results = brevo.send_bulk_emails(emails_to_send)
        
        success_count = sum(1 for r in results if r.get("success"))
        failure_count = len(results) - success_count
        
        return {
            "mode": "production",
            "tier": tier.value,
            "total_users": len(users),
            "success_count": success_count,
            "failure_count": failure_count
        }
    
    @classmethod
    async def send_product_update(
        cls,
        tier: SubscriptionTier,
        title: str,
        features: list[dict],
        test_email: Optional[str] = None
    ) -> dict:
        """
        Send product update/feature announcement to users
        
        Args:
            tier: Subscription tier to target
            title: Update title
            features: List of feature dicts with 'title', 'description', 'icon'
            test_email: If provided, send only to this email
        
        Returns:
            Dict with success count, failure count, and details
        """
        brevo = BrevoService()
        
        if test_email:
            email_content = get_product_update_email(
                title=title,
                features=features,
                name="Test User",
                language="en"
            )
            
            result = brevo.send_email(
                to_email=test_email,
                to_name="Test User",
                subject=email_content["subject"],
                html_content=email_content["html_content"]
            )
            
            return {
                "mode": "test",
                "success_count": 1 if result.get("success") else 0,
                "failure_count": 0 if result.get("success") else 1,
                "details": [result]
            }
        
        # Get users for the specified tier
        users = await cls.get_users_by_tier(tier, newsletter_subscribed=True)
        
        if not users:
            return {
                "mode": "production",
                "tier": tier.value,
                "success_count": 0,
                "failure_count": 0,
                "message": "No users found for the specified tier"
            }
        
        # Prepare emails
        emails_to_send = []
        for user in users:
            email_content = get_product_update_email(
                title=title,
                features=features,
                name=user["name"],
                language=user["language"]
            )
            emails_to_send.append({
                "to_email": user["email"],
                "to_name": user["name"],
                "subject": email_content["subject"],
                "html_content": email_content["html_content"]
            })
        
        # Send in batches
        results = brevo.send_bulk_emails(emails_to_send)
        
        success_count = sum(1 for r in results if r.get("success"))
        failure_count = len(results) - success_count
        
        return {
            "mode": "production",
            "tier": tier.value,
            "total_users": len(users),
            "success_count": success_count,
            "failure_count": failure_count
        }
