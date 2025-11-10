# LinkedIn Data Enrichment - Usage Guide

## 🎯 Workflow: Finding Warm Introductions

This guide shows you how to use the LinkedIn enrichment tools to find the best people to introduce you to target companies.

## Setup

1. **Place your LinkedIn data** in the `Linkedin/` directory
   - Supported formats: JSON (`.json`) or CSV (`.csv`)
   - See `sample_data.json` for expected format

2. **Install requirements**:
   ```bash
   pip install pandas python-dateutil
   ```

## Two Scripts Available

### 1. Basic Enrichment (`enrich_linkedin_data.py`)
Simple company cross-referencing and counting.

**Use when**: You just want basic statistics about companies.

```bash
python Linkedin/enrich_linkedin_data.py
```

**Output**:
- `company_summary.csv` - Basic counts
- `master_connections.csv` - All connections
- `enriched/` - Company JSON files

---

### 2. Advanced Intelligence (`enrich_linkedin_advanced.py`) ⭐ **RECOMMENDED**
Sophisticated warm introduction intelligence with scoring.

**Use when**: You want to know WHO to contact for introductions.

```bash
python Linkedin/enrich_linkedin_advanced.py
```

**Output**:
- `introduction_intelligence.csv` - Scored introduction recommendations
- `enriched_advanced/` - Detailed intelligence per company

## 🔍 Example Workflow

### Scenario: You want an introduction to Google

#### Step 1: Run the advanced enrichment

```bash
python Linkedin/enrich_linkedin_advanced.py
```

**Output**:
```
🎯 TOP 20 COMPANIES FOR WARM INTRODUCTIONS
=================================================================================================
Rank  Company                            Curr  Past  Best Intro               Score   Level
-------------------------------------------------------------------------------------------------
1     Google                             4     3     Carol Davis              0.85    VP
2     Microsoft                          2     2     Emma Wilson              0.78    Senior
3     Meta                               1     2     Bob Smith                0.82    Director
...
```

#### Step 2: Search for specific company

```bash
python Linkedin/enrich_linkedin_advanced.py --search "Google"
```

**Output**:
```
================================================================================
🏢 Google LLC
================================================================================
  Total Connections: 7
  Current Employees: 4
  Past Employees: 3

  🎯 Best Introduction Paths:

  1. Carol Davis - Score: 0.85
     📅 Left 2022-05
     Title: Engineering Director
     Seniority: Director | Depts: Engineering, Executive
     Profile: https://linkedin.com/in/caroldavis

  2. Bob Smith - Score: 0.81
     📅 Left 2020-12
     Title: Senior Product Manager
     Seniority: Senior | Depts: Product
     Profile: https://linkedin.com/in/bobsmith

  3. Alice Johnson - Score: 0.78
     ✅ CURRENT
     Title: Senior Software Engineer
     Seniority: Senior | Depts: Engineering
     Profile: https://linkedin.com/in/alicejohnson
```

#### Step 3: Review detailed intelligence

Open `Linkedin/enriched_advanced/Google.json` to see:
- All connections (current + past)
- Grouped by department
- Grouped by seniority level
- Recent posts by these people

#### Step 4: Use the CSV for batch analysis

Open `Linkedin/introduction_intelligence.csv` in Excel:

| Company | Intro Score | Status | Contact Name | Title | Seniority | Departments |
|---------|-------------|--------|--------------|-------|-----------|-------------|
| Google  | 0.85        | Past   | Carol Davis  | Engineering Director | Director | Engineering, Executive |
| Google  | 0.81        | Past   | Bob Smith    | Senior Product Manager | Senior | Product |
| Google  | 0.78        | Current| Alice Johnson| Senior Software Engineer | Senior | Engineering |

**Sort by**:
- **Intro Score** (highest = best introduction)
- **Company** (to focus on specific targets)
- **Status** (Current employees first)

## 📊 Understanding the Scores

### Introduction Score (0.0 - 1.0)

The intro score combines multiple factors:

**Formula**:
```
Intro Score = (Recency × 40%) + (Seniority × 30%) + (Profile Quality × 20%) + (Engagement × 10%)
```

**What makes a good intro (score > 0.7)?**
- ✅ Current employee OR left recently (<2 years)
- ✅ Senior level (Director+, VP, C-Level)
- ✅ Complete LinkedIn profile with photo, summary
- ✅ Active on LinkedIn (posts regularly)

### Recency Score

| Status | Time Since Leaving | Score | Quality |
|--------|-------------------|-------|---------|
| Current | Still there | 1.0 | 🟢 Excellent |
| Alumni | < 1 year | 0.9 | 🟢 Excellent |
| Alumni | 1-2 years | 0.7 | 🟡 Good |
| Alumni | 2-5 years | 0.5 | 🟠 Fair |
| Alumni | 5+ years | 0.3 | 🔴 Weak |

### Seniority Levels (Detected from Job Titles)

| Level | Score | Examples |
|-------|-------|----------|
| C-Level | 7 | CEO, CTO, CFO, Chief, Founder |
| VP | 6 | VP, Vice President, SVP, EVP |
| Director | 5 | Director, Head of |
| Manager | 4 | Manager, Team Lead |
| Senior | 3 | Senior Engineer, Principal |
| Mid-Level | 2 | Engineer, Designer, Analyst |
| Junior | 1 | Junior, Associate, Intern |

### Department Detection

Automatically tags people by department based on job title:

- **Engineering**: Software Engineer, Developer, Architect, DevOps
- **Product**: Product Manager, PM
- **Sales**: Account Executive, Business Development
- **Marketing**: Marketing Manager, Growth, Content
- **Executive**: C-Level titles
- **Data**: Data Scientist, ML Engineer, Analytics
- And more...

## 🎯 Best Practices

### 1. Prioritize Current Employees
Current employees are your best bet for warm intros:
```
Status = "Current" AND Seniority Score >= 5
```

### 2. Recent Alumni Are Gold
People who left in the last 1-2 years still have strong connections:
```
Recency Score >= 0.7 AND Seniority = "Director" or higher
```

### 3. Match Department to Your Goal

| Your Goal | Target Department |
|-----------|-------------------|
| Technical role | Engineering, Product |
| Sales role | Sales, Business Development |
| Partnership | Executive, Business Development |
| Marketing role | Marketing, Growth |

### 4. Check Profile Quality
High profile quality = more responsive:
```
Profile Quality >= 70/100 AND Engagement = "High" or "Medium"
```

### 5. Look for Decision Makers
For partnerships or sales:
```
Seniority = "Director", "VP", or "C-Level"
```

## 📈 Advanced Use Cases

### Use Case 1: Job Search

**Goal**: Find warm intros for job applications

1. Run enrichment
2. Filter for target companies
3. Prioritize: `Current employees with Seniority >= "Manager"`
4. Reach out: "I saw you work at [Company]. I'm exploring opportunities there..."

### Use Case 2: Sales & Partnerships

**Goal**: Get introduced to decision-makers

1. Run enrichment
2. Filter for: `Seniority in ["VP", "Director", "C-Level"]`
3. Look at Department: Focus on relevant departments
4. Reach out to connections: "Would you be open to introducing me to [Person]?"

### Use Case 3: Market Research

**Goal**: Understand company movements

1. Review `enriched_advanced/[Company].json`
2. Look at `by_department` to see org structure
3. Check `past_employees` to see where people went
4. Analyze patterns in career movements

### Use Case 4: Recruiting

**Goal**: Find passive candidates

1. Filter: `Status = "Current" at competitor companies`
2. Look for: `Seniority = "Senior" or "Mid-Level"`
3. Check: `Engagement = "High"` (more responsive)
4. Warm intro through mutual connection

## 🔧 Command Line Options

### Basic Script
```bash
# Default
python Linkedin/enrich_linkedin_data.py

# Custom data directory
python Linkedin/enrich_linkedin_data.py --data-dir /path/to/data

# Show top 50 companies
python Linkedin/enrich_linkedin_data.py --top-n 50
```

### Advanced Script
```bash
# Default (full enrichment)
python Linkedin/enrich_linkedin_advanced.py

# Search for specific company
python Linkedin/enrich_linkedin_advanced.py --search "Google"

# Custom data directory
python Linkedin/enrich_linkedin_advanced.py --data-dir /path/to/data

# Show top 50 opportunities
python Linkedin/enrich_linkedin_advanced.py --top-n 50
```

## 📝 Tips for Best Results

### 1. Clean Your Data
- Ensure dates are in consistent format (YYYY-MM-DD or YYYY-MM)
- Mark current positions with `end_date: null` or `is_current: true`
- Include job titles for accurate seniority detection

### 2. Regular Updates
- Re-run enrichment when you get new connections
- Update when people change jobs
- Refresh quarterly to maintain accurate scores

### 3. Combine with Your CRM
- Export CSV files to Excel/Google Sheets
- Import into your CRM (Salesforce, HubSpot, etc.)
- Track outreach and responses

### 4. Privacy & Ethics
- ⚠️ Only use for your own network
- Don't share enriched data publicly
- Follow LinkedIn Terms of Service
- Be respectful in your outreach

## 🆘 Troubleshooting

### Problem: No profiles found
**Solution**: Check that your data files are in `Linkedin/` directory with `.json` or `.csv` extension

### Problem: All intro scores are low
**Solution**:
- Check that your data includes recent positions
- Verify dates are properly formatted
- Ensure titles are included

### Problem: Company not found
**Solution**:
- Check spelling (search is case-insensitive)
- Try company name variations (e.g., "Google" vs "Google LLC")
- Check `company_summary.csv` for actual company names in your data

### Problem: Wrong seniority detection
**Solution**:
- Seniority is detected from job titles
- Make sure titles are complete (not just "Engineer" but "Senior Software Engineer")
- Check SENIORITY_LEVELS dict in the code to see detection keywords

## 📊 Example Output Files

### introduction_intelligence.csv
```csv
Company,Intro Score,Status,Recency Score,Contact Name,Title,Seniority,Departments,Profile Quality
Google,0.85,Past,0.70,Carol Davis,Engineering Director,Director,"Engineering, Executive",85/100
Google,0.81,Past,0.70,Bob Smith,Senior Product Manager,Senior,Product,78/100
Google,0.78,Current,1.00,Alice Johnson,Senior Software Engineer,Senior,Engineering,82/100
```

### enriched_advanced/Google.json
```json
{
  "company_name": "Google LLC",
  "statistics": {
    "total_connections": 7,
    "current_employees": 4,
    "past_employees": 3
  },
  "best_intro_paths": [
    {
      "profile_name": "Carol Davis",
      "title": "Engineering Director",
      "seniority_level": "Director",
      "intro_score": 0.85,
      ...
    }
  ],
  "by_department": {
    "Engineering": [...],
    "Product": [...],
    "Executive": [...]
  },
  "by_seniority": {
    "Director": [...],
    "Senior": [...],
    "Mid-Level": [...]
  }
}
```

---

## 🚀 Quick Start Checklist

- [ ] Install requirements: `pip install pandas python-dateutil`
- [ ] Place LinkedIn data in `Linkedin/` directory
- [ ] Run: `python Linkedin/enrich_linkedin_advanced.py`
- [ ] Open `introduction_intelligence.csv` in Excel
- [ ] Sort by Intro Score (highest first)
- [ ] Identify target companies
- [ ] Search specific company: `--search "CompanyName"`
- [ ] Review detailed JSON for deep dive
- [ ] Reach out to best connections!

**Happy networking!** 🎉
