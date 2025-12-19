# ⛪ DSG and Schedule Downloader

An automated tool to download church schedules and sync your personal assignments directly to **Google Calendar**.

## ✨ Features
- **Automatic Downloads**: Scrapes the NACC website for the latest schedules.
- **Smart Parsing**: Reads PDF grids to find exactly where you are scheduled.
- **Calendar Sync**: Automatically creates Google Calendar events with 24 hour reminders.
- **Duplicate Prevention**: Skips events already on your calendar.

---

## 🚀 Getting Started

## 🛠️ Prerequisites
Before starting, ensure you have these installed:
1. **Python 3.10 or higher**: [Download here](https://www.python.org/downloads/)
2. **Git**: [Download here](https://git-scm.com/downloads) (Required for the 'git clone' command).

### 1. Clone and Install

Open your terminal and run:

```powershell
# Clone the repository
git clone https://github.com/MAGAweSome/DSGDownloader.git
cd DSGDownloader

# Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

---

## 2. Google Calendar API Setup (Detailed)

This step allows the program to safely communicate with your Google Calendar. Follow these steps exactly.

### Step 1: Open Google Cloud Console
Go to:  
https://console.cloud.google.com/

---

### Step 2: Create a Project
1. Click the project dropdown at the top left.  
2. Select **New Project**.  
3. Name it **My Calendar Sync**.  
4. Click **Create**.

---

### Step 3: Enable the Google Calendar API
1. In the search bar at the top, type **Google Calendar API**.  
2. Click it in the results.  
3. Click the blue **Enable** button.

---

### Step 4: Configure OAuth Consent Screen
1. On the left sidebar, click **APIs and Services** > **OAuth consent screen**.  
2. Select **External** and click **Create**.  
3. Fill in:
   - **App name** (example: My Sync)  
   - **User support email**  
   - **Developer contact info**  
4. Click **Save and Continue** through the remaining pages.

---

### Step 5: Create OAuth Credentials
1. On the left sidebar, click **Credentials**.  
2. Click **+ Create Credentials** at the top.  
3. Choose **OAuth client ID**.  
4. For **Application type**, select **Desktop App**.  
5. Name it **My Desk Sync**.  
6. Click **Create**.

---

### Step 6: Download Your Key
1. A box will appear saying **OAuth client created**.  
2. Click **Download JSON**.  
3. Go to your Downloads folder and rename the file to:  
   **credentials.json**  
4. Move it into your **DSGDownloader** project folder.

---

### 3. Configure Your Environment

1. Copy `.env.example` and rename it to `.env`.  
2. Fill in your NAC website `USERNAME` and `PASSWORD`.  
3. Set `SEARCH_NAME` to your name exactly as it appears on the PDF schedule.

---

## 📅 How to Run

Simply run the main orchestrator:

```powershell
python main.py
```

### What happens next

- **Selection**: A window pops up for you to select which schedules or DSGs to download.  
- **Download**: Microsoft Edge opens and automatically downloads your files into organized folders.  
- **Parsing**: The script scans the new PDFs for your `SEARCH_NAME`.  
- **Sync**: If matches are found, they are pushed to Google Calendar.  
  - On the first run, a browser tab will open for you to authorize the application.

---

## 🛡️ Security Note

This project uses a `.gitignore` file to ensure your `credentials.json`, `token.json`, and `.env` files are never uploaded to GitHub.  
Never share these files or your Client Secret with anyone.

---
