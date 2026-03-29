<#
.SYNOPSIS
    Migrate secrets from source project to dev project
    
.DESCRIPTION
    Copies secret values from the production project to the dev project.
    Use this when setting up a new environment or syncing secrets.
    
.PARAMETER DryRun
    Show what would be migrated without actually copying secrets.

.EXAMPLE
    .\migrate-secrets.ps1
    Migrates all secrets to dev environment.

.EXAMPLE
    .\migrate-secrets.ps1 -DryRun
    Shows what would be migrated without making changes.
#>

param(
    [switch]$DryRun
)

$SOURCE_PROJECT = "YOUR_SOURCE_PROJECT_ID"
$TARGET_PROJECT = "YOUR_DEV_PROJECT_ID"

$SECRETS_TO_MIGRATE = @(
    "openai-api-key-pdf-scanner",
    "stripe-api-key",
    "stripe-webhook-secret",
    "stripe-publishable-key",
    "firebase-storage-private-key",
    "github-oauth-client-id",
    "github-oauth-client-secret",
    "notion-oauth-client-id",
    "notion-oauth-client-secret",
    "firebase-api-key",
    "firebase-app-id",
    "firebase-messaging-sender-id"
)

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " LumTrails Secret Migration Script" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Info "Source: $SOURCE_PROJECT"
Write-Info "Target: $TARGET_PROJECT"
Write-Host ""

if ($DryRun) {
    Write-Warn "DRY RUN MODE - No changes will be made"
    Write-Host ""
}

$successful = 0
$failed = 0
$skipped = 0

foreach ($secret in $SECRETS_TO_MIGRATE) {
    Write-Host "  Migrating: $secret" -ForegroundColor White
    
    if ($DryRun) {
        Write-Host "    (dry-run: would copy)" -ForegroundColor DarkYellow
        $successful++
        continue
    }
    
    $secretValue = $null
    try {
        $secretValue = gcloud secrets versions access latest --secret=$secret --project=$SOURCE_PROJECT 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Skipped (no value in source)" -ForegroundColor DarkYellow
            $skipped++
            continue
        }
    } catch {
        Write-Host "    Failed to read from source" -ForegroundColor Red
        $failed++
        continue
    }
    
    try {
        $secretValue | gcloud secrets versions add $secret --data-file=- --project=$TARGET_PROJECT 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Done" -ForegroundColor Green
            $successful++
        } else {
            Write-Host "    ✗ Failed to write" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "    ✗ Failed to write" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Success "Migrated: $successful secrets"
if ($skipped -gt 0) {
    Write-Warn "Skipped: $skipped secrets"
}
if ($failed -gt 0) {
    Write-Err "Failed: $failed secrets"
}
Write-Host ""
