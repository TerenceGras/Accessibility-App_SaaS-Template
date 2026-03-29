# =============================================================================
# LumTrails Infrastructure - Variables (PRODUCTION)
# =============================================================================

# -----------------------------------------------------------------------------
# Project Configuration
# -----------------------------------------------------------------------------

variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "The display name for the Google Cloud project"
  type        = string
  default     = ""
}

variable "billing_account_id" {
  description = "The billing account ID to associate with the project"
  type        = string
  # This must be set in terraform.tfvars or as an environment variable
}

variable "org_id" {
  description = "The organization ID (optional, leave empty for personal accounts)"
  type        = string
  default     = ""
}

variable "folder_id" {
  description = "The folder ID to create the project in (optional)"
  type        = string
  default     = ""
}

variable "region" {
  description = "The default region for resources"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# -----------------------------------------------------------------------------
# Production Domain Configuration
# -----------------------------------------------------------------------------

variable "production_domain" {
  description = "The production domain for the application"
  type        = string
  default     = "your-domain.com"
}

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

variable "alert_email" {
  description = "Email address for monitoring alert notifications"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Firebase Configuration
# -----------------------------------------------------------------------------

variable "firebase_storage_bucket" {
  description = "Firebase Storage bucket name (auto-generated from project_id)"
  type        = string
  default     = "" # Will be computed as ${project_id}.firebasestorage.app
}

variable "create_storage_bucket" {
  description = "Whether to create the Firebase Storage bucket (set to false if Firebase manages it)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Cloud Run Service Configuration
# -----------------------------------------------------------------------------

variable "cloud_run_timeout" {
  description = "Default timeout for Cloud Run services in seconds"
  type        = number
  default     = 600
}

variable "cloud_run_memory" {
  description = "Default memory allocation for Cloud Run services"
  type        = string
  default     = "512Mi"
}

variable "cloud_run_cpu" {
  description = "Default CPU allocation for Cloud Run services"
  type        = string
  default     = "1"
}

# -----------------------------------------------------------------------------
# Web Scanner Worker Configuration
# -----------------------------------------------------------------------------

variable "web_scanner_memory" {
  description = "Memory allocation for Web Scanner Worker"
  type        = string
  default     = "2Gi"
}

variable "web_scanner_cpu" {
  description = "CPU allocation for Web Scanner Worker"
  type        = string
  default     = "2"
}

# -----------------------------------------------------------------------------
# PDF Scanner Worker Configuration
# -----------------------------------------------------------------------------

variable "pdf_scanner_max_concurrent_scans" {
  description = "Maximum concurrent GPT scans for PDF Scanner"
  type        = number
  default     = 50
}

variable "pdf_scanner_memory" {
  description = "Memory allocation for PDF Scanner Worker (requires more for large PDFs)"
  type        = string
  default     = "4Gi"
}

variable "pdf_scanner_cpu" {
  description = "CPU allocation for PDF Scanner Worker"
  type        = string
  default     = "2"
}

variable "pdf_scanner_timeout" {
  description = "Timeout in seconds for PDF Scanner Worker (long GPT processing)"
  type        = number
  default     = 900
}

# -----------------------------------------------------------------------------
# Cloud Tasks Configuration
# -----------------------------------------------------------------------------

variable "cloud_tasks_max_dispatches_per_second" {
  description = "Maximum dispatches per second for Cloud Tasks queues"
  type        = number
  default     = 100
}

variable "cloud_tasks_max_concurrent_dispatches" {
  description = "Maximum concurrent dispatches for Cloud Tasks queues"
  type        = number
  default     = 500
}

variable "cloud_tasks_max_attempts" {
  description = "Maximum retry attempts for Cloud Tasks"
  type        = number
  default     = 50
}

# -----------------------------------------------------------------------------
# Report Generator Configuration
# -----------------------------------------------------------------------------

variable "report_generator_timeout" {
  description = "Timeout for Report Generator service in seconds"
  type        = number
  default     = 300
}

# -----------------------------------------------------------------------------
# Pricing Service Configuration
# -----------------------------------------------------------------------------

variable "pricing_service_memory" {
  description = "Memory allocation for Pricing Service"
  type        = string
  default     = "512Mi"
}

# -----------------------------------------------------------------------------
# Production Scaling Configuration
# -----------------------------------------------------------------------------

variable "min_instance_count" {
  description = "Minimum instance count for Cloud Run services in production (keeps services warm)"
  type        = number
  default     = 0  # Set to 1 for critical services to avoid cold starts (costs more)
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "lumtrails"
    environment = "prod"
    managed_by  = "terraform"
  }
}

# =============================================================================
# Feature Flags
# =============================================================================

variable "create_cloud_run_services" {
  description = "Whether to create Cloud Run services (set to false if images aren't built yet)"
  type        = bool
  default     = false
}

# =============================================================================
# PRODUCTION: No Email Whitelist
# =============================================================================
# In PRODUCTION, we do NOT use an email whitelist.
# All authenticated users can access the system.
# The DEV_WHITELIST_EMAILS env var will be set to empty string.

# =============================================================================
# Stripe Price IDs
# =============================================================================

variable "stripe_standard_monthly_price_id" {
  description = "Stripe Price ID for Standard Monthly plan (PRODUCTION)"
  type        = string
  default     = ""
}

variable "stripe_standard_yearly_price_id" {
  description = "Stripe Price ID for Standard Yearly plan (PRODUCTION)"
  type        = string
  default     = ""
}

variable "stripe_business_monthly_price_id" {
  description = "Stripe Price ID for Business Monthly plan (PRODUCTION)"
  type        = string
  default     = ""
}

variable "stripe_business_yearly_price_id" {
  description = "Stripe Price ID for Business Yearly plan (PRODUCTION)"
  type        = string
  default     = ""
}

# =============================================================================
# Slack Webhook URLs
# =============================================================================

variable "slack_new_user_webhook" {
  description = "Slack webhook URL for new user signup notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_subscription_webhook" {
  description = "Slack webhook URL for subscription event notifications"
  type        = string
  default     = ""
  sensitive   = true
}
