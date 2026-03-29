# =============================================================================
# LumTrails Infrastructure - Secret Manager
# =============================================================================
# This file defines all secrets and IAM bindings for:
# - OpenAI API Key (PDF Scanner)
# - Firebase Storage Private Key
# - Stripe API Keys (Pricing Service)
# - GitHub OAuth Credentials (Integrations)
# - Notion OAuth Credentials (Integrations)
# =============================================================================

# -----------------------------------------------------------------------------
# OpenAI API Key (for PDF Scanner)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key-pdf-scanner"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant PDF Scanner access to OpenAI API key
resource "google_secret_manager_secret_iam_member" "pdf_scanner_openai_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.openai_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Firebase Storage Private Key
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "firebase_storage_private_key" {
  secret_id = "firebase-storage-private-key"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant PDF Scanner access to Firebase Storage key
resource "google_secret_manager_secret_iam_member" "pdf_scanner_firebase_storage_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.firebase_storage_private_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Stripe API Key (for Pricing Service)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "stripe_api_key" {
  secret_id = "stripe-api-key"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Pricing Service access to Stripe API key
resource "google_secret_manager_secret_iam_member" "pricing_stripe_api_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.stripe_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Stripe Webhook Secret (for Pricing Service)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "stripe_webhook_secret" {
  secret_id = "stripe-webhook-secret"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Pricing Service access to Stripe Webhook secret
resource "google_secret_manager_secret_iam_member" "pricing_stripe_webhook_secret_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.stripe_webhook_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Stripe Publishable Key (for Frontend)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "stripe_publishable_key" {
  secret_id = "stripe-publishable-key"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# -----------------------------------------------------------------------------
# GitHub OAuth Client ID (for Integrations)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "github_oauth_client_id" {
  secret_id = "github-oauth-client-id"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Integrations Worker access to GitHub Client ID
resource "google_secret_manager_secret_iam_member" "integrations_github_client_id_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.github_oauth_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# GitHub OAuth Client Secret (for Integrations)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "github_oauth_client_secret" {
  secret_id = "github-oauth-client-secret"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Integrations Worker access to GitHub Client Secret
resource "google_secret_manager_secret_iam_member" "integrations_github_client_secret_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.github_oauth_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Notion OAuth Client ID (for Integrations)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "notion_oauth_client_id" {
  secret_id = "notion-oauth-client-id"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Integrations Worker access to Notion Client ID
resource "google_secret_manager_secret_iam_member" "integrations_notion_client_id_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.notion_oauth_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Notion OAuth Client Secret (for Integrations)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "notion_oauth_client_secret" {
  secret_id = "notion-oauth-client-secret"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Integrations Worker access to Notion Client Secret
resource "google_secret_manager_secret_iam_member" "integrations_notion_client_secret_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.notion_oauth_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# Firebase Config Secrets (for Frontend)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "firebase_api_key" {
  secret_id = "firebase-api-key"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

resource "google_secret_manager_secret" "firebase_messaging_sender_id" {
  secret_id = "firebase-messaging-sender-id"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

resource "google_secret_manager_secret" "firebase_app_id" {
  secret_id = "firebase-app-id"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# -----------------------------------------------------------------------------
# Brevo API Key (for Mailing Service)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "brevo_api_key" {
  secret_id = "brevo-api-key"
  project   = var.project_id

  labels = var.labels

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis["secretmanager.googleapis.com"]
  ]
}

# Grant Mailing Service access to Brevo API key
resource "google_secret_manager_secret_iam_member" "mailing_brevo_api_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.brevo_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.compute_service_account}"
}
