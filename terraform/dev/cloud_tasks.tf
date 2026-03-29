# =============================================================================
# LumTrails Infrastructure - Cloud Tasks Queues
# =============================================================================
# This file defines all 3 Cloud Tasks queues:
# 1. Web Scan Queue (web-scan-queue)
# 2. PDF Scan Queue (pdf-scan-queue)
# 3. Integration Queue (integration-queue)
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Web Scan Queue
# -----------------------------------------------------------------------------

resource "google_cloud_tasks_queue" "web_scan_queue" {
  name     = "web-scan-queue"
  location = var.region
  project  = var.project_id

  rate_limits {
    max_dispatches_per_second = var.cloud_tasks_max_dispatches_per_second
    max_concurrent_dispatches = var.cloud_tasks_max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = var.cloud_tasks_max_attempts
    max_retry_duration = "0s"
    min_backoff        = "1s"
    max_backoff        = "3600s"
    max_doublings      = 16
  }

  depends_on = [
    google_project_service.required_apis["cloudtasks.googleapis.com"]
  ]
}

# -----------------------------------------------------------------------------
# 2. PDF Scan Queue
# -----------------------------------------------------------------------------

resource "google_cloud_tasks_queue" "pdf_scan_queue" {
  name     = "pdf-scan-queue"
  location = var.region
  project  = var.project_id

  rate_limits {
    max_dispatches_per_second = var.cloud_tasks_max_dispatches_per_second
    max_concurrent_dispatches = var.cloud_tasks_max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = var.cloud_tasks_max_attempts
    max_retry_duration = "0s"
    min_backoff        = "1s"
    max_backoff        = "3600s"
    max_doublings      = 16
  }

  depends_on = [
    google_project_service.required_apis["cloudtasks.googleapis.com"]
  ]
}

# -----------------------------------------------------------------------------
# 3. Integration Queue
# -----------------------------------------------------------------------------

resource "google_cloud_tasks_queue" "integration_queue" {
  name     = "integration-queue"
  location = var.region
  project  = var.project_id

  rate_limits {
    max_dispatches_per_second = var.cloud_tasks_max_dispatches_per_second
    max_concurrent_dispatches = var.cloud_tasks_max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = var.cloud_tasks_max_attempts
    max_retry_duration = "0s"
    min_backoff        = "1s"
    max_backoff        = "3600s"
    max_doublings      = 16
  }

  depends_on = [
    google_project_service.required_apis["cloudtasks.googleapis.com"]
  ]
}
