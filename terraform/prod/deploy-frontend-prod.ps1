# LumTrails Frontend Deploy Script - PRODUCTION Environment
# Deploys frontend to Firebase Hosting with custom domain
# Location: terraform/prod/deploy-frontend-prod.ps1

Write-Host ""
Write-Host "================================================================" -ForegroundColor Red
Write-Host "         Frontend Deployment - PRODUCTION                      " -ForegroundColor Red
Write-Host "                   !!! PRODUCTION !!!                          " -ForegroundColor Red
Write-Host "================================================================" -ForegroundColor Red
Write-Host ""

# IMPORTANT: Set your production project ID here
$PROD_PROJECT_ID = "YOUR_PROD_PROJECT_ID"
$PROD_DOMAIN = "your-domain.com"

# Safety confirmation
Write-Host "You are about to deploy the frontend to PRODUCTION!" -ForegroundColor Yellow
Write-Host "Domain: $PROD_DOMAIN" -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Type 'DEPLOY-PROD' to confirm"
if ($confirmation -ne "DEPLOY-PROD") {
    Write-Host "[ABORTED] Deployment cancelled." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Store original location
$originalLocation = Get-Location

# Navigate to web folder (from terraform/prod, go up two levels then into web)
$webPath = Join-Path $PSScriptRoot "..\..\web"
$rootPath = Join-Path $PSScriptRoot "..\.."

Push-Location $webPath

try {
    # Step 1: Copy PROD environment file
    Write-Host "[1/4] Setting up PRODUCTION environment..." -ForegroundColor Yellow
    if (-not (Test-Path ".env.prod")) {
        Write-Host "[ERROR] .env.prod file not found!" -ForegroundColor Red
        Write-Host "  Please create web/.env.prod with production configuration" -ForegroundColor Red
        throw ".env.prod not found"
    }
    Copy-Item ".env.prod" ".env" -Force
    Write-Host "  -> .env.prod copied to .env" -ForegroundColor Green

    # Step 2: Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
        npm install
    } else {
        Write-Host "[2/4] Dependencies already installed" -ForegroundColor Green
    }

    # Step 3: Build the app
    Write-Host "[3/4] Building production bundle..." -ForegroundColor Yellow
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed!"
    }
    Write-Host "  -> Build successful" -ForegroundColor Green

    # Step 4: Deploy to Firebase Hosting (PRODUCTION)
    Write-Host "[4/4] Deploying to Firebase Hosting (PRODUCTION)..." -ForegroundColor Yellow
    Push-Location $rootPath
    firebase deploy --only hosting --project=$PROD_PROJECT_ID
    Pop-Location

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host "PRODUCTION Deployment Successful!" -ForegroundColor Green
        Write-Host "================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your app is live at:" -ForegroundColor Cyan
        Write-Host "  https://$PROD_DOMAIN" -ForegroundColor White
        Write-Host "  https://$PROD_PROJECT_ID.web.app (fallback)" -ForegroundColor DarkGray
        Write-Host "  https://$PROD_PROJECT_ID.firebaseapp.com (fallback)" -ForegroundColor DarkGray
    } else {
        throw "Firebase deployment failed!"
    }
}
catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
finally {
    # Always return to web folder first, then pop back to original
    Pop-Location
}
