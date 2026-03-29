# Deploy Mailing Service to Cloud Run
# Run from the mailing/ directory

param(
    [string]$ProjectId = "YOUR_PROJECT_ID",  # Replace with your GCP project ID
    [string]$Region = "europe-west1"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying LumTrails Mailing Service..." -ForegroundColor Cyan

# Set project
gcloud config set project $ProjectId

# Build and deploy using source-based deployment
Write-Host "📦 Building and deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy lumtrails-mailing `
    --source . `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --set-secrets=BREVO_API_KEY=brevo-api-key:latest `
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$ProjectId,FIREBASE_PROJECT_ID=$ProjectId,FRONTEND_URL=https://$ProjectId.web.app" `
    --memory=256Mi `
    --cpu=1 `
    --min-instances=0 `
    --max-instances=10 `
    --timeout=60s

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Mailing service deployed successfully!" -ForegroundColor Green
    
    # Get the service URL
    $serviceUrl = gcloud run services describe lumtrails-mailing --region $Region --format="value(status.url)"
    Write-Host "🌐 Service URL: $serviceUrl" -ForegroundColor Cyan
} else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}
