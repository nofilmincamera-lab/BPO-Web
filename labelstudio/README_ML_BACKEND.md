# Label Studio ML Backend Setup

## Option 1: Pre-annotations (Recommended for Quick Start)

You already have pre-annotated tasks ready to import:

```bash
# 5k sample with predictions
data/label-studio/tasks_with_predictions_5k.json

# Full dataset with predictions (if you want to generate it)
python scripts/gen_predictions.py --input data/preprocessed/dataset_45000_converted.jsonl --output data/label-studio/predictions_full.json --limit 0
python scripts/merge_tasks_predictions.py --tasks data/label-studio/tasks_full.json --predictions data/label-studio/predictions_full.json --output data/label-studio/tasks_with_predictions_full.json
```

**Import these directly into Label Studio via the UI.**

## Option 2: Live ML Backend (For Active Learning)

### Setup ML Backend

1. **Create ML Backend Container:**
```bash
# Build ML backend image
docker build -t bpo-ml-backend -f labelstudio/Dockerfile.ml .

# Run ML backend
docker run -d \
  --name bpo-ml-backend \
  --network bpo-network \
  -p 9090:9090 \
  -v $(pwd)/data:/data \
  bpo-ml-backend
```

2. **Attach to Label Studio:**
   - Go to Label Studio UI: http://localhost:8082
   - Create/Open your project
   - Go to Settings → Machine Learning
   - Add ML Backend:
     - URL: `http://bpo-ml-backend:9090`
     - Title: "BPO Entity Extraction"
     - Description: "spaCy-based entity extraction"

### ML Backend Features

- **Pre-annotations**: Automatically suggests entities for new tasks
- **Active Learning**: Learns from your corrections
- **Batch Processing**: Process multiple tasks at once
- **Confidence Scoring**: Shows prediction confidence

### API Endpoints

The ML backend provides these endpoints:

- `POST /predict` - Generate predictions for tasks
- `POST /fit` - Train/update model with new annotations
- `GET /health` - Health check
- `GET /` - Backend info

### Configuration

The ML backend uses your existing spaCy pipeline and heuristics, so it will:
- Extract the same entity types (COMPANY, PERSON, DATE, etc.)
- Use the same confidence thresholds
- Apply the same business rules

## Quick Start (Pre-annotations)

1. **Start Label Studio:**
```bash
docker-compose up label-studio -d
```

2. **Import Pre-annotated Tasks:**
   - Go to http://localhost:8082
   - Create new project
   - Import `data/label-studio/tasks_with_predictions_5k.json`
   - Start labeling!

The pre-annotations will appear as suggestions that you can accept, modify, or reject.

