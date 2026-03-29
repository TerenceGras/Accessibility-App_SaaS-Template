#!/usr/bin/env python3
"""
LumTrails Pricing Service - Webhook Handler

Main webhook router that dispatches events to appropriate handlers.
Uses idempotency to prevent duplicate processing.
"""
import os
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Header
from google.cloud import secretmanager, firestore
from datetime import datetime
from zoneinfo import ZoneInfo

from services.stripe_service import stripe_service
from services.subscription_service import subscription_service
from services.credit_service import credit_service
from webhooks.idempotency import idempotency_service
from notifications.email import send_subscription_upgrade_email
from notifications.slack import (
    notify_subscription_created,
    notify_subscription_updated,
    notify_subscription_deleted
)

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")

router = APIRouter(tags=["webhooks"])


def get_webhook_secret() -> str:
    """Get Stripe webhook secret from Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        secret_name = f"projects/{project_id}/secrets/stripe-webhook-secret/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        secret = response.payload.data.decode("UTF-8").strip()
        return secret
    except Exception as e:
        logger.error(f"Failed to get webhook secret: {e}")
        raise


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhook events.
    
    This is the SINGLE entry point for all Stripe webhooks.
    Events are deduplicated using the idempotency service.
    
    Supported events:
    - checkout.session.completed: New subscription checkout completed
    - invoice.payment_succeeded: Payment confirmed - ACTIVATE subscription here
    - invoice.payment_failed: Payment failed
    - customer.subscription.updated: Status changes (cancel at period end, etc.)
    - customer.subscription.deleted: Subscription fully canceled
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    try:
        payload = await request.body()
        webhook_secret = get_webhook_secret()
        
        try:
            event = stripe_service.verify_webhook_signature(
                payload=payload,
                signature=stripe_signature,
                webhook_secret=webhook_secret
            )
        except Exception as sig_error:
            logger.error(f"Webhook signature verification failed: {sig_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook signature verification failed"
            )
        
        event_id = event["id"]
        event_type = event["type"]
        data = event["data"]["object"]
        
        # Check for duplicate event
        if idempotency_service.is_event_processed(event_id):
            logger.info(f"Skipping duplicate event: {event_id} ({event_type})")
            return {"success": True, "message": "Already processed"}
        
        logger.info(f"Processing Stripe webhook: {event_type} (event_id: {event_id})")
        
        # Dispatch to appropriate handler
        user_id = None
        
        if event_type == "checkout.session.completed":
            user_id = await handle_checkout_completed(data)
        
        elif event_type == "invoice.payment_succeeded":
            user_id = await handle_invoice_payment_succeeded(data)
        
        elif event_type == "invoice.payment_failed":
            user_id = await handle_invoice_payment_failed(data)
        
        elif event_type == "customer.subscription.updated":
            user_id = await handle_subscription_updated(data)
        
        elif event_type == "customer.subscription.deleted":
            user_id = await handle_subscription_deleted(data)
        
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        # Mark event as processed
        idempotency_service.mark_event_processed(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            details={"processed_at": datetime.now(CET).isoformat()}
        )
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def handle_checkout_completed(session: Dict[str, Any]) -> str:
    """
    Handle checkout.session.completed event.
    
    THIS IS THE PRIMARY EVENT FOR SUBSCRIPTION ACTIVATION VIA CHECKOUT.
    
    When payment_status is 'paid' and mode is 'subscription':
    - The payment is confirmed
    - The subscription exists (session.subscription contains the ID)
    - We activate the subscription and grant credits here
    
    Returns:
        user_id if found, None otherwise
    """
    import stripe
    
    session_id = session["id"]
    mode = session.get("mode")
    payment_status = session.get("payment_status")
    subscription_id = session.get("subscription")
    
    user_id = session.get("metadata", {}).get("firebase_user_id")
    plan = session.get("metadata", {}).get("plan")
    interval = session.get("metadata", {}).get("interval", "monthly")
    customer_id = session.get("customer")
    
    logger.info(f"Checkout completed: session={session_id}, mode={mode}, "
               f"payment_status={payment_status}, subscription={subscription_id}, "
               f"user={user_id}, plan={plan}, interval={interval}")
    
    # Only process subscription checkouts with confirmed payment
    if mode != "subscription":
        logger.info(f"Checkout session {session_id} is not a subscription (mode={mode}), skipping")
        return user_id
    
    if payment_status != "paid":
        logger.info(f"Checkout session {session_id} payment not confirmed (status={payment_status}), skipping")
        return user_id
    
    if not subscription_id:
        logger.error(f"Checkout session {session_id} has no subscription ID")
        return user_id
    
    if not user_id:
        logger.error(f"Checkout session {session_id} has no firebase_user_id in metadata")
        return None
    
    # Get subscription details from Stripe
    try:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    except Exception as e:
        logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
        return user_id
    
    # Get user info for notifications
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    db = firestore.Client(project=project_id)
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    user_email = user_data.get("email", "unknown")
    user_name = user_data.get("display_name") or user_data.get("name") or ""
    user_language = user_data.get("language", "en")
    old_plan = user_data.get("subscription", {}).get("plan", "free")
    
    # Activate subscription and grant credits
    logger.info(f"ACTIVATING SUBSCRIPTION from checkout.session.completed: "
               f"user={user_id}, plan={plan}, interval={interval}, subscription={subscription_id}")
    
    result = subscription_service.activate_subscription(
        user_id=user_id,
        subscription_id=subscription_id,
        plan=plan,
        interval=interval,
        status="active",
        current_period_start=stripe_subscription.current_period_start,
        current_period_end=stripe_subscription.current_period_end,
        customer_id=customer_id
    )
    
    # If already activated (idempotency), skip notifications
    if result.get("already_activated"):
        logger.info(f"Subscription already activated for user {user_id}, skipping notifications")
        return user_id
    
    # Send upgrade email
    if user_email and user_email != "unknown":
        await send_subscription_upgrade_email(
            email=user_email,
            name=user_name,
            old_tier=old_plan,
            new_tier=plan,
            interval=interval,
            language=user_language
        )
    
    # Send Slack notification
    await notify_subscription_created(
        email=user_email,
        user_id=user_id,
        plan=plan,
        interval=interval
    )
    
    logger.info(f"Subscription activated successfully for user {user_id}: {plan} ({interval})")
    
    return user_id


async def handle_invoice_payment_succeeded(invoice: Dict[str, Any]) -> str:
    """
    Handle invoice.payment_succeeded event.
    
    THIS IS THE SINGLE SOURCE OF TRUTH FOR SUBSCRIPTION ACTIVATION.
    
    When this event fires for a subscription invoice, we:
    1. Activate the subscription in Firestore
    2. Grant credits to the user
    3. Send upgrade email
    4. Send Slack notification
    
    Returns:
        user_id if found, None otherwise
    """
    import stripe
    
    invoice_id = invoice.get("id")
    billing_reason = invoice.get("billing_reason")  # 'subscription_create', 'subscription_cycle', etc.
    
    # Get subscription ID - can be a string or an object with 'id' field
    subscription_field = invoice.get("subscription")
    if isinstance(subscription_field, dict):
        subscription_id = subscription_field.get("id")
    else:
        subscription_id = subscription_field
    
    # Also check subscription_details for expanded data
    if not subscription_id:
        subscription_details = invoice.get("subscription_details", {})
        if subscription_details:
            metadata = subscription_details.get("metadata", {})
            logger.info(f"Invoice {invoice_id}: subscription_details metadata = {metadata}")
    
    # Log invoice structure for debugging
    logger.info(f"Invoice {invoice_id}: subscription_field type={type(subscription_field)}, "
               f"value={subscription_field}, billing_reason={billing_reason}")
    
    if not subscription_id:
        # Check if this is a checkout session invoice by looking at lines
        lines = invoice.get("lines", {}).get("data", [])
        for line in lines:
            if line.get("subscription"):
                sub_field = line.get("subscription")
                if isinstance(sub_field, dict):
                    subscription_id = sub_field.get("id")
                else:
                    subscription_id = sub_field
                logger.info(f"Found subscription ID in invoice line items: {subscription_id}")
                break
    
    if not subscription_id:
        logger.info(f"Invoice {invoice_id} paid but no subscription attached (billing_reason={billing_reason})")
        return None
    
    # Get subscription details from Stripe
    try:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    except Exception as e:
        logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
        return None
    
    user_id = stripe_subscription.metadata.get("firebase_user_id")
    plan = stripe_subscription.metadata.get("plan", "standard")
    interval = stripe_subscription.metadata.get("interval", "monthly")
    customer_id = stripe_subscription.customer
    
    if not user_id:
        # Try to find user by customer ID in Firestore
        logger.warning(f"No firebase_user_id in subscription {subscription_id} metadata, trying customer lookup")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        # Look up user by stripe_customer_id
        users_query = db.collection("users").where("subscription.stripe_customer_id", "==", customer_id).limit(1)
        users = list(users_query.stream())
        
        if users:
            user_id = users[0].id
            logger.info(f"Found user {user_id} by customer ID {customer_id}")
        else:
            logger.error(f"Invoice paid but cannot find user for subscription {subscription_id}")
            return None
    
    logger.info(f"Invoice payment succeeded: invoice={invoice_id}, subscription={subscription_id}, "
               f"user={user_id}, plan={plan}, billing_reason={billing_reason}")
    
    # Get user info for notifications
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    db = firestore.Client(project=project_id)
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    user_email = user_data.get("email", "unknown")
    user_name = user_data.get("display_name") or user_data.get("name") or ""
    user_language = user_data.get("language", "en")
    old_plan = user_data.get("subscription", {}).get("plan", "free")
    previous_status = user_data.get("subscription", {}).get("status", "incomplete")
    
    # Activate subscription and grant credits
    subscription_service.activate_subscription(
        user_id=user_id,
        subscription_id=subscription_id,
        plan=plan,
        interval=interval,
        status="active",
        current_period_start=stripe_subscription.current_period_start,
        current_period_end=stripe_subscription.current_period_end,
        customer_id=customer_id
    )
    
    # Send notifications based on billing reason
    if billing_reason == "subscription_create":
        # New subscription - send upgrade email and Slack notification
        logger.info(f"NEW SUBSCRIPTION ACTIVATED for user {user_id}: {plan} ({interval})")
        
        if user_email and user_email != "unknown":
            await send_subscription_upgrade_email(
                email=user_email,
                name=user_name,
                old_tier=old_plan,
                new_tier=plan,
                interval=interval,
                language=user_language
            )
        
        await notify_subscription_created(
            email=user_email,
            user_id=user_id,
            plan=plan,
            interval=interval
        )
    
    elif billing_reason == "subscription_cycle":
        # Recurring payment - just log, credits are already renewed
        logger.info(f"Recurring payment succeeded for user {user_id}: {plan}")
    
    return user_id


async def handle_invoice_payment_failed(invoice: Dict[str, Any]) -> str:
    """
    Handle invoice.payment_failed event.
    
    Log the failure and potentially notify the user.
    The subscription will move to 'past_due' status which will be
    handled by handle_subscription_updated.
    
    Returns:
        user_id if found, None otherwise
    """
    import stripe
    
    invoice_id = invoice.get("id")
    subscription_id = invoice.get("subscription")
    
    if not subscription_id:
        logger.info(f"Invoice {invoice_id} failed but no subscription attached")
        return None
    
    try:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        user_id = stripe_subscription.metadata.get("firebase_user_id")
        
        logger.warning(f"Invoice payment failed: invoice={invoice_id}, "
                      f"subscription={subscription_id}, user={user_id}")
        
        # TODO: Send payment failed notification email
        
        return user_id
    except Exception as e:
        logger.error(f"Error handling invoice payment failed: {e}")
        return None


async def handle_subscription_updated(subscription: Dict[str, Any]) -> str:
    """
    Handle customer.subscription.updated event.
    
    This handles status changes like:
    - cancel_at_period_end changing
    - Status changing (active -> past_due, canceled, etc.)
    
    NOTE: Primary subscription activation happens in checkout.session.completed.
    This handler is a fallback that also calls activate_subscription for 
    incomplete -> active transitions (with idempotency protection).
    
    Returns:
        user_id if found, None otherwise
    """
    subscription_id = subscription.get("id")
    user_id = subscription.get("metadata", {}).get("firebase_user_id")
    
    if not user_id:
        logger.warning("Subscription updated without firebase_user_id metadata")
        return None
    
    plan = subscription.get("metadata", {}).get("plan", "standard")
    interval = subscription.get("metadata", {}).get("interval", "monthly")
    new_status = subscription.get("status")
    cancel_at_period_end = subscription.get("cancel_at_period_end", False)
    customer_id = subscription.get("customer")
    current_period_start = subscription.get("current_period_start")
    current_period_end = subscription.get("current_period_end")
    
    # Get current user data for comparison
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    db = firestore.Client(project=project_id)
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    previous_status = user_data.get("subscription", {}).get("status", "incomplete")
    user_email = user_data.get("email", "unknown")
    
    logger.info(f"Subscription updated: user={user_id}, {previous_status} -> {new_status}, "
               f"cancel_at_period_end={cancel_at_period_end}")
    
    # Handle incomplete -> active as a fallback (with idempotency protection)
    # Primary activation should happen in checkout.session.completed
    if previous_status in ["incomplete", None, ""] and new_status == "active":
        logger.info(f"Subscription activation fallback via subscription.updated: user={user_id}")
        
        result = subscription_service.activate_subscription(
            user_id=user_id,
            subscription_id=subscription_id,
            plan=plan,
            interval=interval,
            status="active",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            customer_id=customer_id
        )
        
        # Only send notifications if this was the actual activation (not a duplicate)
        if not result.get("already_activated"):
            user_name = user_data.get("display_name") or user_data.get("name") or ""
            user_language = user_data.get("language", "en")
            old_plan = user_data.get("subscription", {}).get("plan", "free")
            
            if user_email and user_email != "unknown":
                await send_subscription_upgrade_email(
                    email=user_email,
                    name=user_name,
                    old_tier=old_plan,
                    new_tier=plan,
                    interval=interval,
                    language=user_language
                )
            
            await notify_subscription_created(
                email=user_email,
                user_id=user_id,
                plan=plan,
                interval=interval
            )
        
        return user_id
    
    # For other status changes, just update status (no credit changes)
    subscription_service.update_subscription_status(
        user_id=user_id,
        status=new_status,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end
    )
    
    # Send Slack notification for status changes
    if new_status != previous_status:
        await notify_subscription_updated(
            email=user_email,
            user_id=user_id,
            old_status=previous_status,
            new_status=new_status,
            plan=plan,
            interval=interval
        )
    
    return user_id


async def handle_subscription_deleted(subscription: Dict[str, Any]) -> str:
    """
    Handle customer.subscription.deleted event.
    
    This fires when a subscription is fully canceled (not just set to cancel at period end).
    Downgrade the user to free plan and revoke premium features.
    
    Returns:
        user_id if found, None otherwise
    """
    user_id = subscription.get("metadata", {}).get("firebase_user_id")
    plan = subscription.get("metadata", {}).get("plan", "unknown")
    
    if not user_id:
        logger.warning("Subscription deleted without firebase_user_id metadata")
        return None
    
    logger.info(f"Subscription deleted: user={user_id}, previous_plan={plan}")
    
    # Get user email for notification
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    db = firestore.Client(project=project_id)
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    user_email = user_data.get("email", "unknown")
    
    # Downgrade to free plan
    subscription_service.downgrade_to_free(user_id)
    
    # Revoke API keys
    await revoke_all_api_keys_for_user(db, user_id)
    
    # Disable integrations
    await disable_all_integrations_for_user(db, user_id)
    
    # Send Slack notification
    await notify_subscription_deleted(
        email=user_email,
        user_id=user_id,
        plan=plan
    )
    
    return user_id


async def revoke_all_api_keys_for_user(db, user_id: str) -> int:
    """
    Revoke all API keys for a user during subscription downgrade.
    
    Returns:
        Number of keys revoked
    """
    try:
        now = datetime.now(CET)
        
        active_keys = db.collection("api_keys")\
            .where('user_id', '==', user_id)\
            .where('revoked', '==', False)\
            .stream()
        
        count = 0
        for doc in active_keys:
            doc.reference.update({
                'revoked': True,
                'revoked_at': now,
                'revoked_reason': 'subscription_downgrade'
            })
            count += 1
        
        if count > 0:
            logger.info(f"Revoked {count} API keys for user {user_id}")
        
        return count
    except Exception as e:
        logger.error(f"Error revoking API keys for user {user_id}: {e}")
        return 0


async def disable_all_integrations_for_user(db, user_id: str) -> int:
    """
    Disable all integrations for a user during subscription downgrade.
    
    Returns:
        Number of integrations disabled
    """
    try:
        integrations_ref = db.collection("user_integrations").document(user_id)
        integrations_doc = integrations_ref.get()
        
        if not integrations_doc.exists:
            return 0
        
        integrations_data = integrations_doc.to_dict()
        integrations = integrations_data.get("integrations", {})
        
        count = 0
        update_data = {}
        
        for platform, config in integrations.items():
            if config.get("enabled", False):
                update_data[f"integrations.{platform}.enabled"] = False
                update_data[f"integrations.{platform}.disabled_reason"] = "subscription_downgrade"
                update_data[f"integrations.{platform}.disabled_at"] = datetime.now(CET)
                count += 1
        
        if count > 0:
            integrations_ref.update(update_data)
            logger.info(f"Disabled {count} integrations for user {user_id}")
        
        return count
    except Exception as e:
        logger.error(f"Error disabling integrations for user {user_id}: {e}")
        return 0
