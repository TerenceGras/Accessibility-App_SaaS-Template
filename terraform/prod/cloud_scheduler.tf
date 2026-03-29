# =============================================================================
# LumTrails Infrastructure - Cloud Scheduler Jobs (PRODUCTION)
# =============================================================================
# This file defines all Cloud Scheduler jobs for:
# - Free tier weekly web scan + PDF credit renewal (Monday 00:00 CET)
# - Paid plan monthly credit renewal
# - Scan results cleanup (30-minute temp results)
# - Plan-based scan data cleanup (Free: 30 days, Standard: 6 months, Business: 1 year)
# - API key expiration cleanup
#
# Note: These are only created when Cloud Run services are deployed
# All times use CET (Europe/Paris) timezone for EU service consistency
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Free Tier Weekly Credit Renewal (Web + PDF combined)
# -----------------------------------------------------------------------------

resource "google_cloud_scheduler_job" "free_tier_weekly_renewal" {
  count       = var.create_cloud_run_services ? 1 : 0
  name        = "free-tier-weekly-renewal"
  description = "Renew weekly web and PDF credits for free tier users at 00:00 CET on Mondays"
  project     = var.project_id
  region      = var.region

  schedule  = "0 0 * * 1" # Every Monday at 00:00 CET
  time_zone = "Europe/Paris"

  http_target {
    uri         = "${google_cloud_run_v2_service.pricing_service[0].uri}/admin/renew-free-tier-credits"
    http_method = "POST"

    headers = {
      "Content-Type" = "application/json"
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 5
  }

  depends_on = [
    google_project_service.required_apis["cloudscheduler.googleapis.com"],
    google_cloud_run_v2_service.pricing_service
  ]
}

# -----------------------------------------------------------------------------
# 2. Paid Plan Monthly Credit Renewal
# -----------------------------------------------------------------------------

resource "google_cloud_scheduler_job" "paid_plan_monthly_renewal" {
  count       = var.create_cloud_run_services ? 1 : 0
  name        = "paid-plan-monthly-renewal"
  description = "Renew monthly credits for paid plan users at 00:02 CET on the 1st"
  project     = var.project_id
  region      = var.region

  schedule  = "2 0 1 * *" # 1st of month at 00:02 CET
  time_zone = "Europe/Paris"

  http_target {
    uri         = "${google_cloud_run_v2_service.pricing_service[0].uri}/admin/renew-monthly-credits"
    http_method = "POST"

    headers = {
      "Content-Type" = "application/json"
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 5
  }

  depends_on = [
    google_project_service.required_apis["cloudscheduler.googleapis.com"],
    google_cloud_run_v2_service.pricing_service
  ]
}

# -----------------------------------------------------------------------------
# 4. Scan Results Cleanup (Every 30 minutes - temporary PDF results only)
# -----------------------------------------------------------------------------

resource "google_cloud_scheduler_job" "scan_results_cleanup" {
  count       = var.create_cloud_run_services ? 1 : 0
  name        = "scan-results-cleanup"
  description = "Delete temporary PDF scan results from Firestore (older than 30 minutes)"
  project     = var.project_id
  region      = var.region

  schedule  = "*/30 * * * *" # Every 30 minutes
  time_zone = "Europe/Paris"

  http_target {
    uri         = "${google_cloud_run_v2_service.main_api[0].uri}/admin/cleanup-old-scans"
    http_method = "POST"

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = local.compute_service_account
      audience              = google_cloud_run_v2_service.main_api[0].uri
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 5
  }

  depends_on = [
    google_project_service.required_apis["cloudscheduler.googleapis.com"],
    google_cloud_run_v2_service.main_api
  ]
}

# -----------------------------------------------------------------------------
# 5. Plan-Based Scan Data Cleanup (Daily - based on subscription plan)
# Retention: Free = 30 days, Standard = 6 months, Business = 1 year
# -----------------------------------------------------------------------------

resource "google_cloud_scheduler_job" "old_scan_data_cleanup" {
  count       = var.create_cloud_run_services ? 1 : 0
  name        = "old-scan-data-cleanup"
  description = "Delete scan data based on plan: Free 30d, Standard 6mo, Business 1yr"
  project     = var.project_id
  region      = var.region

  schedule  = "0 3 * * *" # Daily at 03:00 CET (low traffic period)
  time_zone = "Europe/Paris"

  http_target {
    uri         = "${google_cloud_run_v2_service.main_api[0].uri}/admin/cleanup-expired-scans"
    http_method = "POST"

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = local.compute_service_account
      audience              = google_cloud_run_v2_service.main_api[0].uri
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 5
  }

  depends_on = [
    google_project_service.required_apis["cloudscheduler.googleapis.com"],
    google_cloud_run_v2_service.main_api
  ]
}

# -----------------------------------------------------------------------------
# 6. API Key Expiration Cleanup (Every hour)
# -----------------------------------------------------------------------------

resource "google_cloud_scheduler_job" "api_key_expiration" {
  count       = var.create_cloud_run_services ? 1 : 0
  name        = "api-key-expiration-cleanup"
  description = "Mark expired API keys as revoked"
  project     = var.project_id
  region      = var.region

  schedule  = "0 * * * *" # Every hour
  time_zone = "Europe/Paris"

  http_target {
    uri         = "${google_cloud_run_v2_service.main_api[0].uri}/admin/expire-api-keys"
    http_method = "POST"

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = local.compute_service_account
      audience              = google_cloud_run_v2_service.main_api[0].uri
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 5
  }

  depends_on = [
    google_project_service.required_apis["cloudscheduler.googleapis.com"],
    google_cloud_run_v2_service.main_api
  ]
}

# -----------------------------------------------------------------------------
# 7. Scheduled Account Deletions (Daily at 03:30 CET)
# -----------------------------------------------------------------------------

resource "google_cloud_scheduler_job" "scheduled_account_deletions" {
  count       = var.create_cloud_run_services ? 1 : 0
  name        = "scheduled-account-deletions"
  description = "Process scheduled account deletions for users past their deletion date"
  project     = var.project_id
  region      = var.region

  schedule  = "30 3 * * *" # Daily at 03:30 CET (after old scan cleanup)
  time_zone = "Europe/Paris"

  http_target {
    uri         = "${google_cloud_run_v2_service.pricing_service[0].uri}/admin/process-scheduled-deletions"
    http_method = "POST"

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = local.compute_service_account
      audience              = google_cloud_run_v2_service.pricing_service[0].uri
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_doublings        = 5
  }

  depends_on = [
    google_project_service.required_apis["cloudscheduler.googleapis.com"],
    google_cloud_run_v2_service.pricing_service
  ]
}
