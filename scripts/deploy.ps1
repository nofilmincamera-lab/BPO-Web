# BPO Intelligence Pipeline - Deployment Script
# Runs on Windows domain machines via GPO

param(
    [switch]$SkipMigrations,
    [switch]$SkipValidation,
    [string]$Profile = "base"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BPO Intelligence - Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1] Checking prerequisites..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "  ERROR: Docker not found. Run prereqs-install.ps1 first." -ForegroundColor Red
    exit 1
}
Write-Host "  Docker version: $((docker --version).Split(',')[0])" -ForegroundColor Green

# Validate heuristics
if (-not $SkipValidation) {
    Write-Host "[2] Validating heuristics..." -ForegroundColor Yellow
    python scripts/validate_taxonomy.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Heuristics validation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Validation passed" -ForegroundColor Green
}

# Start postgres first
Write-Host "[3] Starting PostgreSQL..." -ForegroundColor Yellow
docker-compose up -d postgres
Start-Sleep -Seconds 10

# Wait for postgres to be ready
$maxRetries = 30
$retry = 0
while ($retry -lt $maxRetries) {
    $health = docker inspect bpo-postgres --format='{{.State.Health.Status}}' 2>$null
    if ($health -eq "healthy") {
        Write-Host "  PostgreSQL is healthy" -ForegroundColor Green
        break
    }
    $retry++
    Start-Sleep -Seconds 2
}
if ($retry -eq $maxRetries) {
    Write-Host "  ERROR: PostgreSQL failed to start" -ForegroundColor Red
    docker-compose logs postgres
    exit 1
}

# Run migrations
if (-not $SkipMigrations) {
    Write-Host "[4] Running database migrations..." -ForegroundColor Yellow
    docker exec bpo-postgres alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Migrations failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Migrations applied" -ForegroundColor Green
}

# Start services
Write-Host "[5] Starting services (profile: $Profile)..." -ForegroundColor Yellow
docker-compose --profile $Profile up -d
Start-Sleep -Seconds 5

# Verify services
Write-Host "[6] Verifying services..." -ForegroundColor Yellow
$services = docker-compose ps --format json | ConvertFrom-Json
$healthy = ($services | Where-Object { $_.State -eq "running" }).Count
$total = $services.Count
Write-Host "  Running: $healthy/$total services" -ForegroundColor Green

# Check API
Write-Host "[7] Checking API..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "  API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "  WARNING: API not responding yet" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  Temporal UI:  http://localhost:8233" -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Health Check: http://localhost:8000/healthz" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoring:" -ForegroundColor White
Write-Host "  docker-compose logs -f" -ForegroundColor Gray
Write-Host "  docker-compose ps" -ForegroundColor Gray
Write-Host ""

