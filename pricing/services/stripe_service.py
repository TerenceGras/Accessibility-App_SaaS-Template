#!/usr/bin/env python3
"""
LumTrails Pricing Service - Stripe Service

Handles all Stripe API interactions for subscriptions, payments, and webhooks.
This is a low-level wrapper around the Stripe API.
"""
import os
import logging
import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import secretmanager

from config import PRICING_TIERS, STRIPE_CONFIG, CHECKOUT_SUCCESS_URL, CHECKOUT_CANCEL_URL

logger = logging.getLogger(__name__)

# CET timezone for EU service - all dates stored in CET
CET = ZoneInfo("Europe/Paris")


class StripeService:
    """Low-level service for Stripe API operations"""
    
    def __init__(self):
        """Initialize Stripe service"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self._initialize_stripe()
    
    def _initialize_stripe(self):
        """Initialize Stripe with API key from Secret Manager"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{self.project_id}/secrets/stripe-api-key/versions/latest"
            response = client.access_secret_version(request={"name": secret_name})
            stripe_key = response.payload.data.decode("UTF-8").strip()
            
            stripe.api_key = stripe_key
            stripe.api_version = STRIPE_CONFIG["api_version"]
            stripe.max_network_retries = STRIPE_CONFIG["max_network_retries"]
            
            logger.info("Stripe initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")
            raise
    
    # =========================================================================
    # Customer Operations
    # =========================================================================
    
    def get_or_create_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        existing_customer_id: Optional[str] = None
    ) -> str:
        """
        Get existing Stripe customer or create a new one.
        
        Args:
            user_id: Firebase user ID
            email: Customer email
            name: Customer name (optional)
            existing_customer_id: Existing Stripe customer ID to verify
        
        Returns:
            Stripe customer ID
        """
        try:
            # If we have an existing customer ID, verify it exists
            if existing_customer_id:
                try:
                    customer = stripe.Customer.retrieve(existing_customer_id)
                    if not customer.get("deleted"):
                        return existing_customer_id
                except stripe.error.InvalidRequestError:
                    pass  # Customer doesn't exist, create new one
            
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "firebase_user_id": user_id
                }
            )
            logger.info(f"Created Stripe customer: {customer.id} for user: {user_id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get/create Stripe customer: {e}")
            raise
    
    # =========================================================================
    # Checkout Session Operations (Recommended for new subscriptions)
    # =========================================================================
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        user_id: str,
        plan: str,
        interval: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session for subscription.
        
        This is the RECOMMENDED way to create subscriptions as it handles:
        - Payment collection
        - 3D Secure / SCA
        - Error handling
        - Success/failure redirects
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the plan
            user_id: Firebase user ID (stored in metadata)
            plan: Plan name (standard, business)
            interval: Billing interval (monthly, yearly)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
        
        Returns:
            Dict with checkout_url and session_id
        """
        try:
            success_url = success_url or f"{CHECKOUT_SUCCESS_URL}&session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = cancel_url or CHECKOUT_CANCEL_URL
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    "metadata": {
                        "firebase_user_id": user_id,
                        "plan": plan,
                        "interval": interval
                    }
                },
                metadata={
                    "firebase_user_id": user_id,
                    "plan": plan,
                    "interval": interval
                },
                # Allow promotion codes if you want
                allow_promotion_codes=True,
                # Collect billing address
                billing_address_collection="required"
            )
            
            logger.info(f"Created checkout session: {session.id} for user: {user_id}, plan: {plan}")
            
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
    
    def get_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a checkout session.
        
        Args:
            session_id: Stripe checkout session ID
        
        Returns:
            Session details
        """
        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["subscription", "customer"]
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve checkout session: {e}")
            raise
    
    # =========================================================================
    # Subscription Operations
    # =========================================================================
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve a subscription from Stripe.
        
        Args:
            subscription_id: Stripe subscription ID
        
        Returns:
            Subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """
        Cancel a Stripe subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period
        
        Returns:
            Updated subscription details
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.cancel(subscription_id)
            
            logger.info(f"Cancelled subscription: {subscription_id}, at_period_end: {at_period_end}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at, tz=CET) if subscription.canceled_at else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise
    
    def resume_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Resume a cancelled subscription (before period ends).
        
        Args:
            subscription_id: Stripe subscription ID
        
        Returns:
            Updated subscription details
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            logger.info(f"Resumed subscription: {subscription_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to resume subscription: {e}")
            raise
    
    def update_subscription_plan(self, subscription_id: str, new_price_id: str, plan: str, interval: str) -> Dict[str, Any]:
        """
        Update subscription to a different plan.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID
            plan: New plan name
            interval: New interval
        
        Returns:
            Updated subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_price_id,
                }],
                metadata={
                    "firebase_user_id": subscription.metadata.get("firebase_user_id"),
                    "plan": plan,
                    "interval": interval
                },
                proration_behavior="always_invoice"
            )
            
            logger.info(f"Updated subscription: {subscription_id} to plan: {plan}")
            
            return {
                "subscription_id": updated.id,
                "status": updated.status,
                "current_period_start": datetime.fromtimestamp(updated.current_period_start, tz=CET),
                "current_period_end": datetime.fromtimestamp(updated.current_period_end, tz=CET)
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            raise
    
    # =========================================================================
    # Payment Method Operations
    # =========================================================================
    
    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> Dict[str, Any]:
        """
        Attach payment method to customer.
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
        
        Returns:
            Payment method details
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            logger.info(f"Attached payment method: {payment_method_id} to customer: {customer_id}")
            
            return {
                "payment_method_id": payment_method.id,
                "type": payment_method.type,
                "card": {
                    "brand": payment_method.card.brand,
                    "last4": payment_method.card.last4,
                    "exp_month": payment_method.card.exp_month,
                    "exp_year": payment_method.card.exp_year
                } if payment_method.type == "card" else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise
    
    def set_default_payment_method(self, customer_id: str, payment_method_id: str) -> bool:
        """
        Set default payment method for customer.
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
        
        Returns:
            Success status
        """
        try:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            logger.info(f"Set default payment method: {payment_method_id} for customer: {customer_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to set default payment method: {e}")
            raise
    
    def detach_payment_method(self, payment_method_id: str) -> bool:
        """
        Detach payment method from customer.
        
        Args:
            payment_method_id: Stripe payment method ID
        
        Returns:
            Success status
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Detached payment method: {payment_method_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to detach payment method: {e}")
            raise
    
    def list_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        List all payment methods for customer.
        
        Args:
            customer_id: Stripe customer ID
        
        Returns:
            List of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            
            return [{
                "payment_method_id": pm.id,
                "type": pm.type,
                "card": {
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year
                }
            } for pm in payment_methods.data]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            raise
    
    # =========================================================================
    # Invoice Operations
    # =========================================================================
    
    def list_invoices(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
        
        Returns:
            List of invoices
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            
            result = []
            for inv in invoices.data:
                if inv.status == "paid":
                    plan_name = "Subscription"
                    if inv.lines and inv.lines.data:
                        line = inv.lines.data[0]
                        if line.description:
                            plan_name = line.description
                    
                    result.append({
                        "id": inv.id,
                        "description": plan_name,
                        "amount": inv.amount_paid / 100,  # Convert cents to euros
                        "currency": inv.currency.upper(),
                        "created_at": datetime.fromtimestamp(inv.created, tz=CET).isoformat(),
                        "invoice_url": inv.hosted_invoice_url or inv.invoice_pdf,
                        "type": "subscription"
                    })
            
            return result
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list invoices: {e}")
            raise
    
    # =========================================================================
    # Webhook Verification
    # =========================================================================
    
    def verify_webhook_signature(self, payload: bytes, signature: str, webhook_secret: str) -> Any:
        """
        Verify Stripe webhook signature.
        
        Args:
            payload: Request body
            signature: Stripe-Signature header
            webhook_secret: Webhook signing secret
        
        Returns:
            Verified event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise


# Global Stripe service instance
stripe_service = StripeService()
