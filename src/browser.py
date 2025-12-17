from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os
from shutil import which
from src.config import EDGE_DRIVER_PATH, SKIP_WEBDRIVER_MANAGER


def init_driver():
    """Initialize Edge WebDriver using webdriver-manager and return the driver."""
    options = webdriver.EdgeOptions()
    options.use_chromium = True
    options.add_argument("--start-maximized")
    # First, check for an explicit local driver path from env (EDGE_DRIVER_PATH)
    local_path = EDGE_DRIVER_PATH.strip() if isinstance(EDGE_DRIVER_PATH, str) else ""
    if local_path:
        if os.path.exists(local_path):
            service = Service(local_path)
            return webdriver.Edge(service=service, options=options)
        else:
            print(f"EDGE_DRIVER_PATH is set but not found: {local_path}")

    # If user requested to skip webdriver-manager (e.g., offline or it hangs), only
    # try local path and PATH lookup, then error out with instructions.
    if SKIP_WEBDRIVER_MANAGER:
        # Try PATH
        path_driver = which("msedgedriver") or which("msedgedriver.exe")
        if path_driver:
            service = Service(path_driver)
            return webdriver.Edge(service=service, options=options)
        raise RuntimeError(
            "SKIP_WEBDRIVER_MANAGER is enabled and no local EdgeDriver was found.\n"
            "Place msedgedriver.exe on your PATH or set EDGE_DRIVER_PATH in .env to its full path.\n"
            "Download: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
        )

    # Try automatic download via webdriver-manager; if that fails (offline/network),
    # fallback to searching PATH for msedgedriver.exe or raise a helpful error.
    try:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        return driver
    except Exception as e:
        print("Automatic msedgedriver download failed:", e)
        # If env var exists and file is present, use it
        if local_path and os.path.exists(local_path):
            service = Service(local_path)
            return webdriver.Edge(service=service, options=options)

        # Try to find msedgedriver on PATH
        path_driver = which("msedgedriver") or which("msedgedriver.exe")
        if path_driver:
            service = Service(path_driver)
            return webdriver.Edge(service=service, options=options)

        raise RuntimeError(
            "Could not obtain EdgeDriver automatically.\n"
            "Options:\n"
            " - Ensure you have internet access so webdriver-manager can download the driver, OR\n"
            " - Download EdgeDriver manually (matching your Edge version) from https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/ and set EDGE_DRIVER_PATH in your .env, OR add the driver binary to your PATH."
        ) from e
