#!/usr/bin/env python3
"""
LumTrails Pricing Service - Credit Renewal Cron Job

Scheduled job to renew credits for all users.
All credit renewal jobs use CET timezone for consistency with EU-focused service.
"""
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore

from services.credit_service import credit_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")


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


async def renew_all_credits():
    """
    Renew monthly credits for all active subscriptions.
    
    This function:
    1. Queries all users with active paid subscriptions
    2. Resets their monthly credits based on their plan
    3. Logs the renewal
    """
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        logger.info("Starting monthly credit renewal process")
        
        users_ref = db.collection("users")
        query = users_ref.where("subscription.status", "==", "active")
        
        users = query.stream()
        
        renewed_count = 0
        error_count = 0
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            plan = user_data.get("subscription", {}).get("plan", "free")
            current_period_end = user_data.get("subscription", {}).get("current_period_end")
            
            # Skip free plan users (they have daily/weekly renewal)
            if plan == "free":
                continue
            
            try:
                success = credit_service.renew_paid_user_credits(
                    user_id=user_id,
                    plan=plan,
                    period_end=current_period_end
                )
                
                if success:
                    renewed_count += 1
                    logger.info(f"Renewed credits for user {user_id} ({plan} plan)")
                else:
                    error_count += 1
                    logger.warning(f"Failed to renew credits for user {user_id}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error renewing credits for user {user_id}: {e}")
        
        logger.info(f"Credit renewal complete: {renewed_count} users renewed, {error_count} errors")
        
        return {
            "success": True,
            "renewed": renewed_count,
            "errors": error_count,
            "timestamp": datetime.now(CET).isoformat(),
            "timezone": "Europe/Paris (CET)"
        }
    
    except Exception as e:
        logger.error(f"Error in credit renewal process: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(CET).isoformat(),
            "timezone": "Europe/Paris (CET)"
        }


async def renew_free_plan_weekly_credits():
    """
    Renew weekly web scan and PDF scan credits for free plan users.
    Sets web_scan_credits to 40 and pdf_scan_credits to 2 (no stockpiling).
    Runs every Monday at 00:00 CET.
    """
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        logger.info("Starting weekly credit renewal for free users (CET timezone)")
        
        users_ref = db.collection("users")
        all_users = users_ref.stream()
        
        renewed_count = 0
        
        for user_doc in all_users:
            user_id = user_doc.id
            user_data = user_doc.to_dict()
            
            subscription = user_data.get("subscription", {})
            plan = subscription.get("plan", "free")
            status = subscription.get("status", "active")
            
            # Only renew for users who are on free tier
            if plan != "free" and status == "active":
                continue
            
            try:
                # Renew both web and PDF credits for free users
                web_success = credit_service.renew_free_tier_web_credits(user_id)
                pdf_success = credit_service.renew_free_tier_pdf_credits(user_id)
                if web_success and pdf_success:
                    renewed_count += 1
            except Exception as e:
                logger.error(f"Error renewing weekly credits for user {user_id}: {e}")
        
        logger.info(f"Weekly credit renewal complete: {renewed_count} free users renewed (40 web + 2 PDF)")
        
        return {
            "success": True,
            "renewed": renewed_count,
            "timestamp": datetime.now(CET).isoformat(),
            "timezone": "Europe/Paris (CET)"
        }
    
    except Exception as e:
        logger.error(f"Error in weekly credit renewal: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(CET).isoformat(),
            "timezone": "Europe/Paris (CET)"
        }


async def process_scheduled_account_deletions():
    """
    Process scheduled account deletions.
    Runs daily at 03:00 CET.
    """
    try:
        import httpx
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        api_url = os.getenv("MAIN_API_URL")
        if not api_url:
            logger.error("MAIN_API_URL environment variable not set, cannot process account deletions")
            return
        
        logger.info("Starting scheduled account deletion processing")
        
        now = datetime.now(CET)
        
        users_ref = db.collection("users")
        query = users_ref.where("account_deletion_scheduled", "==", True)
        
        users = query.stream()
        
        deleted_count = 0
        error_count = 0
        skipped_count = 0
        
        auth_token = await get_service_auth_token(api_url)
        if not auth_token:
            logger.error("Failed to get OIDC token for main API call")
            return {
                "success": False,
                "error": "Failed to authenticate with main API",
                "timestamp": datetime.now(CET).isoformat(),
                "timezone": "Europe/Paris (CET)"
            }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            for user_doc in users:
                user_data = user_doc.to_dict()
                user_id = user_doc.id
                deletion_date = user_data.get("account_deletion_date")
                
                if not deletion_date:
                    logger.warning(f"User {user_id} has deletion scheduled but no deletion_date")
                    continue
                
                if hasattr(deletion_date, 'isoformat'):
                    del_date = deletion_date
                else:
                    del_date = datetime.fromisoformat(deletion_date.replace('Z', '+00:00'))
                
                if del_date.tzinfo is None:
                    del_date = del_date.replace(tzinfo=CET)
                
                if del_date > now:
                    skipped_count += 1
                    logger.debug(f"Skipping user {user_id} - deletion scheduled for {del_date}")
                    continue
                
                try:
                    logger.info(f"Deleting account for user {user_id} (scheduled for {del_date})")
                    
                    response = await client.post(
                        f"{api_url}/admin/delete-user-data/{user_id}",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        deleted_count += 1
                        logger.info(f"Successfully deleted account for user {user_id}")
                    else:
                        error_count += 1
                        logger.error(f"Failed to delete user {user_id}: {response.text}")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error deleting user {user_id}: {e}")
        
        logger.info(f"Scheduled deletion processing complete: {deleted_count} deleted, {skipped_count} skipped, {error_count} errors")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "skipped": skipped_count,
            "errors": error_count,
            "timestamp": datetime.now(CET).isoformat(),
            "timezone": "Europe/Paris (CET)"
        }
    
    except Exception as e:
        logger.error(f"Error in scheduled deletion processing: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(CET).isoformat(),
            "timezone": "Europe/Paris (CET)"
        }


if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "weekly-free":
            result = asyncio.run(renew_free_plan_weekly_credits())
        elif sys.argv[1] == "monthly":
            result = asyncio.run(renew_all_credits())
        elif sys.argv[1] == "process-deletions":
            result = asyncio.run(process_scheduled_account_deletions())
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python cronjob.py [weekly-free|monthly|process-deletions]")
            sys.exit(1)
    else:
        result = asyncio.run(renew_all_credits())
    
    print(result)
