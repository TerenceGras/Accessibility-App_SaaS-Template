#!/usr/bin/env python3
"""
LumTrails Pricing Service Configuration

Centralized configuration for pricing tiers and Stripe settings.
"""
import os
from typing import Dict, Any
from datetime import timedelta

# Stripe Price IDs from environment (set via Cloud Run env vars or terraform)
STANDARD_MONTHLY_PRICE_ID = os.getenv("STRIPE_STANDARD_MONTHLY_PRICE_ID", "")
STANDARD_YEARLY_PRICE_ID = os.getenv("STRIPE_STANDARD_YEARLY_PRICE_ID", "")
BUSINESS_MONTHLY_PRICE_ID = os.getenv("STRIPE_BUSINESS_MONTHLY_PRICE_ID", "")
BUSINESS_YEARLY_PRICE_ID = os.getenv("STRIPE_BUSINESS_YEARLY_PRICE_ID", "")

# Stripe Checkout Session URLs
# These URLs handle where users are redirected after Stripe Checkout
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

CHECKOUT_SUCCESS_URL = os.getenv(
    "CHECKOUT_SUCCESS_URL", 
    f"{FRONTEND_URL}/profile?subscription=success"
)
CHECKOUT_CANCEL_URL = os.getenv(
    "CHECKOUT_CANCEL_URL", 
    f"{FRONTEND_URL}/pricing?subscription=cancelled"
)

# Pricing Tiers
PRICING_TIERS = {
    "free": {
        "name": "Free",
        "price": 0.00,
        "currency": "eur",
        "interval": "week",
        "web_scan_credits": 40,  # Per week (renewed on Monday 00:00 CET)
        "pdf_scan_credits": 2,   # Per week (renewed on Monday 00:00 CET)
        "web_scan_renewal": "weekly",
        "pdf_scan_renewal": "weekly",
        "scan_retention_days": 30,  # Free users: 30 days
        "stripe_price_id": None,  # Free tier has no Stripe price
        "stripe_yearly_price_id": None,
        "features": [
            "40 web scan credits per week",
            "2 PDF scan credits per week",
            "Basic Accessibility Reports",
            "Scan history retained for 30 days"
        ]
    },
    "standard": {
        "name": "Standard",
        "price": 49.00,
        "yearly_price": 539.00,  # 11 months (1 month free)
        "currency": "eur",
        "interval": "month",
        "web_scan_credits": 1000,
        "pdf_scan_credits": 50,
        "web_scan_renewal": "monthly",
        "pdf_scan_renewal": "monthly",
        "scan_retention_days": 180,  # Standard users: 6 months
        "stripe_price_id": STANDARD_MONTHLY_PRICE_ID,
        "stripe_yearly_price_id": STANDARD_YEARLY_PRICE_ID,
        "features": [
            "1,000 web scan credits per month",
            "50 PDF scan credits per month",
            "Basic Accessibility Reports",
            "Scan history retained for 6 months",
            "Integrations: GitHub, Notion, Slack",
            "API Access"
        ]
    },
    "business": {
        "name": "Business",
        "price": 109.00,
        "yearly_price": 1199.00,  # 11 months (1 month free)
        "currency": "eur",
        "interval": "month",
        "web_scan_credits": 10000,
        "pdf_scan_credits": 500,
        "web_scan_renewal": "monthly",
        "pdf_scan_renewal": "monthly",
        "scan_retention_days": 365,  # Business users: 1 year
        "stripe_price_id": BUSINESS_MONTHLY_PRICE_ID,
        "stripe_yearly_price_id": BUSINESS_YEARLY_PRICE_ID,
        "features": [
            "10,000 web scan credits per month",
            "500 PDF scan credits per month",
            "Basic Accessibility Reports",
            "Scan history retained for 1 year",
            "Integrations: GitHub, Notion, Slack",
            "API Access"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": None,  # Custom pricing
        "yearly_price": None,
        "currency": "eur",
        "interval": "month",
        "web_scan_credits": None,  # Custom
        "pdf_scan_credits": None,  # Custom
        "web_scan_renewal": "monthly",
        "pdf_scan_renewal": "monthly",
        "scan_retention_days": 365,  # Enterprise: at least 1 year
        "stripe_price_id": None,
        "stripe_yearly_price_id": None,
        "features": [
            "Custom Web Scans Volumes",
            "Custom PDF Scans Volumes",
            "Custom Integrations",
            "Custom Accessibility Reports",
            "Custom API Limits"
        ],
        "contact_sales": True
    }
}

# Stripe Configuration
STRIPE_CONFIG = {
    "api_version": "2023-10-16",
    "webhook_tolerance": 300,  # 5 minutes
    "max_network_retries": 2
}

# Credit Renewal Schedule
RENEWAL_SCHEDULE = {
    "free_web_weekly": {
        "plan": "free",
        "credit_type": "web_scan",
        "amount": 40,
        "frequency": "weekly",
        "day": "monday",  # Start of week
        "time": "00:00"  # Midnight CET
    },
    "free_pdf_weekly": {
        "plan": "free",
        "credit_type": "pdf_scan",
        "amount": 2,
        "frequency": "weekly",
        "day": "monday",  # Start of week
        "time": "00:00"
    },
    "standard_monthly": {
        "plan": "standard",
        "credit_type": "both",
        "frequency": "monthly",
        "day": 1,
        "time": "00:00"
    },
    "business_monthly": {
        "plan": "business",
        "credit_type": "both",
        "frequency": "monthly",
        "day": 1,
        "time": "00:00"
    }
}

# Scan Data Retention (in days) per plan
SCAN_RETENTION_DAYS = {
    "free": 30,      # 30 days
    "standard": 180, # 6 months
    "business": 365, # 1 year
    "enterprise": 365  # At least 1 year
}

# Usage Tracking
USAGE_RETENTION_DAYS = 365  # Keep usage history for 1 year

# Feature Limits - API and Integrations now available to all users
FEATURE_LIMITS = {
    "free": {
        "max_api_keys": None,  # API access now available to all
        "integrations_enabled": True,  # Integrations now available to all
        "priority_support": False,
        "api_access": True  # API access now available to all
    },
    "standard": {
        "max_api_keys": None,
        "integrations_enabled": True,
        "priority_support": False,
        "api_access": True
    },
    "business": {
        "max_api_keys": None,
        "integrations_enabled": True,
        "priority_support": True,
        "api_access": True
    },
    "enterprise": {
        "max_api_keys": None,  # Unlimited
        "integrations_enabled": True,
        "priority_support": True,
        "api_access": True
    }
}

def get_pricing_tier(tier: str) -> Dict[str, Any]:
    """Get pricing tier configuration"""
    return PRICING_TIERS.get(tier)

def get_feature_limits(tier: str) -> Dict[str, Any]:
    """Get feature limits for a pricing tier"""
    return FEATURE_LIMITS.get(tier, FEATURE_LIMITS["free"])
