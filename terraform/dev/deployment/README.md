# LumTrails Deployment Scripts

This folder contains deployment scripts for the LumTrails DEV environment.

## Scripts

### `deploy.ps1` - Main Deployment Script

Builds and deploys Cloud Run services to Google Cloud.

**Usage:**
```powershell
# Deploy all services
.\deploy.ps1 all

# Deploy specific services
.\deploy.ps1 api pricing

# Deploy multiple services
.\deploy.ps1 api web-scan pdf-scan

# Skip build and just redeploy existing images
.\deploy.ps1 api -SkipBuild

# Dry run - see what would happen without making changes
.\deploy.ps1 all -DryRun
```

**Available Services:**
| Service | Cloud Run Name | Description |
|---------|----------------|-------------|
| `api` | lumtrails-api | Main API gateway |
| `web-scan` | web-scan-worker | Web accessibility scanner |
| `pdf-scan` | pdf-scan-worker | PDF accessibility scanner |
| `integrations` | lumtrails-integrations-worker | GitHub/Slack/Notion integrations |
| `external-api` | lumtrails-external-api | External API for third-party access |
| `report-generator` | lumtrails-report-generator | PDF report generation |
| `pricing` | lumtrails-pricing | Subscription and billing |

### `migrate-secrets.ps1` - Secret Migration Script

Copies secrets from production to dev environment.

**Usage:**
```powershell
# Migrate all secrets
.\migrate-secrets.ps1

# Dry run
.\migrate-secrets.ps1 -DryRun
```

## Prerequisites

1. **Google Cloud SDK** installed and authenticated:
   ```powershell
   gcloud auth login
   gcloud config set project YOUR_DEV_PROJECT_ID
   ```

2. **Permissions** required:
   - `roles/run.admin` - Deploy Cloud Run services
   - `roles/cloudbuild.builds.editor` - Submit Cloud Build jobs
   - `roles/secretmanager.secretAccessor` - Access secrets (for migration)

## Common Deployment Scenarios

### Deploy after code changes
```powershell
# Deploy only modified services
.\deploy.ps1 api pricing web-scan pdf-scan
```

### Quick redeploy (no rebuild)
```powershell
# Redeploy using existing images
.\deploy.ps1 api -SkipBuild
```

### Full environment deploy
```powershell
# Deploy everything
.\deploy.ps1 all
```

## Troubleshooting

### Build fails
- Check Docker is running
- Verify Dockerfile exists in service folder
- Check Cloud Build logs in GCP Console

### Deploy fails
- Verify Cloud Run service exists (run `terraform apply` first)
- Check service account permissions
- Review Cloud Run logs in GCP Console
