#!/usr/bin/env python3
"""
LumTrails Pricing Service - Usage Service

Handles usage statistics and history.
"""
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore

from services.stripe_service import stripe_service

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")


class UsageService:
    """Service for managing usage statistics and history"""
    
    def __init__(self):
        """Initialize usage service"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.db = firestore.Client(project=self.project_id)
    
    def get_usage_history(
        self,
        user_id: str,
        limit: int = 30,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get credit usage history from daily summary collection.
        
        Args:
            user_id: Firebase user ID
            limit: Maximum number of days to return
            offset: Offset for pagination
        
        Returns:
            List of daily usage summary records
        """
        try:
            query = self.db.collection("credit_usage_daily_summary")\
                .where("user_id", "==", user_id)\
                .order_by("date", direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .offset(offset)
            
            docs = query.stream()
            
            history = []
            for doc in docs:
                data = doc.to_dict()
                
                history.append({
                    "id": doc.id,
                    "date": data.get("date"),
                    "total_web_credits_used": data.get("total_web_credits_used", 0),
                    "total_pdf_credits_used": data.get("total_pdf_credits_used", 0),
                    "scan_count": data.get("scan_count", 0)
                })
            
            logger.info(f"Retrieved {len(history)} daily usage records for user {user_id}")
            return history
        except Exception as e:
            logger.error(f"Error getting usage history for user {user_id}: {e}", exc_info=True)
            return []
    
    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get usage statistics from daily summary collection.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Usage statistics
        """
        try:
            now = datetime.now(CET)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_start_str = month_start.strftime('%Y-%m-%d')
            
            query = self.db.collection("credit_usage_daily_summary")\
                .where("user_id", "==", user_id)
            
            docs = query.stream()
            
            total_web_scans = 0
            total_pdf_scans = 0
            all_time_web_scans = 0
            all_time_pdf_scans = 0
            
            for doc in docs:
                data = doc.to_dict()
                date_str = data.get("date", "")
                
                web_credits = data.get("total_web_credits_used", 0)
                pdf_credits = data.get("total_pdf_credits_used", 0)
                
                all_time_web_scans += web_credits
                all_time_pdf_scans += pdf_credits
                
                if date_str >= month_start_str:
                    total_web_scans += web_credits
                    total_pdf_scans += pdf_credits
            
            # Get API keys count
            api_keys_count = 0
            try:
                api_keys_query = self.db.collection("api_keys")\
                    .where("user_id", "==", user_id)\
                    .where("revoked", "==", False)
                api_keys_docs = api_keys_query.stream()
                api_keys_count = sum(1 for _ in api_keys_docs)
            except Exception as e:
                logger.error(f"Error counting API keys: {e}")
            
            # Get integrations count
            integrations_stats = {"github": 0, "slack": 0, "notion": 0}
            try:
                user_integrations_ref = self.db.collection("user_integrations").document(user_id)
                user_integrations_doc = user_integrations_ref.get()
                
                if user_integrations_doc.exists:
                    integrations_data = user_integrations_doc.to_dict()
                    integrations = integrations_data.get("integrations", {})
                    
                    for platform in ["github", "slack", "notion"]:
                        config = integrations.get(platform, {}).get("config", {})
                        if config.get("connected", False):
                            integrations_stats[platform] = 1
            except Exception as e:
                logger.error(f"Error counting integrations: {e}")
            
            logger.info(f"Retrieved usage stats for user {user_id}: "
                       f"current={total_web_scans}w/{total_pdf_scans}p, "
                       f"all_time={all_time_web_scans}w/{all_time_pdf_scans}p")
            
            return {
                "current_month": {
                    "web_scans": total_web_scans,
                    "pdf_scans": total_pdf_scans,
                    "period_start": month_start.isoformat()
                },
                "all_time": {
                    "web_scans": all_time_web_scans,
                    "pdf_scans": all_time_pdf_scans
                },
                "api_keys_count": api_keys_count,
                "integrations": integrations_stats
            }
        except Exception as e:
            logger.error(f"Error getting usage stats for user {user_id}: {e}", exc_info=True)
            now = datetime.now(CET)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return {
                "current_month": {
                    "web_scans": 0,
                    "pdf_scans": 0,
                    "period_start": month_start.isoformat()
                },
                "all_time": {
                    "web_scans": 0,
                    "pdf_scans": 0
                },
                "api_keys_count": 0,
                "integrations": {}
            }
    
    def get_invoices(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get invoices for a user (credit purchases + subscriptions).
        
        Args:
            user_id: Firebase user ID
            limit: Maximum number of records
        
        Returns:
            List of invoice records
        """
        try:
            invoices = []
            
            # Get legacy credit purchases from Firestore
            query = self.db.collection("credit_purchases")\
                .where(filter=firestore.FieldFilter("user_id", "==", user_id))\
                .where(filter=firestore.FieldFilter("status", "==", "completed"))\
                .order_by("created_at", direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                created_at = data.get("created_at")
                if created_at and hasattr(created_at, 'isoformat'):
                    created_at = created_at.isoformat()
                elif created_at:
                    try:
                        created_at = created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    except:
                        created_at = str(created_at)
                
                package_type = data.get("package_type", "")
                amount = data.get("amount", 0)
                
                if "web" in package_type.lower():
                    description = f"Web Scan Credits - {amount} credits"
                elif "pdf" in package_type.lower():
                    description = f"PDF Scan Credits - {amount} credits"
                else:
                    description = f"Credit Purchase - {amount} credits"
                
                invoices.append({
                    "id": doc.id,
                    "description": description,
                    "amount": data.get("price", 0),
                    "currency": data.get("currency", "eur").upper(),
                    "created_at": created_at or datetime.now(CET).isoformat(),
                    "invoice_url": None,
                    "type": "credit_purchase",
                    "package_type": package_type,
                    "credits": amount
                })
            
            logger.info(f"Found {len(invoices)} credit purchase invoices for user {user_id}")
            
            # Get subscription invoices from Stripe
            user_doc = self.db.collection("users").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                subscription_data = user_data.get("subscription", {})
                stripe_customer_id = subscription_data.get("stripe_customer_id")
                
                if stripe_customer_id:
                    try:
                        stripe_invoices = stripe_service.list_invoices(
                            customer_id=stripe_customer_id,
                            limit=limit
                        )
                        invoices.extend(stripe_invoices)
                        logger.info(f"Found {len(stripe_invoices)} subscription invoices for user {user_id}")
                    except Exception as stripe_error:
                        logger.warning(f"Failed to fetch Stripe invoices for user {user_id}: {stripe_error}")
            
            # Sort by date
            invoices.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            invoices = invoices[:limit]
            
            logger.info(f"Retrieved {len(invoices)} total invoices for user {user_id}")
            return invoices
        except Exception as e:
            logger.error(f"Error getting invoices for user {user_id}: {e}", exc_info=True)
            return []


# Global usage service instance
usage_service = UsageService()
