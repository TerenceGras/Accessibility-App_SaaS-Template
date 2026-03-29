# =============================================================================
# LumTrails Infrastructure - Firebase / Firestore Configuration
# =============================================================================
# This file defines Firestore database and Firebase resources
# Note: Firebase project creation is typically done via Firebase Console
# This file manages Firestore indexes and database configuration
# =============================================================================

# -----------------------------------------------------------------------------
# Firestore Database (Native Mode)
# -----------------------------------------------------------------------------

# Note: If the Firestore database already exists, you may need to import it
# terraform import google_firestore_database.database "(default)"

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  # Prevent accidental deletion
  deletion_policy = "DELETE"

  depends_on = [
    google_project_service.required_apis["firestore.googleapis.com"],
    google_firebase_project.default
  ]

  lifecycle {
    # Prevent recreation if already exists
    ignore_changes = [location_id]
  }
}

# -----------------------------------------------------------------------------
# Firestore Composite Indexes
# -----------------------------------------------------------------------------

# API Keys - User Keys Lookup
resource "google_firestore_index" "api_keys_user_lookup" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "api_keys"

  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "revoked"
    order      = "ASCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# API Keys - Key Hash Lookup
resource "google_firestore_index" "api_keys_hash_lookup" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "api_keys"

  fields {
    field_path = "key_hash"
    order      = "ASCENDING"
  }

  fields {
    field_path = "revoked"
    order      = "ASCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# API Keys - Expired Keys Cleanup
resource "google_firestore_index" "api_keys_expiration" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "api_keys"

  fields {
    field_path = "revoked"
    order      = "ASCENDING"
  }

  fields {
    field_path = "expires_at"
    order      = "ASCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# Web Scan Results - User and Timestamp
resource "google_firestore_index" "web_scan_results_user" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "web_scan_results"

  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# PDF Scan Results - User and Timestamp
resource "google_firestore_index" "pdf_scan_results_user" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "pdf_scan_results"

  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# Integration Logs - User and Timestamp
resource "google_firestore_index" "integration_logs_user" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "integration_logs"

  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# Credit Usage History - User and Timestamp
resource "google_firestore_index" "credit_usage_history_user" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "credit_usage_history"

  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# Credit Usage Daily Summary - User Date Lookup
resource "google_firestore_index" "credit_usage_daily_summary_user" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "credit_usage_daily_summary"

  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "date"
    order      = "DESCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# Users - Subscription Status Lookup
resource "google_firestore_index" "users_subscription" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "users"

  fields {
    field_path = "subscription.plan"
    order      = "ASCENDING"
  }

  fields {
    field_path = "subscription.status"
    order      = "ASCENDING"
  }

  depends_on = [google_firestore_database.database]
}

# -----------------------------------------------------------------------------
# Firestore TTL Policies
# -----------------------------------------------------------------------------

# TTL for credit_usage_daily_summary - auto-delete after 30 days
resource "google_firestore_field" "credit_usage_daily_summary_ttl" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "credit_usage_daily_summary"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_firestore_database.database]
}

# TTL for credit_reservations - auto-delete abandoned reservations
resource "google_firestore_field" "credit_reservations_ttl" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "credit_reservations"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_firestore_database.database]
}

# TTL for scheduled_deletions - auto-cleanup after processing
resource "google_firestore_field" "scheduled_deletions_ttl" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "scheduled_deletions"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_firestore_database.database]
}

# TTL for verification_codes - auto-delete after verification code expires (15 minutes)
resource "google_firestore_field" "verification_codes_ttl" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "verification_codes"
  field      = "expires_at"

  ttl_config {}

  depends_on = [google_firestore_database.database]
}
