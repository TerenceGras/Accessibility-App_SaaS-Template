# Frontend Deploy Script - DEV Environment
# Deploys frontend to Firebase Hosting
# Location: terraform/dev/deploy-frontend-dev.ps1

# IMPORTANT: Set your dev project ID here
$DEV_PROJECT_ID = "YOUR_DEV_PROJECT_ID"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Frontend Deployment - DEV" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Store original location
$originalLocation = Get-Location

# Navigate to web folder (from terraform/dev, go up two levels then into web)
$webPath = Join-Path $PSScriptRoot "..\..\web"
$rootPath = Join-Path $PSScriptRoot "..\.."

Push-Location $webPath

try {
    # Step 1: Copy DEV environment file
    Write-Host "[1/4] Setting up DEV environment..." -ForegroundColor Yellow
    Copy-Item ".env.dev" ".env" -Force
    Write-Host "  -> .env.dev copied to .env" -ForegroundColor Green

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

    # Step 4: Deploy to Firebase Hosting
    Write-Host "[4/4] Deploying to Firebase Hosting..." -ForegroundColor Yellow
    Push-Location $rootPath
    firebase deploy --only hosting --project=$DEV_PROJECT_ID
    Pop-Location

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Deployment Successful!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your app is live at:" -ForegroundColor Cyan
        Write-Host "  https://$DEV_PROJECT_ID.web.app" -ForegroundColor White
        Write-Host "  https://$DEV_PROJECT_ID.firebaseapp.com" -ForegroundColor White
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
