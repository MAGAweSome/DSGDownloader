from src.config import (
    URL,
    BUTTON_SELECTOR,
    SELECTOR_TYPE,
    SIGNIN_LINK_SELECTOR,
    SIGNIN_LINK_SELECTOR_TYPE,
    USERNAME_SELECTOR,
    USERNAME_SELECTOR_TYPE,
    PASSWORD_SELECTOR,
    PASSWORD_SELECTOR_TYPE,
    SUBMIT_SELECTOR,
    SUBMIT_SELECTOR_TYPE,
    USERNAME,
    PASSWORD,
    MINIHQ_LINK_SELECTOR,
    MINIHQ_LINK_SELECTOR_TYPE,
)
from src.ui import get_user_selection
from src.browser import init_driver
from src.actions import (
    fill_input_field,
    submit_form,
    click_element,
    get_webpart_links_by_heading,
    get_webpart_link_elements,
    extract_accordion_items,
    filter_accordion_items_by_selection,
)
from src.actions import map_link_to_destination
from src.actions import list_files_in_dir
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import socket
from urllib.parse import urlparse
from selenium.common.exceptions import WebDriverException
import time
import os


def main():
    # Try a DNS lookup but continue even if it fails — user requested a simple open-wait-close test
    host = urlparse(URL).hostname
    if host:
        try:
            socket.getaddrinfo(host, None)
        except socket.gaierror:
            print(f"DNS resolution failed for host: {host} - continuing to try opening the URL anyway.")

    # Ask user what to extract before starting browser
    user_choices = get_user_selection()

    driver = init_driver()
    try:
        try:
            driver.get(URL)
            print("Opened URL; waiting for Sign In link...")
        except WebDriverException as e:
            print("WebDriver failed to load the page:", e)
            print("This is usually a network/DNS issue (net::ERR_NAME_NOT_RESOLVED).")
            return
        # After opening the site, try to click Sign In and fill credentials if provided.
        try:
            # click the sign in link (using the exact selector you provided)
            click_element(driver, SIGNIN_LINK_SELECTOR, SIGNIN_LINK_SELECTOR_TYPE, timeout=10)

            # fill username and password using the exact selectors provided
            if USERNAME:
                try:
                    print("Using USERNAME from env:", repr(USERNAME))
                    fill_input_field(driver, [(USERNAME_SELECTOR, USERNAME_SELECTOR_TYPE)], USERNAME, timeout=8)
                    print("Filled username")
                except Exception as e:
                    print("Could not fill username:", e)

            if PASSWORD:
                try:
                    pwd_el = fill_input_field(driver, [(PASSWORD_SELECTOR, PASSWORD_SELECTOR_TYPE)], PASSWORD, timeout=8)
                    print("Filled password")
                    # submit using the provided submit selector
                    submitted = submit_form(driver, [(SUBMIT_SELECTOR, SUBMIT_SELECTOR_TYPE)], timeout=6)
                    if submitted:
                        print("Submitted login form")
                    else:
                        from selenium.webdriver.common.keys import Keys

                        pwd_el.send_keys(Keys.ENTER)
                        print("Submitted login form via Enter key")
                except Exception as e:
                    print("Could not fill/submit password:", e)
                    submitted = False
                else:
                    submitted = True
        except Exception as e:
            print("Login sequence encountered an error:", e)

        # After login attempt (successful or not), click MiniHQ and extract the requested webpart link texts
        try:
            # After submit, wait for a post-login indicator so the browser isn't closed prematurely.
            try:
                post_login_wait = WebDriverWait(driver, 20)
                # Wait until MiniHQ link appears OR the Sign In link disappears (login state changed)
                post_login_wait.until(
                    lambda d: (
                        len(d.find_elements(By.CSS_SELECTOR, MINIHQ_LINK_SELECTOR)) > 0
                        or len(d.find_elements(By.CSS_SELECTOR, SIGNIN_LINK_SELECTOR)) == 0
                    )
                )
                print("Detected post-login state or MiniHQ link.")
            except Exception:
                print("Timed out waiting for post-login indicator; proceeding anyway.")

            # Click miniHQ link
            click_element(driver, MINIHQ_LINK_SELECTOR, MINIHQ_LINK_SELECTOR_TYPE, timeout=8)
            print("Clicked MiniHQ link; waiting for page to load...")
            # wait for document ready
            WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')

            # extract items
            divine_links = get_webpart_links_by_heading(driver, "Divine Service Prep", timeout=6)
            schedules_links = get_webpart_links_by_heading(driver, "Schedules", timeout=6)

            if divine_links:
                print("Divine Service Prep items:")
                for t in divine_links:
                    print("- ", t)
            else:
                print("No Divine Service Prep items found.")

            if schedules_links:
                print("Schedules items:")
                for t in schedules_links:
                    print("- ", t)
            else:
                print("No Schedules items found.")
        except Exception as e:
            print("MiniHQ sequence error:", e)

        # List local DSG files from configured folder and ensure year/month/subfolders exist
        try:
            from src.config import DSGS_DIR
            local_files = list_files_in_dir(DSGS_DIR, "*")
            print(f"Files in {DSGS_DIR}:")
            if local_files:
                for fn in local_files:
                    print("- ", fn)
            else:
                print("(no files found)")

            # Extract years from the link texts we found and ensure year folders exist
            from src.actions import extract_years_from_texts, ensure_year_folders_exist

            years_divine = extract_years_from_texts(divine_links)
            years_sched = extract_years_from_texts(schedules_links)
            years = sorted(set(years_divine + years_sched))
            if years:
                created, existing = ensure_year_folders_exist(DSGS_DIR, years)
                if created:
                    print("Created year folders:")
                    for p in created:
                        print("- ", p)
                if existing:
                    print("Already existing year folders:")
                    for p in existing:
                        print("- ", p)
            else:
                print("No years extracted from MiniHQ items; no folders changed.")

            # Ensure month folders inside the year folders for each Month Year item
            from src.actions import extract_month_year_pairs, ensure_month_folders_exist

            month_year_pairs = extract_month_year_pairs(divine_links + schedules_links)
            if month_year_pairs:
                created_m, existing_m = ensure_month_folders_exist(DSGS_DIR, month_year_pairs)
                if created_m:
                    print("Created month folders:")
                    for p in created_m:
                        print("- ", p)
                if existing_m:
                    print("Already existing month folders:")
                    for p in existing_m:
                        print("- ", p)
            else:
                print("No month-year pairs found to create month folders.")

            # Ensure subfolders inside each month folder
            from src.actions import ensure_subfolders_in_months
            subfolders = ["DSG", "Schedule", "Youth"]
            created_s, existing_s = ensure_subfolders_in_months(DSGS_DIR, month_year_pairs, subfolders)
            if created_s:
                print("Created subfolders:")
                for p in created_s:
                    print("- ", p)
            if existing_s:
                print("Already existing subfolders:")
                for p in existing_s:
                    print("- ", p)
        except Exception as e:
            print("Could not list DSG files or ensure year/month/subfolders:", e)

        # Open the first Divine Service Prep month link (if any) and extract accordion items
        try:
            divine_link_elements = get_webpart_link_elements(driver, "Divine Service Prep", timeout=6)
            if not divine_link_elements:
                print("No Divine Service Prep month links found to open.")
            else:
                # Collect static list of (text, href) to avoid stale element issues
                month_links = []
                for item in divine_link_elements:
                    text = item.get('text') or ''
                    href = item.get('href') or ''
                    if href:
                        month_links.append({'text': text, 'href': href})

                from urllib.parse import urljoin

                for idx, ml in enumerate(month_links):
                    print(f"Processing month {idx+1}/{len(month_links)}: {ml['text']}")
                    full = urljoin(URL, ml['href'])
                    try:
                        driver.get(full)
                        WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    except Exception as e:
                        print(f"Could not open month page {ml['text']} ({ml['href']}):", e)
                        continue

                    # extract accordion items and filter by user choices
                    items = extract_accordion_items(driver, timeout=8)
                    filtered = filter_accordion_items_by_selection(items, user_choices)
                    if filtered:
                        print(f"Accordion items on {ml['text']} page:")
                        for hdr, links in filtered:
                            print(f"- {hdr}")
                            for lt, lh in links:
                                print(f"    - {lt} -> {lh}")
                                try:
                                    from src.config import DSGS_DIR
                                    from src.actions import save_url_to_path

                                    dest, newname = map_link_to_destination(lh, lt, hdr, DSGS_DIR)
                                    ok, reason = save_url_to_path(lh, dest, newname, driver=driver, overwrite=False)
                                    if ok:
                                        print(f"        -> Saved: {newname}")
                                        print(f"           at: {dest}")
                                    else:
                                        if reason == 'exists':
                                            print(f"        -> Skipped (exists): {os.path.join(dest, newname)}")
                                        else:
                                            print(f"        -> Failed to save ({reason}): {lh}")
                                except Exception as e:
                                    print("        -> Could not map/save destination/filename:", e)
                    else:
                        print(f"No accordion items found on {ml['text']} page for selected filters.")

                    # go back to the previous page (MiniHQ) before processing next month, per your request
                    try:
                        driver.back()
                        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                        time.sleep(1)
                    except Exception:
                        # if back fails, continue — we will open next month via absolute URL
                        pass
        except Exception as e:
            print("Error opening Divine Service Prep month or extracting items:", e)
    finally:
        print("Closing browser...")
        driver.quit()


if __name__ == "__main__":
    main()
