"""Browser interaction helpers"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
