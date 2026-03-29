#!/usr/bin/env python3
"""
LumTrails Pricing Service - Subscription Service

Handles all subscription-related business logic:
- Creating checkout sessions for new subscriptions
- Managing subscription lifecycle
- Syncing subscription state from Stripe
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore

from config import get_pricing_tier, PRICING_TIERS
from services.stripe_service import stripe_service
from services.credit_service import credit_service

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")


class SubscriptionService:
    """Service for managing subscriptions"""
    
    def __init__(self):
        """Initialize subscription service"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.db = firestore.Client(project=self.project_id)
    
    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's current subscription details from Firestore.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Subscription details
        """
        try:
            user_doc = self.db.collection("users").document(user_id).get()
            
            if not user_doc.exists:
                return {
                    "plan": "free",
                    "status": "active",
                    "web_scan_credits": 0,
                    "pdf_scan_credits": 0
                }
            
            user_data = user_doc.to_dict()
            subscription = user_data.get("subscription", {"plan": "free", "status": "active"})
            
            return {
                "plan": subscription.get("plan", "free"),
                "status": subscription.get("status", "active"),
                "interval": subscription.get("interval"),
                "web_scan_credits": user_data.get("web_scan_credits", 0),
                "pdf_scan_credits": user_data.get("pdf_scan_credits", 0),
                "stripe_customer_id": subscription.get("stripe_customer_id"),
                "stripe_subscription_id": subscription.get("stripe_subscription_id"),
                "current_period_start": subscription.get("current_period_start"),
                "current_period_end": subscription.get("current_period_end"),
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
                "credits_expire_at": user_data.get("credits_expire_at")
            }
        except Exception as e:
            logger.error(f"Error getting subscription for user {user_id}: {e}")
            return {
                "plan": "free",
                "status": "active",
                "web_scan_credits": 0,
                "pdf_scan_credits": 0
            }
    
    def create_checkout_session(
        self,
        user_id: str,
        email: str,
        plan: str,
        interval: str = "monthly",
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session for a new subscription.
        
        This method:
        1. Gets or creates a Stripe customer
        2. Creates a Checkout Session
        3. Returns the checkout URL
        
        NO subscription is created here - it happens via webhook after payment.
        
        Args:
            user_id: Firebase user ID
            email: User email
            plan: Pricing plan (standard, business)
            interval: Billing interval (monthly, yearly)
            name: User name (optional)
        
        Returns:
            Dict with checkout_url and session_id
        """
        if plan not in ["standard", "business"]:
            raise ValueError(f"Invalid plan: {plan}. Only 'standard' and 'business' can be subscribed to.")
        
        if interval not in ["monthly", "yearly"]:
            raise ValueError(f"Invalid interval: {interval}. Only 'monthly' and 'yearly' are supported.")
        
        tier = get_pricing_tier(plan)
        
        # Select the appropriate Stripe price ID based on interval
        if interval == "yearly":
            price_id = tier.get("stripe_yearly_price_id")
        else:
            price_id = tier.get("stripe_price_id")
        
        if not tier or not price_id:
            raise ValueError(f"Plan {plan} with interval {interval} is not configured properly")
        
        # Get or create Stripe customer
        user_doc = self.db.collection("users").document(user_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}
        existing_customer_id = user_data.get("subscription", {}).get("stripe_customer_id")
        
        customer_id = stripe_service.get_or_create_customer(
            user_id=user_id,
            email=email,
            name=name,
            existing_customer_id=existing_customer_id
        )
        
        # Store customer ID if it's new
        if not existing_customer_id:
            self.db.collection("users").document(user_id).set({
                "subscription": {
                    "stripe_customer_id": customer_id
                },
                "updated_at": datetime.now(CET)
            }, merge=True)
        
        # Create Checkout Session
        session = stripe_service.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            user_id=user_id,
            plan=plan,
            interval=interval
        )
        
        logger.info(f"Created checkout session for user {user_id}: plan={plan}, interval={interval}")
        
        return session
    
    def activate_subscription(
        self,
        user_id: str,
        subscription_id: str,
        plan: str,
        interval: str,
        status: str,
        current_period_start: int,
        current_period_end: int,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Activate a subscription after successful payment.
        
        This is called by the webhook handler when subscription becomes active.
        It is the SINGLE POINT where subscriptions become active.
        
        IDEMPOTENCY: If the subscription is already active with the same
        subscription_id and period, this is a no-op to prevent double credit grants.
        
        Args:
            user_id: Firebase user ID
            subscription_id: Stripe subscription ID
            plan: Subscription plan
            interval: Billing interval
            status: Subscription status (should be 'active')
            current_period_start: Unix timestamp
            current_period_end: Unix timestamp
            customer_id: Stripe customer ID
        
        Returns:
            Updated subscription details
        """
        period_start = datetime.fromtimestamp(current_period_start, tz=CET)
        period_end = datetime.fromtimestamp(current_period_end, tz=CET)
        
        # IDEMPOTENCY CHECK: Prevent double activation for same subscription period
        user_doc = self.db.collection("users").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            existing_subscription = user_data.get("subscription", {})
            existing_sub_id = existing_subscription.get("stripe_subscription_id")
            existing_status = existing_subscription.get("status")
            existing_period_start = existing_subscription.get("current_period_start")
            
            # If already active with same subscription and period, skip activation
            if (existing_sub_id == subscription_id and 
                existing_status == "active" and
                existing_period_start == period_start):
                logger.info(f"Subscription {subscription_id} already activated for user {user_id}, skipping duplicate activation")
                return {
                    "plan": plan,
                    "interval": interval,
                    "status": status,
                    "current_period_start": period_start,
                    "current_period_end": period_end,
                    "already_activated": True
                }
        
        # Update subscription in Firestore
        update_data = {
            "subscription": {
                "plan": plan,
                "interval": interval,
                "status": status,
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id,
                "current_period_start": period_start,
                "current_period_end": period_end,
                "cancel_at_period_end": False
            },
            "updated_at": datetime.now(CET)
        }
        
        self.db.collection("users").document(user_id).set(update_data, merge=True)
        
        # Grant credits
        credits = credit_service.grant_subscription_credits(
            user_id=user_id,
            plan=plan,
            period_end_timestamp=current_period_end
        )
        
        logger.info(f"Activated subscription for user {user_id}: plan={plan}, interval={interval}")
        
        return {
            "plan": plan,
            "interval": interval,
            "status": status,
            "current_period_start": period_start,
            "current_period_end": period_end,
            **credits
        }
    
    def update_subscription_status(
        self,
        user_id: str,
        status: str,
        current_period_start: int = None,
        current_period_end: int = None,
        cancel_at_period_end: bool = False
    ):
        """
        Update subscription status in Firestore.
        
        Used for status changes that don't involve credit changes.
        
        Args:
            user_id: Firebase user ID
            status: New subscription status
            current_period_start: Unix timestamp (optional)
            current_period_end: Unix timestamp (optional)
            cancel_at_period_end: Whether subscription will cancel at period end
        """
        update_data = {
            "subscription.status": status,
            "subscription.cancel_at_period_end": cancel_at_period_end,
            "updated_at": datetime.now(CET)
        }
        
        # Only update period dates if provided
        if current_period_start is not None:
            period_start = datetime.fromtimestamp(current_period_start, tz=CET)
            update_data["subscription.current_period_start"] = period_start
        
        if current_period_end is not None:
            period_end = datetime.fromtimestamp(current_period_end, tz=CET)
            update_data["subscription.current_period_end"] = period_end
        
        self.db.collection("users").document(user_id).update(update_data)
        
        logger.info(f"Updated subscription status for user {user_id}: status={status}")
    
    def cancel_subscription(self, user_id: str, immediate: bool = False) -> Dict[str, Any]:
        """
        Cancel user's subscription.
        
        Args:
            user_id: Firebase user ID
            immediate: If True, cancel immediately; otherwise at period end
        
        Returns:
            Updated subscription details
        """
        user_doc = self.db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            raise ValueError("User not found")
        
        user_data = user_doc.to_dict()
        subscription = user_data.get("subscription", {})
        stripe_subscription_id = subscription.get("stripe_subscription_id")
        
        if not stripe_subscription_id:
            raise ValueError("No active subscription found")
        
        # Cancel in Stripe
        cancel_data = stripe_service.cancel_subscription(
            subscription_id=stripe_subscription_id,
            at_period_end=not immediate
        )
        
        # Update Firestore
        update_data = {
            "subscription.status": cancel_data["status"],
            "subscription.cancel_at_period_end": cancel_data["cancel_at_period_end"],
            "updated_at": datetime.now(CET)
        }
        
        if immediate:
            # Downgrade to free plan immediately
            update_data["subscription.plan"] = "free"
            credit_service.reset_to_free_tier(user_id)
        
        self.db.collection("users").document(user_id).update(update_data)
        
        logger.info(f"Cancelled subscription for user {user_id}, immediate={immediate}")
        
        return cancel_data
    
    def resume_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Resume a cancelled subscription.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Updated subscription details
        """
        user_doc = self.db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            raise ValueError("User not found")
        
        user_data = user_doc.to_dict()
        subscription = user_data.get("subscription", {})
        stripe_subscription_id = subscription.get("stripe_subscription_id")
        
        if not stripe_subscription_id:
            raise ValueError("No subscription found")
        
        # Resume in Stripe
        resume_data = stripe_service.resume_subscription(stripe_subscription_id)
        
        # Update Firestore
        self.db.collection("users").document(user_id).update({
            "subscription.status": resume_data["status"],
            "subscription.cancel_at_period_end": False,
            "updated_at": datetime.now(CET)
        })
        
        logger.info(f"Resumed subscription for user {user_id}")
        
        return resume_data
    
    def update_subscription_plan(self, user_id: str, new_plan: str) -> Dict[str, Any]:
        """
        Update subscription to a different plan.
        
        Args:
            user_id: Firebase user ID
            new_plan: New pricing plan
        
        Returns:
            Updated subscription details
        """
        if new_plan not in ["standard", "business"]:
            raise ValueError(f"Invalid plan: {new_plan}")
        
        new_tier = get_pricing_tier(new_plan)
        if not new_tier or not new_tier.get("stripe_price_id"):
            raise ValueError(f"Plan {new_plan} is not configured properly")
        
        user_doc = self.db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            raise ValueError("User not found")
        
        user_data = user_doc.to_dict()
        subscription = user_data.get("subscription", {})
        current_plan = subscription.get("plan", "free")
        current_interval = subscription.get("interval", "monthly")
        stripe_subscription_id = subscription.get("stripe_subscription_id")
        
        if current_plan == new_plan:
            raise ValueError("Already on this plan")
        
        if not stripe_subscription_id:
            raise ValueError("No active subscription found")
        
        # Get appropriate price ID based on current interval
        if current_interval == "yearly":
            new_price_id = new_tier.get("stripe_yearly_price_id")
        else:
            new_price_id = new_tier.get("stripe_price_id")
        
        # Update in Stripe
        update_data = stripe_service.update_subscription_plan(
            subscription_id=stripe_subscription_id,
            new_price_id=new_price_id,
            plan=new_plan,
            interval=current_interval
        )
        
        # Update in Firestore
        self.db.collection("users").document(user_id).update({
            "subscription.plan": new_plan,
            "subscription.status": update_data["status"],
            "subscription.current_period_start": update_data["current_period_start"],
            "subscription.current_period_end": update_data["current_period_end"],
            "web_scan_credits": new_tier["web_scan_credits"],
            "pdf_scan_credits": new_tier["pdf_scan_credits"],
            "updated_at": datetime.now(CET)
        })
        
        logger.info(f"Updated subscription for user {user_id}: {current_plan} -> {new_plan}")
        
        return {
            "subscription_id": update_data["subscription_id"],
            "status": update_data["status"],
            "plan": new_plan,
            "web_scan_credits": new_tier["web_scan_credits"],
            "pdf_scan_credits": new_tier["pdf_scan_credits"]
        }
    
    def downgrade_to_free(self, user_id: str):
        """
        Downgrade user to free plan when subscription is deleted.
        
        Args:
            user_id: Firebase user ID
        """
        self.db.collection("users").document(user_id).update({
            "subscription.plan": "free",
            "subscription.status": "canceled",
            "subscription.stripe_subscription_id": firestore.DELETE_FIELD,
            "updated_at": datetime.now(CET)
        })
        
        # Reset credits to free tier
        credit_service.reset_to_free_tier(user_id)
        
        logger.info(f"Downgraded user {user_id} to free plan")
    
    def cleanup_incomplete_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Cleanup an incomplete subscription when user cancels payment.
        
        This method:
        1. Cancels the incomplete Stripe subscription
        2. Resets the user's subscription data to free plan defaults
        
        CRITICAL: This should only be called when the user explicitly cancels
        the payment modal, not when payment fails during retries.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Updated subscription details (free plan)
        """
        try:
            user_doc = self.db.collection("users").document(user_id).get()
            
            if not user_doc.exists:
                logger.warning(f"User {user_id} not found for incomplete subscription cleanup")
                return {"plan": "free", "status": "active", "cleaned_up": False}
            
            user_data = user_doc.to_dict()
            subscription = user_data.get("subscription", {})
            stripe_subscription_id = subscription.get("stripe_subscription_id")
            current_status = subscription.get("status", "")
            
            # Only cleanup if the subscription is incomplete
            if current_status not in ["incomplete", "incomplete_expired"]:
                logger.info(f"User {user_id} subscription status is '{current_status}', no cleanup needed")
                return {
                    "plan": subscription.get("plan", "free"),
                    "status": current_status,
                    "cleaned_up": False
                }
            
            # Cancel the incomplete subscription in Stripe
            if stripe_subscription_id:
                try:
                    import stripe
                    stripe.Subscription.delete(stripe_subscription_id)
                    logger.info(f"Cancelled incomplete Stripe subscription {stripe_subscription_id} for user {user_id}")
                except Exception as stripe_error:
                    logger.warning(f"Failed to cancel Stripe subscription {stripe_subscription_id}: {stripe_error}")
                    # Continue with cleanup even if Stripe cancellation fails
            
            # Reset user's subscription to free plan defaults
            # Keep the stripe_customer_id for future subscriptions
            stripe_customer_id = subscription.get("stripe_customer_id")
            
            reset_data = {
                "subscription": {
                    "plan": "free",
                    "status": "active",
                    "stripe_customer_id": stripe_customer_id,  # Preserve for future use
                },
                "updated_at": datetime.now(CET)
            }
            
            self.db.collection("users").document(user_id).set(reset_data, merge=True)
            
            logger.info(f"Cleaned up incomplete subscription for user {user_id}, reset to free plan")
            
            return {
                "plan": "free",
                "status": "active",
                "stripe_customer_id": stripe_customer_id,
                "cleaned_up": True
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up incomplete subscription for user {user_id}: {e}")
            raise
    
    def sync_subscription_from_stripe(self, user_id: str) -> Dict[str, Any]:
        """
        Sync subscription status from Stripe to Firestore.
        
        This can be called after payment confirmation as a fallback
        if webhook hasn't processed yet.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Updated subscription details
        """
        user_doc = self.db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            return {"plan": "free", "status": "active", "synced": False}
        
        user_data = user_doc.to_dict()
        subscription = user_data.get("subscription", {})
        stripe_subscription_id = subscription.get("stripe_subscription_id")
        
        if not stripe_subscription_id:
            return {"plan": subscription.get("plan", "free"), "status": subscription.get("status", "active"), "synced": False}
        
        # Get current status from Stripe
        stripe_subscription = stripe_service.get_subscription(stripe_subscription_id)
        
        status = stripe_subscription.status
        period_start = datetime.fromtimestamp(stripe_subscription.current_period_start, tz=CET)
        period_end = datetime.fromtimestamp(stripe_subscription.current_period_end, tz=CET)
        cancel_at_period_end = stripe_subscription.cancel_at_period_end
        
        # Update Firestore
        self.db.collection("users").document(user_id).update({
            "subscription.status": status,
            "subscription.current_period_start": period_start,
            "subscription.current_period_end": period_end,
            "subscription.cancel_at_period_end": cancel_at_period_end,
            "updated_at": datetime.now(CET)
        })
        
        logger.info(f"Synced subscription from Stripe for user {user_id}: status={status}")
        
        return {
            "plan": subscription.get("plan", "free"),
            "status": status,
            "current_period_start": period_start,
            "current_period_end": period_end,
            "cancel_at_period_end": cancel_at_period_end,
            "web_scan_credits": user_data.get("web_scan_credits", 0),
            "pdf_scan_credits": user_data.get("pdf_scan_credits", 0),
            "synced": True
        }


# Global subscription service instance
subscription_service = SubscriptionService()
