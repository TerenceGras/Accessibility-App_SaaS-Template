# =============================================================================
# LumTrails Infrastructure - Firebase Storage Configuration
# =============================================================================
# This file defines lifecycle rules for Firebase Storage buckets
# Note: Firebase Storage bucket may already exist; import it first if needed:
# terraform import google_storage_bucket.firebase_storage YOUR_DEV_PROJECT_ID.firebasestorage.app
# =============================================================================

# -----------------------------------------------------------------------------
# Firebase Storage Bucket Lifecycle Rules
# -----------------------------------------------------------------------------

# Note: This resource manages the existing Firebase Storage bucket
# If the bucket already exists, import it before applying:
# terraform import google_storage_bucket.firebase_storage ${var.project_id}.firebasestorage.app

resource "google_storage_bucket" "firebase_storage" {
  name                        = local.firebase_storage_bucket
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  # Lifecycle rule: Delete temporary PDFs after 1 day
  lifecycle_rule {
    condition {
      age            = 1
      matches_prefix = ["temp-pdfs/"]
    }
    action {
      type = "Delete"
    }
  }

  # Lifecycle rule: Delete temporary images after 1 day
  lifecycle_rule {
    condition {
      age            = 1
      matches_prefix = ["temp-images/"]
    }
    action {
      type = "Delete"
    }
  }

  # Lifecycle rule: Move scan results to Nearline after 12 months (cost savings)
  lifecycle_rule {
    condition {
      age            = 365
      matches_prefix = ["scan_results/", "web_scan_results/", "pdf_scan_results/"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  # Lifecycle rule: Delete scan results after 24 months (per privacy policy)
  lifecycle_rule {
    condition {
      age            = 730
      matches_prefix = ["scan_results/", "web_scan_results/", "pdf_scan_results/"]
    }
    action {
      type = "Delete"
    }
  }

  # Prevent accidental destruction
  lifecycle {
    prevent_destroy = false  # Set to true in production
  }

  depends_on = [
    google_project_service.required_apis["storage.googleapis.com"],
    google_firebase_project.default
  ]
}
