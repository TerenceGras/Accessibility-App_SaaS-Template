#!/usr/bin/env python3
"""
LumTrails Pricing Service - Pydantic Models

All request/response models for the pricing service API.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class SubscriptionPlan(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"


# =============================================================================
# Request Models
# =============================================================================

class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe Checkout Session for subscription"""
    plan: str  # standard or business
    interval: str = "monthly"  # monthly or yearly


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription to a different plan"""
    new_plan: str


class BillingInfoRequest(BaseModel):
    """Request to update billing information"""
    company_name: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[Dict[str, str]] = None


class AddPaymentMethodRequest(BaseModel):
    """Request to add a payment method"""
    payment_method_id: str
    set_as_default: bool = False


class SetDefaultPaymentMethodRequest(BaseModel):
    """Request to set default payment method"""
    payment_method_id: str


# =============================================================================
# Response Models
# =============================================================================

class SubscriptionResponse(BaseModel):
    """Subscription details response"""
    plan: str
    status: str
    interval: Optional[str] = None
    web_scan_credits: int = 0
    pdf_scan_credits: int = 0
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    credits_expire_at: Optional[datetime] = None


class CheckoutSessionResponse(BaseModel):
    """Checkout session creation response"""
    checkout_url: str
    session_id: str


class UsageStatsResponse(BaseModel):
    """Usage statistics response"""
    current_month: Dict[str, Any]
    all_time: Dict[str, Any]
    api_keys_count: int = 0
    integrations: Dict[str, int] = {}


class InvoiceResponse(BaseModel):
    """Single invoice response"""
    id: str
    description: str
    amount: float
    currency: str
    created_at: str
    invoice_url: Optional[str] = None
    type: str  # "subscription" or "credit_purchase"


class BillingInfoResponse(BaseModel):
    """Billing information response"""
    company_name: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    payment_methods: List[Dict[str, Any]] = []


class PaymentMethodResponse(BaseModel):
    """Payment method details"""
    stripe_payment_method_id: str
    type: str
    is_default: bool = False
    last4: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None


class DeletionStatusResponse(BaseModel):
    """Account deletion status response"""
    scheduled: bool
    deletion_date: Optional[str] = None
    can_delete_immediately: bool
    subscription_ends: Optional[str] = None


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
