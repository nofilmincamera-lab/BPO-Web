# Docker Network Configuration for BPO Project

## Overview

This document describes the Docker network architecture for the BPO Intelligence Pipeline project. The network is designed to provide secure, isolated communication between different types of services while maintaining optimal performance.

## Network Architecture

### Network Types

| Network Name | Subnet | Gateway | Purpose |
|--------------|--------|---------|---------|
| `bpo-main-network` | 172.30.0.0/16 | 172.30.0.1 | Main BPO network for all services |
| `bpo-gpu-network` | 172.31.0.0/16 | 172.31.0.1 | GPU-enabled network for ML/AI containers |
| `bpo-db-network` | 172.32.0.0/16 | 172.32.0.1 | Database network for data services |
| `bpo-monitoring-network` | 172.33.0.0/16 | 172.33.0.1 | Monitoring network for observability |
| `bpo-external-network` | 172.34.0.0/16 | 172.34.0.1 | External network for public-facing services |

### Service Network Assignments

#### Core Services
- **PostgreSQL**: `bpo-main-network`, `bpo-db-network`
- **Prefect Server**: `bpo-main-network`, `bpo-external-network`
- **Prefect Agent**: `bpo-main-network`, `bpo-gpu-network`
- **API Service**: `bpo-main-network`, `bpo-gpu-network`, `bpo-external-network`
- **PgBouncer**: `bpo-main-network`, `bpo-db-network`

#### Database Services
- **PostgreSQL**: `bpo-main-network`, `bpo-db-network`
- **Prefect DB**: `bpo-main-network`, `bpo-db-network`
- **Redis**: `bpo-main-network`

#### GPU Services
- **Prefect Agent**: `bpo-gpu-network`
- **API Service**: `bpo-gpu-network`
- **Ollama**: `bpo-main-network`, `bpo-gpu-network`

#### External Services
- **Prefect Server**: `bpo-external-network`
- **API Service**: `bpo-external-network`
- **Label Studio**: `bpo-main-network`, `bpo-external-network`
- **Grafana**: `bpo-main-network`, `bpo-monitoring-network`

#### Monitoring Services
- **Prometheus**: `bpo-main-network`, `bpo-monitoring-network`
- **Grafana**: `bpo-main-network`, `bpo-monitoring-network`

## Network Management

### Creating Networks

```bash
# Create all networks
python manage_docker_networks.py create

# Or create individual networks
docker network create --driver bridge --subnet=172.30.0.0/16 --ip-range=172.30.240.0/20 --gateway=172.30.0.1 bpo-main-network
```

### Managing Networks

```bash
# List all networks
python manage_docker_networks.py status

# Remove all networks
python manage_docker_networks.py remove

# Connect container to network
docker network connect bpo-main-network container-name
```

### PowerShell Scripts

```powershell
# Create networks (Windows)
.\create_docker_networks.ps1

# Or use the Python manager
python manage_docker_networks.py create
```

## Network Security

### Isolation Levels

1. **Database Layer**: Isolated in `bpo-db-network`
2. **GPU Layer**: Isolated in `bpo-gpu-network` with GPU access
3. **External Layer**: Public-facing services in `bpo-external-network`
4. **Monitoring Layer**: Observability services in `bpo-monitoring-network`

### Communication Rules

- **Internal Services**: Can communicate within their assigned networks
- **Cross-Network**: Services can communicate across networks they're connected to
- **External Access**: Only services on `bpo-external-network` are accessible from outside

## Container Communication

### Within Same Network
```bash
# Container A can reach Container B using container name
curl http://prefect-server:4200/api/health
```

### Across Networks
```bash
# Container must be connected to multiple networks
docker network connect bpo-gpu-network api-container
```

### From Host
```bash
# Access external services
curl http://localhost:4200  # Prefect UI
curl http://localhost:8000  # API
```

## Troubleshooting

### Check Network Status
```bash
# List all networks
docker network ls

# Inspect specific network
docker network inspect bpo-main-network

# Check container networks
docker inspect container-name | grep -A 10 "Networks"
```

### Common Issues

1. **Container can't reach another service**
   - Check if both containers are on the same network
   - Verify container names are correct
   - Check if service is listening on the correct port

2. **External access not working**
   - Ensure service is on `bpo-external-network`
   - Check port mapping in docker-compose.yml
   - Verify firewall settings

3. **GPU not accessible**
   - Ensure container is on `bpo-gpu-network`
   - Check NVIDIA runtime configuration
   - Verify GPU drivers are installed

### Network Diagnostics

```bash
# Test connectivity between containers
docker exec container-a ping container-b

# Check DNS resolution
docker exec container-a nslookup container-b

# Test port connectivity
docker exec container-a telnet container-b 5432
```

## Best Practices

1. **Use descriptive network names** with `bpo-` prefix
2. **Assign services to appropriate networks** based on their function
3. **Minimize cross-network connections** for security
4. **Use static IP ranges** to avoid conflicts
5. **Monitor network usage** for performance optimization

## Network Monitoring

### Available Tools
- **Docker Network Inspector**: Built-in Docker tool
- **Prometheus + Grafana**: For network metrics
- **Custom Scripts**: `manage_docker_networks.py`

### Key Metrics
- Network traffic between containers
- Latency measurements
- Bandwidth utilization
- Error rates

## Migration Guide

### From Single Network
1. Create new networks using the management script
2. Update docker-compose.yml with new network assignments
3. Restart services to apply new network configuration
4. Test connectivity between services

### Rollback Plan
1. Keep `bpo-network` for backward compatibility
2. Services can be moved back to single network if needed
3. Update docker-compose.yml to use `bpo-network` only

## Support

For network-related issues:
1. Check this documentation
2. Run network diagnostics
3. Review Docker logs
4. Contact system administrator

---

**Last Updated**: 2025-10-29
**Version**: 1.0
**Maintainer**: BPO Project Team

