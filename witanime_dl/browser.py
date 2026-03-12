"""
Browser setup — returns a configured Selenium WebDriver.
Prefers Brave for its built-in ad blocking, falls back to Chrome.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from witanime_dl.config import cfg


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    # Use Brave if available and configured
    if cfg.browser == "brave" and os.path.exists(cfg.brave_path):
        opts.binary_location = cfg.brave_path
        print("  [browser] Using Brave (ad blocking active)")
    else:
        print("  [browser] Using Chrome")

    # Always use SeleniumManager (built into Selenium 4.6+) instead of
    # webdriver-manager — it automatically downloads the correct ChromeDriver
    # version to match whatever browser version you have installed.
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(cfg.page_timeout)
    return driver


def load_page_safely(driver, url: str, retries: int = 3) -> bool:
    from selenium.common.exceptions import TimeoutException
    import time

    for attempt in range(1, retries + 1):
        try:
            driver.get(url)
        except TimeoutException:
            print(f"  [browser] Timed out loading {url[:60]} (attempt {attempt}/{retries})")
            time.sleep(2)
            continue
        time.sleep(cfg.js_wait)
        return True

    return False
