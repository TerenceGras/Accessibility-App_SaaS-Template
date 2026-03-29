param(
    [Parameter(Position = 0)]
    [string[]]$Service = @("all"),
    [switch]$SkipBuild,
    [switch]$DryRun
)

$PROJECT_ID = "YOUR_PROD_PROJECT_ID"  # Replace with your production GCP project ID
$PROD_DOMAIN = "your-domain.com"     # Replace with your production domain
$REGION = "europe-west1"
$REGISTRY = "$REGION-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = (Get-Item $SCRIPT_DIR).Parent.Parent.FullName

$SERVICES = @{
    "api" = @{
        SourcePath = "api"
        CloudRunName = "lumtrails-api"
        Port = 8000
    }
    "web-scan" = @{
        SourcePath = "scans\web-scan"
        CloudRunName = "web-scan-worker"
        Port = 8080
    }
    "pdf-scan" = @{
        SourcePath = "scans\pdf-scan"
        CloudRunName = "pdf-scan-worker"
        Port = 8080
    }
    "integrations" = @{
        SourcePath = "integrations"
        CloudRunName = "lumtrails-integrations-worker"
        Port = 8080
    }
    "external-api" = @{
        SourcePath = "external-api"
        CloudRunName = "lumtrails-external-api"
        Port = 8080
    }
    "report-generator" = @{
        SourcePath = "report-generator"
        CloudRunName = "lumtrails-report-generator"
        Port = 8080
    }
    "pricing" = @{
        SourcePath = "pricing"
        CloudRunName = "lumtrails-pricing"
        Port = 8080
    }
    "mailing" = @{
        SourcePath = "mailing"
        CloudRunName = "lumtrails-mailing"
        Port = 8080
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Red
Write-Host "         LumTrails PRODUCTION Deployment Script                " -ForegroundColor Red
Write-Host "                   !!! PRODUCTION !!!                          " -ForegroundColor Red
Write-Host "================================================================" -ForegroundColor Red
Write-Host ""

# Safety confirmation for production
if (-not $DryRun) {
    Write-Host "You are about to deploy to PRODUCTION ($PROJECT_ID)!" -ForegroundColor Yellow
    Write-Host "Domain: $PROD_DOMAIN" -ForegroundColor Yellow
    Write-Host ""
    $confirmation = Read-Host "Type 'DEPLOY-PROD' to confirm"
    if ($confirmation -ne "DEPLOY-PROD") {
        Write-Host "[ABORTED] Deployment cancelled." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

gcloud config set project $PROJECT_ID 2>$null

$servicesToDeploy = @()
if ($Service -contains "all") {
    $servicesToDeploy = $SERVICES.Keys | Sort-Object
    Write-Host "[INFO] Deploying ALL services to PRODUCTION" -ForegroundColor Cyan
} else {
    $servicesToDeploy = $Service
    Write-Host "[INFO] Deploying: $($servicesToDeploy -join ', ') to PRODUCTION" -ForegroundColor Cyan
}

if ($DryRun) { Write-Host "[WARNING] DRY RUN MODE" -ForegroundColor Yellow }
if ($SkipBuild) { Write-Host "[WARNING] SKIP BUILD MODE" -ForegroundColor Yellow }
Write-Host ""

$successful = @()
$failed = @()

foreach ($svc in $servicesToDeploy) {
    $config = $SERVICES[$svc]
    if (-not $config) {
        Write-Host "[ERROR] Unknown service: $svc" -ForegroundColor Red
        $failed += $svc
        continue
    }
    
    $sourcePath = Join-Path $ROOT_DIR $config.SourcePath
    $imageName = "$REGISTRY/$($config.CloudRunName):latest"
    $cloudRunName = $config.CloudRunName
    $port = $config.Port
    
    Write-Host ""
    Write-Host "=== Deploying $svc (PROD) ===" -ForegroundColor Magenta
    Write-Host "  Source: $sourcePath"
    Write-Host "  Image: $imageName"
    Write-Host "  Cloud Run: $cloudRunName"
    
    if (-not (Test-Path $sourcePath)) {
        Write-Host "[ERROR] Source not found: $sourcePath" -ForegroundColor Red
        $failed += $svc
        continue
    }
    
    if (-not (Test-Path (Join-Path $sourcePath "Dockerfile"))) {
        Write-Host "[ERROR] Dockerfile not found" -ForegroundColor Red
        $failed += $svc
        continue
    }
    
    if (-not $SkipBuild) {
        Write-Host "  Building with Cloud Build..." -ForegroundColor Cyan
        if (-not $DryRun) {
            gcloud builds submit $sourcePath --tag $imageName --project $PROJECT_ID --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Build failed" -ForegroundColor Red
                $failed += $svc
                continue
            }
        } else {
            Write-Host "  (dry-run: would build)" -ForegroundColor DarkYellow
        }
    }
    
    Write-Host "  Deploying to Cloud Run (PROD)..." -ForegroundColor Cyan
    if (-not $DryRun) {
        gcloud run deploy $cloudRunName --image $imageName --region $REGION --project $PROJECT_ID --port $port --allow-unauthenticated --cpu-throttling --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Deploy failed" -ForegroundColor Red
            $failed += $svc
            continue
        }
    } else {
        Write-Host "  (dry-run: would deploy)" -ForegroundColor DarkYellow
    }
    
    Write-Host "[SUCCESS] $svc deployed to PRODUCTION!" -ForegroundColor Green
    $successful += $svc
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "PRODUCTION Deployment Summary" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

if ($successful.Count -gt 0) {
    Write-Host "[SUCCESS] Deployed: $($successful -join ', ')" -ForegroundColor Green
}
if ($failed.Count -gt 0) {
    Write-Host "[FAILED] Failed: $($failed -join ', ')" -ForegroundColor Red
}

if (-not $DryRun -and $successful.Count -gt 0) {
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor Cyan
    foreach ($svc in $successful) {
        $name = $SERVICES[$svc].CloudRunName
        $url = gcloud run services describe $name --region $REGION --project $PROJECT_ID --format "value(status.url)" 2>$null
        if ($url) {
            Write-Host "  $svc : $url" -ForegroundColor Green
        }
    }
    Write-Host ""
    Write-Host "Remember: Production domain is https://$PROD_DOMAIN" -ForegroundColor Yellow
}
