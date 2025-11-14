# Quick Start: Venmo Q&A Dataset Refactoring

## Your Data → Q&A CSV in 2 Steps

### Step 1: Save Your Raw Data

Copy all your Venmo data and paste it into this file:
```
data/venmo_raw_paste.txt
```

**Format:** Each line should look like:
```
0	{ url: "...", pageTitle: "...", fullText: "..." }
1	{ url: "...", pageTitle: "...", fullText: "..." }
...
```

### Step 2: Run the Converter

```bash
python3 scripts/direct_venmo_converter.py
```

**Output:** `data/venmo_qa_dataset.csv`

---

## What You Get

A structured CSV with these columns:

| Column | Example |
|--------|---------|
| **question** | "How do I verify my bank account?" |
| **answer** | "To verify your bank account, you'll need to confirm..." |
| **source_title** | "Verifying Your Bank Account \| Venmo" |
| **source_url** | "https://help.venmo.com/..." |
| **topic_category** | "Banking" |
| **keywords** | "Account, Bank, Verification" |
| **article_id** | "vhel304" |

---

## Example Transformation

### Input (from your data):
```
24	{ url: "https://help.venmo.com/cs/articles/customer-identification-document-requirements-vhel168",
     pageTitle: "Customer Identification Document Requirements | Venmo",
     fullText: "Help CenterHow can we help you?VenmoAccounts...article_page|vhel168" }
```

### Output (in CSV):
| id | question | answer | topic_category | keywords |
|----|----------|--------|----------------|----------|
| 24 | What are the requirements for Customer Identification Document? | To provide required customer identification documents... | Accounts & Settings | Customer, Document, Identification, Requirements |

---

## Full Dataset Processing

To process your complete 283-entry dataset:

1. **Replace** `data/venmo_raw_paste.txt` with your full data
2. **Run**: `python3 scripts/direct_venmo_converter.py`
3. **Check**: `data/venmo_qa_dataset.csv` for 283 Q&A pairs

---

## Output Structure

The generated CSV will have approximately:
- **283 rows** (one per entry)
- **10 columns** (structured data)
- **Auto-categorized** into 12 topic categories
- **Natural questions** generated from page titles
- **Concise answers** extracted from full text

---

## Topic Categories (Auto-Detected)

Your data will be categorized into:

✓ Accounts & Settings
✓ Payments & Transfers
✓ Wallet & Cards
✓ Security & Privacy
✓ Banking
✓ Business Profiles
✓ Charity Profiles
✓ Tax Center
✓ Disputes
✓ Cryptocurrency
✓ Buying & Selling
✓ Troubleshooting
✓ General Support

---

## Already Done ✓

I've created:

1. **Three conversion scripts** in `scripts/`:
   - `direct_venmo_converter.py` ← **Use this one**
   - `parse_and_transform_venmo.py` (for JSON input)
   - `refactor_qa_structure.py` (library functions)

2. **Sample data** in `data/venmo_raw_paste.txt` (5 entries)

3. **Sample output** in `data/venmo_qa_dataset.csv`

4. **Documentation** in `data/README_QA_REFACTOR.md`

---

## Next Steps

1. **Replace sample data** with your full 283 entries
2. **Run the converter**
3. **Review the output** in Excel or any CSV viewer
4. **Use the Q&A dataset** for:
   - AI training
   - RAG systems
   - Knowledge bases
   - Chatbot training
   - Search indexing

---

## Need Help?

Check `data/README_QA_REFACTOR.md` for:
- Detailed documentation
- Troubleshooting guide
- Customization options
- Advanced features

---

**Ready to process your full dataset? Just paste it into `data/venmo_raw_paste.txt` and run the script!**
