# Venmo Q&A Dataset Refactoring

## Overview

This directory contains tools to transform scraped Venmo help center data into a structured Question-Answer format suitable for AI training.

## Input Format

Your raw data should be in one of these formats:

### Format 1: Tab-separated (as you provided)
```
0	{ url: "https://www.venmo.com/", pageTitle: "Pay Friends | Venmo", fullText: "..." }
1	{ url: "https://help.venmo.com/...", pageTitle: "...", fullText: "..." }
```

### Format 2: JSON Array
```json
[
  {
    "url": "https://www.venmo.com/",
    "pageTitle": "Pay Friends | Venmo",
    "fullText": "..."
  }
]
```

## Output Format

The scripts generate a CSV with these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Unique identifier | 1, 2, 3... |
| `question` | Natural language question | "How do I verify my bank account?" |
| `answer` | Concise answer extracted from content | "To verify your bank account..." |
| `source_title` | Original page title | "Bank Account Verification \| Venmo" |
| `source_url` | Original URL | "https://help.venmo.com/..." |
| `topic_category` | Categorized topic | "Banking", "Security & Privacy" |
| `keywords` | Extracted keywords | "Bank, Account, Verification" |
| `article_id` | Article identifier | "vhel168" |
| `data_source` | Source identifier | "Venmo Help Center" |
| `language` | Content language | "en-US" |

## Usage

### Option 1: Quick Conversion (Recommended)

1. Save your raw data to `data/venmo_raw_paste.txt`
2. Run:
```bash
python scripts/direct_venmo_converter.py
```

### Option 2: JSON Input

1. Save your data as JSON to `data/venmo_raw_input.json`
2. Run:
```bash
python scripts/parse_and_transform_venmo.py
```

### Option 3: Custom Processing

Use the refactor script with custom logic:
```bash
python scripts/refactor_qa_structure.py
```

## Topic Categories

The system automatically categorizes content into:

- **Accounts & Settings** - Profile management, account settings
- **Payments & Transfers** - Sending/receiving money, transfers
- **Wallet & Cards** - Debit/credit cards, wallet management
- **Security & Privacy** - Security features, privacy settings
- **Banking** - Bank accounts, verification
- **Business Profiles** - Business account features
- **Charity Profiles** - Charity/non-profit features
- **Tax Center** - Tax documentation, requirements
- **Disputes** - Payment disputes, chargebacks
- **Cryptocurrency** - Crypto features
- **Buying & Selling** - Merchant transactions
- **Troubleshooting** - Problem resolution
- **General Support** - Other help topics

## Examples

### Input:
```
0	{ url: "https://help.venmo.com/cs/articles/verifying-your-bank-account-vhel304",
    pageTitle: "Verifying Your Bank Account | Venmo",
    fullText: "Help Center...To verify your bank account..." }
```

### Output:
| question | answer | topic_category | keywords |
|----------|--------|----------------|----------|
| How do I verify my bank account? | To verify your bank account, you'll need to confirm two small deposits... | Banking | Account, Bank, Verifying |

## Scripts Overview

### `direct_venmo_converter.py`
- **Purpose**: Direct conversion of your exact data format
- **Input**: `data/venmo_raw_paste.txt` (tab-separated format)
- **Output**: `data/venmo_qa_dataset.csv`
- **Best for**: Quick conversion of the data format you provided

### `parse_and_transform_venmo.py`
- **Purpose**: Comprehensive transformation with advanced parsing
- **Input**: `data/venmo_raw_input.json` (JSON format)
- **Output**: `data/venmo_qa_dataset.csv`
- **Best for**: Clean JSON input with full feature set

### `refactor_qa_structure.py`
- **Purpose**: Modular transformation library
- **Best for**: Custom processing needs, integration into other tools

## Quality Assurance

The scripts perform these quality checks:

1. **Deduplication**: Skips records with missing URLs or titles
2. **Text Cleaning**: Removes navigation elements and boilerplate
3. **Answer Extraction**: Pulls meaningful content (50-450 characters)
4. **Question Generation**: Converts titles to natural questions
5. **Categorization**: Auto-assigns topic categories
6. **Keyword Extraction**: Identifies relevant search terms

## Troubleshooting

### "No records processed"
- Check input file exists
- Verify data format matches expected structure
- Look for parsing errors in console output

### "Questions don't make sense"
- Review title transformation patterns in code
- Manually adjust specific patterns as needed

### "Answers too short/long"
- Adjust `max_length` parameter in `extract_answer()` function
- Modify sentence extraction logic

## Next Steps

After generation:

1. **Review**: Check sample Q&A pairs for quality
2. **Validate**: Verify topic categorization accuracy
3. **Enhance**: Add custom context columns if needed
4. **Export**: Use CSV for AI training, RAG systems, or knowledge bases

## File Structure

```
BPO-Web/
├── data/
│   ├── venmo_raw_paste.txt          # Your raw data (input)
│   ├── venmo_raw_input.json         # JSON format (input)
│   ├── venmo_qa_dataset.csv         # Generated Q&A dataset (output)
│   └── README_QA_REFACTOR.md        # This file
└── scripts/
    ├── direct_venmo_converter.py    # Main converter
    ├── parse_and_transform_venmo.py # Advanced parser
    └── refactor_qa_structure.py     # Modular library
```
