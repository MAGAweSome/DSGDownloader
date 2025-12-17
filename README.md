Project: Simple Selenium Edge scraper

What it does
- Opens the page set in `.env` and returns the text (or `value`) of the button targeted by `BUTTON_SELECTOR`.

Files
- `src/config.py`: loads `.env` variables (`URL`, `BUTTON_SELECTOR`, `SELECTOR_TYPE`).
- `src/browser.py`: initializes Edge WebDriver (uses `webdriver-manager` to download driver).
- `src/actions.py`: finds the button and returns its text/value.
- `main.py`: runner that ties everything together.
 - `main.py`: runner that ties everything together and now clicks the site's "Sign In" element by default.

Setup (Windows PowerShell)

1) Create and activate a virtualenv (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

(If using cmd.exe: `.venv\Scripts\activate.bat`)

2) Install dependencies:

```powershell
pip install -r requirements.txt
```

3) Run the script:

```powershell
python main.py
```

Notes
- Ensure Microsoft Edge is installed. `webdriver-manager` will download the appropriate EdgeDriver.
- If Google changes markup, update `BUTTON_SELECTOR` in `.env` to the correct CSS or set `SELECTOR_TYPE=xpath` and provide an XPath.
 - The project now defaults to `https://naccanada.org` and clicks the "Sign In" element. If the site markup changes, update `BUTTON_SELECTOR` in `.env` (use `SELECTOR_TYPE=xpath` for XPath selectors).

Troubleshooting
- If EdgeDriver download fails, you can manually download a matching EdgeDriver and add it to PATH.
Manual EdgeDriver fallback

- If automatic download fails (offline, DNS, or corporate blocking), download the matching EdgeDriver for your Edge version from:
	https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

- Place `msedgedriver.exe` somewhere convenient and either:
	- Add its folder to your `PATH`, or
	- Set `EDGE_DRIVER_PATH` in `.env` to the full path to `msedgedriver.exe` (example: `C:\drivers\msedgedriver.exe`).

- The script will try (in order): `EDGE_DRIVER_PATH` from `.env`, automatic download via `webdriver-manager`, then look for `msedgedriver` on `PATH`.
 - The script will try (in order): `EDGE_DRIVER_PATH` from `.env`, automatic download via `webdriver-manager`, then look for `msedgedriver` on `PATH`.

Skip webdriver-manager (if it hangs)

- If webdriver-manager is causing long waits or hangs while detecting your Edge version, set `SKIP_WEBDRIVER_MANAGER=true` in `.env` to avoid calling webdriver-manager. When enabled, the script will only use `EDGE_DRIVER_PATH` or a driver found on `PATH`.
