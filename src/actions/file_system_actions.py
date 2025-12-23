"File system and PDF helpers"
import os
import glob
import re
import shutil
import pdfplumber
def list_files_in_dir(path, pattern="*"):
    """Return list of filenames in `path` matching `pattern` (glob)."""
    import os
    import glob

    if not path:
        return []
    if not os.path.exists(path):
        return []
    search = os.path.join(path, pattern)
    files = glob.glob(search)
    # return basenames
    return [os.path.basename(f) for f in files]
def ensure_year_folders_exist(base_dir, years):
    """Ensure a folder exists for each year under `base_dir`. Returns tuple (created, existing) lists of full paths."""
    import os

    created = []
    existing = []
    if not base_dir:
        return created, existing
    for y in years:
        folder = os.path.join(base_dir, str(y))
        if os.path.exists(folder):
            existing.append(folder)
        else:
            os.makedirs(folder, exist_ok=True)
            created.append(folder)
    return created, existing
def ensure_month_folders_exist(base_dir, month_year_pairs):
    """Ensure folders exist for each (Month, Year) pair under base_dir/Year/Month.

    Returns (created, existing) lists of full paths.
    """
    import os

    created = []
    existing = []
    if not base_dir:
        return created, existing
    for month, year in month_year_pairs:
        year_folder = os.path.join(base_dir, year)
        month_folder = os.path.join(year_folder, month)
        if os.path.exists(month_folder):
            existing.append(month_folder)
        else:
            os.makedirs(month_folder, exist_ok=True)
            created.append(month_folder)
    return created, existing
def ensure_subfolders_in_months(base_dir, month_year_pairs, subfolders):
    """Ensure each month folder has the listed `subfolders` (e.g. 'DSG','Schedule','Youth').

    Returns (created, existing) lists of full paths for subfolders.
    """
    import os

    created = []
    existing = []
    if not base_dir:
        return created, existing
    for month, year in month_year_pairs:
        month_folder = os.path.join(base_dir, year, month)
        for sub in subfolders:
            p = os.path.join(month_folder, sub)
            if os.path.exists(p):
                existing.append(p)
            else:
                os.makedirs(p, exist_ok=True)
                created.append(p)
    return created, existing
def save_url_to_path(url, dest_folder, filename, driver=None, overwrite=False):
    """Download `url` to `os.path.join(dest_folder, filename)`.

    - Creates `dest_folder` if missing.
    - Skips download if file exists and `overwrite` is False.
    - Tries `requests` first; on failure (or missing auth) falls back to using Selenium cookies with urllib.
    - Returns (True, reason) on success, (False, reason) on failure.
    """
    import os
    import shutil

    path = os.path.join(dest_folder, filename)
    try:
        os.makedirs(dest_folder, exist_ok=True)
    except Exception as e:
        return False, f"mkdir_failed: {e}"

    if os.path.exists(path) and not overwrite:
        return False, "exists"

    # First attempt: requests
    try:
        import requests

        with requests.Session() as s:
            resp = s.get(url, stream=True, timeout=30)
            if resp.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in resp.iter_content(1024 * 8):
                        if chunk:
                            f.write(chunk)
                return True, 'downloaded_via_requests'
            # if not OK, continue to fallback
    except Exception:
        pass

    # Fallback: try urllib with cookies from Selenium (if provided)
    try:
        import urllib.request

        headers = {'User-Agent': 'Mozilla/5.0'}
        if driver is not None:
            try:
                cookies = driver.get_cookies()
                cookie_header = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                headers['Cookie'] = cookie_header
            except Exception:
                pass
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp, open(path, 'wb') as out:
            shutil.copyfileobj(resp, out)
        return True, 'downloaded_via_urllib'
    except Exception as e:
        # cleanup partial file
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        return False, f'failed: {e}'


# -----------------------------
# PDF text extraction utilities
# -----------------------------
def extract_text_from_pdf(path: str) -> str:
    """Uses coordinate-based table extraction to preserve the grid structure."""
    if not path or not os.path.exists(path):
        return ""

    formatted_text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                # Extract the table using the visible lines in your PDF
                table = page.extract_table({
                    "vertical_strategy": "lines", 
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                })
                
                if table:
                    for row in table:
                        # Join each cell with a unique delimiter to preserve columns
                        # Filter out None values and clean up extra newlines
                        clean_row = [" ".join((cell or "").split()) for cell in row]
                        formatted_text += " | ".join(clean_row) + "\n"
                else:
                    # Fallback if lines aren't detected
                    formatted_text += page.extract_text() or ""
        return formatted_text
    except Exception as e:
        print(f"Coordinate extraction failed: {e}")
        return ""

def find_date_and_location_for_query(text: str, query: str):
    import re
    if not text or not query:
        return []

    # Get the structure first
    meta = extract_schedule_metadata(text)
    dates = meta.get('dates', [])
    locations = [
        "London", "Sarnia", "Windsor", "Cambridge", "Woodstock", 
        "Kitchener Spanish", "Kitchener East", "Margaret Ave", 
        "New Hamburg", "Guelph", "Fergus", "Hanover", "Owen Sound"
    ]

    matches = []
    # Split text into logical blocks based on the Date headers
    # This ensures we only look for your name within a specific 'Date Column'
    date_segments = re.split(r'(\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.?\s+[A-Za-z]{3,9}\s+\d{1,2}\b)', text)
    
    current_date = "Unknown Date"
    for segment in date_segments:
        # If the segment is a date, update our 'Current Column'
        if any(d in segment for d in dates):
            current_date = segment.strip()
            continue
        
        # If your name is in this date's column, find which 'Row' it is in
        if query.lower() in segment.lower():
            # Split the column into lines to find the Location anchor
            location_for_this_match = "Unknown Location"
            
            # We look for which city name is 'closest' in the text stream 
            # within this specific date column
            for loc in locations:
                if loc.lower() in segment.lower():
                    # We verify this is the correct row by checking 
                    # surrounding text for the location header
                    location_for_this_match = loc
            
            matches.append({
                'date': current_date,
                'location': location_for_this_match,
                'context': segment.strip()[:100] # Keep context small
            })

    return matches


def extract_schedule_metadata(text: str):
    """Try to infer schedule metadata from extracted PDF text.

    Returns a dict with keys: 'location' (str), 'month' (str or None),
    'year' (str or None), 'dates' (list of date-like strings).
    """
    import re

    res = {'location': None, 'month': None, 'year': None, 'dates': []}
    if not text:
        return res

    lines = [l.strip() for l in text.splitlines() if l and l.strip()]

    # Guess location: look for a line containing 'District' in the first 10 lines
    for ln in lines[:20]:
        if 'district' in ln.lower():
            res['location'] = ln.strip()
            break
    # fallback: first non-empty line
    if not res['location'] and lines:
        res['location'] = lines[0].strip()

    # Find month-year like 'December 2025' or short 'Dec 2025'
    m_my = re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(20\d{2})\b', text, re.IGNORECASE)
    if m_my:
        res['month'] = m_my.group(1).title()
        res['year'] = m_my.group(2)
    else:
        # try abbreviated month + year
        m2 = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*(20\d{2})\b', text, re.IGNORECASE)
        if m2:
            res['month'] = m2.group(1).title()
            res['year'] = m2.group(2)

    # date-like tokens (weekday + month + day) collect unique in order
    date_re = re.compile(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.?\s+[A-Za-z]{3,9}\s+\d{1,2}\b", re.IGNORECASE)
    dates = [m.group(0).strip() for m in date_re.finditer(text)]
    # dedupe while preserving order
    seen = set()
    dedup = []
    for d in dates:
        k = d.lower()
        if k not in seen:
            seen.add(k)
            dedup.append(d)
    res['dates'] = dedup

    return res


def find_schedule_pdfs(base_dir: str):
    """Find PDF files under Year/Month/Schedules inside `base_dir`.

    Returns list of absolute file paths to PDFs.
    """
    import glob
    import re

    results = []
    if not base_dir or not os.path.exists(base_dir):
        return results

    for year in os.listdir(base_dir):
        year_path = os.path.join(base_dir, year)
        if not os.path.isdir(year_path):
            continue
        # prefer folders that look like years
        if not re.match(r'^20\d{2}$', year):
            continue
        for month in os.listdir(year_path):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                continue
            sched_dir = os.path.join(month_path, 'Schedules')
            if not os.path.isdir(sched_dir):
                continue
            # collect PDFs
            pdfs = glob.glob(os.path.join(sched_dir, '*.pdf'))
            for p in pdfs:
                results.append(os.path.abspath(p))

    return results

def is_excluded_schedule_path(path: str, exclude_names=None) -> bool:
    """Return True if the given path is inside a folder that should be excluded

    By default excludes folders named 'youth' or 'seniors' (case-insensitive).
    """
    if not path:
        return False
    if exclude_names is None:
        exclude_names = {'youth', 'seniors'}
    try:
        parts = {p.lower() for p in os.path.normpath(path).split(os.path.sep) if p}
    except Exception:
        parts = {p.lower() for p in path.replace('\\', '/').split('/') if p}
    return len(parts & set(n.lower() for n in exclude_names)) > 0
