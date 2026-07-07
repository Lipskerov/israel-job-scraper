#!/usr/bin/env python3
"""
AllJobs.co.il Custom Scraper
=============================
A configurable scraper for https://www.alljobs.co.il/ that allows selection of
domains (categories), roles (positions), regions, job types, and more.

Outputs structured job listing data to CSV or JSON.

Usage:
    python3 alljobs_scraper.py --help
    python3 alljobs_scraper.py --list-categories
    python3 alljobs_scraper.py --list-regions
    python3 alljobs_scraper.py --list-types
    python3 alljobs_scraper.py --list-roles --category 235
    python3 alljobs_scraper.py --category 235 --pages 3 --output jobs.csv
    python3 alljobs_scraper.py --category 235 --role 1994 --region 1 --output jobs.json
    python3 alljobs_scraper.py --search "python developer" --pages 2 --output jobs.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

BASE_URL = "https://www.alljobs.co.il"
SEARCH_URL = f"{BASE_URL}/SearchResultsGuest.aspx"
FREE_SEARCH_URL = f"{BASE_URL}/SearchResultsGuest.aspx"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.alljobs.co.il/",
}

# Request delay between pages (seconds) - be respectful to the server
REQUEST_DELAY = 2.0

# ============================================================================
# DOMAIN CATEGORIES (תחומים)
# ============================================================================

CATEGORIES = {
    1998: {"he": "AI", "en": "AI"},
    376:  {"he": "אבטחה, שמירה וביטחון", "en": "Security and Safety"},
    431:  {"he": "אבטחת איכות QA", "en": "QA"},
    236:  {"he": "אבטחת מידע וסייבר", "en": "Cyber Security"},
    262:  {"he": "אדמיניסטרציה", "en": "Administration"},
    278:  {"he": "אומנות, בידור ומדיה", "en": "Arts, Entertainment and Media"},
    292:  {"he": "אופטיקה", "en": "Optics"},
    299:  {"he": "אופנה וטקסטיל", "en": "Fashion and Textile"},
    449:  {"he": "אחזקה ואנשי מקצוע", "en": "Maintenance and Professionals"},
    320:  {"he": "אינטרנט ודיגיטל", "en": "Internet and Digital"},
    1380: {"he": "ביוטכנולוגיה", "en": "Biotechnology"},
    366:  {"he": "ביטוח", "en": "Insurance"},
    722:  {"he": "בכירים", "en": "Senior Management"},
    383:  {"he": "בניין, בינוי ותשתיות", "en": "Construction and Infrastructure"},
    644:  {"he": "בתי קפה, מסעדות ואירועים", "en": "Cafes, Restaurants and Events"},
    1806: {"he": "דאטה", "en": "Data"},
    469:  {"he": "הוראה, חינוך והדרכה", "en": "Teaching, Education and Training"},
    969:  {"he": "הנדסה", "en": "Engineering"},
    1464: {"he": "התנדבות", "en": "Volunteering"},
    330:  {"he": "חומרה", "en": "Hardware"},
    484:  {"he": "חשמל ואלקטרוניקה", "en": "Electrical and Electronics"},
    442:  {"he": "יבוא יצוא", "en": "Import Export"},
    527:  {"he": "יופי, טיפוח וספא", "en": "Beauty and Spa"},
    1423: {"he": "יזמות", "en": "Entrepreneurship"},
    552:  {"he": "ייצור ותעשייה", "en": "Manufacturing and Industry"},
    594:  {"he": "כללי וללא ניסיון", "en": "General and No Experience"},
    576:  {"he": "כספים וכלכלה", "en": "Finance and Economics"},
    634:  {"he": "מדעי החברה", "en": "Social Sciences"},
    609:  {"he": "מדעי החיים, טבע וחקלאות", "en": "Life Sciences, Nature and Agriculture"},
    627:  {"he": "מדעים מדוייקים", "en": "Exact Sciences"},
    1805: {"he": "מוצר", "en": "Product"},
    1637: {"he": "מחסנאות", "en": "Warehousing"},
    357:  {"he": "מחשבים ורשתות", "en": "Computers and Networks"},
    493:  {"he": "מכירות", "en": "Sales"},
    1541: {"he": "מערכות מידע", "en": "Information Systems"},
    1657: {"he": "מקצועות דת", "en": "Religious Professions"},
    660:  {"he": "משאבי אנוש", "en": "Human Resources"},
    668:  {"he": "משפטים", "en": "Law"},
    676:  {"he": 'נדל"ן', "en": "Real Estate"},
    1564: {"he": "נהגים שליחים והפצה", "en": "Drivers, Couriers and Distribution"},
    1807: {"he": "ניהול ביניים", "en": "Middle Management"},
    1381: {"he": "ניתוח מערכות", "en": "Systems Analysis"},
    1439: {"he": "סטודנטים", "en": "Students"},
    714:  {"he": "ספורט, כושר ואורח חיים", "en": "Sports, Fitness and Lifestyle"},
    1498: {"he": 'עבודה בחו"ל', "en": "Work Abroad"},
    1578: {"he": "עבודה ראשונה", "en": "First Job"},
    402:  {"he": "עיצוב ותקשורת חזותית", "en": "Design and Visual Communication"},
    700:  {"he": "עריכה, תוכן וספרות", "en": "Editing, Content and Literature"},
    513:  {"he": "פרסום שיווק ויחסי ציבור", "en": "Advertising, Marketing and PR"},
    505:  {"he": "קמעונאות", "en": "Retail"},
    685:  {"he": "רכב ומכונאות", "en": "Automotive and Mechanics"},
    570:  {"he": "רכש ולוגיסטיקה", "en": "Procurement and Logistics"},
    537:  {"he": "רפואה ופארמה", "en": "Medicine and Pharma"},
    1427: {"he": "רפואה משלימה", "en": "Alternative Medicine"},
    692:  {"he": "שירות לקוחות", "en": "Customer Service"},
    235:  {"he": "תוכנה", "en": "Software"},
    654:  {"he": "תיירות ומלונאות", "en": "Tourism and Hospitality"},
    709:  {"he": "תעופה וימאות", "en": "Aviation and Maritime"},
}

# ============================================================================
# REGIONS (אזורים)
# ============================================================================

REGIONS = {
    1:  {"he": "מרכז", "en": "Central"},
    2:  {"he": "שרון", "en": "Sharon"},
    3:  {"he": "שפלה", "en": "Shfela (Lowlands)"},
    4:  {"he": "צפון", "en": "North"},
    5:  {"he": "חיפה וסביבתה", "en": "Haifa Area"},
    6:  {"he": "דרום", "en": "South"},
    7:  {"he": "ירושלים והסביבה", "en": "Jerusalem Area"},
    8:  {"he": "יהודה ושומרון", "en": "Judea and Samaria"},
    9:  {"he": "אילת והערבה", "en": "Eilat and Arava"},
    10: {"he": "עבודה היברידית", "en": "Hybrid Work"},
    11: {"he": "עבודה מהבית", "en": "Work from Home"},
}

# ============================================================================
# JOB TYPES (סוגי משרה)
# ============================================================================

JOB_TYPES = {
    1:  {"he": "משרה מלאה", "en": "Full-time"},
    2:  {"he": "משרה חלקית", "en": "Part-time"},
    3:  {"he": "עבודה זמנית", "en": "Temporary"},
    4:  {"he": "פרילנס", "en": "Freelance"},
    5:  {"he": "התמחות / סטאז'", "en": "Internship"},
    6:  {"he": "עבודה היברידית", "en": "Hybrid"},
    13: {"he": "עבודות ללא קורות חיים", "en": "No CV Required"},
    33: {"he": "מתאים גם לבני 50 פלוס", "en": "Suitable for 50+"},
    37: {"he": "לדוברי אנגלית", "en": "English Speakers"},
}


# ============================================================================
# SCRAPER CLASS
# ============================================================================

class AllJobsScraper:
    """Scraper for AllJobs.co.il job listings."""

    def __init__(self, delay: float = REQUEST_DELAY, verbose: bool = True):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.delay = delay
        self.verbose = verbose

    def _log(self, message: str):
        """Print log message if verbose mode is on."""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            self._log(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            self._log(f"Error fetching {url}: {e}")
            return None

    def _build_search_url(
        self,
        page: int = 1,
        category: Optional[int] = None,
        role: Optional[int] = None,
        region: Optional[int] = None,
        job_type: Optional[int] = None,
        search_text: Optional[str] = None,
        city: Optional[str] = None,
    ) -> str:
        """Build the search URL with given parameters."""
        params = {
            "page": page,
            "position": category or "",
            "type": job_type or "",
            "city": city or "",
            "region": region or "",
        }

        if search_text:
            params["txtsearch"] = search_text

        if role:
            params["position"] = f"{category},{role}" if category else str(role)

        # Build URL manually to handle empty params correctly
        url = f"{SEARCH_URL}?page={page}"
        if search_text:
            url += f"&txtsearch={requests.utils.quote(search_text)}"
        if category:
            url += f"&position={category}"
            if role:
                url += f",{role}"
        else:
            url += "&position="
        url += f"&type={job_type if job_type else ''}"
        url += f"&city={city if city else ''}"
        url += f"&region={region if region else ''}"

        return url

    def _parse_job_box(self, job_box) -> Optional[dict]:
        """Parse a single job box element and extract job data.
        
        The HTML structure varies between regular and premium/confidential listings.
        We use link patterns as the most reliable extraction method:
        - Title: a[href*='UploadSingle'] with class 'N'
        - Company: a[href*='Employer/HP/Default.aspx'] (first with text)
        - Location: a[href*='city='] 
        - Job type: a[href*='type='] within type section
        """
        try:
            job = {}

            # Extract Job ID from the moretext element
            id_match = re.search(r'moretext(\d+)', str(job_box))
            job["job_id"] = id_match.group(1) if id_match else ""

            # ---- TITLE ----
            # Primary method: find the link to UploadSingle (job detail page)
            title_el = job_box.select_one('a[href*="UploadSingle"]')
            if title_el:
                job["title"] = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job["job_url"] = (BASE_URL + href) if href and not href.startswith("http") else href
            else:
                # Fallback: try the .job-content-top-title selector
                title_div = job_box.select_one(".job-content-top-title")
                if title_div:
                    first_link = title_div.select_one("a")
                    job["title"] = first_link.get_text(strip=True) if first_link else ""
                    href = first_link.get("href", "") if first_link else ""
                    job["job_url"] = (BASE_URL + href) if href else ""
                else:
                    job["title"] = ""
                    job["job_url"] = ""

            # ---- COMPANY ----
            # Find links to employer pages
            company_links = job_box.select('a[href*="Employer/HP/Default.aspx"]')
            job["company"] = ""
            job["company_url"] = ""
            for cl in company_links:
                text = cl.get_text(strip=True)
                if text:  # First link with actual text is the company name
                    job["company"] = text
                    href = cl.get("href", "")
                    job["company_url"] = (BASE_URL + href) if href and not href.startswith("http") else href
                    break

            # ---- COMPANY LOGO ----
            img_el = job_box.select_one('img[src*="logo"], img[src*="Logo"], .job-content-top-img img, img[src*="employer"]')
            if not img_el:
                # Try any img inside company link
                for cl in company_links:
                    img_el = cl.select_one("img")
                    if img_el:
                        break
            job["company_logo"] = img_el["src"] if img_el and img_el.get("src") else ""

            # ---- LOCATION ----
            # Method 1: Use the location div
            location_el = job_box.select_one(".job-content-top-location")
            if location_el:
                # Get location link texts
                loc_links = location_el.select("a")
                location_parts = [a.get_text(strip=True) for a in loc_links if a.get_text(strip=True)]
                job["location"] = ", ".join(location_parts) if location_parts else location_el.get_text(strip=True).replace("מיקום המשרה:", "").strip()
                job["location_areas"] = location_parts
            else:
                # Method 2: Find links with city= parameter
                city_links = job_box.select('a[href*="city="]')
                location_parts = [a.get_text(strip=True) for a in city_links if a.get_text(strip=True) and "SearchResults" in a.get("href", "")]
                job["location"] = ", ".join(location_parts)
                job["location_areas"] = location_parts

            # ---- JOB TYPE ----
            type_el = job_box.select_one('[class*="job-content-top-type"]')
            if type_el:
                # Get the type links for clean text
                type_links = type_el.select("a")
                if type_links:
                    type_parts = [a.get_text(strip=True) for a in type_links if a.get_text(strip=True)]
                    job["job_type"] = ", ".join(type_parts)
                else:
                    type_text = type_el.get_text(" ", strip=True)
                    job["job_type"] = type_text.replace("סוג משרה:", "").strip()
            else:
                job["job_type"] = ""

            # ---- DATE POSTED ----
            date_el = job_box.select_one(".job-content-top-date")
            job["date_posted"] = date_el.get_text(strip=True) if date_el else ""

            # ---- STATUS ----
            # Status like "חברת השמה / כח אדם" or "משרה בלעדית"
            status_el = job_box.select_one(".job-content-top-status-text")
            if status_el:
                job["status"] = status_el.get_text(strip=True)
            else:
                # Check for status link (e.g., Mador links)
                mador_link = job_box.select_one('a[href*="/Mador/"]')
                job["status"] = mador_link.get_text(strip=True) if mador_link else ""

            # ---- DESCRIPTION ----
            desc_el = job_box.select_one('.job-content-top-desc')
            if desc_el:
                desc_text = desc_el.get_text("\n", strip=True)
                # Clean up common artifacts
                desc_text = re.sub(r'עוד\.{3}$', '', desc_text).strip()
                job["description"] = desc_text
            else:
                job["description"] = ""

            # ---- REQUIREMENTS ----
            req_el = job_box.select_one(".job-content-top-req")
            if req_el:
                req_text = req_el.get_text("\n", strip=True)
                job["requirements"] = re.sub(r'^דרישות:\s*', '', req_text).strip()
            else:
                job["requirements"] = ""

            # ---- CONDITIONS ----
            cond_el = job_box.select_one(".job-content-top-conditions")
            if cond_el:
                job["conditions"] = cond_el.get_text(strip=True).replace("תנאים נוספים:", "").strip()
            else:
                job["conditions"] = ""

            # ---- DIRECT URL ----
            if job["job_id"]:
                job["direct_url"] = f"{BASE_URL}/Search/UploadSingle.aspx?JobID={job['job_id']}"

            return job

        except Exception as e:
            self._log(f"Error parsing job box: {e}")
            return None

    def _get_total_results(self, soup: BeautifulSoup) -> int:
        """Extract total number of results from the page."""
        try:
            # The total results text appears as "נמצאו X משרות" in the page body
            full_text = soup.get_text()
            match = re.search(r'נמצאו\s*([\d,]+)\s*משרות', full_text)
            if match:
                return int(match.group(1).replace(",", ""))
            # Fallback: any "X משרות" pattern
            match = re.search(r'([\d,]+)\s*משרות', full_text)
            if match:
                return int(match.group(1).replace(",", ""))
        except Exception:
            pass
        return 0

    def scrape_jobs(
        self,
        category: Optional[int] = None,
        role: Optional[int] = None,
        region: Optional[int] = None,
        job_type: Optional[int] = None,
        search_text: Optional[str] = None,
        city: Optional[str] = None,
        max_pages: int = 5,
    ) -> list[dict]:
        """
        Scrape job listings with the given filters.

        Args:
            category: Category/domain ID (see CATEGORIES dict)
            role: Role/position ID within the category
            region: Region ID (see REGIONS dict)
            job_type: Job type ID (see JOB_TYPES dict)
            search_text: Free text search query
            city: City name filter
            max_pages: Maximum number of pages to scrape

        Returns:
            List of job dictionaries
        """
        all_jobs = []
        total_results = 0

        for page_num in range(1, max_pages + 1):
            url = self._build_search_url(
                page=page_num,
                category=category,
                role=role,
                region=region,
                job_type=job_type,
                search_text=search_text,
                city=city,
            )

            soup = self._get_page(url)
            if not soup:
                self._log(f"Failed to fetch page {page_num}, stopping.")
                break

            # Get total results on first page
            if page_num == 1:
                total_results = self._get_total_results(soup)
                self._log(f"Total results found: {total_results:,}")

            # Find all job boxes
            job_boxes = soup.select(".job-box")
            if not job_boxes:
                self._log(f"No jobs found on page {page_num}, stopping.")
                break

            self._log(f"Page {page_num}: Found {len(job_boxes)} job listings")

            for box in job_boxes:
                job = self._parse_job_box(box)
                if job and job.get("job_id"):
                    all_jobs.append(job)

            # Check if there are more pages
            pagination = soup.select("a[href*='page=']")
            next_page_exists = any(
                f"page={page_num + 1}" in (a.get("href", "") or "")
                for a in pagination
            )

            if not next_page_exists and page_num < max_pages:
                self._log(f"No more pages after page {page_num}.")
                break

            # Respectful delay between requests
            if page_num < max_pages:
                time.sleep(self.delay)

        self._log(f"Scraping complete. Total jobs collected: {len(all_jobs)}")
        return all_jobs

    def list_roles_for_category(self, category_id: int) -> list[dict]:
        """
        Fetch available roles/positions for a given category.
        Roles are listed in the sidebar with title attributes like 'דרושים XXX'.
        """
        url = self._build_search_url(page=1, category=category_id)
        soup = self._get_page(url)
        if not soup:
            return []

        roles = []
        seen_ids = set()

        # Method 1: Find sidebar role links with title="דרושים XXX"
        role_links = soup.select('a[title^="דרושים "]')
        for link in role_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            title = link.get("title", "")

            # Must be a search results link with a position parameter
            if "SearchResults" not in href or "position=" not in href:
                continue

            # Extract position ID
            match = re.search(r'position=(\d+)', href)
            if not match:
                continue

            role_id = int(match.group(1))
            if role_id == category_id or role_id in seen_ids:
                continue

            seen_ids.add(role_id)

            # Extract count if present in text
            count_match = re.search(r'\((\d+)\)', text)
            count = int(count_match.group(1)) if count_match else 0
            name = re.sub(r'\s*\(\d+\)\s*$', '', text).strip()

            # Skip generic/navigation links
            if name and name not in ('משרות חברה', 'משרות פנויות'):
                roles.append({"id": role_id, "name": name, "count": count})

        return roles


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def save_to_csv(jobs: list[dict], filepath: str):
    """Save job listings to a CSV file."""
    if not jobs:
        print("No jobs to save.")
        return

    # Define column order
    columns = [
        "job_id", "title", "company", "location", "job_type",
        "date_posted", "status", "description", "requirements",
        "conditions", "job_url", "company_url", "direct_url",
    ]

    # Add any extra columns from the data
    all_keys = set()
    for job in jobs:
        all_keys.update(job.keys())
    extra_cols = sorted(all_keys - set(columns) - {"location_areas", "company_logo"})
    columns.extend(extra_cols)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for job in jobs:
            # Convert list fields to strings
            row = dict(job)
            if "location_areas" in row:
                row["location_areas"] = ", ".join(row["location_areas"])
            writer.writerow(row)

    print(f"Saved {len(jobs)} jobs to {filepath}")


def save_to_json(jobs: list[dict], filepath: str):
    """Save job listings to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(jobs)} jobs to {filepath}")


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def print_table(headers: list[str], rows: list[list], col_widths: Optional[list[int]] = None):
    """Print a formatted table."""
    if not col_widths:
        col_widths = []
        for i, h in enumerate(headers):
            max_w = len(h)
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(str(row[i])))
            col_widths.append(min(max_w, 50))

    # Header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)
    print(header_line)
    print(separator)

    # Rows
    for row in rows:
        line = " | ".join(str(row[i]).ljust(col_widths[i])[:col_widths[i]] for i in range(len(headers)))
        print(line)


def list_categories():
    """Display all available categories."""
    print("\n=== Available Categories (תחומים) ===\n")
    rows = []
    for cat_id, names in sorted(CATEGORIES.items(), key=lambda x: x[1]["en"]):
        rows.append([str(cat_id), names["en"], names["he"]])
    print_table(["ID", "English Name", "Hebrew Name"], rows, [6, 45, 40])
    print(f"\nTotal: {len(CATEGORIES)} categories")


def list_regions():
    """Display all available regions."""
    print("\n=== Available Regions (אזורים) ===\n")
    rows = []
    for reg_id, names in sorted(REGIONS.items()):
        rows.append([str(reg_id), names["en"], names["he"]])
    print_table(["ID", "English Name", "Hebrew Name"], rows, [4, 30, 25])


def list_job_types():
    """Display all available job types."""
    print("\n=== Available Job Types (סוגי משרה) ===\n")
    rows = []
    for type_id, names in sorted(JOB_TYPES.items()):
        rows.append([str(type_id), names["en"], names["he"]])
    print_table(["ID", "English Name", "Hebrew Name"], rows, [4, 30, 30])


def list_roles(category_id: int):
    """Display available roles for a category."""
    cat_info = CATEGORIES.get(category_id)
    if not cat_info:
        print(f"Error: Category ID {category_id} not found.")
        return

    print(f"\n=== Roles for: {cat_info['en']} ({cat_info['he']}) ===\n")
    print("Fetching roles from AllJobs.co.il...")

    scraper = AllJobsScraper(verbose=False)
    roles = scraper.list_roles_for_category(category_id)

    if not roles:
        print("No specific roles found for this category.")
        return

    rows = []
    for role in sorted(roles, key=lambda x: x["name"]):
        rows.append([str(role["id"]), role["name"], str(role["count"])])
    print_table(["ID", "Role Name", "Count"], rows, [6, 50, 8])
    print(f"\nTotal: {len(roles)} roles")


def display_results_summary(jobs: list[dict]):
    """Display a summary of scraped results."""
    if not jobs:
        print("\nNo jobs found.")
        return

    print(f"\n=== Results Summary ===")
    print(f"Total jobs scraped: {len(jobs)}")

    # Company distribution
    companies = {}
    for job in jobs:
        comp = job.get("company", "Unknown") or "Unknown"
        companies[comp] = companies.get(comp, 0) + 1

    print(f"\nTop companies hiring:")
    for comp, count in sorted(companies.items(), key=lambda x: -x[1])[:10]:
        print(f"  {comp}: {count} positions")

    # Location distribution
    locations = {}
    for job in jobs:
        loc = job.get("location", "Unknown") or "Unknown"
        locations[loc] = locations.get(loc, 0) + 1

    print(f"\nTop locations:")
    for loc, count in sorted(locations.items(), key=lambda x: -x[1])[:10]:
        print(f"  {loc}: {count} positions")

    # Sample jobs
    print(f"\n--- Sample Jobs (first 5) ---\n")
    for i, job in enumerate(jobs[:5], 1):
        print(f"{i}. {job.get('title', 'N/A')}")
        print(f"   Company:  {job.get('company', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        print(f"   Type:     {job.get('job_type', 'N/A')}")
        print(f"   Posted:   {job.get('date_posted', 'N/A')}")
        print()


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def interactive_mode():
    """Run the scraper in interactive mode with guided selection."""
    print("\n" + "=" * 60)
    print("  AllJobs.co.il Interactive Scraper")
    print("=" * 60)

    scraper = AllJobsScraper()

    # Step 1: Choose search mode
    print("\nSearch Mode:")
    print("  1. Search by Category (Domain)")
    print("  2. Free Text Search")
    print("  3. Browse All Jobs")

    mode = input("\nSelect mode (1-3): ").strip()

    category = None
    role = None
    search_text = None

    if mode == "1":
        # Show categories
        print("\n--- Available Categories ---\n")
        cat_list = sorted(CATEGORIES.items(), key=lambda x: x[1]["en"])
        for i, (cat_id, names) in enumerate(cat_list, 1):
            print(f"  {i:2d}. [{cat_id:5d}] {names['en']:<45s} {names['he']}")

        cat_input = input("\nEnter category ID (number): ").strip()
        try:
            category = int(cat_input)
            if category not in CATEGORIES:
                print(f"Invalid category ID: {category}")
                return
        except ValueError:
            print("Invalid input.")
            return

        # Ask about specific role
        print(f"\nSelected: {CATEGORIES[category]['en']}")
        want_role = input("Filter by specific role? (y/n): ").strip().lower()
        if want_role == "y":
            print("\nFetching available roles...")
            roles = scraper.list_roles_for_category(category)
            if roles:
                for r in sorted(roles, key=lambda x: x["name"]):
                    print(f"  [{r['id']:5d}] {r['name']:<50s} ({r['count']} jobs)")
                role_input = input("\nEnter role ID (or press Enter to skip): ").strip()
                if role_input:
                    try:
                        role = int(role_input)
                    except ValueError:
                        print("Invalid input, skipping role filter.")
            else:
                print("No specific roles available.")

    elif mode == "2":
        search_text = input("\nEnter search text: ").strip()
        if not search_text:
            print("No search text provided.")
            return

    # Step 2: Region filter
    print("\n--- Region Filter (optional) ---")
    for reg_id, names in sorted(REGIONS.items()):
        print(f"  [{reg_id:2d}] {names['en']:<30s} {names['he']}")

    region = None
    reg_input = input("\nEnter region ID (or press Enter to skip): ").strip()
    if reg_input:
        try:
            region = int(reg_input)
        except ValueError:
            pass

    # Step 3: Job type filter
    print("\n--- Job Type Filter (optional) ---")
    for type_id, names in sorted(JOB_TYPES.items()):
        print(f"  [{type_id:2d}] {names['en']:<30s} {names['he']}")

    job_type = None
    type_input = input("\nEnter job type ID (or press Enter to skip): ").strip()
    if type_input:
        try:
            job_type = int(type_input)
        except ValueError:
            pass

    # Step 4: Number of pages
    pages_input = input("\nMax pages to scrape (default 5): ").strip()
    max_pages = 5
    if pages_input:
        try:
            max_pages = int(pages_input)
        except ValueError:
            pass

    # Step 5: Output format
    print("\nOutput format:")
    print("  1. CSV")
    print("  2. JSON")
    print("  3. Display only (no file)")

    format_input = input("\nSelect format (1-3, default 1): ").strip() or "1"

    output_file = None
    if format_input in ("1", "2"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format_input == "1":
            output_file = f"alljobs_results_{timestamp}.csv"
        else:
            output_file = f"alljobs_results_{timestamp}.json"

        custom_name = input(f"Output filename (default: {output_file}): ").strip()
        if custom_name:
            output_file = custom_name

    # Run the scraper
    print("\n" + "=" * 60)
    print("Starting scraper...")
    print("=" * 60 + "\n")

    jobs = scraper.scrape_jobs(
        category=category,
        role=role,
        region=region,
        job_type=job_type,
        search_text=search_text,
        max_pages=max_pages,
    )

    # Display summary
    display_results_summary(jobs)

    # Save output
    if output_file and jobs:
        if output_file.endswith(".json"):
            save_to_json(jobs, output_file)
        else:
            save_to_csv(jobs, output_file)


# ============================================================================
# MAIN / CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AllJobs.co.il Custom Scraper - Scrape job listings with configurable filters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-categories                    List all available categories
  %(prog)s --list-regions                       List all available regions
  %(prog)s --list-types                         List all available job types
  %(prog)s --list-roles --category 235          List roles for Software category
  %(prog)s --category 235 --pages 3             Scrape Software jobs (3 pages)
  %(prog)s --category 235 --role 1994           Scrape Backend Engineer jobs
  %(prog)s --search "python developer"          Free text search
  %(prog)s --category 969 --region 1 -o eng.csv Scrape Engineering in Central region
  %(prog)s --interactive                        Run in interactive mode
        """,
    )

    # List commands
    list_group = parser.add_argument_group("List Options")
    list_group.add_argument("--list-categories", action="store_true",
                           help="List all available domain categories")
    list_group.add_argument("--list-regions", action="store_true",
                           help="List all available regions")
    list_group.add_argument("--list-types", action="store_true",
                           help="List all available job types")
    list_group.add_argument("--list-roles", action="store_true",
                           help="List roles for a category (requires --category)")

    # Search filters
    filter_group = parser.add_argument_group("Search Filters")
    filter_group.add_argument("-c", "--category", type=int, default=None,
                             help="Category/domain ID (use --list-categories to see options)")
    filter_group.add_argument("-r", "--role", type=int, default=None,
                             help="Role/position ID (use --list-roles to see options)")
    filter_group.add_argument("--region", type=int, default=None,
                             help="Region ID (use --list-regions to see options)")
    filter_group.add_argument("-t", "--type", type=int, default=None,
                             help="Job type ID (use --list-types to see options)")
    filter_group.add_argument("-s", "--search", type=str, default=None,
                             help="Free text search query")
    filter_group.add_argument("--city", type=str, default=None,
                             help="City name filter")

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("-o", "--output", type=str, default=None,
                             help="Output file path (.csv or .json)")
    output_group.add_argument("-p", "--pages", type=int, default=5,
                             help="Maximum number of pages to scrape (default: 5)")
    output_group.add_argument("--delay", type=float, default=REQUEST_DELAY,
                             help=f"Delay between requests in seconds (default: {REQUEST_DELAY})")
    output_group.add_argument("-q", "--quiet", action="store_true",
                             help="Suppress progress output")

    # Interactive mode
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Run in interactive mode with guided selection")

    args = parser.parse_args()

    # Handle list commands
    if args.list_categories:
        list_categories()
        return

    if args.list_regions:
        list_regions()
        return

    if args.list_types:
        list_job_types()
        return

    if args.list_roles:
        if not args.category:
            print("Error: --list-roles requires --category <ID>")
            print("Use --list-categories to see available category IDs.")
            return
        list_roles(args.category)
        return

    # Interactive mode
    if args.interactive:
        interactive_mode()
        return

    # If no search criteria provided, show help
    if not args.category and not args.search and not args.type and not args.region:
        parser.print_help()
        print("\nTip: Use --interactive for guided mode, or --list-categories to see options.")
        return

    # Run scraper
    scraper = AllJobsScraper(delay=args.delay, verbose=not args.quiet)

    # Display search info
    search_info = []
    if args.category:
        cat_name = CATEGORIES.get(args.category, {}).get("en", f"ID:{args.category}")
        search_info.append(f"Category: {cat_name}")
    if args.role:
        search_info.append(f"Role ID: {args.role}")
    if args.region:
        reg_name = REGIONS.get(args.region, {}).get("en", f"ID:{args.region}")
        search_info.append(f"Region: {reg_name}")
    if args.type:
        type_name = JOB_TYPES.get(args.type, {}).get("en", f"ID:{args.type}")
        search_info.append(f"Type: {type_name}")
    if args.search:
        search_info.append(f"Search: '{args.search}'")

    if not args.quiet:
        print(f"\n{'='*60}")
        print(f"  AllJobs.co.il Scraper")
        print(f"{'='*60}")
        print(f"  Filters: {' | '.join(search_info)}")
        print(f"  Max pages: {args.pages}")
        print(f"{'='*60}\n")

    jobs = scraper.scrape_jobs(
        category=args.category,
        role=args.role,
        region=args.region,
        job_type=args.type,
        search_text=args.search,
        city=args.city,
        max_pages=args.pages,
    )

    # Display summary
    if not args.quiet:
        display_results_summary(jobs)

    # Save output
    if args.output and jobs:
        if args.output.endswith(".json"):
            save_to_json(jobs, args.output)
        else:
            save_to_csv(jobs, args.output)
    elif not args.output and jobs:
        # Default: save to CSV with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = f"alljobs_results_{timestamp}.csv"
        save_to_csv(jobs, default_file)


if __name__ == "__main__":
    main()
