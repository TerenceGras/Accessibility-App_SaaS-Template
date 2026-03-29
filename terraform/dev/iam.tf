# =============================================================================
# LumTrails Infrastructure - IAM Configuration
# =============================================================================
# This file defines IAM roles and permissions for the default service account
# =============================================================================

# Wait for Compute API to be fully enabled (creates the service account)
resource "time_sleep" "wait_for_compute_sa" {
  depends_on = [google_project_service.required_apis["compute.googleapis.com"]]
  create_duration = "60s"
}

# -----------------------------------------------------------------------------
# Cloud Tasks Enqueue Permission
# -----------------------------------------------------------------------------

resource "google_project_iam_member" "cloud_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${local.compute_service_account}"

  depends_on = [time_sleep.wait_for_compute_sa]
}

# -----------------------------------------------------------------------------
# Firestore User Permission
# -----------------------------------------------------------------------------

resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${local.compute_service_account}"

  depends_on = [time_sleep.wait_for_compute_sa]
}

# -----------------------------------------------------------------------------
# Storage Admin Permission (for Firebase Storage)
# -----------------------------------------------------------------------------

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${local.compute_service_account}"

  depends_on = [time_sleep.wait_for_compute_sa]
}

# -----------------------------------------------------------------------------
# Cloud Run Invoker Permission (for service-to-service calls)
# -----------------------------------------------------------------------------

resource "google_project_iam_member" "cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${local.compute_service_account}"

  depends_on = [time_sleep.wait_for_compute_sa]
}

# -----------------------------------------------------------------------------
# Logging Writer Permission
# -----------------------------------------------------------------------------

resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${local.compute_service_account}"

  depends_on = [time_sleep.wait_for_compute_sa]
}

# -----------------------------------------------------------------------------
# Cloud Tasks Task Runner Permission
# -----------------------------------------------------------------------------

resource "google_project_iam_member" "cloud_tasks_task_runner" {
  project = var.project_id
  role    = "roles/cloudtasks.taskRunner"
  member  = "serviceAccount:${local.compute_service_account}"

  depends_on = [time_sleep.wait_for_compute_sa]
}
