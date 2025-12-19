"""
Actions and helpers for scraping and saving DSG and Schedules content.

This module provides small, focused helpers used by `main.py`:
- browser interaction helpers (click, find inputs)
- page extractors (webpart links, accordion items, schedule sections)
- local filesystem helpers to create year/month/subfolder structure
- mapping and download helpers to name and save files

Comments are placed above non-obvious functions to explain intent.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pdfplumber


def get_button_text(driver, selector, selector_type="css", timeout=10):
    # Return the visible text for a control, or its value attribute for inputs.
    # This helps detect buttons/inputs whose caption is stored as `value`.
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
    by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
    el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
    text = el.text.strip()
    if text:
        return text
        import urllib.parse

        raw_href = href or ''
        # decode percent-encoding to help detection (e.g., '%20' -> ' ')
        h_decoded = urllib.parse.unquote(raw_href)
    tag = el.tag_name.lower()
    if tag in ("input", "button"):
        val = el.get_attribute("value")
        if val:
            return val.strip()
    return text


def click_element(driver, selector, selector_type="css", timeout=10):
    # Click an element, falling back to JS click if needed.
    by = By.CSS_SELECTOR if selector_type.lower() == "css" else By.XPATH
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
    try:
        el.click()
        return True
    except Exception:
        # Some pages prevent normal click; use JS click as a fallback.
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


def extract_schedule_sections(driver, timeout=8):
    """Extract schedule page sections (h3 headings) and their links.

    Returns list of (section_title, [(link_text, href), ...]).
    It walks each <table> on the page and groups anchors under the most
    recent <h3> encountered in table rows.
    """
    from selenium.webdriver.common.by import By
    sections = []
    try:
        tables = driver.find_elements(By.XPATH, '//table')
    except Exception:
        return []

    for table in tables:
        try:
            rows = table.find_elements(By.XPATH, './/tr')
        except Exception:
            continue
        current = None
        for r in rows:
            try:
                h3s = r.find_elements(By.XPATH, './/h3')
                if h3s:
                    current = h3s[0].text.strip()
                    sections.append((current, []))
                    continue
                anchors = r.find_elements(By.XPATH, './/a')
                if anchors and current is not None:
                    # append all anchors to the latest section
                    for a in anchors:
                        try:
                            t = a.text.strip()
                            h = a.get_attribute('href') or ''
                            if t or h:
                                sections[-1][1].append((t, h))
                        except Exception:
                            continue
            except Exception:
                continue
    # filter out empty sections
    filtered = [(s, links) for s, links in sections if links]
    return filtered


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
        # detect serving schedules / schedule PDFs
        flags['serving'] = 'serving schedules' in h or '/serving schedules/' in h or 'serving schedule' in h or 'serving schedule' in fname or 'serving schedules' in fname or 'serving' in h
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
    """Generate destination folder and filename for a link.

    Returns (dest_folder, filename_with_ext).
    """
    import os
    import re
    import urllib.parse
    from datetime import datetime

    raw = href or ''
    decoded = urllib.parse.unquote(raw)
    h = decoded.lower()
    fname = os.path.basename(decoded)
    ext = os.path.splitext(fname)[1] or ''

    # detect simple flags
    flags = {
        'serving': 'serving' in h and 'schedule' in h,
        'youth': 'youth' in h or 'youth' in fname.lower() or ('youth' in (header_text or '').lower()),
        'children': 'children' in h or 'child' in fname.lower() or ('children' in (header_text or '').lower()),
        'senior': 'senior' in h or 'seniors' in h or 'senior' in fname.lower() or 'seniors' in fname.lower() or ('senior' in (header_text or '').lower()),
        'nacc': 'nacc' in (header_text or '').lower() or 'nacc' in h,
    }

    # detect DSG-related flags
    flags['dsg'] = ('divine service prep' in h) or ('dsg' in fname.lower()) or ('divine' in h) or ('divine' in (header_text or '').lower())
    flags['full_dsg'] = 'full' in h and 'dsg' in h or 'full dsg' in h or 'full-dsg' in fname.lower()
    flags['se_dsg'] = 'special edition' in h or 'se dsg' in h or 'se-dsg' in fname.lower()
    flags['foreword'] = 'foreword' in h or 'foreword' in fname.lower() or 'foreword' in (header_text or '').lower() or 'forward' in (header_text or '').lower()
    flags['audio'] = 'audio' in h or 'audio' in fname.lower()
    flags['transcript'] = 'transcript' in h or 'transcript' in fname.lower()
    flags['bibleref'] = ('bible' in h and 'reference' in h) or 'bible-references' in fname.lower() or 'bible references' in h

    # try ISO date in raw href
    date_obj = None
    m_iso = re.search(r'(20\d{2}-\d{2}-\d{2})', raw)
    if m_iso:
        try:
            date_obj = datetime.strptime(m_iso.group(1), '%Y-%m-%d')
        except Exception:
            date_obj = None

    year = None
    month = None
    if date_obj:
        year = str(date_obj.year)
        month = date_obj.strftime('%B')
    else:
        # try to find Month Year in decoded path (e.g., 'January 2026')
        m_my = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)[\s%20_-]+(20\d{2})', h)
        if m_my:
            month = m_my.group(1).title()
            year = m_my.group(2)
        else:
            m_year = re.search(r'(20\d{2})', raw)
            if m_year:
                year = m_year.group(1)

        # If month/year still not found, try parsing from the visible link text or header_text
        if not month or not year:
            combined_search = ' '.join([decoded, link_text or '', header_text or '']).lower()
            m_comb = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)[\s\-_,]+(20\d{2})', combined_search)
            if m_comb:
                month = m_comb.group(1).title()
                year = m_comb.group(2)
            else:
                # look for numeric year-month patterns like 2025-12 or 2025_12 or 2025.12
                m_num = re.search(r'(20\d{2})[-_\.](0[1-9]|1[0-2])', combined_search)
                if not m_num:
                    # also try patterns in filename/decoded path
                    m_num = re.search(r'(20\d{2})[-_\.](0[1-9]|1[0-2])', decoded)
                if m_num:
                    y = m_num.group(1)
                    mm = m_num.group(2)
                    month_map = {
                        '01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June',
                        '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December'
                    }
                    year = y
                    month = month_map.get(mm, None)

    # choose subfolder — preference order: DSG-related categories, then schedules
    sub = 'DSG'
    if flags.get('dsg'):
        # dsg subcategories
        if flags.get('foreword'):
            sub = 'Forward'
        elif flags.get('youth'):
            sub = 'Youth'
        elif flags.get('children'):
            sub = 'Childrens Service'
        elif flags.get('full_dsg'):
            sub = 'Full DSGs'
        elif flags.get('se_dsg'):
            sub = 'Special DSG'
        elif flags.get('bibleref'):
            sub = 'Bible References'
        elif flags.get('audio'):
            sub = 'Audio'
        elif flags.get('transcript'):
            sub = 'Transcripts'
        else:
            sub = 'DSG'
    else:
        # not DSG -> schedules area
        # prefer Youth when 'youth' appears in name/href, then serving schedules, then seniors, then NACC
        if flags.get('youth'):
            sub = 'Youth'
        elif flags.get('serving'):
            sub = 'Schedules'
        elif flags.get('senior'):
            sub = 'Seniors'
        elif flags.get('nacc'):
            sub = 'NACC Calendars'

    # build dest folder
    dest = base_dir
    if year:
        dest = os.path.join(dest, year)
    if month:
        dest = os.path.join(dest, month)
    if sub:
        dest = os.path.join(dest, sub)

    # build filename according to requested conventions
    def clean_loc(s):
        return (s or '').strip().replace('/', '-').replace('\\', '-')

    loc = clean_loc(link_text)

    # DSG items
    if sub in ('DSG', 'Full DSGs', 'Special DSG', 'Forward', 'Childrens Service'):
        # language detection for file label
        lang = ''
        # prefer language words in decoded href or filename
        for name in ('English', 'French', 'German', 'Italian', 'Portuguese', 'Russian', 'Spanish'):
            if name.lower() in h:
                lang = name
                break

        if sub == 'Forward':
            # "[Month] [Year] Forward [Language]"
            if month and year:
                label = f"{month} {year} Forward {lang}" if lang else f"{month} {year} Forward"
            elif year:
                label = f"{year} Forward {lang}" if lang else f"{year} Forward"
            else:
                label = f"Forward {loc}"
        elif sub == 'Full DSGs' or sub == 'Special DSG':
            # "[Month] [Year] Full DSG [Language]" or Special Edition
            tag = 'Full DSG' if sub == 'Full DSGs' else 'Special Edition DSG'
            if month and year:
                label = f"{month} {year} {tag} {lang}" if lang else f"{month} {year} {tag}"
            elif year:
                label = f"{year} {tag} {lang}" if lang else f"{year} {tag}"
            else:
                label = f"{tag} {loc}"
        elif sub == 'Childrens Service':
            # "[Month] [Year] Children's Service [Language]" (fall back)
            if month and year:
                label = f"{month} {year} Childrens Service {lang}" if lang else f"{month} {year} Childrens Service"
            elif year:
                label = f"{year} Childrens Service {lang}" if lang else f"{year} Childrens Service"
            else:
                label = f"Childrens Service {loc}"
        else:
            # regular DSG service with date -> "[Weekday] [Month] [Day] [Year] Divine Service Prep [Language]"
            if date_obj:
                weekday = date_obj.strftime('%A')
                day = date_obj.day
                y = date_obj.year
                if lang:
                    label = f"{weekday} {month} {day} {y} Divine Service Prep {lang}"
                else:
                    # try literal language in href or default to English
                    label_lang = 'English' if 'en' in h or 'english' in h else ''
                    label = f"{weekday} {month} {day} {y} Divine Service Prep {label_lang}".strip()
            else:
                # fallback
                label = loc or 'Divine Service Prep'

    # Schedules items
    elif sub == 'Schedules':
        # "[Month] [Year] [Location] Serving Schedule"
        if month and year:
            label = f"{month} {year} {loc} Serving Schedule"
        elif year:
            label = f"{year} {loc} Serving Schedule"
        else:
            label = f"{loc} Serving Schedule"
    elif sub == 'Youth':
        # Youth schedules (from schedule area) or youth DSG (from DSG area)
        if flags.get('serving'):
            if month and year:
                label = f"{month} {year} {loc} Youth Schedule"
            elif year:
                label = f"{year} {loc} Youth Schedule"
            else:
                label = f"{loc} Youth Schedule"
        else:
            # youth DSG under Divine Service Prep: "[Month] [Year] Youth [Language]"
            lang = ''
            for name in ('English', 'French'):
                if name.lower() in h:
                    lang = name
                    break
            if month and year:
                label = f"{month} {year} Youth {lang}" if lang else f"{month} {year} Youth"
            elif year:
                label = f"{year} Youth {lang}" if lang else f"{year} Youth"
            else:
                label = f"Youth {loc}"
    elif sub == 'Seniors':
        if month and year:
            label = f"{month} {year} {loc} Seniors Schedule"
        elif year:
            label = f"{year} {loc} Seniors Schedule"
        else:
            label = f"{loc} Seniors Schedule"
    elif sub == 'NACC Calendars':
        # "[Month] [Year] NACC Calendar [National/Districts]"
        if month and year:
            label = f"{month} {year} NACC Calendar {loc}"
        elif year:
            label = f"{year} NACC Calendar {loc}"
        else:
            label = f"NACC Calendar {loc}"
    else:
        # fallback to original filename
        label = os.path.splitext(fname)[0] or loc or 'download'

    filename = label + (ext or '')
    filename = re.sub(r'[\\/]+', '-', filename)
    return dest, filename


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
