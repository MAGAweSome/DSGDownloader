"""
WebDriver initialization helper.

This module encapsulates Edge WebDriver creation logic. It prefers a locally
configured driver (via `EDGE_DRIVER_PATH`), otherwise tries webdriver-manager,
and finally checks PATH. Errors include actionable instructions.
"""
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os
from shutil import which
from src.config import EDGE_DRIVER_PATH, SKIP_WEBDRIVER_MANAGER


def init_driver():
    """Create and return a configured Edge WebDriver instance.

    The function tries, in order:
    1. `EDGE_DRIVER_PATH` if set and exists
    2. webdriver-manager automatic download
    3. `msedgedriver` on PATH

    It raises a RuntimeError with guidance if no driver can be obtained.
    """
    options = webdriver.EdgeOptions()
    options.use_chromium = True
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
            "Place msedgedriver.exe on your PATH or set EDGE_DRIVER_PATH in .env to its full path.\n"
            "Download: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
        )

    # Try webdriver-manager (automatic download)
    try:
        service = Service(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=options)
    except (requests.exceptions.ConnectionError, OSError) as e:
        # fallback: PATH
        path_driver = which("msedgedriver") or which("msedgedriver.exe")
        if path_driver:
            service = Service(path_driver)
            return webdriver.Edge(service=service, options=options)
        # Last resort: if local path exists and now accessible
        if local_path and os.path.exists(local_path):
            service = Service(local_path)
            return webdriver.Edge(service=service, options=options)
        raise RuntimeError(
            "Could not obtain EdgeDriver automatically. This is likely a network issue.\n"
            "Options:\n"
            " - Ensure you have a stable internet connection, OR\n"
            " - Download EdgeDriver manually (matching your Edge version) and set EDGE_DRIVER_PATH in .env, OR add the driver binary to your PATH."
        ) from e
    except Exception as e:
        # fallback: PATH
        path_driver = which("msedgedriver") or which("msedgedriver.exe")
        if path_driver:
            service = Service(path_driver)
            return webdriver.Edge(service=service, options=options)
        # Last resort: if local path exists and now accessible
        if local_path and os.path.exists(local_path):
            service = Service(local_path)
            return webdriver.Edge(service=service, options=options)
        raise RuntimeError(
            "Could not obtain EdgeDriver automatically.\n"
            "Options:\n"
            " - Ensure you have internet access so webdriver-manager can download the driver, OR\n"
            " - Download EdgeDriver manually (matching your Edge version) and set EDGE_DRIVER_PATH in .env, OR add the driver binary to your PATH."
        ) from e
