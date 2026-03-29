# LumTrails Infrastructure - Terraform Configuration

This directory contains the complete Terraform Infrastructure as Code (IaC) configuration for the LumTrails accessibility scanning platform on Google Cloud Platform.

## ⚠️ IMPORTANT: Manual Setup Required

Some Firebase/GCP resources **cannot be provisioned via Terraform** and must be configured manually in the console:

### 1. Firebase Authentication (Required)
1. Go to: https://console.firebase.google.com/project/YOUR_DEV_PROJECT_ID/authentication/providers
2. Click **"Get started"** if not initialized
3. Go to **"Sign-in method"** tab
4. Enable **"Google"** provider:
   - Toggle **Enable**
   - Set **Project support email**
   - Click **Save**
5. Go to **"Settings" → "Authorized domains"** and add:
   - `YOUR_DEV_PROJECT_ID.web.app`
   - `YOUR_DEV_PROJECT_ID.firebaseapp.com`
   - `localhost`

### 2. Firebase Storage (Required)
1. Go to: https://console.firebase.google.com/project/YOUR_DEV_PROJECT_ID/storage
2. Click **"Get started"**
3. Choose **"Start in production mode"**
4. Select location: **europe-west1**
5. Click **"Done"**
6. Deploy storage rules: `firebase deploy --only storage --project=YOUR_DEV_PROJECT_ID`

### 3. Cloud Run Environment Variables (Required)
All Cloud Run services need these environment variables set:
```
GOOGLE_CLOUD_PROJECT=YOUR_DEV_PROJECT_ID
FIREBASE_PROJECT_ID=YOUR_DEV_PROJECT_ID
FIREBASE_STORAGE_BUCKET=YOUR_DEV_PROJECT_ID.firebasestorage.app
```

Update services after deployment:
```powershell
$ENV_VARS = "GOOGLE_CLOUD_PROJECT=YOUR_DEV_PROJECT_ID,FIREBASE_PROJECT_ID=YOUR_DEV_PROJECT_ID,FIREBASE_STORAGE_BUCKET=YOUR_DEV_PROJECT_ID.firebasestorage.app"
$services = @("lumtrails-api", "lumtrails-external-api", "lumtrails-integrations-worker", "lumtrails-report-generator", "lumtrails-pricing", "pdf-scan-worker", "web-scan-worker")
foreach ($svc in $services) {
    gcloud run services update $svc --project=YOUR_DEV_PROJECT_ID --region=europe-west1 --set-env-vars $ENV_VARS --quiet
}
```

## 📁 Directory Structure

```
terraform/dev/
├── main.tf                 # Provider configuration and API enablement
├── variables.tf            # Variable definitions
├── outputs.tf              # Output values
├── terraform.tfvars        # Variable values for dev environment
├── cloud_run.tf            # Cloud Run services (7 services)
├── cloud_tasks.tf          # Cloud Tasks queues (3 queues)
├── cloud_scheduler.tf      # Cloud Scheduler jobs (5 jobs)
├── secrets.tf              # Secret Manager secrets and IAM bindings
├── artifact_registry.tf    # Docker image repository
├── iam.tf                  # IAM roles and permissions
├── firestore.tf            # Firestore database and indexes
└── README.md               # This file
```

## 🚀 Prerequisites

### 1. Install Terraform

**Windows (using Chocolatey):**
```powershell
choco install terraform
```

**Windows (using Winget):**
```powershell
winget install Hashicorp.Terraform
```

**Windows (Manual Installation):**
1. Download Terraform from https://developer.hashicorp.com/terraform/downloads
2. Extract the zip file
3. Add the directory to your PATH

**Verify Installation:**
```powershell
terraform version
```

### 2. Install Google Cloud SDK

```powershell
# Install gcloud CLI
winget install Google.CloudSDK

# Authenticate with Google Cloud
gcloud auth login

# Set the project
gcloud config set project YOUR_PROJECT_ID

# Create application default credentials (for Terraform)
gcloud auth application-default login
```

### 3. Terraform Cloud Setup

1. Create an account at https://app.terraform.io
2. Create an organization (e.g., "LumTrails")
3. Create a workspace named "YOUR_DEV_PROJECT_ID"
4. Generate an API token at https://app.terraform.io/app/settings/tokens

**Login to Terraform Cloud:**
```powershell
terraform login
```

## 📋 Infrastructure Components

### Cloud Run Services (7)

| Service | Port | Description |
|---------|------|-------------|
| `lumtrails-api` | 8000 | Main API Gateway |
| `web-scan-worker` | 8080 | Web accessibility scanner |
| `pdf-scan-worker` | 8080 | PDF accessibility scanner with GPT-5 Vision |
| `lumtrails-integrations-worker` | 8080 | GitHub, Slack, Notion integrations |
| `lumtrails-external-api` | 8080 | Public REST API with API key auth |
| `lumtrails-report-generator` | 8080 | PDF report generation |
| `lumtrails-pricing` | 8080 | Subscription and billing service |

### Cloud Tasks Queues (3)

| Queue | Purpose |
|-------|---------|
| `web-scan-queue` | Website scan requests |
| `pdf-scan-queue` | PDF scan requests |
| `integration-queue` | Integration push tasks |

### Cloud Scheduler Jobs (5)

| Job | Schedule | Purpose |
|-----|----------|---------|
| `free-tier-daily-renewal` | 0 0 * * * | Daily web scan credit reset |
| `free-tier-weekly-pdf-renewal` | 0 0 * * 1 | Weekly PDF credit reset |
| `paid-plan-monthly-renewal` | 2 0 1 * * | Monthly credit reset |
| `scan-results-cleanup` | */30 * * * * | Clean old scan results |
| `api-key-expiration-cleanup` | 0 * * * * | Expire old API keys |

### Secret Manager Secrets (12)

| Secret | Used By |
|--------|---------|
| `openai-api-key-pdf-scanner` | PDF Scanner Worker |
| `firebase-storage-private-key` | PDF Scanner Worker |
| `stripe-api-key` | Pricing Service |
| `stripe-webhook-secret` | Pricing Service |
| `stripe-publishable-key` | Frontend |
| `github-oauth-client-id` | Integrations Worker |
| `github-oauth-client-secret` | Integrations Worker |
| `notion-oauth-client-id` | Integrations Worker |
| `notion-oauth-client-secret` | Integrations Worker |
| `firebase-api-key` | Frontend |
| `firebase-messaging-sender-id` | Frontend |
| `firebase-app-id` | Frontend |

## 🔧 Usage

### Initialize Terraform

```powershell
cd terraform/dev
terraform init
```

### Review the Plan

```powershell
terraform plan
```

### Apply Changes

```powershell
terraform apply
```

### Destroy Infrastructure (Caution!)

```powershell
terraform destroy
```

## ⚠️ Important Notes

### First-Time Setup

1. **Secret Values**: After `terraform apply`, you must manually add secret versions:
   ```powershell
   # Example: Add OpenAI API key
   echo "sk-your-openai-key" | gcloud secrets versions add openai-api-key-pdf-scanner --data-file=-
   
   # Example: Add Stripe API key
   echo "sk_live_your_stripe_key" | gcloud secrets versions add stripe-api-key --data-file=-
   ```

   ⚠️ **IMPORTANT: BOM Character Prevention**
   
   When migrating secrets from another environment or copying from external sources, **ensure there are no BOM (Byte Order Mark) characters** at the start of secret values. BOM characters (`\ufeff`) are invisible Unicode characters that can corrupt API keys and cause authentication failures.
   
   **Common symptoms of BOM corruption:**
   - `UnicodeEncodeError: 'ascii' codec can't encode character '\ufeff'`
   - OpenAI API authentication failures with valid keys
   - HTTP header encoding errors
   
   **To prevent BOM issues:**
   ```powershell
   # Option 1: Create secret from a clean text file (recommended)
   # Use a text editor that saves without BOM (e.g., VS Code with "UTF-8" encoding, NOT "UTF-8 with BOM")
   
   # Option 2: Pipe the key directly without any file
   echo -n "sk-your-key-here" | gcloud secrets versions add openai-api-key-pdf-scanner --data-file=-
   
   # Option 3: Use PowerShell to strip BOM before uploading
   $key = "sk-your-key-here"
   [System.IO.File]::WriteAllText("temp-key.txt", $key, [System.Text.UTF8Encoding]::new($false))
   gcloud secrets versions add openai-api-key-pdf-scanner --data-file=temp-key.txt
   Remove-Item temp-key.txt
   ```
   
   **To check if a secret has BOM:**
   ```powershell
   # This will show the raw bytes - BOM appears as "EF BB BF" at the start
   gcloud secrets versions access latest --secret=openai-api-key-pdf-scanner | Format-Hex
   ```
   
   **Note:** The PDF scanner code includes BOM stripping as a safety measure, but it's best to store clean secrets from the start.

2. **Existing Resources**: If resources already exist, import them:
   ```powershell
   # Import existing Firestore database
   terraform import google_firestore_database.database "(default)"
   
   # Import existing Cloud Run service
   terraform import google_cloud_run_v2_service.main_api projects/YOUR_PROJECT_ID/locations/europe-west1/services/lumtrails-api
   ```

3. **Docker Images**: Before deploying Cloud Run services, build and push images:
   ```powershell
   # Build and deploy Main API
   cd api
   gcloud run deploy lumtrails-api --source . --region europe-west1
   ```

### Terraform Cloud Workspace

Update the `main.tf` file with your Terraform Cloud organization:

```hcl
cloud {
  organization = "YOUR-ORGANIZATION-NAME"  # Update this

  workspaces {
    name = "YOUR_DEV_PROJECT_ID"
  }
}
```

### State Management

When using Terraform Cloud:
- State is stored remotely and encrypted
- Team members can collaborate safely
- State locking prevents concurrent modifications

## 🔒 Security Considerations

1. **Never commit secret values** to version control
2. Use Terraform Cloud's variable encryption for sensitive values
3. Service accounts use principle of least privilege
4. All Cloud Run services have appropriate IAM bindings

## 📊 Outputs

After `terraform apply`, you'll see outputs including:
- All Cloud Run service URLs
- Queue names
- Artifact Registry repository URL
- Secret IDs

Access outputs anytime:
```powershell
terraform output
```

## 🔄 CI/CD Integration

For automated deployments, configure Terraform Cloud:

1. Connect your VCS repository
2. Enable auto-apply for `main` branch
3. Use run triggers for dependent workspaces

## 📚 Resources

- [Terraform Google Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Terraform Cloud Documentation](https://developer.hashicorp.com/terraform/cloud-docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [LumTrails OVERVIEW.md](../../OVERVIEW.md)

## 🆘 Troubleshooting

### Common Issues

1. **"Error 403: Permission denied"**
   - Ensure `gcloud auth application-default login` was run
   - Verify project permissions

2. **"Resource already exists"**
   - Import the resource: `terraform import <resource> <id>`

3. **"API not enabled"**
   - The configuration enables APIs automatically
   - Wait a few minutes for API propagation

4. **"Quota exceeded"**
   - Check GCP quotas in Cloud Console
   - Request quota increases if needed

---

*Last updated: December 2025*
