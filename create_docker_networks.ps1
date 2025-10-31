# PowerShell script to create Docker networks for BPO Project

Write-Host "Creating Docker networks for BPO Project..." -ForegroundColor Green

# Create main bridge network for all BPO services
Write-Host "Creating main BPO network..." -ForegroundColor Yellow
docker network create `
  --driver bridge `
  --subnet=172.20.0.0/16 `
  --ip-range=172.20.240.0/20 `
  --gateway=172.20.0.1 `
  bpo-main-network

# Create GPU-enabled network for ML/AI containers
Write-Host "Creating GPU network..." -ForegroundColor Yellow
docker network create `
  --driver bridge `
  --subnet=172.21.0.0/16 `
  --ip-range=172.21.240.0/20 `
  --gateway=172.21.0.1 `
  bpo-gpu-network

# Create database network for data services
Write-Host "Creating database network..." -ForegroundColor Yellow
docker network create `
  --driver bridge `
  --subnet=172.22.0.0/16 `
  --ip-range=172.22.240.0/20 `
  --gateway=172.22.0.1 `
  bpo-db-network

# Create monitoring network for observability
Write-Host "Creating monitoring network..." -ForegroundColor Yellow
docker network create `
  --driver bridge `
  --subnet=172.23.0.0/16 `
  --ip-range=172.23.240.0/20 `
  --gateway=172.23.0.1 `
  bpo-monitoring-network

# Create external network for public-facing services
Write-Host "Creating external network..." -ForegroundColor Yellow
docker network create `
  --driver bridge `
  --subnet=172.24.0.0/16 `
  --ip-range=172.24.240.0/20 `
  --gateway=172.24.0.1 `
  bpo-external-network

Write-Host "Docker networks created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Available networks:" -ForegroundColor Cyan
docker network ls | Select-String "bpo"

Write-Host ""
Write-Host "Network details:" -ForegroundColor Cyan
Write-Host "Main BPO Network: bpo-main-network (172.20.0.0/16)"
Write-Host "GPU Network: bpo-gpu-network (172.21.0.0/16)"
Write-Host "Database Network: bpo-db-network (172.22.0.0/16)"
Write-Host "Monitoring Network: bpo-monitoring-network (172.23.0.0/16)"
Write-Host "External Network: bpo-external-network (172.24.0.0/16)"

