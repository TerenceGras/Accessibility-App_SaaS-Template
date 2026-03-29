# =============================================================================
# LumTrails Infrastructure - Firebase Storage Configuration (PRODUCTION)
# =============================================================================
# This file defines lifecycle rules for Firebase Storage buckets
# Note: Firebase Storage bucket is created by Firebase when you initialize Storage
# After Firebase creates it, you can import it to manage lifecycle rules:
# terraform import google_storage_bucket.firebase_storage[0] YOUR_PROD_PROJECT_ID.firebasestorage.app
# =============================================================================

# -----------------------------------------------------------------------------
# Firebase Storage Bucket Lifecycle Rules
# -----------------------------------------------------------------------------

# Note: Set create_storage_bucket = true only after:
# 1. Creating Firebase project in Firebase Console
# 2. Initializing Firebase Storage in Firebase Console
# 3. Importing the bucket: terraform import google_storage_bucket.firebase_storage[0] ${project_id}.firebasestorage.app

resource "google_storage_bucket" "firebase_storage" {
  count                       = var.create_storage_bucket ? 1 : 0
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

  # PRODUCTION: Prevent accidental destruction
  lifecycle {
    prevent_destroy = true
  }

  depends_on = [
    google_project_service.required_apis["storage.googleapis.com"],
    google_firebase_project.default
  ]
}
