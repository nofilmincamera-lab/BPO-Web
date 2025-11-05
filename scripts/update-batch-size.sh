#!/bin/bash
# ============================================================================
# Update Batch Size - Quick Helper Script
# ============================================================================
# Usage: ./scripts/update-batch-size.sh <size>
# Example: ./scripts/update-batch-size.sh 1024
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

BATCH_SIZE=${1:-1024}

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Updating Batch Size to: ${BATCH_SIZE}${NC}"
echo -e "${BLUE}============================================================================${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Run: cp .env.example .env${NC}"
    exit 1
fi

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✓ Backed up .env${NC}"

# Update batch size
if grep -q "EMBEDDING_BATCH_SIZE=" .env; then
    sed -i.bak "s/EMBEDDING_BATCH_SIZE=.*/EMBEDDING_BATCH_SIZE=${BATCH_SIZE}/" .env
    echo -e "${GREEN}✓ Updated EMBEDDING_BATCH_SIZE to ${BATCH_SIZE}${NC}"
else
    echo "EMBEDDING_BATCH_SIZE=${BATCH_SIZE}" >> .env
    echo -e "${GREEN}✓ Added EMBEDDING_BATCH_SIZE=${BATCH_SIZE}${NC}"
fi

# Show current GPU memory allocation
echo ""
echo -e "${YELLOW}GPU Memory Estimates (RTX 6000 Pro 96GB):${NC}"

case $BATCH_SIZE in
    256)
        echo "  Batch: 256  -> ~11GB GPU memory"
        echo "  Conservative mode"
        ;;
    512)
        echo "  Batch: 512  -> ~22GB GPU memory"
        echo "  Balanced mode"
        ;;
    1024)
        echo "  Batch: 1024 -> ~43GB GPU memory"
        echo "  High performance mode (RECOMMENDED)"
        ;;
    2048)
        echo "  Batch: 2048 -> ~85GB GPU memory"
        echo "  Maximum throughput mode"
        ;;
    *)
        echo "  Batch: ${BATCH_SIZE} -> ~$(echo "${BATCH_SIZE} * 0.042" | bc)GB GPU memory (estimated)"
        ;;
esac

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Restart services:"
echo "   ${BLUE}docker-compose restart prefect-agent api${NC}"
echo ""
echo "2. Monitor GPU memory:"
echo "   ${BLUE}nvidia-smi -l 1${NC}"
echo ""
echo "3. Test performance:"
echo "   ${BLUE}docker exec bpo-prefect-agent python -c '${NC}"
echo "   ${BLUE}import time; from src.extraction.gpu_embeddings import generate_embeddings;${NC}"
echo "   ${BLUE}texts = [\"test\"] * 1000; start = time.time();${NC}"
echo "   ${BLUE}embeddings = generate_embeddings(texts, batch_size=${BATCH_SIZE});${NC}"
echo "   ${BLUE}print(f\"Throughput: {len(texts)/(time.time()-start):.1f} emb/sec\")'${NC}"
echo ""
echo -e "${GREEN}Batch size updated to ${BATCH_SIZE}!${NC}"
