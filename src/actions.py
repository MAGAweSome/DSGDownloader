from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_button_text(driver, selector, selector_type="css", timeout=10):
    """Find an element by selector and return its visible text or value attribute.

    - `selector_type` should be either "css" or "xpath".
    - For <input> elements, the function will return the `value` attribute if `.text` is empty.
    """
    by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
    el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
    text = el.text.strip()
    if text:
        return text
    tag = el.tag_name.lower()
    if tag in ("input", "button"):
        val = el.get_attribute("value")
        if val:
            return val.strip()
    return text


def click_element(driver, selector, selector_type="css", timeout=10):
    """Wait for element to be clickable and click it.

    Returns True if click was performed, raises on timeout or other failures.
    """
    by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
    try:
        el.click()
        return True
    except Exception:
        # Fallback to JS click
        driver.execute_script("arguments[0].click();", el)
        return True


def find_first_visible(driver, candidates, timeout=6):
    """Try a list of (selector, selector_type) tuples and return the first visible element."""
    for selector, selector_type in candidates:
        by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
        try:
            el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, selector)))
            return el
        except Exception:
            continue
    return None


def fill_input_field(driver, candidates, text, timeout=6):
    """Find the first input from `candidates` and fill `text` into it."""
    el = find_first_visible(driver, candidates, timeout=timeout)
    if el is None:
        raise RuntimeError(f"No input found for candidates: {candidates}")
    el.clear()
    el.send_keys(text)
    # Ensure the exact value is set (some pages overwrite typed input); set via JS and fire input event
    try:
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
            el,
            text,
        )
    except Exception:
        pass
    return el


def submit_form(driver, submit_candidates, timeout=6):
    """Try to click the first available submit control from candidates. Returns True if clicked."""
    el = find_first_visible(driver, submit_candidates, timeout=timeout)
    if el is None:
        return False
    try:
        el.click()
        return True
    except Exception:
        driver.execute_script("arguments[0].click();", el)
        return True


def get_webpart_links_by_heading(driver, heading_text, timeout=10):
    """Return a list of link texts under the `.iMIS-WebPart` container whose H2 equals `heading_text`.

    Example: heading_text='Divine Service Prep' returns ['December 2025', 'January 2026']
    """
    from selenium.webdriver.common.by import By
    xpath_container = f"//h2[normalize-space()={repr(heading_text)}]/ancestor::div[contains(@class,'iMIS-WebPart')][1]"
    try:
        container = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath_container))
        )
    except Exception:
        return []

    links = container.find_elements(By.XPATH, ".//a")
    texts = [lnk.text.strip() for lnk in links if lnk.text and lnk.text.strip()]
    return texts


def get_webpart_link_elements(driver, heading_text, timeout=10):
    """Return list of anchor elements under the webpart identified by H2 == heading_text.

    Each item is a dict: {'text': visible text, 'href': href attribute, 'element': WebElement}
    """
    from selenium.webdriver.common.by import By
    xpath_container = f"//h2[normalize-space()={repr(heading_text)}]/ancestor::div[contains(@class,'iMIS-WebPart')][1]"
    try:
        container = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath_container))
        )
    except Exception:
        return []

    anchors = container.find_elements(By.XPATH, ".//a")
    results = []
    for a in anchors:
        text = a.text.strip()
        href = a.get_attribute('href') or a.get_attribute('data-href') or ''
        results.append({'text': text, 'href': href, 'element': a})
    return results


def extract_accordion_items(driver, timeout=10):
    """Extract accordion headers and link items from a Divine Service Prep month page.

    Returns list of (header_text, [ (link_text, href), ... ])
    """
    from selenium.webdriver.common.by import By
    # Wait for accordion presence
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div#accordion2'))
        )
    except Exception:
        # try without specific id
        pass

    headers = driver.find_elements(By.CSS_SELECTOR, 'h4.ui-accordion-header')
    results = []
    for hdr in headers:
        try:
            heading_text = hdr.text.strip()
        except Exception:
            heading_text = ''
        # following sibling content div - use xpath to find the next div
        try:
            content = hdr.find_element(By.XPATH, 'following-sibling::div[1]')
            links = content.find_elements(By.XPATH, './/a')
            items = []
            for l in links:
                t = l.text.strip()
                h = l.get_attribute('href') or ''
                if t or h:
                    items.append((t, h))
            results.append((heading_text, items))
        except Exception:
            results.append((heading_text, []))
    return results


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


def extract_years_from_texts(texts):
    """Extract 4-digit years (e.g. 2025) from a list of strings. Returns sorted list of unique years as strings."""
    import re

    years = set()
    for t in texts:
        if not t:
            continue
        m = re.search(r"\b(20\d{2})\b", t)
        if m:
            years.add(m.group(1))
    return sorted(years)


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


def extract_month_year_pairs(texts):
    """From a list of strings like 'December 2025' return list of (Month, Year) tuples.

    Month will be title-cased (e.g., 'December').
    """
    import re

    pairs = []
    for t in texts:
        if not t:
            continue
        m = re.search(r"\b([A-Za-z]+)\s+(20\d{2})\b", t)
        if m:
            month = m.group(1).strip().title()
            year = m.group(2)
            pairs.append((month, year))
    return pairs


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


def filter_accordion_items_by_selection(items, user_choices):
    """Filter accordion items according to the `user_choices` dict from `src.ui.get_user_selection()`.

    - `items` is list of (header, [ (link_text, href), ... ])
    - `user_choices` is the dict with keys: 'selections', 'bible_reading_langs', 'full_dsg_langs', 'se_dsg_langs'

    Returns filtered list of (header, [(text, href), ...]) where empty-headers or items with no links are omitted.
    """
    import os

    selections = set(user_choices.get('selections') or [])
    # normalize
    selections = {s.lower() for s in selections}

    english_selected = 'english' in selections
    french_selected = 'french' in selections

    # per-type language preferences (lowercase names)
    br_langs = {l.lower() for l in (user_choices.get('bible_reading_langs') or [])}
    full_langs = {l.lower() for l in (user_choices.get('full_dsg_langs') or [])}
    se_langs = {l.lower() for l in (user_choices.get('se_dsg_langs') or [])}
    foreword_langs = {l.lower() for l in (user_choices.get('foreword_langs') or [])}
    bibref_langs = {l.lower() for l in (user_choices.get('bible_references_langs') or [])}

    # detect which specific "type" selections are present
    type_selections = set()
    for key in (
        'audio',
        'transcript',
        'references',
        'bible references',
        'bible reading',
        'full dsg',
        'special edition dsg',
        'foreword',
    ):
        if key in selections:
            type_selections.add(key)

    def detect_flags(href):
        h = (href or '').lower()
        fname = os.path.basename(h)
        flags = {}
        # detect language codes in path or filename (en, fr, de, it, pt, ru, es)
        import re as _re
        codes = set()
        if '/english/' in h:
            codes.add('en')
        if '/french/' in h:
            codes.add('fr')
        # look for language codes in filename or path segments: -en., _en., .en., /en/
        m = _re.search(r'(?:(?:-|_|\.|/))(en|fr|de|it|pt|ru|es)(?:\.|_|/|-|$)', h)
        if m:
            codes.add(m.group(1))
        # also detect full language names in the path (English, French, German, etc.)
        names = set()
        for name, code in (('english', 'en'), ('french', 'fr'), ('german', 'de'), ('italian', 'it'), ('portuguese', 'pt'), ('russian', 'ru'), ('spanish', 'es')):
            if name in h or name in fname.lower():
                names.add(code)
                codes.add(code)
        flags['codes'] = codes
        flags['lang_names'] = names
        flags['english'] = 'en' in codes
        flags['french'] = 'fr' in codes
        flags['audio'] = 'audio' in h or 'audio%20' in h or '-audio-' in fname
        flags['transcript'] = 'transcript' in h
        flags['bible_references'] = (
            ('bible' in h and 'reference' in h) or 'bible-references' in fname or 'bible_references' in fname
        )
        flags['bible_reading'] = 'bible-reading' in h or 'bible%20reading' in h or 'bible-reading' in fname
        flags['full_dsg'] = ('full' in h and 'dsg' in h) or 'full%20dsg' in h or 'full-dsg' in fname
        flags['se_dsg'] = (
            'se%20dsg' in h
            or 'se-dsg' in h
            or ('/se%20' in h and 'dsg' in h)
            or ('/document%20library' in h and 'se' in h)
        )
        flags['foreword'] = 'foreword' in h or 'foreword' in fname
        return flags

    def link_matches(href):
        flags = detect_flags(href)

        # language selection handling
        langs_selected = english_selected or french_selected

        # If type selections exist (e.g., audio/transcript/full dsg/se dsg/etc.) then require type match
        has_type_selection = len(type_selections) > 0

        # map type selection keys to checks
        def lang_ok_for_link(flags, per_langs):
            # per_langs is a set of lowercase language names; if empty -> no restriction
            lang_map = {
                'english': 'en',
                'french': 'fr',
                'german': 'de',
                'italian': 'it',
                'portuguese': 'pt',
                'russian': 'ru',
                'spanish': 'es',
            }
            req_codes = set()
            for ln in (per_langs or []):
                code = lang_map.get(ln.lower())
                if code:
                    req_codes.add(code)
            if req_codes:
                # match by detected codes OR by language name presence
                if len(flags.get('codes', set()) & req_codes) > 0:
                    return True
                # also check lang_names (from literal name matches)
                if len(flags.get('lang_names', set()) & req_codes) > 0:
                    return True
                return False
            # fall back to global English/French selections
            glob_codes = set()
            if english_selected:
                glob_codes.add('en')
            if french_selected:
                glob_codes.add('fr')
            if glob_codes:
                return len(flags.get('codes', set()) & glob_codes) > 0
            return True

        def type_check():
            # if any of the type selections match, return True (respecting per-type language choices)
            for t in type_selections:
                if t == 'audio' and flags.get('audio'):
                    if lang_ok_for_link(flags, set()):
                        return True
                if t == 'transcript' and flags.get('transcript'):
                    if lang_ok_for_link(flags, set()):
                        return True
                if t in ('references', 'bible references') and flags.get('bible_references'):
                    # if this link is also a Full DSG item, require Full DSG to be selected as well
                    if flags.get('full_dsg') and 'full dsg' not in type_selections:
                        continue
                    if lang_ok_for_link(flags, bibref_langs):
                        return True
                if t == 'bible reading' and flags.get('bible_reading'):
                    if lang_ok_for_link(flags, br_langs):
                        return True
                if t == 'full dsg' and flags.get('full_dsg'):
                    # if this link is a bible reference inside Full DSG, only include if bible references also selected
                    if flags.get('bible_references') and 'bible references' not in type_selections:
                        continue
                    if lang_ok_for_link(flags, full_langs):
                        return True
                if t == 'special edition dsg' and flags.get('se_dsg'):
                    if lang_ok_for_link(flags, se_langs):
                        return True
                if t == 'foreword' and flags.get('foreword'):
                    if lang_ok_for_link(flags, foreword_langs):
                        return True
            return False

        # If languages are explicitly selected
        if langs_selected:
            # standard DSG (language file) is a link that is language-specific but not any special type
            is_standard = (flags.get('english') or flags.get('french')) and not (
                flags.get('audio')
                or flags.get('transcript')
                or flags.get('bible_references')
                or flags.get('bible_reading')
                or flags.get('full_dsg')
                or flags.get('se_dsg')
                or flags.get('foreword')
            )
            if has_type_selection:
                # include standard language files only if they match the selected global language(s)
                include_standard = False
                if english_selected and flags.get('english'):
                    include_standard = True
                if french_selected and flags.get('french'):
                    include_standard = include_standard or True if flags.get('french') else include_standard
                # include standard if it matches global languages, or include any matching types
                return (is_standard and include_standard) or type_check()
            # no type selection: include only standard language files
            # require the standard file to match the selected global language(s)
            if english_selected and flags.get('english'):
                return is_standard
            if french_selected and flags.get('french'):
                return is_standard
            return False

        # No explicit language selection
        if has_type_selection:
            return type_check()

        # No selections at all — default to include everything
        return True

    filtered = []
    for hdr, links in items:
        kept = []
        for t, h in links:
            if not h:
                continue
            try:
                if link_matches(h):
                    kept.append((t, h))
            except Exception:
                # if detection fails, be conservative and skip
                continue
        if kept:
            filtered.append((hdr, kept))
    return filtered


def map_link_to_destination(href, link_text, header_text, base_dir):
    """Given a link href and context, return (destination_folder, new_filename).

    - Attempts to extract a YYYY-MM-DD date from the href or header_text.
    - Chooses a subfolder based on link type (audio, transcript, full dsg, etc.).
    - Builds a human-friendly filename preserving the original extension.
    """
    import os
    import re
    from datetime import datetime

    h = (href or '').lower()
    fname = os.path.basename(href or '')
    # detect extension
    ext = os.path.splitext(fname)[1] or ''

    # basic flags detection (small subset of detect_flags)
    flags = {
        'audio': 'audio' in h or 'audio%20' in h or '-audio-' in fname,
        'transcript': 'transcript' in h,
        'bible_references': ('bible' in h and 'reference' in h) or 'bible-references' in fname,
        'bible_reading': 'bible-reading' in h or 'bible%20reading' in h,
        'full_dsg': ('full' in h and 'dsg' in h) or 'full%20dsg' in h,
        'se_dsg': 'se%20dsg' in h or 'se-dsg' in h or '/se%20' in h,
        'foreword': 'foreword' in h or 'foreword' in fname,
        'children': 'children' in h or 'child' in fname,
        'youth': 'youth' in h or 'youth' in fname or '-youth-' in fname,
    }

    # try to extract ISO date from filename or href: look for 2025-12-21 patterns
    date_match = re.search(r'(20\d{2}-\d{2}-\d{2})', href)
    date_str = None
    date_obj = None
    if date_match:
        date_str = date_match.group(1)
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            date_obj = None

    # fallback: try to find day and month in header like 'Sunday, December 21, 2025'
    if date_obj is None and header_text:
        m = re.search(r"(20\d{2})", header_text)
        # try to parse full date from header using known formats
        try:
            # remove long dash separators
            cleaned = header_text.replace('—', '-').replace('\u2013', '-')
            # attempt to find Month Day, Year
            m2 = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})', cleaned)
            if m2:
                month_name = m2.group(1)
                day = int(m2.group(2))
                year = int(m2.group(3))
                date_obj = datetime.strptime(f"{month_name} {day} {year}", '%B %d %Y')
        except Exception:
            date_obj = None

    # determine subfolder
    sub = 'DSG'
    if flags['full_dsg']:
        sub = 'Full DSGs'
    elif flags['se_dsg']:
        sub = 'Special DSG'
    elif flags['audio']:
        sub = 'Audio'
    elif flags['transcript']:
        sub = 'Transcripts'
    elif flags['bible_reading']:
        sub = 'Bible Reading'
    elif flags['bible_references']:
        sub = 'Bible References'
    elif flags['foreword']:
        sub = 'Foreword'
    elif flags['youth']:
        sub = 'Youth'
    elif flags['children']:
        sub = 'Childrens Service'

    # year/month path
    year = None
    month = None
    if date_obj:
        year = f"{date_obj.year}"
        month = date_obj.strftime('%B')
    else:
        # try to extract year/month from href
        m = re.search(r'/(january|february|march|april|may|june|july|august|september|october|november|december)(?:%20)?(20\d{2})', h)
        if m:
            month = m.group(1).title()
            year = m.group(2)
        else:
            my = re.search(r'(20\d{2})', href)
            if my:
                year = my.group(1)

    # build destination path
    dest_folder = base_dir
    if year:
        dest_folder = os.path.join(dest_folder, year)
    if month:
        dest_folder = os.path.join(dest_folder, month)
    if sub:
        dest_folder = os.path.join(dest_folder, sub)

    # create a human-friendly filename
    if date_obj:
        # e.g., 'Sunday December 21 2025 English DSG.pdf' - try to include link_text language if present
        weekday = date_obj.strftime('%A')
        month_day = date_obj.strftime('%B %d, %Y')
        # try to detect language code in href
        lang = ''
        if re.search(r'(?:(?:-|_|\.))(en|fr|de|it|pt|ru|es)(?:\.|_|/|-|$)', href):
            lang = re.search(r'(?:(?:-|_|\.))(en|fr|de|it|pt|ru|es)(?:\.|_|/|-|$)', href).group(1)
            lang_map = {'en': 'English', 'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'es': 'Spanish'}
            lang = lang_map.get(lang, lang.upper())
        else:
            # check for literal language names in href
            for name in ('english', 'french', 'german', 'italian', 'portuguese', 'russian', 'spanish'):
                if name in h:
                    lang = name.title()
                    break

        # base label from subfolder
        label = sub
        # if sub is 'Full DSGs' use 'Full DSG'
        if sub == 'Full DSGs':
            label = 'Full DSG'
        # if transcript make label 'DSG Transcript' etc.
        if sub == 'Transcripts':
            label = 'DSG Transcript'

        parts = [weekday, month_day]
        if lang:
            parts.append(lang)
        parts.append(label)
        new_name = ' '.join(parts) + ext
    else:
        # fallback: use original filename
        new_name = fname or (link_text or 'download')

    # normalize filename (simple replace of slashes)
    new_name = re.sub(r'[\\/]+', '-', new_name)

    return dest_folder, new_name


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
