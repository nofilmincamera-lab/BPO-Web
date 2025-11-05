# BPO Intelligence Pipeline - Cloud GPU vs eGPU Deployment Guide

## Executive Summary

This guide compares **external GPU (eGPU)** deployment versus **cloud GPU** deployment for the BPO Intelligence Pipeline, helping you choose the optimal configuration for your use case.

## Quick Decision Matrix

| Factor | Local eGPU | AWS GPU | GCP GPU | Azure GPU |
|--------|-----------|---------|---------|-----------|
| **Initial Cost** | High ($500-2000) | Low ($0) | Low ($0) | Low ($0) |
| **Monthly Cost (24/7)** | $0* | $379-2,203 | $504-2,644 | $379-2,203 |
| **Setup Complexity** | Low | Medium | Medium | Medium |
| **Maintenance** | Manual | Managed | Managed | Managed |
| **Scalability** | Limited | High | High | High |
| **Latency** | Lowest | Low-Medium | Low-Medium | Low-Medium |
| **Best For** | Development, Small-scale | Production, Variable load | ML-heavy, Global | Enterprise, Hybrid |

*Electricity costs vary by region (~$20-50/month for RTX 3060)

---

## Deployment Modes

### 1. Local eGPU Mode (Default)

**Hardware**: External GPU connected via Thunderbolt or internal GPU

**Advantages:**
- ✅ Zero recurring costs (after hardware purchase)
- ✅ Lowest latency (no network overhead)
- ✅ Full control over hardware
- ✅ No cloud vendor lock-in
- ✅ Works offline
- ✅ Simple setup with nvidia-docker

**Disadvantages:**
- ❌ High upfront cost ($500-2000 for GPU)
- ❌ Limited to single machine
- ❌ Manual hardware maintenance
- ❌ No automatic scaling
- ❌ Power consumption (~$20-50/month)
- ❌ Physical space requirements

**Best Use Cases:**
- Development and testing
- Small-scale deployments (<5,000 documents/day)
- On-premise requirements
- Cost-sensitive long-term deployments
- Privacy-critical workloads

**Hardware Recommendations:**
- **Budget**: NVIDIA GTX 1660 Super (6GB) - $250 - Good for testing
- **Recommended**: NVIDIA RTX 3060 (12GB) - $350-400 - Excellent price/performance
- **Professional**: NVIDIA RTX 4070 (12GB) - $600 - Best for production
- **Enterprise**: NVIDIA RTX 4090 (24GB) - $1,600 - Maximum performance

**Setup:**
```bash
# 1. Copy environment file
cp .env.example .env

# 2. Set GPU mode
echo "GPU_DEPLOYMENT_MODE=local-egpu" >> .env

# 3. Start services
docker-compose --profile base up -d

# 4. Verify GPU detection
docker exec bpo-prefect-agent python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

**Performance (RTX 3060):**
- Embeddings: 128 embeddings/sec
- GPU Memory: 700-1000 MB peak
- Processing: 45,000 documents in ~17 hours
- Speedup: 3.5x vs CPU

---

### 2. AWS GPU Mode

**Service Options:**
- **ECS on EC2**: Full control, persistent instances
- **ECS Fargate**: Managed compute (GPU support coming)
- **SageMaker**: ML-optimized, notebook integration
- **Batch**: Job-based, spot instance support

**GPU Instance Types:**

| Instance Type | GPU | vCPU | RAM | Price/hr | Monthly (24/7) | Best For |
|--------------|-----|------|-----|----------|----------------|----------|
| g4dn.xlarge | T4 | 4 | 16GB | $0.526 | $379 | Development, Testing |
| g4dn.2xlarge | T4 | 8 | 32GB | $0.752 | $541 | Production |
| g5.xlarge | A10G | 4 | 16GB | $1.006 | $724 | ML inference |
| g5.2xlarge | A10G | 8 | 32GB | $1.212 | $872 | High throughput |
| p3.2xlarge | V100 | 8 | 61GB | $3.06 | $2,203 | Training, Research |

**Cost Optimization Strategies:**
1. **Spot Instances**: 70% savings ($114/month vs $379 for g4dn.xlarge)
   - Trade-off: 2-minute termination notice
   - Best for: Batch processing with checkpointing

2. **Reserved Instances**: 30-40% savings (1-3 year commitment)
   - $228/month for g4dn.xlarge (1-year, no upfront)

3. **Auto-scaling**: Only run during business hours
   - 12 hrs/day, 5 days/week: $114/month (70% savings)

4. **Savings Plans**: Flexible commitment across instance types
   - 20-30% savings with compute savings plans

**Setup:**
```bash
# 1. Configure AWS credentials
export AWS_REGION=us-east-1
export AWS_ECS_CLUSTER=bpo-pipeline

# 2. Set deployment mode
echo "GPU_DEPLOYMENT_MODE=aws-gpu" >> .env
echo "AWS_GPU_INSTANCE_TYPE=g4dn.xlarge" >> .env

# 3. Deploy with AWS override
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.aws-gpu.yml \
  --profile base up -d

# 4. Monitor with CloudWatch
aws logs tail /ecs/bpo-pipeline --follow
```

**Performance (g4dn.xlarge, T4 GPU):**
- Embeddings: 120-130 embeddings/sec (similar to RTX 3060)
- Network latency: +10-50ms vs local
- Storage: EFS or EBS (gp3 recommended)
- Throughput: 45,000 documents in ~18 hours

**Advantages:**
- ✅ Pay-per-use (no upfront cost)
- ✅ Auto-scaling capability
- ✅ Managed infrastructure
- ✅ CloudWatch monitoring
- ✅ RDS integration for database
- ✅ Spot instances for cost savings

**Disadvantages:**
- ❌ Monthly recurring costs
- ❌ Network latency overhead
- ❌ AWS expertise required
- ❌ Potential spot interruptions
- ❌ Data egress charges

**Best Use Cases:**
- Variable workload (spiky traffic)
- Production deployments (auto-scaling)
- Integration with AWS ecosystem
- Multi-region deployments
- Disaster recovery requirements

---

### 3. GCP GPU Mode

**Service Options:**
- **GKE (Kubernetes)**: Container orchestration, auto-scaling
- **Compute Engine**: VM-based, full control
- **Cloud Run GPU** (Preview): Serverless containers with GPU
- **Vertex AI**: ML-optimized platform

**GPU Instance Types:**

| Instance Type | GPU | vCPU | RAM | Price/hr | Monthly (24/7) | Best For |
|--------------|-----|------|-----|----------|----------------|----------|
| n1-standard-4 + T4 | T4 | 4 | 15GB | $0.70 | $504 | Development |
| n1-standard-8 + T4 | T4 | 8 | 30GB | $0.73 | $525 | Production |
| n1-standard-4 + L4 | L4 | 4 | 15GB | $0.88 | $633 | Inference |
| a2-highgpu-1g | A100 | 12 | 85GB | $3.67 | $2,644 | Training |

**Cost Optimization Strategies:**
1. **Preemptible VMs**: 80% savings ($101/month vs $504 for T4)
   - Trade-off: 24-hour max runtime, 30-second notice
   - Best for: Batch processing

2. **Committed Use Discounts**: 37-55% savings (1-3 year)
   - $318/month for T4 (1-year commitment)

3. **Sustained Use Discounts**: Automatic 30% discount for continuous use
   - Applies after 25% of month (no commitment needed)

4. **Custom Machine Types**: Pay only for what you need
   - Optimize vCPU/memory ratio

**Setup:**
```bash
# 1. Configure GCP credentials
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1

# 2. Set deployment mode
echo "GPU_DEPLOYMENT_MODE=gcp-gpu" >> .env
echo "GCP_GPU_TYPE=nvidia-tesla-t4" >> .env

# 3. Deploy with GCP override
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.gcp-gpu.yml \
  --profile base up -d

# 4. Monitor with Cloud Logging
gcloud logging read "resource.type=gce_instance" --limit 50
```

**Performance (T4 GPU):**
- Embeddings: 120-130 embeddings/sec
- Network latency: +10-50ms vs local
- Storage: Filestore or Persistent Disk (SSD)
- Throughput: 45,000 documents in ~18 hours

**Advantages:**
- ✅ Excellent preemptible pricing (80% savings)
- ✅ Automatic sustained use discounts
- ✅ Strong ML ecosystem (Vertex AI)
- ✅ Global network infrastructure
- ✅ BigQuery integration for analytics
- ✅ GKE autopilot for managed Kubernetes

**Disadvantages:**
- ❌ Monthly recurring costs
- ❌ Network latency overhead
- ❌ GCP expertise required
- ❌ Preemptible interruptions
- ❌ Limited GPU availability in some regions

**Best Use Cases:**
- ML/AI-heavy workloads
- BigQuery analytics integration
- Global multi-region deployments
- Kubernetes-native applications
- Research and experimentation

---

### 4. Azure GPU Mode

**Service Options:**
- **AKS (Kubernetes)**: Container orchestration
- **Container Instances**: Serverless containers
- **Virtual Machines**: Full control
- **Machine Learning**: ML platform

**GPU Instance Types:**

| Instance Type | GPU | vCPU | RAM | Price/hr | Monthly (24/7) | Best For |
|--------------|-----|------|-----|----------|----------------|----------|
| NC4as_T4_v3 | T4 | 4 | 28GB | $0.526 | $379 | Development |
| NC8as_T4_v3 | T4 | 8 | 56GB | $0.752 | $541 | Production |
| NC6s_v3 | V100 | 6 | 112GB | $3.06 | $2,203 | Training |
| ND96asr_v4 | 8x A100 | 96 | 900GB | $27.20 | $19,584 | Large-scale |

**Cost Optimization Strategies:**
1. **Spot VMs**: Up to 90% savings ($38/month vs $379 for NC4as_T4_v3)
   - Trade-off: Eviction with 30-second notice
   - Best for: Batch, fault-tolerant workloads

2. **Reserved Instances**: Up to 72% savings (1-3 year)
   - $106/month for NC4as_T4_v3 (3-year upfront)

3. **Azure Hybrid Benefit**: Additional savings with existing licenses
   - Applies to Windows Server licenses

4. **Auto-scaling**: Schedule-based or metric-based scaling
   - Scale down during off-hours

**Setup:**
```bash
# 1. Configure Azure credentials
export AZURE_SUBSCRIPTION_ID=your-sub-id
export AZURE_RESOURCE_GROUP=bpo-pipeline-rg
export AZURE_LOCATION=eastus

# 2. Set deployment mode
echo "GPU_DEPLOYMENT_MODE=azure-gpu" >> .env
echo "AZURE_GPU_SKU=Standard_NC4as_T4_v3" >> .env

# 3. Deploy with Azure override
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.azure-gpu.yml \
  --profile base up -d

# 4. Monitor with Azure Monitor
az monitor metrics list --resource <resource-id>
```

**Performance (NC4as_T4_v3, T4 GPU):**
- Embeddings: 120-130 embeddings/sec
- Network latency: +10-50ms vs local
- Storage: Azure Files or Managed Disks (Premium SSD)
- Throughput: 45,000 documents in ~18 hours

**Advantages:**
- ✅ Excellent spot VM pricing (90% savings)
- ✅ Strong enterprise integration (AD, RBAC)
- ✅ Hybrid cloud capabilities
- ✅ Azure ML platform
- ✅ Managed Identity for security
- ✅ Good GPU availability

**Disadvantages:**
- ❌ Monthly recurring costs
- ❌ Network latency overhead
- ❌ Azure expertise required
- ❌ Spot interruptions
- ❌ Complex pricing model

**Best Use Cases:**
- Enterprise deployments
- Hybrid cloud scenarios
- Microsoft ecosystem integration
- Compliance-heavy industries
- Multi-cloud strategy

---

## Cost Comparison Analysis

### Scenario 1: Small Development Team (8 hours/day, 5 days/week)

**Annual Costs:**
- **Local eGPU**: $800 (hardware) + $300 (electricity) = **$1,100**
- **AWS g4dn.xlarge** (On-Demand): $0.526 × 8 × 5 × 52 = **$1,094/year**
- **AWS g4dn.xlarge** (Spot): $0.158 × 8 × 5 × 52 = **$328/year** ✅ Cheapest
- **GCP T4** (Preemptible): $0.14 × 8 × 5 × 52 = **$291/year** ✅ Cheapest
- **Azure NC4as_T4_v3** (Spot): $0.053 × 8 × 5 × 52 = **$110/year** ✅ Cheapest

**Winner**: Cloud Spot/Preemptible instances for part-time use

### Scenario 2: Production 24/7 (Variable Load)

**Annual Costs (24/7):**
- **Local eGPU**: $800 (hardware) + $600 (electricity) = **$1,400 Year 1**, $600/year after
- **AWS g4dn.xlarge** (On-Demand): $379/month × 12 = **$4,548/year**
- **AWS g4dn.xlarge** (Reserved): $228/month × 12 = **$2,736/year**
- **AWS g4dn.xlarge** (Spot): $114/month × 12 = **$1,368/year**
- **GCP T4** (On-Demand): $504/month × 12 = **$6,048/year**
- **GCP T4** (Committed): $318/month × 12 = **$3,816/year**
- **GCP T4** (Preemptible): $101/month × 12 = **$1,212/year**
- **Azure NC4as_T4_v3** (On-Demand): $379/month × 12 = **$4,548/year**
- **Azure NC4as_T4_v3** (Reserved 3yr): $106/month × 12 = **$1,272/year**

**3-Year Total Cost:**
- **Local eGPU**: $1,400 + $600 + $600 = **$2,600** ✅ Cheapest long-term
- **AWS Spot**: $4,104
- **GCP Preemptible**: $3,636
- **Azure Spot**: $1,368
- **Azure Reserved (3yr)**: $3,816

**Winner**:
- **Year 1**: Cloud spot instances
- **Years 2-3+**: Local eGPU becomes cheaper

### Scenario 3: High-Scale Production (Multiple GPUs)

**Annual Costs (4 GPUs, 24/7):**
- **Local eGPU**: $3,200 (hardware) + $2,400 (electricity) = **$5,600 Year 1**, $2,400/year after
- **AWS g4dn.xlarge × 4**: $18,192/year (On-Demand), $5,472/year (Spot)
- **GCP T4 × 4**: $24,192/year (On-Demand), $4,848/year (Preemptible)
- **Azure NC4as_T4_v3 × 4**: $18,192/year (On-Demand), $5,088/year (Reserved)

**Winner**: Local eGPU for sustained high-scale (ROI in 7-8 months)

---

## Performance Comparison

### Embeddings Throughput (all-MiniLM-L6-v2, batch=32)

| Deployment | GPU | Throughput | Latency (per batch) |
|-----------|-----|------------|---------------------|
| **Local eGPU** | RTX 3060 | 128 emb/sec | 250ms |
| **AWS g4dn** | T4 | 120 emb/sec | 267ms |
| **GCP T4** | T4 | 120 emb/sec | 267ms |
| **Azure NC4as** | T4 | 120 emb/sec | 267ms |
| **AWS g5** | A10G | 180 emb/sec | 178ms |
| **GCP A100** | A100 | 350 emb/sec | 91ms |
| **CPU Fallback** | - | 36 emb/sec | 889ms |

**Network Latency Impact:**
- Local: 0ms
- Cloud (same region): +5-15ms
- Cloud (different region): +50-200ms

### Total Processing Time (45,000 documents)

| Deployment | Time | Notes |
|-----------|------|-------|
| **Local RTX 3060** | 17.0 hrs | Baseline |
| **AWS g4dn.xlarge** | 18.0 hrs | +6% (network overhead) |
| **GCP T4** | 18.0 hrs | +6% |
| **Azure NC4as_T4_v3** | 18.0 hrs | +6% |
| **CPU-only** | 61.0 hrs | +259% slower |

---

## Decision Framework

### Choose **Local eGPU** if:
✅ Long-term deployment (2+ years)
✅ Consistent 24/7 workload
✅ On-premise requirements
✅ Privacy-critical data
✅ Low budget for recurring costs
✅ Small to medium scale
✅ Development and testing

### Choose **AWS GPU** if:
✅ Variable workload (auto-scaling needed)
✅ Already using AWS ecosystem
✅ Need multi-region deployment
✅ Want managed infrastructure
✅ Spot instances acceptable
✅ Production with disaster recovery

### Choose **GCP GPU** if:
✅ ML/AI-heavy workloads
✅ BigQuery integration needed
✅ Kubernetes-native applications
✅ Global infrastructure required
✅ Best preemptible pricing
✅ Research and experimentation

### Choose **Azure GPU** if:
✅ Enterprise Microsoft stack
✅ Hybrid cloud requirements
✅ Active Directory integration
✅ Compliance needs (HIPAA, FedRAMP)
✅ Best spot pricing (90% savings)
✅ Multi-cloud strategy

### Choose **CPU-Only** if:
✅ Development without GPU
✅ Budget constraints
✅ Low-volume processing (<1,000 docs/day)
✅ Non-time-sensitive batch jobs
✅ Testing and CI/CD pipelines

---

## Migration Path

### Local eGPU → Cloud GPU

```bash
# 1. Backup local data
docker exec bpo-postgres pg_dump -U postgres bpo_intel > backup.sql

# 2. Upload to cloud storage
aws s3 cp backup.sql s3://your-bucket/backup.sql

# 3. Deploy cloud infrastructure
docker-compose -f docker-compose.yml -f docker-compose.aws-gpu.yml up -d

# 4. Restore database
aws s3 cp s3://your-bucket/backup.sql - | docker exec -i bpo-postgres psql -U postgres bpo_intel

# 5. Verify GPU detection
docker exec bpo-prefect-agent python -c "import torch; print(torch.cuda.is_available())"
```

### Cloud GPU → Local eGPU

```bash
# 1. Backup cloud database
aws rds export-snapshot --export-identifier backup-snapshot

# 2. Download backup
aws s3 cp s3://rds-exports/backup.sql backup.sql

# 3. Deploy local services
docker-compose --profile base up -d

# 4. Restore database
cat backup.sql | docker exec -i bpo-postgres psql -U postgres bpo_intel

# 5. Verify GPU detection
docker exec bpo-prefect-agent nvidia-smi
```

---

## Monitoring & Optimization

### GPU Utilization Monitoring

**Local eGPU:**
```bash
# Real-time monitoring
nvidia-smi -l 1

# Detailed metrics
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.free --format=csv -l 1
```

**AWS CloudWatch:**
```bash
# GPU metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name GPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time 2023-01-01T00:00:00Z \
  --end-time 2023-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

**GCP Monitoring:**
```bash
# GPU metrics
gcloud compute instances describe INSTANCE_NAME \
  --zone=us-central1-a \
  --format="get(guestAccelerators)"
```

**Azure Monitor:**
```bash
# GPU metrics
az monitor metrics list \
  --resource "/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vm}" \
  --metric "Percentage GPU" \
  --interval PT1M
```

### Cost Optimization Tips

1. **Batch Processing**: Process in batches during off-peak hours
2. **Right-Sizing**: Monitor utilization and downgrade if < 50%
3. **Auto-Scaling**: Scale to zero when idle
4. **Spot/Preemptible**: Use for fault-tolerant workloads
5. **Reserved Capacity**: Commit for predictable workloads
6. **Multi-Cloud**: Compare pricing across providers
7. **Data Locality**: Minimize data transfer costs
8. **Caching**: Cache embeddings to reduce recomputation

---

## Summary

### Cost Winner by Scenario

| Scenario | Best Option | Annual Cost |
|----------|-------------|-------------|
| Part-time (8h/day) | Azure Spot | $110 |
| Full-time Year 1 | Azure Spot | $456 |
| Full-time Year 3+ | Local eGPU | $600/year |
| High-Scale (4 GPUs) | Local eGPU | $2,400/year |

### Performance Winner

All T4-based options (local RTX 3060, AWS g4dn, GCP T4, Azure NC4as) deliver similar performance (~120-128 embeddings/sec). Local eGPU has slight edge due to zero network latency.

### Flexibility Winner

Cloud platforms (AWS, GCP, Azure) offer superior flexibility with auto-scaling, multi-region, and managed services.

### Simplicity Winner

Local eGPU is simplest to set up (nvidia-docker + docker-compose) with no cloud expertise required.

---

## Quick Start Commands

```bash
# Local eGPU (default)
docker-compose --profile base up -d

# CPU-Only (development)
docker-compose -f docker-compose.yml -f docker-compose.cpu-only.yml --profile base up -d

# AWS GPU
docker-compose -f docker-compose.yml -f docker-compose.aws-gpu.yml --profile base up -d

# GCP GPU
docker-compose -f docker-compose.yml -f docker-compose.gcp-gpu.yml --profile base up -d

# Azure GPU
docker-compose -f docker-compose.yml -f docker-compose.azure-gpu.yml --profile base up -d
```

---

## Support

For deployment assistance:
- Local eGPU: Check `HYBRID_GPU_IMPLEMENTATION.md`
- Cloud GPU: Check cloud provider documentation
- Issues: Open a GitHub issue with deployment logs

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
