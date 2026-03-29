# =============================================================================
# LumTrails Infrastructure - Terraform Variables
# =============================================================================
# This file contains the default values for the LumTrails DEV environment.
# Modify these values according to your environment.
# =============================================================================

# Project Configuration
project_id   = "YOUR_DEV_PROJECT_ID"
project_name = "YOUR_PROJECT_NAME DEV"
region       = "europe-west1"
environment  = "dev"

# IMPORTANT: Set this in Terraform Cloud as a sensitive variable
# billing_account_id = "XXXXXX-XXXXXX-XXXXXX"

# Optional: Organization and Folder (leave empty for personal accounts)
# org_id    = ""
# folder_id = ""

# Firebase Configuration (auto-computed from project_id if left empty)
firebase_storage_bucket = ""

# Cloud Run Service Configuration
cloud_run_timeout = 600
cloud_run_memory  = "512Mi"
cloud_run_cpu     = "1"

# Web Scanner Worker Configuration
web_scanner_memory = "2Gi"
web_scanner_cpu    = "2"

# PDF Scanner Worker Configuration
pdf_scanner_max_concurrent_scans = 50

# Cloud Tasks Configuration
cloud_tasks_max_dispatches_per_second = 100
cloud_tasks_max_concurrent_dispatches = 500
cloud_tasks_max_attempts              = 50

# Report Generator Configuration
report_generator_timeout = 300

# Pricing Service Configuration
pricing_service_memory = "512Mi"

# Labels
labels = {
  project     = "lumtrails"
  environment = "dev"
  managed_by  = "terraform"
}

# Enable Cloud Run services (set to true after Docker images are built)
create_cloud_run_services = true

# Stripe Price IDs (TEST mode)
# Get these from your Stripe Dashboard > Products > Prices
stripe_standard_monthly_price_id = "YOUR_STRIPE_STANDARD_MONTHLY_PRICE_ID"
stripe_standard_yearly_price_id  = "YOUR_STRIPE_STANDARD_YEARLY_PRICE_ID"
stripe_business_monthly_price_id = "YOUR_STRIPE_BUSINESS_MONTHLY_PRICE_ID"
stripe_business_yearly_price_id  = "YOUR_STRIPE_BUSINESS_YEARLY_PRICE_ID"

# Slack Webhook URLs (optional - for notifications)
# IMPORTANT: Set these in Terraform Cloud as sensitive variables, or here
# slack_new_user_webhook     = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
# slack_subscription_webhook = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# DEV Environment Email Whitelist
# Only these email addresses can access the DEV environment
# Add new authorized emails to this list
dev_whitelist_emails = [
  # "your-email@example.com"
]
