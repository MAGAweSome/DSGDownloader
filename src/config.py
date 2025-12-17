from dotenv import load_dotenv, dotenv_values
import os

load_dotenv()
_env_vals = dotenv_values()

# URL of the page to open (default now set to naccanada.org)
URL = os.getenv("URL", "https://naccanada.org")

# Default selector targets a typical "Sign In" link/button on the site.
# We use an XPath that looks for an anchor or element with text "Sign In"; change
# to a more specific selector if the site markup differs.
BUTTON_SELECTOR = os.getenv("BUTTON_SELECTOR", "//a[contains(normalize-space(), 'Sign In')]")
SELECTOR_TYPE = os.getenv("SELECTOR_TYPE", "xpath")

# Precise selectors for the naccanada.org login flow (defaults to the values you provided)
SIGNIN_LINK_SELECTOR = os.getenv("SIGNIN_LINK_SELECTOR", "#ctl01_LoginStatus1")
SIGNIN_LINK_SELECTOR_TYPE = os.getenv("SIGNIN_LINK_SELECTOR_TYPE", "css")

USERNAME_SELECTOR = os.getenv("USERNAME_SELECTOR", "#ctl01_TemplateBody_WebPartManager1_gwpciNewContactSignInCommon_ciNewContactSignInCommon_signInUserName")
USERNAME_SELECTOR_TYPE = os.getenv("USERNAME_SELECTOR_TYPE", "css")

PASSWORD_SELECTOR = os.getenv("PASSWORD_SELECTOR", "#ctl01_TemplateBody_WebPartManager1_gwpciNewContactSignInCommon_ciNewContactSignInCommon_signInPassword")
PASSWORD_SELECTOR_TYPE = os.getenv("PASSWORD_SELECTOR_TYPE", "css")

SUBMIT_SELECTOR = os.getenv("SUBMIT_SELECTOR", "#ctl01_TemplateBody_WebPartManager1_gwpciNewContactSignInCommon_ciNewContactSignInCommon_SubmitButton")
SUBMIT_SELECTOR_TYPE = os.getenv("SUBMIT_SELECTOR_TYPE", "css")

# MiniHQ link (provided id)
MINIHQ_LINK_SELECTOR = os.getenv("MINIHQ_LINK_SELECTOR", "#ctl01_Auxiliary_Auxiliary_rptWrapper_Auxiliary_rptWrapper_rpt_ctl02_NavigationLink")
MINIHQ_LINK_SELECTOR_TYPE = os.getenv("MINIHQ_LINK_SELECTOR_TYPE", "css")

# Local folder containing DSG PDF/HTML files
DSGS_DIR = os.getenv("DSGS_DIR", r"C:\Users\Marcus\OneDrive\Documents\Church\DSGs")
# Optional: path to a locally downloaded msedgedriver executable. If set, this will be used
# when automatic download via `webdriver-manager` fails (e.g., offline or DNS issues).
EDGE_DRIVER_PATH = os.getenv("EDGE_DRIVER_PATH", "")
# Optionally skip webdriver-manager entirely (useful when offline or when webdriver-manager hangs).
# Set to 'true', '1', or 'yes' to enable.
_skip_raw = os.getenv("SKIP_WEBDRIVER_MANAGER", "false")
SKIP_WEBDRIVER_MANAGER = str(_skip_raw).strip().lower() in ("1", "true", "yes")

# Credentials (empty by default). Prefer values from the project's .env file
# so an OS environment variable like USERNAME (Windows account) doesn't override them.
USERNAME = _env_vals.get("USERNAME") if _env_vals.get("USERNAME") is not None else os.getenv("USERNAME", "")
PASSWORD = _env_vals.get("PASSWORD") if _env_vals.get("PASSWORD") is not None else os.getenv("PASSWORD", "")
