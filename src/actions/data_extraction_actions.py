"Data extraction helpers"
import os
import re
import urllib.parse
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_webpart_links_by_heading(driver, heading_text, timeout=10):
    """Return a list of link texts under the `.iMIS-WebPart` container whose H2 equals `heading_text`.

    Example: heading_text='Divine Service Prep' returns ['December 2025', 'January 2026']
    """
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


def extract_schedule_sections(driver, timeout=8):
    """Extract schedule page sections (h3 headings) and their links.

    Returns list of (section_title, [(link_text, href), ...]).
    It walks each <table> on the page and groups anchors under the most
    recent <h3> encountered in table rows.
    """
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


def filter_links(user_choices, links):
    selections = {s.lower() for s in user_choices.get('selections', [])}
    if not selections:
        return []

    def link_matches(href):
        href_lower = href.lower()

        # Check for English
        if 'english' in selections and '/english/' in href_lower and href_lower.endswith('.pdf'):
            # Make sure it's a general DSG, not a special type, unless that type is also selected
            if not any(kw in href_lower for kw in ['audio', 'references', 'transcript', 'foreword', 'se-dsg', 'full-dsg', 'youth', 'children']):
                return True

        # Check for French
        if 'french' in selections and '/french/' in href_lower and href_lower.endswith('.pdf'):
            # Make sure it's a general DSG
            if not any(kw in href_lower for kw in ['audio', 'references', 'transcript', 'foreword', 'se-dsg', 'full-dsg', 'youth', 'children']):
                return True

        # Check for Audio
        if 'audio' in selections and '/audio' in href_lower and href_lower.endswith('.mp3'):
            return True

        # Check for References
        if 'references' in selections and ('/bible%20references/' in href_lower or '/references/' in href_lower) and href_lower.endswith('.pdf'):
            return True

        # Check for Transcript
        if 'transcript' in selections and '/transcripts/' in href_lower and href_lower.endswith('.pdf'):
            return True

        # Check for Foreword
        if 'foreword' in selections and ('foreword' in href_lower or 'foreword' in link_text.lower()):
            return True

        # Check for Special Edition DSG
        if ('special edition dsg' in selections or 'special dsg' in selections) and ('se dsg' in href_lower or 'special edition dsg' in href_lower):
            return True
        
        # Check for Full DSG
        if 'full dsg' in selections and 'full dsg' in href_lower:
            return True

        # Check for Youth DSG
        if 'youth' in selections and 'youth' in href_lower and href_lower.endswith('.pdf'):
            return True

        # Check for Children's Service DSG
        if 'childrens service' in selections and 'children' in href_lower and href_lower.endswith('.pdf'):
            return True

        return False

    filtered_links = []
    for link in links:
        if link_matches(link['href']):
            filtered_links.append(link)
            
    return filtered_links


def map_link_to_destination(href, link_text, header_text, base_dir, month_year_str=None):
    """Generate destination folder and filename for a link.

    Returns (dest_folder, filename_with_ext).
    """
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
    if month_year_str:
        m_my = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)[\s%20_-]+(20\d{2})', month_year_str, re.IGNORECASE)
        if m_my:
            month = m_my.group(1).title()
            year = m_my.group(2)
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
                m_num = re.search(r'(20\d{2})[-_.](\d{2})', combined_search)
                if not m_num:
                    # also try patterns in filename/decoded path
                    m_num = re.search(r'(20\d{2})[-_.](\d{2})', decoded)
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
    elif header_text:
        if header_text.lower() == 'youth schedules':
            sub = 'Youth'
        elif header_text.lower() == 'seniors schedules':
            sub = 'Seniors'
        elif 'nacc calendars' in header_text.lower():
            sub = 'NACC Calendars'
        elif header_text.lower() == 'district serving schedules':
            sub = 'Schedules'
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
