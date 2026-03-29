# =============================================================================
# LumTrails Infrastructure - Artifact Registry
# =============================================================================
# This file defines the Artifact Registry repository for Docker images
# =============================================================================

resource "google_artifact_registry_repository" "cloud_run_images" {
  location      = var.region
  repository_id = "cloud-run-source-deploy"
  description   = "Docker repository for LumTrails Cloud Run services"
  format        = "DOCKER"
  project       = var.project_id

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["artifactregistry.googleapis.com"],
    google_project.lumtrails_dev
  ]
}

# Grant Cloud Build access to push images
resource "google_artifact_registry_repository_iam_member" "cloud_build_writer" {
  project    = var.project_id
  location   = google_artifact_registry_repository.cloud_run_images.location
  repository = google_artifact_registry_repository.cloud_run_images.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${local.project_number}@cloudbuild.gserviceaccount.com"
}

# Grant Cloud Run access to pull images
resource "google_artifact_registry_repository_iam_member" "cloud_run_reader" {
  project    = var.project_id
  location   = google_artifact_registry_repository.cloud_run_images.location
  repository = google_artifact_registry_repository.cloud_run_images.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${local.compute_service_account}"
}
