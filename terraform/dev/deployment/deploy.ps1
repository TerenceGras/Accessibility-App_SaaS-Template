<#
.SYNOPSIS
    LumTrails DEV Deployment Script
    
.DESCRIPTION
    Builds and deploys Cloud Run services for LumTrails DEV environment.
    
.PARAMETER Service
    Service(s) to deploy. Use 'all' for all services, or specify individual services:
    api, web-scan, pdf-scan, integrations, external-api, report-generator, pricing
    
.PARAMETER SkipBuild
    Skip the Docker build step and only deploy existing images.
    
.PARAMETER DryRun
    Show what would be done without actually building or deploying.

.EXAMPLE
    .\deploy.ps1 api pricing
    Deploys only the api and pricing services.

.EXAMPLE
    .\deploy.ps1 all
    Deploys all services.

.EXAMPLE
    .\deploy.ps1 web-scan pdf-scan -SkipBuild
    Deploys web-scan and pdf-scan workers using existing images.
#>

param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Service = @("all"),
    [switch]$SkipBuild,
    [switch]$DryRun
)

# Configuration
$PROJECT_ID = "YOUR_DEV_PROJECT_ID"
$REGION = "europe-west1"
$REGISTRY = "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy"

# Calculate paths - deployment folder is at terraform/dev/deployment
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DEV_DIR = (Get-Item $SCRIPT_DIR).Parent.FullName
$TERRAFORM_DIR = (Get-Item $DEV_DIR).Parent.FullName
$ROOT_DIR = (Get-Item $TERRAFORM_DIR).Parent.FullName

# Service definitions
$SERVICES = @{
    "api" = @{
        SourcePath = "api"
        CloudRunName = "lumtrails-api"
        Port = 8000
        Description = "Main API gateway"
    }
    "web-scan" = @{
        SourcePath = "scans\web-scan"
        CloudRunName = "web-scan-worker"
        Port = 8080
        Description = "Web accessibility scanner worker"
    }
    "pdf-scan" = @{
        SourcePath = "scans\pdf-scan"
        CloudRunName = "pdf-scan-worker"
        Port = 8080
        Description = "PDF accessibility scanner worker"
    }
    "integrations" = @{
        SourcePath = "integrations"
        CloudRunName = "lumtrails-integrations-worker"
        Port = 8080
        Description = "GitHub/Slack/Notion integrations worker"
    }
    "external-api" = @{
        SourcePath = "external-api"
        CloudRunName = "lumtrails-external-api"
        Port = 8080
        Description = "External API for third-party access"
    }
    "report-generator" = @{
        SourcePath = "report-generator"
        CloudRunName = "lumtrails-report-generator"
        Port = 8080
        Description = "PDF report generation service"
    }
    "pricing" = @{
        SourcePath = "pricing"
        CloudRunName = "lumtrails-pricing"
        Port = 8080
        Description = "Subscription and billing service"
    }
}

# Helper functions
function Write-Header {
    param($Message)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Write-ServiceHeader {
    param($ServiceName, $Description)
    Write-Host ""
    Write-Host "┌─────────────────────────────────────────────────────────" -ForegroundColor Magenta
    Write-Host "│ Deploying: $ServiceName" -ForegroundColor Magenta
    Write-Host "│ $Description" -ForegroundColor DarkMagenta
    Write-Host "└─────────────────────────────────────────────────────────" -ForegroundColor Magenta
}

Write-Header "LumTrails DEV Deployment"

Write-Host "Project:    $PROJECT_ID" -ForegroundColor White
Write-Host "Region:     $REGION" -ForegroundColor White
Write-Host "Root:       $ROOT_DIR" -ForegroundColor White
Write-Host ""

# Set GCP project
gcloud config set project $PROJECT_ID 2>$null

# Determine services to deploy
$servicesToDeploy = @()
if ($Service -contains "all") {
    $servicesToDeploy = $SERVICES.Keys | Sort-Object
    Write-Host "Services:   ALL ($($servicesToDeploy.Count) services)" -ForegroundColor Yellow
} else {
    $servicesToDeploy = $Service
    Write-Host "Services:   $($servicesToDeploy -join ', ')" -ForegroundColor Yellow
}

if ($DryRun) { 
    Write-Host ""
    Write-Host "⚠ DRY RUN MODE - No changes will be made" -ForegroundColor Yellow 
}
if ($SkipBuild) { 
    Write-Host "⚠ SKIP BUILD - Using existing images" -ForegroundColor Yellow 
}

# Track results
$successful = @()
$failed = @()
$startTime = Get-Date

foreach ($svc in $servicesToDeploy) {
    $config = $SERVICES[$svc]
    if (-not $config) {
        Write-Host ""
        Write-Host "[ERROR] Unknown service: $svc" -ForegroundColor Red
        Write-Host "Available services: $($SERVICES.Keys -join ', ')" -ForegroundColor DarkGray
        $failed += $svc
        continue
    }
    
    $sourcePath = Join-Path $ROOT_DIR $config.SourcePath
    $imageName = "$REGISTRY/$($config.CloudRunName):latest"
    $cloudRunName = $config.CloudRunName
    $port = $config.Port
    
    Write-ServiceHeader $svc $config.Description
    Write-Host "  Source:     $sourcePath" -ForegroundColor DarkGray
    Write-Host "  Image:      $imageName" -ForegroundColor DarkGray
    Write-Host "  Cloud Run:  $cloudRunName" -ForegroundColor DarkGray
    Write-Host "  Port:       $port" -ForegroundColor DarkGray
    
    # Validate source
    if (-not (Test-Path $sourcePath)) {
        Write-Host "  [ERROR] Source directory not found!" -ForegroundColor Red
        $failed += $svc
        continue
    }
    
    if (-not (Test-Path (Join-Path $sourcePath "Dockerfile"))) {
        Write-Host "  [ERROR] Dockerfile not found!" -ForegroundColor Red
        $failed += $svc
        continue
    }
    
    # Build phase
    if (-not $SkipBuild) {
        Write-Host ""
        Write-Host "  [1/2] Building with Cloud Build..." -ForegroundColor Cyan
        if (-not $DryRun) {
            $buildStart = Get-Date
            gcloud builds submit $sourcePath --tag $imageName --project $PROJECT_ID --quiet 2>&1 | ForEach-Object {
                if ($_ -match "ERROR|error:|failed") {
                    Write-Host "       $_" -ForegroundColor Red
                } elseif ($_ -match "SUCCESS|DONE") {
                    Write-Host "       $_" -ForegroundColor Green
                }
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  [ERROR] Build failed!" -ForegroundColor Red
                $failed += $svc
                continue
            }
            $buildTime = ((Get-Date) - $buildStart).TotalSeconds
            Write-Host "       Build completed in $([math]::Round($buildTime, 1))s" -ForegroundColor Green
        } else {
            Write-Host "       (dry-run: would build image)" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host ""
        Write-Host "  [1/2] Skipping build (using existing image)" -ForegroundColor DarkYellow
    }
    
    # Deploy phase
    Write-Host "  [2/2] Deploying to Cloud Run..." -ForegroundColor Cyan
    if (-not $DryRun) {
        $deployStart = Get-Date
        gcloud run deploy $cloudRunName `
            --image $imageName `
            --region $REGION `
            --project $PROJECT_ID `
            --port $port `
            --allow-unauthenticated `
            --quiet 2>&1 | ForEach-Object {
                if ($_ -match "ERROR|error:") {
                    Write-Host "       $_" -ForegroundColor Red
                }
            }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [ERROR] Deployment failed!" -ForegroundColor Red
            $failed += $svc
            continue
        }
        $deployTime = ((Get-Date) - $deployStart).TotalSeconds
        Write-Host "       Deployed in $([math]::Round($deployTime, 1))s" -ForegroundColor Green
    } else {
        Write-Host "       (dry-run: would deploy)" -ForegroundColor DarkYellow
    }
    
    Write-Host ""
    Write-Host "  ✓ $svc deployed successfully!" -ForegroundColor Green
    $successful += $svc
}

# Summary
$totalTime = ((Get-Date) - $startTime).TotalSeconds

Write-Header "Deployment Summary"

Write-Host "Total time: $([math]::Round($totalTime, 1)) seconds" -ForegroundColor White
Write-Host ""

if ($successful.Count -gt 0) {
    Write-Host "✓ Successfully deployed ($($successful.Count)):" -ForegroundColor Green
    foreach ($svc in $successful) {
        Write-Host "  • $svc" -ForegroundColor Green
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "✗ Failed ($($failed.Count)):" -ForegroundColor Red
    foreach ($svc in $failed) {
        Write-Host "  • $svc" -ForegroundColor Red
    }
}

# Show URLs for successful deployments
if (-not $DryRun -and $successful.Count -gt 0) {
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor Cyan
    foreach ($svc in $successful) {
        $name = $SERVICES[$svc].CloudRunName
        $url = gcloud run services describe $name --region $REGION --project $PROJECT_ID --format "value(status.url)" 2>$null
        if ($url) {
            Write-Host "  $svc" -ForegroundColor White -NoNewline
            Write-Host " → " -ForegroundColor DarkGray -NoNewline
            Write-Host "$url" -ForegroundColor Cyan
        }
    }
}

Write-Host ""

# Exit with error code if any failures
if ($failed.Count -gt 0) {
    exit 1
}
