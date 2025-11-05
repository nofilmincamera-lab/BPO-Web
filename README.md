# BPO Intelligence Pipeline

Enterprise-grade NLP extraction pipeline for Business Process Outsourcing (BPO) intelligence with hybrid GPU/CPU acceleration.

## 🚀 Features

- **Multi-Layer Classification**: 14 content types, 67 industries, 50 services, 9 technologies
- **Named Entity Recognition**: 10 entity types with 90%+ autonomous extraction
- **Hybrid GPU/CPU Architecture**: Optimized for both hardware types
- **Flexible Deployment**: Local eGPU, AWS, GCP, Azure, or CPU-only
- **Heuristics-First Pipeline**: 3,925 company aliases, 940 products, 600+ BPO terms
- **Production-Ready**: Docker orchestration, Prefect workflows, PostgreSQL + pgvector
- **High Performance**: 128 embeddings/sec (GPU), 97-102 docs/sec (CPU NER)

## 📊 Extraction Capabilities

### Classification Layers

1. **Content Types** (14 types)
   - Case Study, Blog/Article, Company Information, Services/Offerings
   - Product/Technology, Pricing, Documentation, News/Press Release
   - Event/Webinar, Legal/Compliance, Careers, Landing Page, Testimonials

2. **Industries** (67 sub-industries across 10 main categories)
   - Financial Services, Healthcare, Public Sector, Industrial/Energy
   - Retail/E-Commerce, Travel/Logistics, Technology/Media
   - Business Services, Agriculture/ESG, Cross-Sector Emerging

3. **Services** (50 sub-services across 11 categories)
   - CX Operations, Collections/Recovery, F&A, HRO
   - Risk/Compliance, AI-Enabled CX, Data/Analytics
   - Back-Office, Technology Services, CX Transformation

4. **Technologies** (9 categories)
   - Agentic AI, Generative AI, Conversational AI
   - Predictive AI/ML, Analytics/BI, RPA/Automation
   - CRM Platforms, Contact Center, Cloud Infrastructure

5. **Named Entities** (10 types)
   - ORG (129+ providers), PERSON, LOC (52 countries)
   - PRODUCT (940+ products), TECHNOLOGY (600+ terms)
   - INDUSTRY, CATEGORY, DATE, MONEY, PERCENT

6. **Relationships** (6 types)
   - belongs_to, partners_with, provides, uses, located_in, works_for

## 🎯 Deployment Options

### Quick Start

Choose your deployment mode:

```bash
# 1. Local eGPU (recommended for development)
./scripts/deploy.sh local-egpu

# 2. CPU-only (no GPU required)
./scripts/deploy.sh cpu-only

# 3. AWS GPU (production, auto-scaling)
./scripts/deploy.sh aws-gpu

# 4. GCP GPU (ML-optimized)
./scripts/deploy.sh gcp-gpu

# 5. Azure GPU (enterprise)
./scripts/deploy.sh azure-gpu
```

### Deployment Comparison

| Mode | Setup | Cost/Month | Performance | Best For |
|------|-------|------------|-------------|----------|
| **Local eGPU** | Easy | $0* | 128 emb/sec | Development, Long-term |
| **AWS GPU** | Medium | $114-379** | 120 emb/sec | Production, Auto-scale |
| **GCP GPU** | Medium | $101-504** | 120 emb/sec | ML workloads, Research |
| **Azure GPU** | Medium | $110-379** | 120 emb/sec | Enterprise, Hybrid |
| **CPU-Only** | Easy | $0 | 36 emb/sec | Testing, Low-volume |

*Plus electricity (~$20-50/month)
**Spot/preemptible pricing to on-demand pricing

📚 **See [DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md](DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md) for detailed comparison**

## 🏗️ Architecture

### Hybrid GPU/CPU Strategy

```
┌─────────────────────────────────────────────┐
│        BPO Extraction Pipeline              │
├─────────────────────────────────────────────┤
│                                             │
│  PHASE 1: Entity Extraction (CPU) ⚡       │
│  ├─ spaCy NER (97-102 docs/sec)            │
│  ├─ EntityRuler (4,500+ patterns)          │
│  └─ Heuristics (3,925 company aliases)     │
│                                             │
│  PHASE 2: Embeddings (GPU) 🚀               │
│  ├─ sentence-transformers                  │
│  ├─ all-MiniLM-L6-v2 (384-dim)             │
│  └─ 128 embeddings/sec (3.5x speedup)      │
│                                             │
│  PHASE 3: Storage (PostgreSQL + pgvector)  │
│  ├─ Entities → entities table              │
│  ├─ Embeddings → entity_embeddings         │
│  └─ Relationships → relationships          │
│                                             │
└─────────────────────────────────────────────┘
```

**Why This Works:**
- ✅ CPU for NER: `en_core_web_sm` is already fast (GPU alternative is 3-4x slower)
- ✅ GPU for embeddings: Transformers benefit from GPU (3.5x speedup)
- ✅ Auto-fallback: Gracefully falls back to CPU if GPU unavailable

## 🛠️ Prerequisites

### All Deployments
- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum
- 50GB disk space

### Local eGPU Mode
- NVIDIA GPU with 6GB+ VRAM (RTX 3060 recommended)
- NVIDIA drivers 525+
- nvidia-docker2

### Cloud GPU Modes
- AWS: AWS CLI, ECS/EC2 access, IAM permissions
- GCP: Google Cloud SDK, Compute Engine/GKE access
- Azure: Azure CLI, VM/AKS access

## 📦 Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/BPO-Web.git
cd BPO-Web
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env

# Key settings:
# - GPU_DEPLOYMENT_MODE: local-egpu, aws-gpu, gcp-gpu, azure-gpu, cpu-only
# - EMBEDDING_MODEL: sentence-transformers/all-MiniLM-L6-v2
# - DB_PASSWORD: Your secure password
```

### 3. Deploy

```bash
# Use deployment script (recommended)
./scripts/deploy.sh local-egpu

# Or use docker-compose directly
docker-compose --profile base up -d
```

### 4. Verify Deployment

```bash
# Check services
docker-compose ps

# Check GPU (if applicable)
docker exec bpo-prefect-agent nvidia-smi

# Check GPU in Python
docker exec bpo-prefect-agent python -c "import torch; print(f'GPU: {torch.cuda.is_available()}')"

# Check logs
docker-compose logs -f
```

## 🌐 Access Services

- **Prefect UI**: http://localhost:4200 (workflow orchestration)
- **API**: http://localhost:8000 (FastAPI endpoints)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **PostgreSQL**: localhost:5432 (database with pgvector)
- **Prometheus**: http://localhost:9090 (metrics, optional)
- **Grafana**: http://localhost:3000 (dashboards, optional)

## 🔧 Configuration

### GPU Configuration

```bash
# .env file
GPU_DEPLOYMENT_MODE=local-egpu     # local-egpu, aws-gpu, gcp-gpu, azure-gpu, cpu-only
FORCE_CPU_ONLY=0                   # Set to 1 to force CPU mode
NVIDIA_VISIBLE_DEVICES=all         # GPU device selection
GPU_MEMORY_FRACTION=0.9            # Limit GPU memory usage
EMBEDDING_BATCH_SIZE=32            # Adjust based on GPU memory
```

### Model Configuration

```bash
# Embedding models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Default, 384-dim, fastest
# EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # 768-dim, higher quality
# EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2  # Multilingual
```

### Performance Tuning

```bash
EMBEDDING_BATCH_SIZE=32            # RTX 3060 (12GB): 32-64
                                    # T4 (16GB): 64-128
                                    # A10G (24GB): 128-256

SPACY_BATCH_SIZE=100               # CPU NER batch size
PREFECT_WORKER_CONCURRENCY=4       # Parallel task execution
```

## 📊 Performance Benchmarks

### GPU Performance (RTX 3060, 12GB)

- **Embeddings**: 128 embeddings/sec (3.5x faster than CPU)
- **GPU Memory**: 700-1000 MB peak
- **Processing**: 45,000 documents in ~17 hours
- **Throughput**: 0.74 docs/sec

### Cloud GPU Performance (T4)

- **Embeddings**: 120 embeddings/sec
- **Processing**: 45,000 documents in ~18 hours
- **Network Overhead**: +5-15ms latency (same region)

### CPU-Only Performance

- **Embeddings**: 36 embeddings/sec (3.5x slower than GPU)
- **Processing**: 45,000 documents in ~61 hours
- **Use Case**: Development, testing, low-volume

## 🚀 Usage

### Run Extraction Pipeline

```bash
# Queue extraction job via API
curl -X POST http://localhost:8000/api/v1/extraction/queue \
  -H "Content-Type: application/json" \
  -d '{"source": "crawl_data", "batch_size": 100}'

# Monitor in Prefect UI
open http://localhost:4200
```

### Check GPU Status

```bash
# GPU availability
docker exec bpo-prefect-agent python -c "import torch; print(torch.cuda.is_available())"

# GPU info
docker exec bpo-prefect-agent python -c "from src.extraction.gpu_embeddings import get_embedding_info; print(get_embedding_info())"

# NVIDIA stats
docker exec bpo-prefect-agent nvidia-smi
```

### Generate Embeddings

```python
from src.extraction.gpu_embeddings import generate_embeddings

# Generate embeddings (GPU-accelerated)
texts = ["Microsoft Corporation", "Cloud Computing", "Customer Experience"]
embeddings = generate_embeddings(texts)

print(embeddings.shape)  # (3, 384)
```

## 🧪 Testing

### GPU Tests

```bash
# Quick GPU test
python test_gpu_extraction.py --quick

# Full GPU test
python test_gpu_extraction.py

# Hybrid GPU/CPU test
python test_hybrid_gpu.py
```

### Integration Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_extraction_flow.py -v
```

## 📁 Project Structure

```
BPO-Web/
├── src/
│   ├── extraction/
│   │   ├── spacy_pipeline.py       # CPU NER (spaCy)
│   │   └── gpu_embeddings.py       # GPU embeddings
│   ├── flows/
│   │   └── extraction_flow.py      # Prefect orchestration
│   ├── api/
│   │   └── main.py                 # FastAPI endpoints
│   └── heuristics/
│       └── loader.py               # Heuristics loading
├── Heuristics/
│   ├── ner_relationships.json      # 129 providers, 940 products
│   ├── company_aliases_clean.json  # 3,925 aliases
│   ├── content_types.json          # 14 content types
│   ├── taxonomy_industries.json    # 67 industries
│   └── taxonomy_services.json      # 50 services
├── docker/
│   ├── Dockerfile.worker           # Prefect worker (GPU)
│   ├── Dockerfile.worker.cpu       # Prefect worker (CPU)
│   ├── Dockerfile.api              # API (GPU)
│   └── Dockerfile.api.cpu          # API (CPU)
├── docker-compose.yml              # Base orchestration
├── docker-compose.cpu-only.yml     # CPU-only override
├── docker-compose.aws-gpu.yml      # AWS GPU override
├── docker-compose.gcp-gpu.yml      # GCP GPU override
├── docker-compose.azure-gpu.yml    # Azure GPU override
├── scripts/
│   └── deploy.sh                   # Deployment helper
├── .env.example                    # Configuration template
└── DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md  # Detailed deployment guide
```

## 📚 Documentation

- **[DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md](DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md)**: Complete deployment comparison (cloud vs eGPU)
- **[HYBRID_GPU_IMPLEMENTATION.md](HYBRID_GPU_IMPLEMENTATION.md)**: GPU/CPU architecture details
- **[GPU_TEST_QUICKREF.md](GPU_TEST_QUICKREF.md)**: Quick GPU testing guide
- **[EXTRACTION_STATUS.md](EXTRACTION_STATUS.md)**: Extraction pipeline status
- **[DOCKER_NETWORKS.md](DOCKER_NETWORKS.md)**: Docker networking guide

## 🔍 Monitoring & Observability

### GPU Monitoring

```bash
# Real-time GPU stats
watch -n 1 nvidia-smi

# GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.free --format=csv -l 1

# Docker container GPU
docker exec bpo-prefect-agent nvidia-smi
```

### Application Monitoring

```bash
# Enable monitoring stack
docker-compose --profile metrics up -d

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3000
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prefect-agent

# Filter logs
docker-compose logs -f | grep ERROR
```

## 💰 Cost Analysis

### Total Cost of Ownership (3 Years)

| Deployment | Year 1 | Year 2 | Year 3 | Total |
|-----------|--------|--------|--------|-------|
| **Local eGPU** | $1,400 | $600 | $600 | **$2,600** ⭐ |
| **AWS Spot** | $1,368 | $1,368 | $1,368 | $4,104 |
| **GCP Preemptible** | $1,212 | $1,212 | $1,212 | $3,636 |
| **Azure Spot** | $456 | $456 | $456 | $1,368 |
| **AWS Reserved** | $2,736 | $2,736 | $2,736 | $8,208 |

**Break-even Point**: Local eGPU becomes cheaper after ~8 months of 24/7 operation

See [DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md](DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md) for detailed cost analysis.

## 🔐 Security

- **Secrets Management**: Use Docker secrets for sensitive data
- **Network Isolation**: Multiple Docker networks for service isolation
- **Database**: PostgreSQL with password-protected access
- **API**: FastAPI with CORS configuration
- **Cloud**: IAM roles, service accounts, managed identities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Open a Pull Request

## 📄 License

This project is proprietary. Contact the repository owner for licensing information.

## 🆘 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check the docs/ directory
- **Deployment Guide**: See DEPLOYMENT_GUIDE_CLOUD_VS_EGPU.md

## 🎉 Acknowledgments

- **spaCy**: Fast and accurate NLP
- **Sentence-Transformers**: GPU-accelerated embeddings
- **Prefect**: Modern workflow orchestration
- **PostgreSQL + pgvector**: Vector similarity search
- **Docker**: Containerization and deployment

---

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Status**: Production Ready ✅
