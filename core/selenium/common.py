import os

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


def initialize_driver():
    options = webdriver.FirefoxOptions()

    # Add headless mode if requested via environment variable
    if os.getenv("HEADLESS_BROWSER", "false").lower() == "true":
        options.add_argument("--headless")

    snap_tmp = os.path.expanduser("~/snap/firefox/common/tmp")
    os.makedirs(snap_tmp, exist_ok=True)
    os.environ["TMPDIR"] = snap_tmp

    # Use version parameter to use cached version and avoid GitHub API rate limits
    service = Service(GeckoDriverManager(version="v0.36.0").install())
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def close_driver(driver):
    driver.quit()
