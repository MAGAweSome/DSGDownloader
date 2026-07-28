"""
WebDriver initialization helper.

This module encapsulates Edge WebDriver creation logic. It prefers a locally
configured driver (via `EDGE_DRIVER_PATH`), otherwise tries webdriver-manager,
and finally checks PATH.
"""

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os
from shutil import which
from src.config import EDGE_DRIVER_PATH, SKIP_WEBDRIVER_MANAGER


def init_driver():
    options = webdriver.EdgeOptions()
    options.use_chromium = True
    
    # Check HEADLESS_DRIVER setting from .env
    headless_env = os.getenv("HEADLESS_DRIVER", "false").strip().lower()
    is_headless = headless_env in ("true", "1", "t", "yes")

    if is_headless:
        # Headless mode: run silently in background (useful for containers)
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
    else:
        # GUI mode: open normal visible browser window
        options.add_argument("--start-maximized")

    local_path = EDGE_DRIVER_PATH.strip() if isinstance(EDGE_DRIVER_PATH, str) else ""
    if local_path and os.path.exists(local_path):
        service = Service(local_path)
        return webdriver.Edge(service=service, options=options)

    if SKIP_WEBDRIVER_MANAGER:
        path_driver = which("msedgedriver") or which("msedgedriver.exe")
        if path_driver:
            service = Service(path_driver)
            return webdriver.Edge(service=service, options=options)
        raise RuntimeError(
            "SKIP_WEBDRIVER_MANAGER is enabled and no local EdgeDriver was found.\n"
            "Place msedgedriver.exe on your PATH or set EDGE_DRIVER_PATH in .env to its full path."
        )

    # Try webdriver-manager (automatic download)
    try:
        service = Service(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=options)
    except Exception as e:
        path_driver = which("msedgedriver") or which("msedgedriver.exe")
        if path_driver:
            service = Service(path_driver)
            return webdriver.Edge(service=service, options=options)
        if local_path and os.path.exists(local_path):
            service = Service(local_path)
            return webdriver.Edge(service=service, options=options)
        raise RuntimeError("Could not obtain EdgeDriver automatically.") from e