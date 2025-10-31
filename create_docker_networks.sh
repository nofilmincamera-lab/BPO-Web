#!/bin/bash
# Create Docker networks for BPO Project

echo "Creating Docker networks for BPO Project..."

# Create main bridge network for all BPO services
echo "Creating main BPO network..."
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --ip-range=172.20.240.0/20 \
  --gateway=172.20.0.1 \
  bpo-main-network

# Create GPU-enabled network for ML/AI containers
echo "Creating GPU network..."
docker network create \
  --driver bridge \
  --subnet=172.21.0.0/16 \
  --ip-range=172.21.240.0/20 \
  --gateway=172.21.0.1 \
  bpo-gpu-network

# Create database network for data services
echo "Creating database network..."
docker network create \
  --driver bridge \
  --subnet=172.22.0.0/16 \
  --ip-range=172.22.240.0/20 \
  --gateway=172.22.0.1 \
  bpo-db-network

# Create monitoring network for observability
echo "Creating monitoring network..."
docker network create \
  --driver bridge \
  --subnet=172.23.0.0/16 \
  --ip-range=172.23.240.0/20 \
  --gateway=172.23.0.1 \
  bpo-monitoring-network

# Create external network for public-facing services
echo "Creating external network..."
docker network create \
  --driver bridge \
  --subnet=172.24.0.0/16 \
  --ip-range=172.24.240.0/20 \
  --gateway=172.24.0.1 \
  bpo-external-network

echo "Docker networks created successfully!"
echo ""
echo "Available networks:"
docker network ls | grep bpo

echo ""
echo "Network details:"
echo "Main BPO Network: bpo-main-network (172.20.0.0/16)"
echo "GPU Network: bpo-gpu-network (172.21.0.0/16)"
echo "Database Network: bpo-db-network (172.22.0.0/16)"
echo "Monitoring Network: bpo-monitoring-network (172.23.0.0/16)"
echo "External Network: bpo-external-network (172.24.0.0/16)"

