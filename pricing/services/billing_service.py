#!/usr/bin/env python3
"""
LumTrails Pricing Service - Billing Service

Handles billing information and payment methods.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore

from services.stripe_service import stripe_service

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")


class BillingService:
    """Service for managing billing information"""
    
    def __init__(self):
        """Initialize billing service"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.db = firestore.Client(project=self.project_id)
        self.billing_info_collection = "billing_info"
    
    def get_billing_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get billing information for a user.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            Billing information or None
        """
        try:
            doc = self.db.collection(self.billing_info_collection).document(user_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            return {
                "company_name": data.get("company_name"),
                "vat_number": data.get("vat_number"),
                "address": data.get("address", {}),
                "payment_methods": data.get("payment_methods", []),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Error getting billing info: {e}")
            raise
    
    def update_billing_info(
        self,
        user_id: str,
        company_name: Optional[str] = None,
        vat_number: Optional[str] = None,
        address: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Update billing information for a user.
        
        Args:
            user_id: Firebase user ID
            company_name: Company name (optional)
            vat_number: VAT number (optional)
            address: Address details (optional)
        
        Returns:
            Updated billing information
        """
        try:
            doc_ref = self.db.collection(self.billing_info_collection).document(user_id)
            doc = doc_ref.get()
            
            update_data = {
                "user_id": user_id,
                "updated_at": datetime.now(CET)
            }
            
            if company_name is not None:
                update_data["company_name"] = company_name
            
            if vat_number is not None:
                update_data["vat_number"] = vat_number
            
            if address is not None:
                update_data["address"] = {
                    "line1": address.get("line1", ""),
                    "line2": address.get("line2", ""),
                    "city": address.get("city", ""),
                    "postal_code": address.get("postal_code", ""),
                    "country": address.get("country", "")
                }
            
            if not doc.exists:
                update_data["created_at"] = datetime.now(CET)
                doc_ref.set(update_data)
            else:
                doc_ref.update(update_data)
            
            logger.info(f"Updated billing info for user {user_id}")
            
            return self.get_billing_info(user_id)
        except Exception as e:
            logger.error(f"Error updating billing info: {e}")
            raise
    
    def add_payment_method(
        self,
        user_id: str,
        stripe_customer_id: str,
        payment_method_id: str,
        set_as_default: bool = False
    ) -> Dict[str, Any]:
        """
        Add payment method to user.
        
        Args:
            user_id: Firebase user ID
            stripe_customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
            set_as_default: Set as default payment method
        
        Returns:
            Payment method details
        """
        try:
            # Attach payment method in Stripe
            payment_method = stripe_service.attach_payment_method(
                customer_id=stripe_customer_id,
                payment_method_id=payment_method_id
            )
            
            if set_as_default:
                stripe_service.set_default_payment_method(
                    customer_id=stripe_customer_id,
                    payment_method_id=payment_method_id
                )
            
            # Update Firestore
            doc_ref = self.db.collection(self.billing_info_collection).document(user_id)
            doc = doc_ref.get()
            
            payment_methods = []
            if doc.exists:
                payment_methods = doc.to_dict().get("payment_methods", [])
            
            # If set as default, unset other defaults
            if set_as_default:
                for pm in payment_methods:
                    pm["is_default"] = False
            
            # Add new payment method
            new_pm = {
                "stripe_payment_method_id": payment_method["payment_method_id"],
                "type": payment_method["type"],
                "is_default": set_as_default
            }
            
            if payment_method.get("card"):
                new_pm["last4"] = payment_method["card"]["last4"]
                new_pm["brand"] = payment_method["card"]["brand"]
                new_pm["exp_month"] = payment_method["card"]["exp_month"]
                new_pm["exp_year"] = payment_method["card"]["exp_year"]
            
            payment_methods.append(new_pm)
            
            if not doc.exists:
                doc_ref.set({
                    "user_id": user_id,
                    "payment_methods": payment_methods,
                    "created_at": datetime.now(CET),
                    "updated_at": datetime.now(CET)
                })
            else:
                doc_ref.update({
                    "payment_methods": payment_methods,
                    "updated_at": datetime.now(CET)
                })
            
            logger.info(f"Added payment method for user {user_id}")
            
            return new_pm
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            raise
    
    def remove_payment_method(
        self,
        user_id: str,
        payment_method_id: str
    ) -> bool:
        """
        Remove payment method from user.
        
        Args:
            user_id: Firebase user ID
            payment_method_id: Stripe payment method ID
        
        Returns:
            Success status
        """
        try:
            # Detach from Stripe
            stripe_service.detach_payment_method(payment_method_id)
            
            # Update Firestore
            doc_ref = self.db.collection(self.billing_info_collection).document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                payment_methods = doc.to_dict().get("payment_methods", [])
                payment_methods = [pm for pm in payment_methods if pm["stripe_payment_method_id"] != payment_method_id]
                
                doc_ref.update({
                    "payment_methods": payment_methods,
                    "updated_at": datetime.now(CET)
                })
            
            logger.info(f"Removed payment method {payment_method_id} for user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error removing payment method: {e}")
            raise
    
    def set_default_payment_method(
        self,
        user_id: str,
        stripe_customer_id: str,
        payment_method_id: str
    ) -> bool:
        """
        Set default payment method for user.
        
        Args:
            user_id: Firebase user ID
            stripe_customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
        
        Returns:
            Success status
        """
        try:
            # Update in Stripe
            stripe_service.set_default_payment_method(
                customer_id=stripe_customer_id,
                payment_method_id=payment_method_id
            )
            
            # Update Firestore
            doc_ref = self.db.collection(self.billing_info_collection).document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                payment_methods = doc.to_dict().get("payment_methods", [])
                
                for pm in payment_methods:
                    pm["is_default"] = (pm["stripe_payment_method_id"] == payment_method_id)
                
                doc_ref.update({
                    "payment_methods": payment_methods,
                    "updated_at": datetime.now(CET)
                })
            
            logger.info(f"Set default payment method for user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error setting default payment method: {e}")
            raise
    
    def get_payment_methods(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all payment methods for user.
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            List of payment methods
        """
        try:
            doc = self.db.collection(self.billing_info_collection).document(user_id).get()
            
            if not doc.exists:
                return []
            
            return doc.to_dict().get("payment_methods", [])
        except Exception as e:
            logger.error(f"Error getting payment methods: {e}")
            raise


# Global billing service instance
billing_service = BillingService()
