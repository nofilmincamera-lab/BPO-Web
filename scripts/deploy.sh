#!/bin/bash
# ============================================================================
# BPO Intelligence Pipeline - Deployment Helper Script
# ============================================================================
# This script helps deploy the pipeline in different GPU modes
#
# Usage:
#   ./scripts/deploy.sh <mode> [options]
#
# Modes:
#   local-egpu   - Local external GPU (default)
#   cpu-only     - CPU-only mode
#   vastai-gpu   - Vast.AI GPU instances (RTX 6000 Pro)
#   aws-gpu      - AWS GPU instances
#   gcp-gpu      - GCP GPU instances
#   azure-gpu    - Azure GPU instances
#
# Examples:
#   ./scripts/deploy.sh local-egpu
#   ./scripts/deploy.sh cpu-only
#   ./scripts/deploy.sh aws-gpu --region us-east-1
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE="${1:-local-egpu}"
PROFILE="base"
DETACH="-d"

# Functions
print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose found: $(docker compose version)"

    # Check .env file
    if [ ! -f .env ]; then
        print_warning ".env file not found, creating from .env.example"
        cp .env.example .env
        print_info "Please edit .env file with your configuration"
    else
        print_success ".env file found"
    fi

    # Check GPU for local-egpu mode
    if [ "$MODE" = "local-egpu" ]; then
        if command -v nvidia-smi &> /dev/null; then
            print_success "NVIDIA GPU detected:"
            nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n 1
        else
            print_warning "nvidia-smi not found - GPU may not be available"
        fi
    fi

    echo ""
}

# Deploy functions
deploy_local_egpu() {
    print_header "Deploying with Local eGPU"

    # Update .env
    sed -i.bak 's/GPU_DEPLOYMENT_MODE=.*/GPU_DEPLOYMENT_MODE=local-egpu/' .env

    # Create networks if they don't exist
    for network in bpo-main-network bpo-gpu-network bpo-db-network bpo-monitoring-network bpo-external-network; do
        if ! docker network inspect $network &> /dev/null; then
            docker network create $network
            print_success "Created network: $network"
        fi
    done

    # Deploy
    print_info "Starting services with GPU support..."
    docker compose --profile base up $DETACH

    print_success "Local eGPU deployment complete!"
    print_info "GPU performance: ~128 embeddings/sec (RTX 3060)"
    print_info "Access Prefect UI: http://localhost:4200"
    print_info "Access API: http://localhost:8000"
}

deploy_vastai_gpu() {
    print_header "Deploying with Vast.AI GPU"

    # Update .env
    sed -i.bak 's/GPU_DEPLOYMENT_MODE=.*/GPU_DEPLOYMENT_MODE=vastai-gpu/' .env
    sed -i.bak 's/EMBEDDING_BATCH_SIZE=.*/EMBEDDING_BATCH_SIZE=512/' .env

    # Create networks
    for network in bpo-main-network bpo-gpu-network bpo-db-network bpo-monitoring-network bpo-external-network; do
        if ! docker network inspect $network &> /dev/null; then
            docker network create $network
            print_success "Created network: $network"
        fi
    done

    # Deploy
    print_info "Starting services with Vast.AI GPU support..."
    docker compose -f docker-compose.yml -f docker-compose.vastai-gpu.yml --profile base up $DETACH

    print_success "Vast.AI GPU deployment complete!"
    print_info "GPU: RTX 6000 Ada Pro (96GB VRAM)"
    print_info "Performance: ~600-700 embeddings/sec (5x faster than RTX 3060)"
    print_info "Batch size: 512 (16x larger than RTX 3060)"
    print_warning "Access via SSH tunnel: http://localhost:4200 (Prefect), http://localhost:8000 (API)"
}

deploy_cpu_only() {
    print_header "Deploying with CPU-Only Mode"

    # Update .env
    sed -i.bak 's/GPU_DEPLOYMENT_MODE=.*/GPU_DEPLOYMENT_MODE=cpu-only/' .env
    sed -i.bak 's/FORCE_CPU_ONLY=.*/FORCE_CPU_ONLY=1/' .env

    # Create networks
    for network in bpo-main-network bpo-db-network bpo-monitoring-network bpo-external-network; do
        if ! docker network inspect $network &> /dev/null; then
            docker network create $network
            print_success "Created network: $network"
        fi
    done

    # Deploy
    print_info "Starting services in CPU-only mode..."
    docker compose -f docker-compose.yml -f docker-compose.cpu-only.yml --profile base up $DETACH

    print_success "CPU-only deployment complete!"
    print_warning "Performance: ~36 embeddings/sec (3.5x slower than GPU)"
    print_info "Access Prefect UI: http://localhost:4200"
    print_info "Access API: http://localhost:8000"
}

deploy_aws_gpu() {
    print_header "Deploying with AWS GPU"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not installed. Install with: pip install awscli"
        exit 1
    fi

    # Update .env
    sed -i.bak 's/GPU_DEPLOYMENT_MODE=.*/GPU_DEPLOYMENT_MODE=aws-gpu/' .env

    # Create networks
    for network in bpo-main-network bpo-gpu-network bpo-db-network bpo-monitoring-network bpo-external-network; do
        if ! docker network inspect $network &> /dev/null; then
            docker network create $network
            print_success "Created network: $network"
        fi
    done

    # Deploy
    print_info "Starting services with AWS GPU support..."
    docker compose -f docker-compose.yml -f docker-compose.aws-gpu.yml --profile base up $DETACH

    print_success "AWS GPU deployment complete!"
    print_info "Instance type: g4dn.xlarge (T4 GPU)"
    print_info "Cost: ~$0.526/hr ($379/month on-demand)"
    print_info "Performance: ~120 embeddings/sec"
    print_warning "Remember to configure CloudWatch logging and IAM roles"
}

deploy_gcp_gpu() {
    print_header "Deploying with GCP GPU"

    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK not installed"
        print_info "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # Update .env
    sed -i.bak 's/GPU_DEPLOYMENT_MODE=.*/GPU_DEPLOYMENT_MODE=gcp-gpu/' .env

    # Create networks
    for network in bpo-main-network bpo-gpu-network bpo-db-network bpo-monitoring-network bpo-external-network; do
        if ! docker network inspect $network &> /dev/null; then
            docker network create $network
            print_success "Created network: $network"
        fi
    done

    # Deploy
    print_info "Starting services with GCP GPU support..."
    docker compose -f docker-compose.yml -f docker-compose.gcp-gpu.yml --profile base up $DETACH

    print_success "GCP GPU deployment complete!"
    print_info "Instance type: n1-standard-4 + T4"
    print_info "Cost: ~$0.70/hr ($504/month on-demand)"
    print_info "Performance: ~120 embeddings/sec"
    print_warning "Remember to configure Cloud Logging and service accounts"
}

deploy_azure_gpu() {
    print_header "Deploying with Azure GPU"

    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI not installed"
        print_info "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi

    # Update .env
    sed -i.bak 's/GPU_DEPLOYMENT_MODE=.*/GPU_DEPLOYMENT_MODE=azure-gpu/' .env

    # Create networks
    for network in bpo-main-network bpo-gpu-network bpo-db-network bpo-monitoring-network bpo-external-network; do
        if ! docker network inspect $network &> /dev/null; then
            docker network create $network
            print_success "Created network: $network"
        fi
    done

    # Deploy
    print_info "Starting services with Azure GPU support..."
    docker compose -f docker-compose.yml -f docker-compose.azure-gpu.yml --profile base up $DETACH

    print_success "Azure GPU deployment complete!"
    print_info "Instance type: Standard_NC4as_T4_v3"
    print_info "Cost: ~$0.526/hr ($379/month on-demand)"
    print_info "Performance: ~120 embeddings/sec"
    print_warning "Remember to configure Azure Monitor and Managed Identity"
}

verify_deployment() {
    print_header "Verifying Deployment"

    # Wait for services to start
    print_info "Waiting for services to start (30 seconds)..."
    sleep 30

    # Check if containers are running
    if ! docker compose ps | grep -q "Up"; then
        print_error "No containers are running"
        print_info "Check logs with: docker compose logs"
        return 1
    fi
    print_success "Containers are running"

    # Check Prefect server
    if curl -f http://localhost:4200/api/health &> /dev/null; then
        print_success "Prefect server is healthy"
    else
        print_warning "Prefect server is not responding"
    fi

    # Check API
    if curl -f http://localhost:8000/healthz &> /dev/null; then
        print_success "API server is healthy"
    else
        print_warning "API server is not responding"
    fi

    # Check GPU (if not cpu-only)
    if [ "$MODE" != "cpu-only" ]; then
        print_info "Checking GPU availability..."
        if docker exec bpo-prefect-agent python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')" 2>/dev/null | grep -q "True"; then
            print_success "GPU is available and detected"
        else
            print_warning "GPU is not detected (may fallback to CPU)"
        fi
    fi

    echo ""
}

show_usage() {
    cat << EOF
Usage: $0 <mode> [options]

Deployment Modes:
  local-egpu    Deploy with local external GPU (default)
  cpu-only      Deploy in CPU-only mode (no GPU)
  aws-gpu       Deploy with AWS GPU instances
  gcp-gpu       Deploy with GCP GPU instances
  azure-gpu     Deploy with Azure GPU instances

Options:
  --no-detach   Run in foreground (don't use -d flag)
  --help        Show this help message

Examples:
  $0 local-egpu               # Deploy with local GPU
  $0 cpu-only                 # Deploy CPU-only for testing
  $0 aws-gpu                  # Deploy on AWS with GPU
  $0 local-egpu --no-detach   # Deploy and show logs

See DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md for detailed information.
EOF
}

# Main script
main() {
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-detach)
                DETACH=""
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$MODE" ]; then
                    MODE=$1
                fi
                shift
                ;;
        esac
    done

    # Check prerequisites
    check_prerequisites

    # Deploy based on mode
    case $MODE in
        local-egpu)
            deploy_local_egpu
            ;;
        cpu-only)
            deploy_cpu_only
            ;;
        vastai-gpu)
            deploy_vastai_gpu
            ;;
        aws-gpu)
            deploy_aws_gpu
            ;;
        gcp-gpu)
            deploy_gcp_gpu
            ;;
        azure-gpu)
            deploy_azure_gpu
            ;;
        *)
            print_error "Unknown mode: $MODE"
            show_usage
            exit 1
            ;;
    esac

    # Verify deployment
    if [ -n "$DETACH" ]; then
        verify_deployment
    fi

    # Show next steps
    print_header "Next Steps"
    echo -e "${GREEN}Deployment successful!${NC}\n"
    echo -e "Monitor services:"
    echo -e "  docker compose logs -f"
    echo -e ""
    echo -e "Access services:"
    echo -e "  Prefect UI: ${BLUE}http://localhost:4200${NC}"
    echo -e "  API: ${BLUE}http://localhost:8000${NC}"
    echo -e "  API Docs: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e ""
    echo -e "Check GPU status (if applicable):"
    echo -e "  docker exec bpo-prefect-agent nvidia-smi"
    echo -e ""
    echo -e "Stop services:"
    echo -e "  docker compose down"
    echo -e ""
    print_info "See DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md for more information"
}

# Run main
main "$@"
