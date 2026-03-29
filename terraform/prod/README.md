# LumTrails Infrastructure - PRODUCTION Environment

This directory contains the Terraform Infrastructure as Code (IaC) configuration for the LumTrails PRODUCTION environment on Google Cloud Platform.

## ⚠️ PRODUCTION ENVIRONMENT WARNING

This is the **PRODUCTION** environment. Changes here affect live users at **your-domain.com**.

- Always test changes in DEV first
- Use `terraform plan` before `terraform apply`
- Require explicit confirmation for deployments
- Keep secrets secure and never commit them

## 🔧 Key Differences from DEV

| Feature | DEV | PROD |
|---------|-----|------|
| Project ID | `YOUR_DEV_PROJECT_ID` | `YOUR_PROD_PROJECT_ID` |
| Domain | `YOUR_DEV_PROJECT_ID.web.app` | `your-domain.com` |
| Email Whitelist | Enabled (restricted access) | Disabled (all users allowed) |
| Stripe Keys | Test keys (`sk_test_...`) | Live keys (`sk_live_...`) |
| GitHub/Notion OAuth | Dev OAuth apps | Prod OAuth apps |
| Prevent Destroy | `false` | `true` (critical resources) |
| Logging | Enabled | Enabled (for debugging) |

## ⚠️ Manual Setup Required

Some Firebase/GCP resources **cannot be provisioned via Terraform** and must be configured manually:

### 1. Firebase Authentication (Required)
1. Go to: https://console.firebase.google.com/project/YOUR_PROD_PROJECT_ID/authentication/providers
2. Click **"Get started"** if not initialized
3. Go to **"Sign-in method"** tab
4. Enable **"Google"** provider:
   - Toggle **Enable**
   - Set **Project support email**
   - Click **Save**
5. Go to **"Settings" → "Authorized domains"** and add:
   - `your-domain.com`
   - `www.your-domain.com`
   - `YOUR_PROD_PROJECT_ID.web.app`
   - `YOUR_PROD_PROJECT_ID.firebaseapp.com`
   - `localhost` (for local development)

### 2. Firebase Storage (Required)
1. Go to: https://console.firebase.google.com/project/YOUR_PROD_PROJECT_ID/storage
2. Click **"Get started"**
3. Choose **"Start in production mode"**
4. Select location: **europe-west1**
5. Click **"Done"**
6. Deploy storage rules: `firebase deploy --only storage --project=YOUR_PROD_PROJECT_ID`

### 3. Custom Domain Setup (your-domain.com)
See the main STEPS.md document for detailed instructions on:
- Firebase Hosting custom domain configuration
- DNS configuration
- SSL certificate provisioning

### 4. Cloud Run Environment Variables (Required)
All Cloud Run services need these environment variables set:
```
GOOGLE_CLOUD_PROJECT=YOUR_PROD_PROJECT_ID
FIREBASE_PROJECT_ID=YOUR_PROD_PROJECT_ID
FIREBASE_STORAGE_BUCKET=YOUR_PROD_PROJECT_ID.firebasestorage.app
```

## 🔐 Secrets Configuration

### ⚠️ BOM Character Prevention

When adding secrets, **ensure there are no BOM (Byte Order Mark) characters**. BOM characters can corrupt API keys and cause authentication failures.

**Use the provided script:**
```powershell
# Interactive mode - prompts for values
.\deployment\migrate-secrets.ps1 -Interactive

# Or set manually (BOM-safe method):
$key = "sk-your-key-here"
[System.IO.File]::WriteAllText("temp.txt", $key, [System.Text.UTF8Encoding]::new($false))
gcloud secrets versions add openai-api-key-pdf-scanner --data-file=temp.txt --project=YOUR_PROD_PROJECT_ID
Remove-Item temp.txt
```

### Required Secrets for PRODUCTION

| Secret | Description | Notes |
|--------|-------------|-------|
| `openai-api-key-pdf-scanner` | OpenAI API Key | Can be shared with DEV |
| `firebase-storage-private-key` | Service account JSON | PROD-specific |
| `stripe-api-key` | Stripe secret key | Use `sk_live_...` |
| `stripe-webhook-secret` | Stripe webhook secret | Create new webhook in Stripe |
| `stripe-publishable-key` | Stripe public key | Use `pk_live_...` |
| `github-oauth-client-id` | GitHub OAuth App ID | Create PROD OAuth app |
| `github-oauth-client-secret` | GitHub OAuth Secret | |
| `notion-oauth-client-id` | Notion OAuth App ID | Create PROD OAuth app |
| `notion-oauth-client-secret` | Notion OAuth Secret | |
| `firebase-api-key` | Firebase Web API Key | From Firebase Console |
| `firebase-messaging-sender-id` | Firebase Sender ID | From Firebase Console |
| `firebase-app-id` | Firebase App ID | From Firebase Console |
| `brevo-api-key` | Brevo Email API Key | Can be shared or separate |

## 🚀 Deployment

### Initial Setup

```powershell
cd terraform/prod
terraform init
terraform plan
terraform apply
```

### Deploy Services

```powershell
# Deploy all services (requires confirmation)
.\deploy.ps1 all

# Deploy specific services
.\deploy.ps1 api pricing mailing

# Dry run
.\deploy.ps1 all -DryRun
```

### Deploy Frontend

```powershell
# Deploys to your-domain.com
.\deploy-frontend-prod.ps1
```

## 📊 Monitoring

Production includes additional monitoring alerts:
- Pricing service error rate (critical - lower threshold)
- API error rates and latency
- Cloud Tasks queue depth
- PDF scanner error rates

Access Cloud Monitoring: https://console.cloud.google.com/monitoring?project=YOUR_PROD_PROJECT_ID

## 🔒 Security Notes

1. **Never commit secrets** to version control
2. All deployments require explicit confirmation
3. Critical resources have `prevent_destroy = true`
4. Use Terraform Cloud for state management
5. Review all changes with `terraform plan` first

## 📚 See Also

- [Main STEPS.md](../../STEPS.md) - Complete production setup guide
- [DEV README](../dev/README.md) - DEV environment documentation
- [OVERVIEW.md](../../OVERVIEW.md) - Project architecture overview
