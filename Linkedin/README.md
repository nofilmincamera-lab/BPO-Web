# LinkedIn Data Enrichment Tool

A comprehensive tool for enriching LinkedIn profile data with company cross-referencing, employee analytics, and post aggregation.

## Features

✨ **What This Tool Does:**

- 📊 **Company Cross-Referencing**: Analyzes all companies from work experiences across all profiles
- 👥 **Employee Analytics**: Counts how many people you know who currently work or previously worked at each company
- 📈 **Connection Tracking**: Tracks both current and past employees for each company
- 📝 **Post Aggregation**: Collects and organizes recent posts by company affiliation
- 📄 **Multiple Report Formats**: Generates summary CSVs and detailed JSON files

## Quick Start

### 1. Add Your LinkedIn Data

Place your LinkedIn scrape data files in the `Linkedin/` directory. Supported formats:
- JSON files (`.json`)
- CSV files (`.csv`)

### 2. Run the Enrichment

```bash
python Linkedin/enrich_linkedin_data.py
```

### 3. View Results

The tool generates three types of outputs:

1. **`company_summary.csv`** - Quick overview of all companies
2. **`master_connections.csv`** - All person-company relationships
3. **`enriched/`** - Detailed JSON files for each company

## Data Format

### Expected Profile Structure

The tool is flexible and supports various field names. Here are the common formats:

#### JSON Format

```json
[
  {
    "id": "person-123",
    "name": "John Doe",
    "url": "https://linkedin.com/in/johndoe",
    "experience": [
      {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "start_date": "2020-01",
        "end_date": "2022-12",
        "is_current": false
      },
      {
        "company": "TechStart Inc",
        "title": "Senior Engineer",
        "start_date": "2023-01",
        "end_date": null,
        "is_current": true
      }
    ],
    "posts": [
      {
        "date": "2024-11-01",
        "text": "Excited to share our latest product launch!",
        "url": "https://linkedin.com/posts/...",
        "likes": 150,
        "comments": 20
      }
    ]
  }
]
```

#### CSV Format

For CSV files, work experience and posts can be stored as JSON strings:

```csv
id,name,url,experience,posts
person-123,John Doe,https://linkedin.com/in/johndoe,"[{""company"":""Acme Corp"",""title"":""Software Engineer""}]","[{""date"":""2024-11-01""}]"
```

### Supported Field Names

The tool automatically recognizes various common field names:

**Profile Fields:**
- `id`, `profile_id`
- `name`, `full_name`, `fullName`
- `url`, `profile_url`, `linkedin_url`

**Work Experience Fields:**
- `experience`, `experiences`, `work_experience`, `positions`, `employment`, `work_history`

**Company Fields (within experience):**
- `company`, `company_name`, `companyName`
- `title`, `position`
- `start_date`, `startDate`, `from`
- `end_date`, `endDate`, `to`
- `is_current`, `isCurrent`

**Posts Fields:**
- `posts`, `activities`, `recent_posts`, `activity`

## Output Files

### 1. Company Summary CSV

`Linkedin/company_summary.csv` contains:

| Column | Description |
|--------|-------------|
| Company Name | Original company name from profiles |
| Normalized Name | Standardized version for matching |
| Current Employees | Count of people currently working there |
| Past Employees | Count of people who previously worked there |
| Total Connections | Total number of connections to this company |
| Recent Posts | Number of posts associated with this company |

### 2. Master Connections CSV

`Linkedin/master_connections.csv` contains:

| Column | Description |
|--------|-------------|
| Company | Company name |
| Normalized Company | Standardized company name |
| Status | Current or Past |
| Person Name | Name of the connection |
| Person Profile | LinkedIn URL |
| Title | Job title at this company |
| Start Date | When they started |
| End Date | When they left (empty if current) |
| Duration | How long they worked there |

### 3. Detailed Company JSON Files

`Linkedin/enriched/[Company Name].json` contains:

```json
{
  "company_name": "Acme Corp",
  "normalized_name": "acme corp",
  "statistics": {
    "total_current_employees": 5,
    "total_past_employees": 12,
    "total_connections": 17,
    "total_posts": 8
  },
  "current_employees": [...],
  "past_employees": [...],
  "recent_posts": [...]
}
```

## Advanced Usage

### Custom Data Directory

```bash
python Linkedin/enrich_linkedin_data.py --data-dir /path/to/linkedin/data
```

### Show More Top Companies

```bash
python Linkedin/enrich_linkedin_data.py --top-n 50
```

## Company Name Normalization

The tool automatically normalizes company names to improve matching:

- Converts to lowercase
- Removes common suffixes (Inc, LLC, Ltd, Corp, etc.)
- Removes special characters
- Collapses multiple spaces

**Examples:**
- "Acme Corporation, Inc." → "acme corporation"
- "TechStart LLC" → "techstart"
- "Big Co." → "big co"

## Use Cases

### 1. Job Search Intelligence
- See which companies have the most connections in your network
- Identify companies where you know current employees (warm introductions!)
- Track companies where you have alumni connections

### 2. Sales & Business Development
- Identify target companies with existing relationships
- Find decision-makers at companies through your network
- Track engagement through posts and activities

### 3. Recruiting
- Find companies with relevant talent pools
- Identify patterns in career movements
- Track alumni networks from specific companies

### 4. Market Research
- Analyze company trends based on employee movements
- Track post activity and engagement by company
- Understand network distribution across industries

## Troubleshooting

### No profiles found

**Problem**: `❌ No profiles found!`

**Solution**: Make sure your LinkedIn data files are in the `Linkedin/` directory with `.json` or `.csv` extensions.

### Missing work experience

**Problem**: Companies showing 0 connections

**Solution**: Check that your data includes work experience fields. The tool looks for: `experience`, `experiences`, `work_experience`, `positions`, `employment`, or `work_history`.

### Incorrect current/past employee counts

**Problem**: All employees showing as "past" or "current"

**Solution**: Ensure your data has proper end date indicators:
- For current positions: `end_date` should be `null`, empty, or "Present"/"Current"
- Or set `is_current: true`

## Data Privacy

⚠️ **Important**: This tool is designed for personal network analysis. Always:
- Use data from your own LinkedIn network only
- Follow LinkedIn's Terms of Service
- Respect data privacy and confidentiality
- Don't share enriched data publicly without consent

## Requirements

```bash
pip install pandas
```

## Support

For issues or questions:
1. Check your data format matches the examples above
2. Review error messages for specific field names
3. Ensure all required files are in the correct directory

## Examples

### Example Output

```
🏆 TOP 20 COMPANIES BY TOTAL CONNECTIONS
================================================================================

Rank  Company                                  Current   Past      Total     Posts
--------------------------------------------------------------------------------
1     Google                                   15        42        57        12
2     Microsoft                                12        38        50        8
3     Amazon                                   18        28        46        15
4     Meta                                     8         32        40        6
5     Apple                                    6         24        30        4
...
```

## Next Steps

After enrichment:

1. **Analyze the Results**: Open `company_summary.csv` in Excel/Google Sheets
2. **Explore Connections**: Review `master_connections.csv` to see specific people
3. **Deep Dive**: Check individual company JSON files in `enriched/` for detailed data
4. **Integrate**: Use the JSON output for further analysis or visualization tools

---

**Happy Networking!** 🎉
