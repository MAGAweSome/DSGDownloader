# Import tools for Google API, timezones, and text patterns
import os.path
import re
import pytz
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define what permissions we need (Reading and Writing to the Calendar)
SCOPES = ['https://www.googleapis.com/auth/calendar']

# This function handles the "Login" with Google
def get_calendar_service():
    creds = None
    # Check if we already have a 'token.json' file (logged in previously)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If not logged in, or the login expired, start the login process
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Look for your 'credentials.json' file from the Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the login info into 'token.json' so you don't have to log in next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Build the official Google Calendar connection tool
    return build('calendar', 'v3', credentials=creds)

# This is the main function that puts your assignment into Google Calendar
def create_google_event(date_str, location_str, title=None):
    try:
        # Get our connection to Google
        service = get_calendar_service()
        
        # 1. Figure out the Year and Time
        now = datetime.now()
        year = now.year
        # If it's currently December but the schedule is for January, it's next year
        if now.month == 12 and "Jan" in date_str:
            year += 1

        # Use a pattern search to find the time (like 10:30 AM) in the location text
        time_match = re.search(r'(\d{1,2}:\d{2}\s+[AP]M)', location_str)
        if not time_match: 
            return
        
        # Combine the date and time into a format Python understands
        clean_time = time_match.group(1)
        start_dt = datetime.strptime(f"{date_str} {year} {clean_time}", "%A %b %d %Y %I:%M %p")
        
        # Get your settings (Timezone, how long the service is, and reminder time) from .env
        tz_name = os.getenv("LOCAL_TIMEZONE", "America/Toronto")
        duration = float(os.getenv("SERVICE_DURATION_HOURS", 1.5))
        reminder_min = int(os.getenv("REMINDER_MINUTES", 1440))
        
        # Attach the correct timezone (Toronto) to the time
        local_tz = pytz.timezone(tz_name)
        start_dt = local_tz.localize(start_dt)
        # Calculate when the service ends (e.g., 1.5 hours after it starts)
        end_dt = start_dt + timedelta(hours=duration)

        # 2. Get the City Name and set the Event Title
        city_name = re.split(r'\b(?:Sun|Wed|Mon|Tue|Thu|Fri|Sat)\b', location_str)[0].strip()
        if title is None:
            title = f"Scheduled in {city_name}"

        # 3. Check for Duplicates (So we don't add the same service twice)
        # Search a 5-minute window around the start time
        time_min = (start_dt - timedelta(minutes=5)).isoformat()
        time_max = (start_dt + timedelta(minutes=5)).isoformat()
        
        # Ask Google for a list of events already in that time slot
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min, 
            timeMax=time_max,
            singleEvents=True
        ).execute()
        
        # If an event with the same title exists, skip adding it
        existing_events = events_result.get('items', [])
        for event in existing_events:
            if event.get('summary') == title:
                print(f"Skipping: '{title}' already exists in your calendar.")
                return 

        # 4. Create the Calendar Event
        event_body = {
            'summary': title,
            'location': city_name,
            'description': f'Scheduled service at {city_name}',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': tz_name,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': tz_name,
            },
            'reminders': {
                'useDefault': False,
                # Set the custom reminder (e.g., 1440 minutes = 1 day before)
                'overrides': [{'method': 'popup', 'minutes': reminder_min}],
            },
        }

        # Send the event to Google and print the success message
        service.events().insert(calendarId='primary', body=event_body).execute()
        print(f"Successfully created: {title} on {date_str}")

    except Exception as e:
        # If anything goes wrong, print the error so we can fix it
        print(f"Error managing Google event: {e}")