#!/usr/bin/env python3
"""
LumTrails Mailing Service - Templates Package
"""
from .base_template import get_base_template
from .verification_template import get_verification_email
from .welcome_template import get_welcome_email
from .subscription_template import get_subscription_upgrade_email
from .deletion_template import get_deletion_request_email, get_account_deleted_email
from .newsletter_template import get_newsletter_email, get_product_update_email

__all__ = [
    "get_base_template",
    "get_verification_email",
    "get_welcome_email",
    "get_subscription_upgrade_email",
    "get_deletion_request_email",
    "get_account_deleted_email",
    "get_newsletter_email",
    "get_product_update_email"
]
