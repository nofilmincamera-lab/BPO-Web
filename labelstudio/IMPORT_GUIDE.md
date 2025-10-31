# Label Studio Import Guide - Pre-annotated Tasks

## ✅ Fixed Files Ready for Import

**Primary file:** `data/label-studio/tasks_with_predictions_5k.json` (5000 tasks with predictions)
**Alternative:** `data/label-studio/tasks_with_predictions_5k.jsonl` (same data, line-delimited)

## 🎯 Import Steps

### 1. Create/Configure Project
- Go to http://localhost:8082
- Create new project or open existing
- **CRITICAL:** Use this exact interface config:

```xml
<View>
  <Labels name="label" toName="text">
    <Label value="COMPANY" background="#1f77b4"/>
    <Label value="PERSON" background="#ff7f0e"/>
    <Label value="DATE" background="#2ca02c"/>
    <Label value="TECHNOLOGY" background="#d62728"/>
    <Label value="MONEY" background="#9467bd"/>
    <Label value="PERCENT" background="#8c564b"/>
    <Label value="PRODUCT" background="#e377c2"/>
    <Label value="COMPUTING_PRODUCT" background="#bcbd22"/>
    <Label value="BUSINESS_TITLE" background="#17becf"/>
    <Label value="LOCATION" background="#7f7f7f"/>
    <Label value="TIME_RANGE" background="#aec7e8"/>
    <Label value="ORL" background="#ffbb78"/>
    <Label value="TEMPORAL" background="#98df8a"/>
    <Label value="SKILL" background="#ff9896"/>
  </Labels>
  <Text name="text" value="$text" granularities="word" highlightColor="#ffff0077"/>
</View>
```

### 2. Import Tasks
- Go to Data Import tab
- Upload `data/label-studio/tasks_with_predictions_5k.json`
- Wait for processing (5000 tasks)

### 3. View Predictions
- Open any task for labeling
- **Toggle predictions visibility:** Look for eye icon (👁️) or "Show predictions" button
- Predictions should appear as highlighted spans with suggested labels
- You can accept, modify, or reject each prediction

## 🔍 Troubleshooting

### If predictions don't show:
1. **Check interface config** - Must match exactly (from_name="label", toName="text")
2. **Toggle visibility** - Click the eye icon or "Show predictions" button
3. **Check task structure** - Run validator: `python scripts/validate_ls_tasks.py`

### If import fails:
1. Try JSONL format: `data/label-studio/tasks_with_predictions_5k.jsonl`
2. Check file size (should be ~50MB for 5k tasks)
3. Verify Label Studio is running: `docker-compose ps label-studio`

## 📊 Expected Results

- **5000 tasks** with pre-annotations
- **Average 20-40 entities per task** (varies by content)
- **Entity types:** COMPANY, PERSON, DATE, TECHNOLOGY, MONEY, PERCENT, PRODUCT, COMPUTING_PRODUCT, BUSINESS_TITLE, LOCATION, TIME_RANGE, ORL, TEMPORAL, SKILL
- **Confidence scores:** 0.8 (can be adjusted in merge script)

## 🚀 Next Steps

1. **Start labeling** - Accept/modify predictions as needed
2. **Export annotations** - Use Label Studio's export feature
3. **Optional ML backend** - Attach for live predictions and active learning

## 📁 File Locations

```
data/label-studio/
├── tasks_with_predictions_5k.json     # Main import file (JSON array)
├── tasks_with_predictions_5k.jsonl    # Alternative format (JSONL)
├── ner_config.xml                     # Interface configuration
└── README_ML_BACKEND.md              # ML backend setup guide
```

