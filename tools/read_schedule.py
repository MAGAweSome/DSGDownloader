# Import system tools to handle files, dates, and text patterns
import sys
import os
import glob
import pathlib
import datetime
import re

# Import the tool that creates pretty tables in your terminal
from prettytable import PrettyTable, HRuleStyle
# Import the tool that lets us use the private settings in your .env file
from dotenv import load_dotenv
# Import the function from your other file to send data to Google
from sync_calendar import create_google_event

# Load the private values (like your name) from the .env file
load_dotenv()

# Tell Python where the 'src' folder is so it can use your PDF reading tools
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import the specific actions for extracting text and finding files
from src.actions.file_system_actions import (
    extract_text_from_pdf,
    find_schedule_pdfs,
)

# This function takes a date like 'Sun Dec 28' and turns it into 'Sunday Dec 28'
def format_display_date(raw_date):
    # Create a dictionary to swap short day names for long ones
    day_map = {
        "Sun": "Sunday", "Mon": "Monday", "Tue": "Tuesday", 
        "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday"
    }
    # Use a pattern search to find the Day, Month, and Date number
    match = re.search(r'(\b\w{3})\b\s+(\b\w{3})\b\s+(\d{1,2})', raw_date)
    if match:
        short_day, month, day_num = match.groups()
        # Look up the long version of the day (e.g., Sunday)
        long_day = day_map.get(short_day, short_day)
        return f"{long_day} {month} {day_num}"
    return raw_date

# This is the main engine that looks through a single PDF for your name
def process_pdf(path: str, query: str | None = None):
    # Get the full path and the simple filename for the PDF
    p_abs = os.path.abspath(path)
    filename = os.path.basename(p_abs)
    
    # Pull the raw text out of the PDF file
    txt = extract_text_from_pdf(path)
    if not txt:
        return

    # Clean the text into individual lines and remove empty ones
    lines = [line for line in txt.splitlines() if line.strip()]
    if not lines:
        return

    # Look at the first line to see if it's the Title (like 'December 2025')
    first_row_cells = [c.strip() for c in lines[0].split("|")]
    content_cells = [c for c in first_row_cells if c]
    
    # If the first row only has one thing in it, it's the title
    if len(content_cells) == 1:
        table_title = content_cells[0]
        header_row_index = 1
    else:
        table_title = filename
        header_row_index = 0

    # Print a big visual divider in the terminal for this file
    print(f"\n{'='*120}")
    print(f" {table_title.upper()}")
    print(f"{'='*120}")

    # Break the header row into individual column names
    raw_headers = [h.strip() for h in lines[header_row_index].split("|")]
    headers = []
    counts = {}
    # Ensure every column has a unique name so the table doesn't break
    for h in raw_headers:
        name = h if h else "---"
        counts[name] = counts.get(name, -1) + 1
        headers.append(f"{name}_{counts[name]}" if counts[name] > 0 else name)
    
    # Create the visual grid table with specific styling
    full_table = PrettyTable(headers)
    full_table.align = "l"
    full_table.max_width = 25 
    full_table.hrules = HRuleStyle.ALL

    # Pull the list of cities from your .env file
    raw_locs = os.getenv("LOCATIONS", "")
    locations_list = [l.strip() for l in raw_locs.split(",")] if raw_locs else []

    # Loop through every row in the PDF
    final_matches = []
    for loc_row in lines[header_row_index + 1:]:
        cells = [c.strip() for c in loc_row.split("|")]
        if not cells: continue
        
        full_table.add_row(cells[:len(headers)])
        raw_location_cell = cells[0] 
        
        for idx, date_header in enumerate(headers):
            if idx == 0: continue 
            cell_content = cells[idx] if idx < len(cells) else ""
            
            # If your name is found, save it
            if query and query.lower() in cell_content.lower():
                display_date = format_display_date(date_header)
                final_matches.append({
                    "date": display_date,
                    "location": raw_location_cell
                })

    # Show the reconstructed schedule
    print(full_table)

    # Sync found assignments to Google
    if query and final_matches:
        print(f"\n--- Assignments Found for: {query} ---")
        res_table = PrettyTable(["DATE", "LOCATION"])
        res_table.hrules = HRuleStyle.ALL
        res_table.align = "l"
        
        for m in final_matches:
            clean_city = re.split(r'\b(?:Sun|Wed|Mon|Tue|Thu|Fri|Sat)\b', m['location'])[0].strip()
            res_table.add_row([m['date'], clean_city])
            create_google_event(m['date'], m['location'])
            
        print(res_table)

# The logic to find and scan the correct month folders
def main():
    if len(sys.argv) < 2:
        try:
            from src.config import DSGS_DIR
        except Exception:
            print("Error: Could not find your schedule directory.")
            return

        # 1. GET CURRENT MONTH INFO
        today = datetime.date.today()
        current_year = today.year
        current_month = today.strftime('%B')

        # 2. CALCULATE NEXT MONTH INFO (Handle Dec -> Jan)
        if today.month == 12:
            next_month_dt = datetime.date(current_year + 1, 1, 1)
        else:
            next_month_dt = datetime.date(current_year, today.month + 1, 1)
        
        next_month = next_month_dt.strftime('%B')
        next_year = next_month_dt.year

        # 3. BUILD FOLDER PATHS
        first_dir = os.path.join(DSGS_DIR, str(current_year), current_month, 'Schedules')
        second_dir = os.path.join(DSGS_DIR, str(next_year), next_month, 'Schedules')

        print(f"Today's date: {today.isoformat()}")
        print('\nChecking folders:')
        print(f"- {first_dir}")
        print(f"- {second_dir}")

        # 4. FIND ALL PDF FILES
        found = []
        for d in (first_dir, second_dir):
            if os.path.isdir(d):
                pdfs = sorted(glob.glob(os.path.join(d, '*.pdf')))
                if pdfs:
                    print(f"\nFound {len(pdfs)} file(s) in {d}:")
                    for f in pdfs:
                        print(f"  - {os.path.basename(f)}")
                    found.extend(pdfs)

        if not found:
            print('\nNo schedule PDFs discovered. Exiting.')
            return

        # 5. PROCESS EVERY DISCOVERED PDF
        search_name = os.getenv("SEARCH_NAME", "Dc. Marcus Grau")
        for f in found:
            process_pdf(f, search_name)
    else:
        # Handle manual file path or 'scan' command
        target = sys.argv[1]
        search_name = os.getenv("SEARCH_NAME", "Dc. Marcus Grau")
        process_pdf(target, search_name)

if __name__ == '__main__':
    main()