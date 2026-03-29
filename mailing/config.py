#!/usr/bin/env python3
"""
LumTrails Mailing Service - Configuration
"""
import os

# Brevo Configuration - strip whitespace/newlines from API key
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip()

# Email Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "no-reply@your-domain.com")
SENDER_NAME = os.getenv("SENDER_NAME", "LumTrails")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "hello@your-domain.com")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "hello@your-domain.com")

# URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
# Logo hosted on Firebase Hosting (public folder) - stable URL that doesn't change with builds
LOGO_URL = os.getenv("LOGO_URL", f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/images/lumtrails_logo.png")

# Project Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", PROJECT_ID)

# Verification Code Settings
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY_MINUTES = 15

# Supported Languages
SUPPORTED_LANGUAGES = ["en", "fr", "de", "es", "it", "pt"]
DEFAULT_LANGUAGE = "en"
