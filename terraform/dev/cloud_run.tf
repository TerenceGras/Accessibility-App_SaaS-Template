# =============================================================================
# LumTrails Infrastructure - Cloud Run Services
# =============================================================================
# This file defines all 7 Cloud Run services:
# 1. Main API Gateway (lumtrails-api)
# 2. Web Scanner Worker (web-scan-worker)
# 3. PDF Scanner Worker (pdf-scan-worker)
# 4. Integrations Worker (lumtrails-integrations-worker)
# 5. External API (lumtrails-external-api)
# 6. Report Generator (lumtrails-report-generator)
# 7. Pricing Service (lumtrails-pricing)
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Main API Gateway
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "main_api" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "lumtrails-api"
  location = var.region
  project  = var.project_id
  
  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/lumtrails-api:latest"
      
      ports {
        container_port = 8000
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PROJECT_NUMBER"
        value = local.project_number
      }
      env {
        name  = "CLOUD_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "CLOUD_TASKS_QUEUE"
        value = "web-scan-queue"
      }
      env {
        name  = "PDF_SCAN_QUEUE"
        value = "pdf-scan-queue"
      }
      env {
        name  = "INTEGRATION_QUEUE_NAME"
        value = "integration-queue"
      }
      env {
        name  = "WORKER_URL"
        value = "https://web-scan-worker-${local.project_number}.${var.region}.run.app"
      }
      env {
        name  = "PDF_WORKER_URL"
        value = "https://pdf-scan-worker-${local.project_number}.${var.region}.run.app"
      }
      env {
        name  = "INTEGRATION_WORKER_URL"
        value = "https://lumtrails-integrations-worker-${local.project_number}.${var.region}.run.app"
      }
      env {
        name  = "FIREBASE_STORAGE_BUCKET"
        value = local.firebase_storage_bucket
      }
      env {
        name = "GITHUB_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = "github-oauth-client-id"
            version = "latest"
          }
        }
      }
      env {
        name = "GITHUB_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = "github-oauth-client-secret"
            version = "latest"
          }
        }
      }
      env {
        name = "NOTION_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = "notion-oauth-client-id"
            version = "latest"
          }
        }
      }
      env {
        name = "NOTION_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = "notion-oauth-client-secret"
            version = "latest"
          }
        }
      }
      env {
        name  = "FRONTEND_URL"
        value = "https://${var.project_id}.web.app"
      }
      # DEV environment email whitelist - only these emails can access the dev API
      env {
        name  = "DEV_WHITELIST_EMAILS"
        value = join(",", var.dev_whitelist_emails)
      }
      # Slack webhook for new user notifications
      env {
        name  = "SLACK_NEW_USER_WEBHOOK"
        value = var.slack_new_user_webhook
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
    }

    # Scale to zero when idle to save costs (DEV environment)
    # Note: This increases cold start latency but saves ~€15-20/month
    scaling {
      min_instance_count = 0
    }

    timeout = "${var.cloud_run_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_project.lumtrails_dev
  ]
}

# Allow unauthenticated access to Main API
resource "google_cloud_run_v2_service_iam_member" "main_api_public" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.main_api[0].location
  name     = google_cloud_run_v2_service.main_api[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# -----------------------------------------------------------------------------
# 2. Web Scanner Worker
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "web_scanner_worker" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "web-scan-worker"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/web-scan-worker:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_STORAGE_BUCKET"
        value = local.firebase_storage_bucket
      }

      resources {
        limits = {
          cpu    = var.web_scanner_cpu
          memory = var.web_scanner_memory
        }
      }
    }

    timeout = "${var.cloud_run_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_project.lumtrails_dev
  ]
}

# Allow Cloud Tasks to invoke this worker service
resource "google_cloud_run_v2_service_iam_member" "web_scanner_invoker" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.web_scanner_worker[0].location
  name     = google_cloud_run_v2_service.web_scanner_worker[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# 3. PDF Scanner Worker
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "pdf_scanner_worker" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "pdf-scan-worker"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/pdf-scan-worker:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "FIREBASE_STORAGE_BUCKET"
        value = local.firebase_storage_bucket
      }
      env {
        name  = "FIREBASE_STORAGE_SA_SECRET_NAME"
        value = "firebase-storage-private-key"
      }
      env {
        name  = "MAX_CONCURRENT_GPT_SCANS"
        value = tostring(var.pdf_scanner_max_concurrent_scans)
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      # OpenAI API Key from Secret Manager
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.pdf_scanner_cpu
          memory = var.pdf_scanner_memory
        }
      }
    }

    timeout = "${var.pdf_scanner_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_secret_manager_secret.openai_api_key,
    google_secret_manager_secret_iam_member.pdf_scanner_openai_access,
    google_project.lumtrails_dev
  ]
}

# Allow Cloud Tasks to invoke this worker service
resource "google_cloud_run_v2_service_iam_member" "pdf_scanner_invoker" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.pdf_scanner_worker[0].location
  name     = google_cloud_run_v2_service.pdf_scanner_worker[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# 4. Integrations Worker
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "integrations_worker" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "lumtrails-integrations-worker"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/lumtrails-integrations-worker:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }

      # GitHub OAuth credentials
      env {
        name = "GITHUB_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.github_oauth_client_id.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GITHUB_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.github_oauth_client_secret.secret_id
            version = "latest"
          }
        }
      }

      # Notion OAuth credentials
      env {
        name = "NOTION_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.notion_oauth_client_id.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "NOTION_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.notion_oauth_client_secret.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
    }

    timeout = "${var.cloud_run_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_secret_manager_secret_iam_member.integrations_github_client_id_access,
    google_secret_manager_secret_iam_member.integrations_github_client_secret_access,
    google_secret_manager_secret_iam_member.integrations_notion_client_id_access,
    google_secret_manager_secret_iam_member.integrations_notion_client_secret_access,
    google_project.lumtrails_dev
  ]
}

# Allow Cloud Tasks to invoke this worker service
resource "google_cloud_run_v2_service_iam_member" "integrations_worker_invoker" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.integrations_worker[0].location
  name     = google_cloud_run_v2_service.integrations_worker[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.compute_service_account}"
}

# -----------------------------------------------------------------------------
# 5. External API
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "external_api" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "lumtrails-external-api"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/lumtrails-external-api:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PROJECT_NUMBER"
        value = local.project_number
      }
      env {
        name  = "CLOUD_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "CLOUD_TASKS_QUEUE"
        value = "web-scan-queue"
      }
      env {
        name  = "PDF_SCAN_QUEUE"
        value = "pdf-scan-queue"
      }
      env {
        name  = "INTEGRATION_QUEUE_NAME"
        value = "integration-queue"
      }
      env {
        name  = "WORKER_URL"
        value = "https://web-scan-worker-${local.project_number}.${var.region}.run.app"
      }
      env {
        name  = "PDF_WORKER_URL"
        value = "https://pdf-scan-worker-${local.project_number}.${var.region}.run.app"
      }
      env {
        name  = "INTEGRATION_WORKER_URL"
        value = "https://lumtrails-integrations-worker-${local.project_number}.${var.region}.run.app"
      }
      env {
        name  = "FIREBASE_STORAGE_BUCKET"
        value = local.firebase_storage_bucket
      }
      # DEV environment email whitelist
      env {
        name  = "DEV_WHITELIST_EMAILS"
        value = join(",", var.dev_whitelist_emails)
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
    }

    timeout = "${var.cloud_run_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_project.lumtrails_dev
  ]
}

# Allow unauthenticated access to External API
resource "google_cloud_run_v2_service_iam_member" "external_api_public" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.external_api[0].location
  name     = google_cloud_run_v2_service.external_api[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# -----------------------------------------------------------------------------
# 6. Report Generator
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "report_generator" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "lumtrails-report-generator"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/lumtrails-report-generator:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
    }

    timeout = "${var.report_generator_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_project.lumtrails_dev
  ]
}

# Allow unauthenticated access to Report Generator (frontend access)
resource "google_cloud_run_v2_service_iam_member" "report_generator_public" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.report_generator[0].location
  name     = google_cloud_run_v2_service.report_generator[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# -----------------------------------------------------------------------------
# 7. Pricing Service
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "pricing_service" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "lumtrails-pricing"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/lumtrails-pricing:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }

      # Stripe API Key from Secret Manager
      env {
        name = "STRIPE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.stripe_api_key.secret_id
            version = "latest"
          }
        }
      }

      # Stripe Webhook Secret from Secret Manager
      env {
        name = "STRIPE_WEBHOOK_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.stripe_webhook_secret.secret_id
            version = "latest"
          }
        }
      }

      # Stripe Price IDs for DEV (TEST mode)
      env {
        name  = "STRIPE_STANDARD_MONTHLY_PRICE_ID"
        value = var.stripe_standard_monthly_price_id
      }
      env {
        name  = "STRIPE_STANDARD_YEARLY_PRICE_ID"
        value = var.stripe_standard_yearly_price_id
      }
      env {
        name  = "STRIPE_BUSINESS_MONTHLY_PRICE_ID"
        value = var.stripe_business_monthly_price_id
      }
      env {
        name  = "STRIPE_BUSINESS_YEARLY_PRICE_ID"
        value = var.stripe_business_yearly_price_id
      }
      # Main API URL for service-to-service calls
      env {
        name  = "MAIN_API_URL"
        value = "https://lumtrails-api-${local.project_number}.${var.region}.run.app"
      }
      # Slack webhook for subscription notifications
      env {
        name  = "SLACK_SUBSCRIPTION_WEBHOOK"
        value = var.slack_subscription_webhook
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.pricing_service_memory
        }
      }
    }

    timeout = "${var.cloud_run_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_secret_manager_secret_iam_member.pricing_stripe_api_key_access,
    google_secret_manager_secret_iam_member.pricing_stripe_webhook_secret_access,
    google_project.lumtrails_dev
  ]
}

# Allow unauthenticated access to Pricing Service
resource "google_cloud_run_v2_service_iam_member" "pricing_service_public" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.pricing_service[0].location
  name     = google_cloud_run_v2_service.pricing_service[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# -----------------------------------------------------------------------------
# 8. Mailing Service
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "mailing_service" {
  count    = var.create_cloud_run_services ? 1 : 0
  name     = "lumtrails-mailing"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/lumtrails-mailing:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "FRONTEND_URL"
        value = "https://${var.project_id}.web.app"
      }

      # Brevo API Key from Secret Manager
      env {
        name = "BREVO_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.brevo_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
    }

    timeout = "${var.cloud_run_timeout}s"

    service_account = local.compute_service_account
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  depends_on = [
    google_project_service.required_apis["run.googleapis.com"],
    google_artifact_registry_repository.cloud_run_images,
    google_secret_manager_secret_iam_member.mailing_brevo_api_key_access,
    google_project.lumtrails_dev
  ]
}

# Internal access only - other services call this via IAM
resource "google_cloud_run_v2_service_iam_member" "mailing_service_internal" {
  count    = var.create_cloud_run_services ? 1 : 0
  location = google_cloud_run_v2_service.mailing_service[0].location
  name     = google_cloud_run_v2_service.mailing_service[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.compute_service_account}"
}
