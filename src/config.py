"""
Configuration values loaded from environment or `.env`.

Keep values minimal and documented so non-developers can review what is configurable.
"""

import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()
_env_vals = dotenv_values()

# URL of the site to open
URL = os.getenv("URL", "https://naccanada.org")

# Selectors used for sign-in and navigation. These are configurable via .env
BUTTON_SELECTOR = os.getenv("BUTTON_SELECTOR", "//a[contains(normalize-space(), 'Sign In')]")
SELECTOR_TYPE = os.getenv("SELECTOR_TYPE", "xpath")

SIGNIN_LINK_SELECTOR = os.getenv("SIGNIN_LINK_SELECTOR", "#ctl01_LoginStatus1")
SIGNIN_LINK_SELECTOR_TYPE = os.getenv("SIGNIN_LINK_SELECTOR_TYPE", "css")

USERNAME_SELECTOR = os.getenv("USERNAME_SELECTOR", "#ctl01_TemplateBody_WebPartManager1_gwpciNewContactSignInCommon_ciNewContactSignInCommon_signInUserName")
USERNAME_SELECTOR_TYPE = os.getenv("USERNAME_SELECTOR_TYPE", "css")

PASSWORD_SELECTOR = os.getenv("PASSWORD_SELECTOR", "#ctl01_TemplateBody_WebPartManager1_gwpciNewContactSignInCommon_ciNewContactSignInCommon_signInPassword")
PASSWORD_SELECTOR_TYPE = os.getenv("PASSWORD_SELECTOR_TYPE", "css")

SUBMIT_SELECTOR = os.getenv("SUBMIT_SELECTOR", "#ctl01_TemplateBody_WebPartManager1_gwpciNewContactSignInCommon_ciNewContactSignInCommon_SubmitButton")
SUBMIT_SELECTOR_TYPE = os.getenv("SUBMIT_SELECTOR_TYPE", "css")

# MiniHQ link selector
MINIHQ_LINK_SELECTOR = os.getenv("MINIHQ_LINK_SELECTOR", "#ctl01_Auxiliary_Auxiliary_rptWrapper_Auxiliary_rptWrapper_rpt_ctl02_NavigationLink")
MINIHQ_LINK_SELECTOR_TYPE = os.getenv("MINIHQ_LINK_SELECTOR_TYPE", "css")

# Local folder for saving DSGs
DSGS_DIR = os.getenv("DSGS_DIR", r"C:\Users\Marcus\OneDrive\Documents\Church\DSGs")

# Edge driver configuration
EDGE_DRIVER_PATH = os.getenv("EDGE_DRIVER_PATH", "")
_skip_raw = os.getenv("SKIP_WEBDRIVER_MANAGER", "false")
SKIP_WEBDRIVER_MANAGER = str(_skip_raw).strip().lower() in ("1", "true", "yes")

# Credentials: prefer values from project .env over OS environment
USERNAME = _env_vals.get("USERNAME") if _env_vals.get("USERNAME") is not None else os.getenv("USERNAME", "")
PASSWORD = _env_vals.get("PASSWORD") if _env_vals.get("PASSWORD") is not None else os.getenv("PASSWORD", "")
