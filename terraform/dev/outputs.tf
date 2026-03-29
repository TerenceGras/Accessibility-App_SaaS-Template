# =============================================================================
# LumTrails Infrastructure - Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# Cloud Run Service URLs (only available when services are created)
# -----------------------------------------------------------------------------

output "main_api_url" {
  description = "URL of the Main API Gateway"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.main_api[0].uri : null
}

output "web_scanner_worker_url" {
  description = "URL of the Web Scanner Worker"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.web_scanner_worker[0].uri : null
}

output "pdf_scanner_worker_url" {
  description = "URL of the PDF Scanner Worker"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.pdf_scanner_worker[0].uri : null
}

output "integrations_worker_url" {
  description = "URL of the Integrations Worker"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.integrations_worker[0].uri : null
}

output "external_api_url" {
  description = "URL of the External API"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.external_api[0].uri : null
}

output "report_generator_url" {
  description = "URL of the Report Generator"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.report_generator[0].uri : null
}

output "pricing_service_url" {
  description = "URL of the Pricing Service"
  value       = var.create_cloud_run_services ? google_cloud_run_v2_service.pricing_service[0].uri : null
}

# -----------------------------------------------------------------------------
# Cloud Tasks Queues
# -----------------------------------------------------------------------------

output "web_scan_queue_name" {
  description = "Name of the Web Scan queue"
  value       = google_cloud_tasks_queue.web_scan_queue.name
}

output "pdf_scan_queue_name" {
  description = "Name of the PDF Scan queue"
  value       = google_cloud_tasks_queue.pdf_scan_queue.name
}

output "integration_queue_name" {
  description = "Name of the Integration queue"
  value       = google_cloud_tasks_queue.integration_queue.name
}

# -----------------------------------------------------------------------------
# Secret Manager
# -----------------------------------------------------------------------------

output "secret_ids" {
  description = "IDs of created secrets"
  value = {
    openai_api_key              = google_secret_manager_secret.openai_api_key.secret_id
    firebase_storage_key        = google_secret_manager_secret.firebase_storage_private_key.secret_id
    stripe_api_key              = google_secret_manager_secret.stripe_api_key.secret_id
    stripe_webhook_secret       = google_secret_manager_secret.stripe_webhook_secret.secret_id
    stripe_publishable_key      = google_secret_manager_secret.stripe_publishable_key.secret_id
    github_oauth_client_id      = google_secret_manager_secret.github_oauth_client_id.secret_id
    github_oauth_client_secret  = google_secret_manager_secret.github_oauth_client_secret.secret_id
    notion_oauth_client_id      = google_secret_manager_secret.notion_oauth_client_id.secret_id
    notion_oauth_client_secret  = google_secret_manager_secret.notion_oauth_client_secret.secret_id
  }
}

# -----------------------------------------------------------------------------
# Cloud Scheduler Jobs (only available when services are created)
# -----------------------------------------------------------------------------

output "scheduler_jobs" {
  description = "Names of created Cloud Scheduler jobs"
  value = var.create_cloud_run_services ? {
    free_tier_weekly_renewal   = google_cloud_scheduler_job.free_tier_weekly_renewal[0].name
    paid_plan_monthly_renewal  = google_cloud_scheduler_job.paid_plan_monthly_renewal[0].name
    scan_results_cleanup       = google_cloud_scheduler_job.scan_results_cleanup[0].name
    old_scan_data_cleanup      = google_cloud_scheduler_job.old_scan_data_cleanup[0].name
    api_key_expiration         = google_cloud_scheduler_job.api_key_expiration[0].name
  } : null
}

# -----------------------------------------------------------------------------
# Artifact Registry
# -----------------------------------------------------------------------------

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cloud_run_images.repository_id}"
}

# -----------------------------------------------------------------------------
# Service Account
# -----------------------------------------------------------------------------

output "compute_service_account_email" {
  description = "Default Compute Engine service account email"
  value       = local.compute_service_account
}

# -----------------------------------------------------------------------------
# Project Info
# -----------------------------------------------------------------------------

output "project_info" {
  description = "Project information"
  value = {
    project_id     = var.project_id
    project_number = local.project_number
    region         = var.region
    environment    = var.environment
  }
}

output "project_number" {
  description = "The project number of the created project"
  value       = local.project_number
}

output "firebase_storage_bucket" {
  description = "Firebase Storage bucket name"
  value       = local.firebase_storage_bucket
}

# -----------------------------------------------------------------------------
# Firebase Configuration
# -----------------------------------------------------------------------------

output "firebase_web_app_id" {
  description = "Firebase Web App ID"
  value       = google_firebase_web_app.lumtrails_web.app_id
}
