<#
.SYNOPSIS
    Migrate secrets from DEV to PROD environment (or create new PROD secrets)
    
.DESCRIPTION
    This script helps set up Secret Manager secrets for the PRODUCTION environment.
    It can either copy secrets from DEV (for shared secrets like OpenAI API key)
    or prompt for new production-specific values.
    
    ⚠️ IMPORTANT: BOM (Byte Order Mark) Prevention
    This script automatically strips BOM characters to prevent encoding issues
    that can corrupt API keys and cause authentication failures.
    
.PARAMETER DryRun
    Show what would be done without making changes.

.PARAMETER Interactive
    Prompt for new secret values instead of copying from DEV.

.EXAMPLE
    .\migrate-secrets.ps1
    Migrates shared secrets from DEV to PROD.

.EXAMPLE
    .\migrate-secrets.ps1 -Interactive
    Prompts for new production secret values.

.EXAMPLE
    .\migrate-secrets.ps1 -DryRun
    Shows what would be migrated without making changes.
#>

param(
    [switch]$DryRun,
    [switch]$Interactive
)

$SOURCE_PROJECT = "YOUR_DEV_PROJECT_ID"
$TARGET_PROJECT = "YOUR_PROD_PROJECT_ID"

# Secrets that can be shared between environments (same API key works for both)
$SHARED_SECRETS = @(
    "openai-api-key-pdf-scanner"   # OpenAI API key - same key for DEV and PROD
)

# Secrets that need NEW production values (different from DEV)
$PROD_ONLY_SECRETS = @(
    "stripe-api-key",              # PRODUCTION Stripe API key (sk_live_...)
    "stripe-webhook-secret",       # PRODUCTION Stripe webhook secret
    "stripe-publishable-key",      # PRODUCTION Stripe publishable key (pk_live_...)
    "firebase-storage-private-key", # PRODUCTION Firebase service account
    "github-oauth-client-id",      # PRODUCTION GitHub OAuth app
    "github-oauth-client-secret",
    "notion-oauth-client-id",      # PRODUCTION Notion OAuth app
    "notion-oauth-client-secret",
    "firebase-api-key",            # PRODUCTION Firebase config
    "firebase-app-id",
    "firebase-messaging-sender-id",
    "brevo-api-key"                # Brevo API key (may be shared or separate)
)

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# Function to strip BOM and clean secret value
function Clean-SecretValue {
    param([string]$Value)
    
    # Remove BOM characters (both UTF-8 BOM and other BOMs)
    $cleaned = $Value -replace '^\xEF\xBB\xBF', ''  # UTF-8 BOM
    $cleaned = $cleaned -replace '^\uFEFF', ''      # UTF-16 BOM
    $cleaned = $cleaned.Trim()                       # Remove whitespace
    
    return $cleaned
}

# Function to add secret without BOM
function Add-SecretWithoutBOM {
    param(
        [string]$SecretName,
        [string]$SecretValue,
        [string]$Project
    )
    
    # Clean the value
    $cleanedValue = Clean-SecretValue -Value $SecretValue
    
    # Create temp file with UTF-8 encoding (no BOM)
    $tempFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tempFile, $cleanedValue, [System.Text.UTF8Encoding]::new($false))
    
    try {
        gcloud secrets versions add $SecretName --data-file=$tempFile --project=$Project 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }
    finally {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║         LumTrails PRODUCTION Secret Migration                 ║" -ForegroundColor Red
Write-Host "║                   ⚠️  PRODUCTION ⚠️                           ║" -ForegroundColor Red
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""
Write-Info "Target: $TARGET_PROJECT"
Write-Host ""

if ($DryRun) {
    Write-Warn "DRY RUN MODE - No changes will be made"
    Write-Host ""
}

# Safety confirmation
if (-not $DryRun) {
    Write-Host "You are about to modify secrets in PRODUCTION!" -ForegroundColor Yellow
    $confirmation = Read-Host "Type 'SECRETS-PROD' to confirm"
    if ($confirmation -ne "SECRETS-PROD") {
        Write-Host "[ABORTED] Operation cancelled." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

$successful = 0
$failed = 0
$skipped = 0

# Process shared secrets (copy from DEV)
if (-not $Interactive) {
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " Copying SHARED Secrets from DEV" -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    foreach ($secret in $SHARED_SECRETS) {
        Write-Host "  Migrating: $secret" -ForegroundColor White
        
        if ($DryRun) {
            Write-Host "    (dry-run: would copy from $SOURCE_PROJECT)" -ForegroundColor DarkYellow
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
        
        $result = Add-SecretWithoutBOM -SecretName $secret -SecretValue $secretValue -Project $TARGET_PROJECT
        if ($result) {
            Write-Host "    ✓ Done (BOM-safe)" -ForegroundColor Green
            $successful++
        } else {
            Write-Host "    ✗ Failed to write" -ForegroundColor Red
            $failed++
        }
    }
}

# Process production-only secrets
Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " PRODUCTION-Only Secrets (require new values)" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($Interactive) {
    foreach ($secret in $PROD_ONLY_SECRETS) {
        Write-Host "  Secret: $secret" -ForegroundColor White
        
        if ($DryRun) {
            Write-Host "    (dry-run: would prompt for value)" -ForegroundColor DarkYellow
            continue
        }
        
        $value = Read-Host "    Enter value (or press Enter to skip)"
        if ([string]::IsNullOrWhiteSpace($value)) {
            Write-Host "    Skipped" -ForegroundColor DarkYellow
            $skipped++
            continue
        }
        
        $result = Add-SecretWithoutBOM -SecretName $secret -SecretValue $value -Project $TARGET_PROJECT
        if ($result) {
            Write-Host "    ✓ Set successfully (BOM-safe)" -ForegroundColor Green
            $successful++
        } else {
            Write-Host "    ✗ Failed to set" -ForegroundColor Red
            $failed++
        }
    }
} else {
    Write-Host "  The following secrets need PRODUCTION-specific values:" -ForegroundColor Yellow
    Write-Host ""
    foreach ($secret in $PROD_ONLY_SECRETS) {
        Write-Host "    - $secret" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "  Run with -Interactive flag to set these values:" -ForegroundColor Cyan
    Write-Host "    .\migrate-secrets.ps1 -Interactive" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Or set them manually using gcloud (BOM-safe method):" -ForegroundColor Cyan
    Write-Host '    $key = "your-secret-value"' -ForegroundColor DarkGray
    Write-Host '    [System.IO.File]::WriteAllText("temp.txt", $key, [System.Text.UTF8Encoding]::new($false))' -ForegroundColor DarkGray
    Write-Host '    gcloud secrets versions add SECRET-NAME --data-file=temp.txt --project=$TARGET_PROJECT' -ForegroundColor DarkGray
    Write-Host '    Remove-Item temp.txt' -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " Summary" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Successful: $successful" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Skipped: $skipped" -ForegroundColor Yellow
Write-Host ""

if ($failed -gt 0) {
    exit 1
}
