"""
DSG Downloader - main orchestrator

This script coordinates UI selection, launches the browser, navigates MiniHQ,
and downloads DSG and schedule files into a Year/Month/<subfolder> structure.

High-level flow:
- load user selection (GUI or terminal)
- init Edge WebDriver
- sign in (if credentials provided)
- open MiniHQ, extract Divine Service Prep and Schedules items
- create folders and save files according to mapping rules
"""

from src.config import (
    URL,
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
from src.ui.main_window import get_user_selection
from src.browser import init_driver
from src.actions.browser_actions import (
    fill_input_field,
    submit_form,
    click_element,
)
from src.actions.data_extraction_actions import (
    get_webpart_links_by_heading,
    get_webpart_link_elements,
    extract_accordion_items,
    filter_links,
    map_link_to_destination,
    extract_years_from_texts,
    extract_month_year_pairs,
    extract_schedule_sections,
)
from src.actions.file_system_actions import (
    list_files_in_dir,
    save_url_to_path,
    ensure_year_folders_exist,
    ensure_month_folders_exist,
    ensure_subfolders_in_months,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import socket
from urllib.parse import urlparse
from selenium.common.exceptions import WebDriverException
import time
import os
import json
from src.pdf_tools.highlighter import highlight_names_in_pdf

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

    if not user_choices:
        print("No selections made. Exiting.")
        return

    driver = init_driver()
    # collect schedule file paths during processing so we can parse them after the browser closes
    schedule_files = []
    divine_links = []
    schedules_links = []
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

            subfolders = []
            schedules_chosen = user_choices.get('schedules_chosen', set())
            dsg_selections = user_choices.get('selections', set())
            all_selections = {s.lower() for s in schedules_chosen.union(dsg_selections)}

            if 'district serving schedules' in all_selections:
                subfolders.append('Schedules')
            if 'youth schedules' in all_selections:
                subfolders.append('Youth')
            if 'seniors schedules' in all_selections:
                subfolders.append('Seniors')
            if 'nacc calendars' in all_selections:
                subfolders.append('NACC Calendars')
            if 'english' in all_selections or 'french' in all_selections:
                subfolders.append('DSG')
            if 'full dsg' in all_selections:
                subfolders.append('Full DSGs')
            if 'special edition dsg' in all_selections:
                subfolders.append('Special DSG')
            if 'forward' in all_selections:
                subfolders.append('Forward')
            if 'childrens service' in all_selections:
                subfolders.append('Childrens Service')
            if 'audio' in all_selections:
                subfolders.append('Audio')
            if 'transcript' in all_selections:
                subfolders.append('Transcripts')
            if 'references' in all_selections or 'bible references' in all_selections:
                subfolders.append('Bible References')

            if subfolders:
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

                    items = extract_accordion_items(driver, timeout=8)
                    if not items:
                        print(f"No accordion items found on {ml['text']} page.")
                        continue

                    # The new filter_links function expects a flat list of link dicts
                    all_links = []
                    for _, links in items:
                        for link_text, href in links:
                            all_links.append({'text': link_text, 'href': href})
                    
                    filtered_links = filter_links(user_choices, all_links)

                    if filtered_links:
                        print(f"Accordion items on {ml['text']} page:")
                        for link in filtered_links:
                            lt = link['text']
                            lh = link['href']
                            print(f"    - {lt} -> {lh}")
                            try:
                                from src.config import DSGS_DIR
                                
                                # We need to find the original header for map_link_to_destination.
                                # Since we filtered `all_links` which are flat, we need to map back to original structure.
                                # A more robust way might be to pass header info through filtering.
                                # For now, let's assume `link_text` itself or part of `href` can give us a hint for subfolder.
                                # The subfolder logic in `map_link_to_destination` is based on flags, which can be derived from href.
                                # Let's pass a placeholder and rely on map_link_to_destination's internal flag detection.
                                dest, newname = map_link_to_destination(lh, lt, "", DSGS_DIR, month_year_str=ml['text'])
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
                                import traceback
                                print("        -> Could not map/save destination/filename:")
                                print(traceback.format_exc())
                    else:
                        print(f"No accordion items found on {ml['text']} page for selected filters.")

                    try:
                        driver.back()
                        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                        time.sleep(1)
                    except Exception:
                        pass

                schedule_files = []
                try:
                    schedule_elements = get_webpart_link_elements(driver, "Schedules", timeout=6)
                    schedule_months = []
                    for item in schedule_elements:
                        text = item.get('text') or ''
                        href = item.get('href') or ''
                        if href:
                            schedule_months.append({'text': text, 'href': href})

                    schedules_chosen = user_choices.get('schedules_chosen') or set()
                    if not schedules_chosen:
                        print("No schedules selected for download.")
                    else:
                        schedules_sub = user_choices.get('schedules_sub') or {}

                        for sm in schedule_months:
                            # Only process months that are selected
                            if not any(keyword in sm['text'] for keyword in schedules_chosen):
                                continue

                            print(f"Processing Schedules month: {sm['text']}")
                            full = urljoin(URL, sm['href'])
                            try:
                                driver.get(full)
                                WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                            except Exception as e:
                                print(f"  Could not open schedule page {sm['text']} ({sm['href']}):", e)
                                continue

                        try:
                            
                            sched_sections = extract_schedule_sections(driver, timeout=8)
                            if sched_sections:
                                print(f"  Options on {sm['text']}:")
                                for title, links in sched_sections:
                                    if schedules_chosen and title.lower() not in {s.lower() for s in schedules_chosen}:
                                        continue
                                    subs = schedules_sub.get(title, set()) or schedules_sub.get(title.title(), set())
                                    print(f"   - {title}")
                                    for lt, lh in links:
                                        if subs:
                                            match = False
                                            for s in subs:
                                                if s.lower() in lt.lower() or s.lower() in (lh or '').lower():
                                                    match = True
                                                    break
                                            if not match:
                                                continue

                                        print(f"       -> {lt} -> {lh}")
                                        try:
                                            from src.config import DSGS_DIR

                                            dest, newname = map_link_to_destination(lh, lt, title, DSGS_DIR, month_year_str=sm['text'])
                                            ok, reason = save_url_to_path(lh, dest, newname, driver=driver, overwrite=False)
                                            if ok:
                                                full_path = os.path.join(dest, newname)
                                                schedule_files.append(full_path)
                                                base_label = os.path.splitext(newname)[0]
                                                display_label = base_label
                                                if base_label.endswith(' Serving Schedule'):
                                                    display_label = base_label.replace(' Serving Schedule', ' Serving')
                                                print(f"        -> File Location <-- {full_path}")
                                                print(f"           New Name: <-- {display_label}")
                                            else:
                                                if reason == 'exists':
                                                    existing_path = os.path.join(dest, newname)
                                                    schedule_files.append(existing_path)
                                                    print(f"        -> Skipped (exists): {existing_path}")
                                                else:
                                                    print(f"        -> Failed to save ({reason}): {lh}")
                                        except Exception as e:
                                            import traceback
                                            print("        -> Could not map/save destination/filename:")
                                            print(traceback.format_exc())
                            else:
                                print(f"  No schedule sections found on {sm['text']}.")
                        except Exception as e:
                            print(f"  Error extracting schedule items for {sm['text']}:", e)

                        try:
                            driver.back()
                            WebDriverWait(driver, 8).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                        except Exception:
                            pass
                except Exception as e:
                    print("Schedules processing error:", e)
        except Exception as e:
            print("Error opening Divine Service Prep month or extracting items:", e)
    finally:
        print("Closing browser...")
        driver.quit()

        print("\n--- Starting Google Calendar Sync ---")
        import subprocess
        import sys

        subprocess.run([sys.executable, "tools/read_schedule.py"])

        filtered_files = [
            path for path in schedule_files 
            if "youth" not in path.lower() and "senior" not in path.lower() and "nacc calendar" not in path.lower()
        ]

        if filtered_files:
            print("\n--- Highlighting Minister Names in PDFs ---")
            
            name_color_map = user_choices.get('minister_colors', {})
            opacity = user_choices.get('highlight_opacity', 0.5)
            
            if name_color_map:
                try:
                    from src.pdf_tools.highlighter import highlight_names_in_pdf
                    for pdf_path in filtered_files:
                        print(f"Processing: {os.path.basename(pdf_path)}")
                        highlight_names_in_pdf(pdf_path, name_color_map, opacity)
                except Exception as e:
                    print(f"Error during highlighting process: {e}")
            else:
                print("No minister colors defined in UI. Skipping highlighting.")

if __name__ == "__main__":
    main()
