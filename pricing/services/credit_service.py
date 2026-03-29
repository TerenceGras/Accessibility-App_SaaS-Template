#!/usr/bin/env python3
"""
LumTrails Pricing Service - Credit Service

Handles all credit-related operations:
- Granting credits on subscription activation
- Deducting credits on scan
- Renewing credits (daily/weekly/monthly)
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore

from config import get_pricing_tier

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")


class CreditService:
    """Service for managing user credits"""
    
    def __init__(self):
        """Initialize credit service"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.db = firestore.Client(project=self.project_id)
    
    def grant_subscription_credits(
        self,
        user_id: str,
        plan: str,
        period_end_timestamp: int
    ) -> Dict[str, int]:
        """
        Grant credits for a subscription.
        
        This is the SINGLE SOURCE OF TRUTH for granting subscription credits.
        Called ONLY when payment is confirmed (invoice.payment_succeeded).
        
        Args:
            user_id: Firebase user ID
            plan: Subscription plan (standard, business)
            period_end_timestamp: Unix timestamp when credits expire
        
        Returns:
            Dict with web_scan_credits and pdf_scan_credits granted
        """
        tier = get_pricing_tier(plan)
        if not tier:
            logger.error(f"Unknown plan '{plan}' for user {user_id}")
            return {"web_scan_credits": 0, "pdf_scan_credits": 0}
        
        web_credits = tier["web_scan_credits"]
        pdf_credits = tier["pdf_scan_credits"]
        credits_expire_at = datetime.fromtimestamp(period_end_timestamp, tz=CET)
        
        # Update user document with credits
        self.db.collection("users").document(user_id).update({
            "web_scan_credits": web_credits,
            "pdf_scan_credits": pdf_credits,
            "credits_expire_at": credits_expire_at,
            "updated_at": datetime.now(CET)
        })
        
        logger.info(f"Granted credits to user {user_id}: {web_credits} web + {pdf_credits} PDF, "
                   f"expires: {credits_expire_at}")
        
        # Log the credit grant
        self._log_credit_change(
            user_id=user_id,
            action="subscription_grant",
            credit_type="both",
            web_amount=web_credits,
            pdf_amount=pdf_credits,
            reason=f"Subscription credits granted for {plan} plan"
        )
        
        return {
            "web_scan_credits": web_credits,
            "pdf_scan_credits": pdf_credits
        }
    
    def deduct_credits(
        self,
        user_id: str,
        credit_type: str,
        amount: int,
        reason: str,
        scan_id: Optional[str] = None
    ) -> bool:
        """
        Deduct credits from user account.
        
        Uses Firestore transaction for atomic deduction.
        
        Args:
            user_id: Firebase user ID
            credit_type: Credit type (web_scan or pdf_scan)
            amount: Amount to deduct
            reason: Reason for deduction
            scan_id: Associated scan ID (optional)
        
        Returns:
            Success status
        
        Raises:
            ValueError: If insufficient credits
        """
        user_ref = self.db.collection("users").document(user_id)
        
        @firestore.transactional
        def deduct_in_transaction(transaction):
            user_doc = user_ref.get(transaction=transaction)
            
            if not user_doc.exists:
                raise ValueError("User not found")
            
            user_data = user_doc.to_dict()
            credit_field = f"{credit_type}_credits"
            current_credits = user_data.get(credit_field, 0)
            
            if current_credits < amount:
                raise ValueError(f"Insufficient {credit_type} credits")
            
            transaction.update(user_ref, {
                credit_field: firestore.Increment(-amount),
                "updated_at": datetime.now(CET)
            })
            
            return current_credits - amount
        
        try:
            transaction = self.db.transaction()
            balance_after = deduct_in_transaction(transaction)
            
            # Log the deduction
            self._log_credit_change(
                user_id=user_id,
                action="deduction",
                credit_type=credit_type,
                web_amount=-amount if credit_type == "web_scan" else 0,
                pdf_amount=-amount if credit_type == "pdf_scan" else 0,
                reason=reason,
                scan_id=scan_id,
                balance_after=balance_after
            )
            
            logger.info(f"Deducted {amount} {credit_type} credits from user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")
            raise
    
    def renew_free_tier_web_credits(self, user_id: str) -> bool:
        """
        Renew weekly web scan credits for a free tier user.
        Sets web_scan_credits to 40 (no stockpiling).
        Renewed every Monday at 00:00 CET.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Success status
        """
        try:
            self.db.collection("users").document(user_id).update({
                "web_scan_credits": 40,
                "updated_at": datetime.now(CET)
            })
            logger.debug(f"Renewed weekly web credits for free user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error renewing weekly web credits for user {user_id}: {e}")
            return False
    
    def renew_free_tier_pdf_credits(self, user_id: str) -> bool:
        """
        Renew weekly PDF scan credits for a free tier user.
        Sets pdf_scan_credits to 2 (no stockpiling).
        Renewed every Monday at 00:00 CET.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Success status
        """
        try:
            self.db.collection("users").document(user_id).update({
                "pdf_scan_credits": 2,
                "updated_at": datetime.now(CET)
            })
            logger.debug(f"Renewed weekly PDF credits for free user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error renewing weekly PDF credits for user {user_id}: {e}")
            return False
    
    def renew_paid_user_credits(self, user_id: str, plan: str, period_end: datetime) -> bool:
        """
        Renew monthly credits for a paid subscription user.
        
        Args:
            user_id: Firebase user ID
            plan: Subscription plan
            period_end: New period end date
        
        Returns:
            Success status
        """
        tier = get_pricing_tier(plan)
        if not tier:
            logger.error(f"Unknown plan '{plan}' for user {user_id}")
            return False
        
        try:
            self.db.collection("users").document(user_id).update({
                "web_scan_credits": tier["web_scan_credits"],
                "pdf_scan_credits": tier["pdf_scan_credits"],
                "credits_expire_at": period_end,
                "updated_at": datetime.now(CET)
            })
            
            # Log the renewal
            self._log_credit_change(
                user_id=user_id,
                action="renewal",
                credit_type="both",
                web_amount=tier["web_scan_credits"],
                pdf_amount=tier["pdf_scan_credits"],
                reason=f"Monthly credit renewal for {tier['name']} plan"
            )
            
            logger.info(f"Renewed monthly credits for user {user_id}: {plan}")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing credits for user {user_id}: {e}")
            return False
    
    def reset_to_free_tier(self, user_id: str) -> bool:
        """
        Reset user credits to free tier when subscription is canceled.
        Free tier: 40 web scans/week, 2 PDF scans/week.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Success status
        """
        try:
            self.db.collection("users").document(user_id).update({
                "web_scan_credits": 40,
                "pdf_scan_credits": 2,
                "updated_at": datetime.now(CET)
            })
            
            logger.info(f"Reset credits to free tier for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting credits for user {user_id}: {e}")
            return False
    
    def _log_credit_change(
        self,
        user_id: str,
        action: str,
        credit_type: str,
        web_amount: int,
        pdf_amount: int,
        reason: str,
        scan_id: Optional[str] = None,
        balance_after: Optional[int] = None
    ):
        """
        Log credit change to usage history.
        
        Args:
            user_id: Firebase user ID
            action: Action type (deduction, subscription_grant, renewal)
            credit_type: Credit type (web_scan, pdf_scan, both)
            web_amount: Web scan credit amount
            pdf_amount: PDF scan credit amount
            reason: Reason for change
            scan_id: Associated scan ID (optional)
            balance_after: Balance after change (optional)
        """
        try:
            self.db.collection("credit_usage_history").add({
                "user_id": user_id,
                "action": action,
                "credit_type": credit_type,
                "web_amount": web_amount,
                "pdf_amount": pdf_amount,
                "reason": reason,
                "scan_id": scan_id,
                "balance_after": balance_after,
                "created_at": datetime.now(CET)
            })
        except Exception as e:
            logger.error(f"Error logging credit change: {e}")
            # Don't raise - logging failure shouldn't break the operation


# Global credit service instance
credit_service = CreditService()
