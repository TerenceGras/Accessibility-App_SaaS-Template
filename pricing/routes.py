#!/usr/bin/env python3
"""
LumTrails Pricing Service - API Routes

REST API endpoints for subscription management, billing, and usage.
Simplified structure with clear separation of concerns.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Depends, status
from google.cloud import firestore
import httpx

from models import (
    CreateCheckoutSessionRequest,
    UpdateSubscriptionRequest,
    BillingInfoRequest,
    AddPaymentMethodRequest
)
from auth_middleware import get_current_user, get_optional_user
from config import PRICING_TIERS
from services.subscription_service import subscription_service
from services.billing_service import billing_service
from services.usage_service import usage_service

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")

router = APIRouter(tags=["pricing"])


async def get_service_auth_token(audience: str) -> str:
    """Get an ID token for authenticated service-to-service calls."""
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token
        
        id_token = google.oauth2.id_token.fetch_id_token(
            google.auth.transport.requests.Request(),
            audience
        )
        return id_token
    except Exception as e:
        logger.error(f"Failed to get service auth token: {e}")
        return None


# =============================================================================
# Pricing Tiers
# =============================================================================

@router.get("/tiers")
async def get_pricing_tiers():
    """Get all available pricing tiers"""
    return {"tiers": PRICING_TIERS}


# =============================================================================
# Subscription Endpoints
# =============================================================================

@router.get("/subscription")
async def get_subscription(user: Dict = Depends(get_current_user)):
    """Get current subscription details"""
    try:
        subscription = subscription_service.get_user_subscription(user["user_id"])
        return {"success": True, "subscription": subscription}
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for subscription.
    
    Returns a checkout URL that redirects the user to Stripe's hosted payment page.
    After payment, the user is redirected to the success_url and the subscription
    is activated via the invoice.payment_succeeded webhook.
    """
    try:
        result = subscription_service.create_checkout_session(
            user_id=user["user_id"],
            email=user["email"],
            plan=request.plan,
            interval=request.interval,
            name=user.get("name")
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/subscribe")
async def subscribe(
    request: CreateCheckoutSessionRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Create a new subscription via Stripe Checkout Session.
    
    This endpoint is kept for backwards compatibility with the frontend.
    It returns a checkout_url that the frontend should redirect to.
    """
    try:
        result = subscription_service.create_checkout_session(
            user_id=user["user_id"],
            email=user["email"],
            plan=request.plan,
            interval=request.interval,
            name=user.get("name")
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/subscription/cleanup-incomplete")
async def cleanup_incomplete_subscription(user: Dict = Depends(get_current_user)):
    """
    Cleanup an incomplete subscription when user cancels payment.
    
    Call this when the payment modal is closed without completing payment.
    This ensures no 'incomplete' subscription data remains in the user's profile.
    """
    try:
        result = subscription_service.cleanup_incomplete_subscription(user["user_id"])
        return {"success": True, "subscription": result}
    except Exception as e:
        logger.error(f"Error cleaning up incomplete subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/subscription/sync")
async def sync_subscription(user: Dict = Depends(get_current_user)):
    """
    Sync subscription status from Stripe to Firestore.
    
    Can be called after payment confirmation as a fallback if webhook hasn't processed yet.
    """
    try:
        subscription = subscription_service.sync_subscription_from_stripe(user["user_id"])
        return {"success": True, "subscription": subscription}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error syncing subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cancel-subscription")
async def cancel_subscription(
    immediate: bool = False,
    user: Dict = Depends(get_current_user)
):
    """Cancel current subscription"""
    try:
        result = subscription_service.cancel_subscription(
            user_id=user["user_id"],
            immediate=immediate
        )
        return {"success": True, "subscription": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/resume-subscription")
async def resume_subscription(user: Dict = Depends(get_current_user)):
    """Resume a cancelled subscription"""
    try:
        result = subscription_service.resume_subscription(user["user_id"])
        return {"success": True, "subscription": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error resuming subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/update-subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    user: Dict = Depends(get_current_user)
):
    """Update subscription to a different plan"""
    try:
        result = subscription_service.update_subscription_plan(
            user_id=user["user_id"],
            new_plan=request.new_plan
        )
        return {"success": True, "subscription": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Usage Endpoints
# =============================================================================

@router.get("/usage-history")
async def get_usage_history(
    limit: int = 50,
    offset: int = 0,
    user: Dict = Depends(get_current_user)
):
    """Get credit usage history"""
    try:
        history = usage_service.get_usage_history(
            user_id=user["user_id"],
            limit=limit,
            offset=offset
        )
        return {"success": True, "history": history, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error getting usage history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/usage-stats")
async def get_usage_stats(user: Dict = Depends(get_current_user)):
    """Get usage statistics"""
    try:
        stats = usage_service.get_usage_stats(user["user_id"])
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/invoices")
async def get_invoices(
    limit: int = 50,
    user: Dict = Depends(get_current_user)
):
    """Get purchase history and invoices"""
    try:
        invoices = usage_service.get_invoices(
            user_id=user["user_id"],
            limit=limit
        )
        return {"success": True, "invoices": invoices}
    except Exception as e:
        logger.error(f"Error getting invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Billing Endpoints
# =============================================================================

@router.get("/billing-info")
async def get_billing_info(user: Dict = Depends(get_current_user)):
    """Get billing information"""
    try:
        info = billing_service.get_billing_info(user["user_id"])
        return {"success": True, "billing_info": info}
    except Exception as e:
        logger.error(f"Error getting billing info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/billing-info")
async def update_billing_info(
    request: BillingInfoRequest,
    user: Dict = Depends(get_current_user)
):
    """Update billing information"""
    try:
        info = billing_service.update_billing_info(
            user_id=user["user_id"],
            company_name=request.company_name,
            vat_number=request.vat_number,
            address=request.address
        )
        return {"success": True, "billing_info": info}
    except Exception as e:
        logger.error(f"Error updating billing info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/payment-method")
async def add_payment_method(
    request: AddPaymentMethodRequest,
    user: Dict = Depends(get_current_user)
):
    """Add payment method"""
    try:
        subscription = subscription_service.get_user_subscription(user["user_id"])
        stripe_customer_id = subscription.get("stripe_customer_id")
        
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe customer found. Please create a subscription first."
            )
        
        payment_method = billing_service.add_payment_method(
            user_id=user["user_id"],
            stripe_customer_id=stripe_customer_id,
            payment_method_id=request.payment_method_id,
            set_as_default=request.set_as_default
        )
        return {"success": True, "payment_method": payment_method}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/payment-method/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: str,
    user: Dict = Depends(get_current_user)
):
    """Remove payment method"""
    try:
        success = billing_service.remove_payment_method(
            user_id=user["user_id"],
            payment_method_id=payment_method_id
        )
        return {"success": success, "message": "Payment method removed successfully"}
    except Exception as e:
        logger.error(f"Error removing payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/payment-method/{payment_method_id}/default")
async def set_default_payment_method(
    payment_method_id: str,
    user: Dict = Depends(get_current_user)
):
    """Set default payment method"""
    try:
        subscription = subscription_service.get_user_subscription(user["user_id"])
        stripe_customer_id = subscription.get("stripe_customer_id")
        
        if not stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe customer found"
            )
        
        success = billing_service.set_default_payment_method(
            user_id=user["user_id"],
            stripe_customer_id=stripe_customer_id,
            payment_method_id=payment_method_id
        )
        return {"success": success, "message": "Default payment method updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/payment-methods")
async def get_payment_methods(user: Dict = Depends(get_current_user)):
    """Get all payment methods"""
    try:
        methods = billing_service.get_payment_methods(user["user_id"])
        return {"success": True, "payment_methods": methods}
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Account Deletion Endpoints
# =============================================================================

@router.get("/account/deletion-status")
async def get_account_deletion_status(user: Dict = Depends(get_current_user)):
    """Check if the user's account is scheduled for deletion."""
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        user_id = user["user_id"]
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return {
                "scheduled": False,
                "deletion_date": None,
                "can_delete_immediately": True,
                "subscription_ends": None
            }
        
        user_data = user_doc.to_dict()
        subscription = user_data.get('subscription', {})
        deletion_scheduled = user_data.get('account_deletion_scheduled', False)
        deletion_date = user_data.get('account_deletion_date')
        
        plan = subscription.get('plan', 'free')
        is_free_plan = plan == 'free'
        cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        current_period_end = subscription.get('current_period_end')
        
        period_end_dt = None
        if current_period_end:
            if hasattr(current_period_end, 'isoformat'):
                period_end_dt = current_period_end
            else:
                period_end_dt = datetime.fromisoformat(str(current_period_end).replace('Z', '+00:00'))
        
        now_cet = datetime.now(CET)
        can_delete_immediately = is_free_plan
        if not is_free_plan and cancel_at_period_end and period_end_dt:
            if period_end_dt.tzinfo is None:
                period_end_dt = period_end_dt.replace(tzinfo=CET)
            can_delete_immediately = period_end_dt <= now_cet
        
        subscription_ends = None
        if not is_free_plan and current_period_end:
            subscription_ends = current_period_end.isoformat() if hasattr(current_period_end, 'isoformat') else current_period_end
        
        deletion_date_str = None
        if deletion_date:
            deletion_date_str = deletion_date.isoformat() if hasattr(deletion_date, 'isoformat') else deletion_date
        
        return {
            "scheduled": deletion_scheduled,
            "deletion_date": deletion_date_str,
            "can_delete_immediately": can_delete_immediately,
            "subscription_ends": subscription_ends
        }
        
    except Exception as e:
        logger.error(f"Error checking deletion status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/account/request-deletion")
async def request_account_deletion(user: Dict = Depends(get_current_user)):
    """Request account deletion."""
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        user_id = user["user_id"]
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user_doc.to_dict()
        subscription = user_data.get('subscription', {})
        
        plan = subscription.get('plan', 'free')
        is_free_plan = plan == 'free'
        cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        current_period_end = subscription.get('current_period_end')
        
        if not is_free_plan and not cancel_at_period_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please cancel your subscription first before requesting account deletion."
            )
        
        now = datetime.now(CET)
        
        subscription_ended = is_free_plan
        end_date = None
        if not is_free_plan and current_period_end:
            if hasattr(current_period_end, 'isoformat'):
                end_date = current_period_end
            else:
                end_date = datetime.fromisoformat(str(current_period_end).replace('Z', '+00:00'))
            
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=CET)
            
            subscription_ended = end_date <= now
        
        if subscription_ended:
            # Delete immediately
            logger.info(f"Deleting account immediately for user {user_id}")
            
            api_url = os.getenv("MAIN_API_URL")
            if not api_url:
                logger.error("MAIN_API_URL environment variable not set")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal configuration error: MAIN_API_URL not set."
                )
            
            auth_token = await get_service_auth_token(api_url)
            if not auth_token:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal authentication error."
                )
            
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{api_url}/admin/delete-user-data/{user_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to delete user data: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to delete account data."
                    )
            
            return {
                "success": True,
                "immediate": True,
                "message": "Your account has been deleted successfully."
            }
        else:
            # Schedule deletion
            deletion_date = end_date
            
            user_ref.update({
                'account_deletion_scheduled': True,
                'account_deletion_date': deletion_date,
                'account_deletion_requested_at': now,
                'updated_at': now
            })
            
            logger.info(f"Scheduled account deletion for user {user_id} on {deletion_date}")
            
            return {
                "success": True,
                "immediate": False,
                "deletion_date": deletion_date.isoformat(),
                "message": f"Your account is scheduled for deletion on {deletion_date.strftime('%B %d, %Y')}."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting account deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/account/cancel-deletion")
async def cancel_account_deletion(user: Dict = Depends(get_current_user)):
    """Cancel a scheduled account deletion."""
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        user_id = user["user_id"]
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user_doc.to_dict()
        
        if not user_data.get('account_deletion_scheduled', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No deletion is scheduled for this account"
            )
        
        user_ref.update({
            'account_deletion_scheduled': False,
            'account_deletion_date': firestore.DELETE_FIELD,
            'account_deletion_requested_at': firestore.DELETE_FIELD,
            'updated_at': datetime.now(CET)
        })
        
        logger.info(f"Cancelled account deletion for user {user_id}")
        
        return {"success": True, "message": "Account deletion has been cancelled."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling account deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Admin Endpoints (Cloud Scheduler Cron Jobs)
# =============================================================================

@router.post("/admin/renew-free-tier-credits")
async def renew_free_tier_credits():
    """Renew weekly web scan and PDF credits for free tier users (40 web + 2 PDF)"""
    try:
        from cronjob import renew_free_plan_weekly_credits
        result = await renew_free_plan_weekly_credits()
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Renewed weekly credits for {result.get('renewed', 0)} free tier users (40 web + 2 PDF)",
                "renewed_count": result.get("renewed", 0),
                "timestamp": result.get("timestamp")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Credit renewal failed: {result.get('error', 'Unknown error')}"
            )
    except Exception as e:
        logger.error(f"Error in admin credit renewal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/admin/renew-monthly-credits")
async def renew_monthly_credits():
    """Renew monthly credits for all active paid subscriptions"""
    try:
        from cronjob import renew_all_credits
        result = await renew_all_credits()
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Renewed credits for {result.get('renewed', 0)} paid users",
                "renewed_count": result.get("renewed", 0),
                "error_count": result.get("errors", 0),
                "timestamp": result.get("timestamp")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Credit renewal failed: {result.get('error', 'Unknown error')}"
            )
    except Exception as e:
        logger.error(f"Error in admin monthly renewal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/admin/process-scheduled-deletions")
async def process_scheduled_deletions():
    """Process scheduled account deletions"""
    try:
        from cronjob import process_scheduled_account_deletions
        result = await process_scheduled_account_deletions()
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Processed {result.get('deleted', 0)} scheduled deletions",
                "deleted_count": result.get("deleted", 0),
                "failed_count": result.get("failed", 0),
                "not_ready_count": result.get("not_ready", 0),
                "timestamp": result.get("timestamp")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scheduled deletion processing failed: {result.get('error', 'Unknown error')}"
            )
    except Exception as e:
        logger.error(f"Error in admin scheduled deletions processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
