# =============================================================================
# LumTrails Infrastructure - Main Configuration (PRODUCTION)
# =============================================================================
# This Terraform configuration manages the LumTrails accessibility scanning
# platform infrastructure on Google Cloud Platform.
#
# Workspace: YOUR_TERRAFORM_CLOUD_WORKSPACE_PROD
# Region: europe-west1 (Belgium)
# Domain: your-domain.com
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }

  # Terraform Cloud Configuration
  # Using local execution mode - Terraform runs locally, state stored in Terraform Cloud
  # Replace with your own organization and workspace names, or remove the cloud block
  # to use local state instead.
  cloud {
    organization = "YOUR_TERRAFORM_CLOUD_ORG"

    workspaces {
      name = "YOUR_TERRAFORM_CLOUD_WORKSPACE_PROD"
    }
  }
}

# =============================================================================
# Provider Configuration
# =============================================================================

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# Create New GCP Project
# =============================================================================

resource "google_project" "lumtrails_prod" {
  name            = var.project_name
  project_id      = var.project_id
  billing_account = var.billing_account_id

  # Optional: Set organization or folder
  org_id    = var.org_id != "" ? var.org_id : null
  folder_id = var.folder_id != "" ? var.folder_id : null

  labels = var.labels

  # Prevent accidental deletion - IMPORTANT for production
  lifecycle {
    prevent_destroy = true
  }
}

# =============================================================================
# Enable Required APIs
# =============================================================================

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudtasks.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "firebase.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "firebasestorage.googleapis.com",
    "storage.googleapis.com",
    "identitytoolkit.googleapis.com",
    # Additional APIs for custom domain and load balancing
    "certificatemanager.googleapis.com",
    "dns.googleapis.com",
    # Google Analytics API
    "analyticsadmin.googleapis.com",
  ])

  project            = google_project.lumtrails_prod.project_id
  service            = each.value
  disable_on_destroy = false

  depends_on = [google_project.lumtrails_prod]
}

# =============================================================================
# Firebase Project Setup
# =============================================================================

resource "google_firebase_project" "default" {
  provider = google-beta
  project  = google_project.lumtrails_prod.project_id

  depends_on = [
    google_project_service.required_apis["firebase.googleapis.com"]
  ]
}

# Firebase Web App
resource "google_firebase_web_app" "lumtrails_web" {
  provider     = google-beta
  project      = google_project.lumtrails_prod.project_id
  display_name = "LumTrails Web App (PROD)"

  depends_on = [google_firebase_project.default]
}

# =============================================================================
# Data Sources
# =============================================================================

data "google_project" "project" {
  project_id = google_project.lumtrails_prod.project_id

  depends_on = [google_project.lumtrails_prod]
}

# =============================================================================
# Local Values
# =============================================================================

locals {
  project_number          = google_project.lumtrails_prod.number
  firebase_storage_bucket = var.firebase_storage_bucket != "" ? var.firebase_storage_bucket : "${var.project_id}.firebasestorage.app"
  
  # Service account email for the default compute service account
  compute_service_account = "${google_project.lumtrails_prod.number}-compute@developer.gserviceaccount.com"
  
  # Production domain
  production_domain = "your-domain.com"
  frontend_url      = "https://${local.production_domain}"
}
