# AllJobs.co.il Custom Scraper

A configurable Python scraper for [AllJobs.co.il](https://www.alljobs.co.il/) — Israel's largest job board. This tool allows you to filter by **domains** (categories), **roles** (positions), **regions**, **job types**, and free text search, then export structured job data to **CSV** or **JSON**.

---

## Features

- **58 domain categories** (Software, Engineering, Sales, Finance, etc.)
- **Role/position filtering** within each category
- **11 region filters** including Work from Home and Hybrid
- **9 job type filters** (Full-time, Part-time, Freelance, Internship, etc.)
- **Free text search** support
- **Multi-page scraping** with configurable page limits
- **CSV and JSON export** with UTF-8 support (Excel-compatible)
- **Interactive mode** with guided step-by-step selection
- **Command-line interface** for scripting and automation
- **Respectful rate limiting** (configurable delay between requests)

---

## Requirements

- Python 3.9+
- `requests`
- `beautifulsoup4`

Install dependencies:

```bash
pip install requests beautifulsoup4
```

---

## Quick Start

```bash
# List all available categories
python3 alljobs_scraper.py --list-categories

# Scrape Software jobs (first 3 pages) to CSV
python3 alljobs_scraper.py --category 235 --pages 3 --output software_jobs.csv

# Run interactive mode
python3 alljobs_scraper.py --interactive
```

---

## Usage

### List Available Options

```bash
# List all 58 domain categories with IDs
python3 alljobs_scraper.py --list-categories

# List all regions
python3 alljobs_scraper.py --list-regions

# List all job types
python3 alljobs_scraper.py --list-types

# List roles for a specific category (e.g., Software = 235)
python3 alljobs_scraper.py --list-roles --category 235
```

### Scrape Jobs

```bash
# By category (Software)
python3 alljobs_scraper.py --category 235 --pages 5 --output jobs.csv

# By category + specific role (Software > Data Analyst)
python3 alljobs_scraper.py --category 235 --role 1732 --output data_analyst.csv

# By category + region (Engineering in Central Israel)
python3 alljobs_scraper.py --category 969 --region 1 --output eng_central.csv

# By category + job type (Software, Full-time only)
python3 alljobs_scraper.py --category 235 --type 1 --output fulltime_sw.csv

# Free text search
python3 alljobs_scraper.py --search "python developer" --pages 3 --output python.csv

# Combined filters (Software + Central + Full-time)
python3 alljobs_scraper.py --category 235 --region 1 --type 1 --pages 5 --output filtered.csv

# JSON output
python3 alljobs_scraper.py --category 235 --pages 2 --output jobs.json

# Quiet mode (suppress progress output)
python3 alljobs_scraper.py --category 235 --pages 3 --output jobs.csv --quiet

# Custom delay between requests (default: 2 seconds)
python3 alljobs_scraper.py --category 235 --pages 10 --delay 3.0 --output jobs.csv
```

### Interactive Mode

```bash
python3 alljobs_scraper.py --interactive
```

This launches a guided step-by-step wizard that walks you through:
1. Choosing search mode (by category, free text, or browse all)
2. Selecting a domain category
3. Optionally filtering by specific role
4. Optionally filtering by region
5. Optionally filtering by job type
6. Setting the number of pages to scrape
7. Choosing output format (CSV, JSON, or display only)

---

## Category Reference (Most Popular)

| ID | Category (English) | Category (Hebrew) |
|----|-------------------|-------------------|
| 235 | Software | תוכנה |
| 969 | Engineering | הנדסה |
| 493 | Sales | מכירות |
| 576 | Finance and Economics | כספים וכלכלה |
| 320 | Internet and Digital | אינטרנט ודיגיטל |
| 660 | Human Resources | משאבי אנוש |
| 236 | Cyber Security | אבטחת מידע וסייבר |
| 431 | QA | אבטחת איכות QA |
| 1806 | Data | דאטה |
| 1998 | AI | AI |
| 513 | Advertising, Marketing and PR | פרסום שיווק ויחסי ציבור |
| 692 | Customer Service | שירות לקוחות |
| 402 | Design and Visual Communication | עיצוב ותקשורת חזותית |
| 668 | Law | משפטים |
| 537 | Medicine and Pharma | רפואה ופארמה |

Use `--list-categories` to see all 58 categories.

---

## Region Reference

| ID | Region (English) | Region (Hebrew) |
|----|-----------------|-----------------|
| 1 | Central | מרכז |
| 2 | Sharon | שרון |
| 3 | Shfela (Lowlands) | שפלה |
| 4 | North | צפון |
| 5 | Haifa Area | חיפה וסביבתה |
| 6 | South | דרום |
| 7 | Jerusalem Area | ירושלים והסביבה |
| 8 | Judea and Samaria | יהודה ושומרון |
| 9 | Eilat and Arava | אילת והערבה |
| 10 | Hybrid Work | עבודה היברידית |
| 11 | Work from Home | עבודה מהבית |

---

## Job Type Reference

| ID | Type (English) | Type (Hebrew) |
|----|---------------|---------------|
| 1 | Full-time | משרה מלאה |
| 2 | Part-time | משרה חלקית |
| 3 | Temporary | עבודה זמנית |
| 4 | Freelance | פרילנס |
| 5 | Internship | התמחות / סטאז' |
| 6 | Hybrid | עבודה היברידית |
| 13 | No CV Required | עבודות ללא קורות חיים |
| 33 | Suitable for 50+ | מתאים גם לבני 50 פלוס |
| 37 | English Speakers | לדוברי אנגלית |

---

## Output Fields

Each scraped job contains the following fields:

| Field | Description |
|-------|-------------|
| `job_id` | Unique AllJobs job ID |
| `title` | Job title |
| `company` | Company name |
| `location` | Job location(s) |
| `job_type` | Employment type(s) |
| `date_posted` | When the job was posted (relative time) |
| `status` | Special status (e.g., "Staffing Agency") |
| `description` | Full job description |
| `requirements` | Job requirements |
| `conditions` | Additional conditions/benefits |
| `job_url` | Link to full job posting |
| `company_url` | Link to company profile |
| `direct_url` | Direct link to job page |
| `location_areas` | List of individual location areas |
| `company_logo` | Company logo image URL |

---

## Python API Usage

You can also use the scraper as a Python library:

```python
from alljobs_scraper import AllJobsScraper, CATEGORIES, REGIONS, JOB_TYPES
from alljobs_scraper import save_to_csv, save_to_json

# Initialize scraper
scraper = AllJobsScraper(delay=2.0, verbose=True)

# Scrape Software jobs in Central Israel
jobs = scraper.scrape_jobs(
    category=235,       # Software
    region=1,           # Central
    job_type=1,         # Full-time
    max_pages=3,
)

# Save results
save_to_csv(jobs, "software_central.csv")
save_to_json(jobs, "software_central.json")

# List available roles for a category
roles = scraper.list_roles_for_category(235)
for role in roles:
    print(f"{role['id']}: {role['name']}")

# Access category/region/type metadata
for cat_id, names in CATEGORIES.items():
    print(f"{cat_id}: {names['en']} / {names['he']}")
```

---

## Notes

- The scraper includes a **2-second delay** between page requests by default to be respectful to the server. You can adjust this with `--delay`.
- Some job listings are **confidential** (חברה חסויה) and won't have a company name.
- The site shows approximately **20-30 jobs per page**.
- Free text search results may include jobs from all categories, not just exact keyword matches.
- CSV files are saved with **UTF-8 BOM encoding** for proper Hebrew display in Excel.

---

## License

This tool is for personal use and research purposes only. Please respect AllJobs.co.il's terms of service and use the scraper responsibly.
