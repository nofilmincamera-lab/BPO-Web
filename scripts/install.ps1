# BPO Intelligence Pipeline - Installation Script
# Complete automated installation with GPU support, BuildKit optimization, and preprocessing

param(
    [string[]]$Profiles = @("base"),
    [switch]$SkipValidation,
    [switch]$SkipPreprocess,
    [switch]$DryRun
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BPO Intelligence - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Phase 1: Pre-Flight Checks
# ============================================================================
Write-Host "[Phase 1] Pre-Flight Checks" -ForegroundColor Yellow
Write-Host ""

# Check Docker
Write-Host "  [1.1] Checking Docker..." -ForegroundColor Gray
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "    ERROR: Docker not found" -ForegroundColor Red
    exit 1
}
Write-Host "    Docker version: $((docker --version).Split(',')[0])" -ForegroundColor Green

# Check Docker Compose v2
Write-Host "  [1.2] Checking Docker Compose..." -ForegroundColor Gray
$composeVersion = docker compose version
if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: Docker Compose not found" -ForegroundColor Red
    exit 1
}
Write-Host "    $composeVersion" -ForegroundColor Green

# Check GPU
Write-Host "  [1.3] Checking GPU availability..." -ForegroundColor Gray
$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    $gpuInfo = nvidia-smi --query-gpu=name,driver_version,cuda_version --format=csv,noheader | Select-Object -First 1
    Write-Host "    GPU detected: $gpuInfo" -ForegroundColor Green
    
    # Check NVIDIA runtime in Docker
    $dockerInfo = docker info 2>&1 | Select-String -Pattern "nvidia"
    if ($dockerInfo) {
        Write-Host "    NVIDIA runtime: Available" -ForegroundColor Green
    } else {
        Write-Host "    WARNING: NVIDIA runtime not detected in Docker" -ForegroundColor Yellow
    }
} else {
    Write-Host "    WARNING: No GPU detected (CPU-only mode)" -ForegroundColor Yellow
}

# Check disk space
Write-Host "  [1.4] Checking disk space..." -ForegroundColor Gray
$drive = Get-PSDrive C
$freeGB = [math]::Round($drive.Free / 1GB, 1)
if ($freeGB -lt 20) {
    Write-Host "    WARNING: Low disk space ($freeGB GB free)" -ForegroundColor Yellow
} else {
    Write-Host "    Disk space: $freeGB GB free" -ForegroundColor Green
}

# Check port availability
Write-Host "  [1.5] Checking port availability..." -ForegroundColor Gray
$ports = @(5432, 7233, 8000, 8233)
$portCheck = $true
foreach ($port in $ports) {
    $listener = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Host "    WARNING: Port $port is in use" -ForegroundColor Yellow
        $portCheck = $false
    }
}
if ($portCheck) {
    Write-Host "    All ports available" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Phase 2: Environment Setup
# ============================================================================
Write-Host "[Phase 2] Environment Setup" -ForegroundColor Yellow
Write-Host ""

# Create .env if missing
Write-Host "  [2.1] Checking environment file..." -ForegroundColor Gray
if (-not (Test-Path ".env")) {
    Write-Host "    Creating .env from env.example..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
    Write-Host "    Created .env" -ForegroundColor Green
} else {
    Write-Host "    .env exists" -ForegroundColor Green
}

# Check secrets
Write-Host "  [2.2] Checking secrets..." -ForegroundColor Gray
if (-not (Test-Path "ops\secrets\postgres_password.txt")) {
    Write-Host "    Generating postgres password..." -ForegroundColor Yellow
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    $password = [Convert]::ToBase64String($bytes).Substring(0, 24)
    New-Item -ItemType Directory -Path "ops\secrets" -Force | Out-Null
    $password | Out-File -FilePath "ops\secrets\postgres_password.txt" -NoNewline -Encoding ASCII
    Write-Host "    Password generated" -ForegroundColor Green
} else {
    Write-Host "    Secrets exist" -ForegroundColor Green
}

# Set secrets permissions
Write-Host "  [2.3] Setting secrets permissions..." -ForegroundColor Gray
try {
    icacls "ops\secrets\postgres_password.txt" /inheritance:r /grant "${env:USERNAME}:F" 2>&1 | Out-Null
    Write-Host "    Permissions set" -ForegroundColor Green
} catch {
    Write-Host "    WARNING: Could not set permissions" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Phase 3: Pre-Build Configuration
# ============================================================================
Write-Host "[Phase 3] Pre-Build Configuration" -ForegroundColor Yellow
Write-Host ""

# Enable BuildKit
Write-Host "  [3.1] Enabling BuildKit..." -ForegroundColor Gray
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"
Write-Host "    BuildKit enabled" -ForegroundColor Green

# Create .dockerignore if missing
Write-Host "  [3.2] Checking .dockerignore..." -ForegroundColor Gray
if (-not (Test-Path ".dockerignore")) {
    @"
**/.git
**/.env
**/archive
**/data/raw
**/data/processed
**/__pycache__
**/*.pyc
**/.pytest_cache
**/.vscode
"@ | Out-File -FilePath ".dockerignore" -Encoding ASCII
    Write-Host "    Created .dockerignore" -ForegroundColor Green
} else {
    Write-Host "    .dockerignore exists" -ForegroundColor Green
}

# Validate docker-compose.yml
Write-Host "  [3.3] Validating docker-compose.yml..." -ForegroundColor Gray
docker-compose config --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: docker-compose.yml validation failed" -ForegroundColor Red
    exit 1
}
Write-Host "    Configuration valid" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Phase 4: Image Preparation
# ============================================================================
Write-Host "[Phase 4] Image Preparation" -ForegroundColor Yellow
Write-Host ""

# Pull base images
Write-Host "  [4.1] Pulling base images..." -ForegroundColor Gray
docker-compose pull postgres temporal temporal-ui
if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: Failed to pull images" -ForegroundColor Red
    exit 1
}
Write-Host "    Base images pulled" -ForegroundColor Green

# Build custom images
Write-Host "  [4.2] Building custom images..." -ForegroundColor Gray
docker-compose build --parallel api worker --progress=plain
if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: Failed to build images" -ForegroundColor Red
    exit 1
}
Write-Host "    Custom images built" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Phase 5: Database Setup
# ============================================================================
Write-Host "[Phase 5] Database Setup" -ForegroundColor Yellow
Write-Host ""

# Start PostgreSQL
Write-Host "  [5.1] Starting PostgreSQL..." -ForegroundColor Gray
docker-compose up -d postgres
Start-Sleep -Seconds 10

# Wait for postgres health
Write-Host "  [5.2] Waiting for PostgreSQL..." -ForegroundColor Gray
$maxRetries = 30
$retry = 0
while ($retry -lt $maxRetries) {
    $health = docker inspect bpo-postgres --format='{{.State.Health.Status}}' 2>$null
    if ($health -eq "healthy") {
        Write-Host "    PostgreSQL is healthy" -ForegroundColor Green
        break
    }
    $retry++
    Start-Sleep -Seconds 2
}
if ($retry -eq $maxRetries) {
    Write-Host "    ERROR: PostgreSQL failed to start" -ForegroundColor Red
    docker-compose logs postgres
    exit 1
}

# Run migrations
Write-Host "  [5.3] Running migrations..." -ForegroundColor Gray
docker exec bpo-postgres alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: Migrations failed" -ForegroundColor Red
    exit 1
}
Write-Host "    Migrations applied" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Phase 6: Service Deployment
# ============================================================================
Write-Host "[Phase 6] Service Deployment" -ForegroundColor Yellow
Write-Host ""

# Start services
Write-Host "  [6.1] Starting services (profiles: $($Profiles -join ', '))..." -ForegroundColor Gray
$profileArg = ($Profiles | ForEach-Object { "--profile $_" }) -join " "
docker-compose $profileArg up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: Failed to start services" -ForegroundColor Red
    exit 1
}
Write-Host "    Services started" -ForegroundColor Green

# Wait for services to be healthy
Write-Host "  [6.2] Waiting for services..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# Check service health
Write-Host "  [6.3] Checking service health..." -ForegroundColor Gray
$services = docker-compose ps --format json | ConvertFrom-Json
$healthy = ($services | Where-Object { $_.State -eq "running" }).Count
$total = $services.Count
Write-Host "    Running: $healthy/$total services" -ForegroundColor Green

Write-Host ""

# ============================================================================
# Phase 7: Validation
# ============================================================================
Write-Host "[Phase 7] Validation" -ForegroundColor Yellow
Write-Host ""

# Validate heuristics
if (-not $SkipValidation) {
    Write-Host "  [7.1] Validating heuristics..." -ForegroundColor Gray
    python scripts/validate_taxonomy.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    ERROR: Heuristics validation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "    Heuristics valid" -ForegroundColor Green
} else {
    Write-Host "  [7.1] Skipping heuristics validation" -ForegroundColor Yellow
}

# Check API
Write-Host "  [7.2] Checking API..." -ForegroundColor Gray
Start-Sleep -Seconds 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "    API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "    WARNING: API not responding yet" -ForegroundColor Yellow
}

# Check Temporal UI
Write-Host "  [7.3] Checking Temporal UI..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8233" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "    Temporal UI is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "    WARNING: Temporal UI not responding yet" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Phase 8: Preprocessing (Optional)
# ============================================================================
if (-not $SkipPreprocess) {
    Write-Host "[Phase 8] Preprocessing" -ForegroundColor Yellow
    Write-Host ""
    
    $rawFile = "data\raw\dataset_webscrape-bpo_2025-10-13_10-15-17-310 (1).json"
    if (Test-Path $rawFile) {
        Write-Host "  [8.1] Found raw data file" -ForegroundColor Gray
        Write-Host "  Run preprocessing manually:" -ForegroundColor Yellow
        Write-Host "    docker exec bpo-worker python scripts/preprocess.py --input /data/raw/dataset_webscrape-bpo_2025-10-13_10-15-17-310` (1`.json --output /data/processed/preprocessed.jsonl" -ForegroundColor Cyan
    } else {
        Write-Host "  [8.1] No raw data file found, skipping preprocessing" -ForegroundColor Gray
    }
    Write-Host ""
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION COMPLETE" -ForegroundColor Cyan
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
Write-Host "Management:" -ForegroundColor White
Write-Host "  docker-compose stop" -ForegroundColor Gray
Write-Host "  docker-compose down" -ForegroundColor Gray
Write-Host ""

