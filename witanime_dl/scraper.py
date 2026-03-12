"""
Core scraper engine.

Responsibilities:
- Click the provider button on an episode page (Selenium)
- Capture the resulting share URL
- Hand off to the provider module to get the direct URL
- Handle all the messy edge cases: new tabs, JS delays, ad redirects
"""

import re
import time
from selenium.webdriver.common.by import By

from witanime_dl.config import cfg
from witanime_dl.providers import get_direct_url
from witanime_dl.utils import dump_debug


def click_provider_button(driver, button) -> str | None:
    """
    Click a provider button and capture the resulting URL through 5 strategies:
    1. href updated dynamically after click
    2. New tab opened
    3. Current tab navigated away
    4. DOM scan for new links after click
    5. Page source regex scan
    """
    original_handles = set(driver.window_handles)
    original_url     = driver.current_url

    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    time.sleep(0.4)
    try:
        button.click()
    except Exception:
        driver.execute_script("arguments[0].click();", button)
    time.sleep(3)

    # Strategy 1: href set dynamically
    try:
        href = button.get_attribute("href") or ""
        if href.startswith("http") and "#" not in href:
            return href
    except Exception:
        pass

    # Strategy 2: new tab
    new_handles = set(driver.window_handles) - original_handles
    if new_handles:
        driver.switch_to.window(new_handles.pop())
        url = driver.current_url
        driver.close()
        driver.switch_to.window(list(original_handles)[0])
        if url.startswith("http") and url != "about:blank":
            return url

    # Strategy 3: tab navigated
    current = driver.current_url
    if current != original_url and current != "about:blank":
        driver.back()
        time.sleep(2)
        return current

    # Strategy 4: DOM scan
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href") or ""
        if href.startswith("http") and "#" not in href and href != original_url:
            return href

    # Strategy 5: page source scan (broad)
    m = re.search(r'https?://(?:www\.)?(?:mediafire|mp4upload|drive\.google|mega)\.(?:com|nz)/\S+',
                  driver.page_source)
    if m:
        url = m.group(0).rstrip("'\"\\)>")
        if "#" not in url:
            return url

    return None


def process_episode(driver, site, ep_num: int) -> tuple[str | None, int | None]:
    """
    Full pipeline for one episode:
      1. Load the episode page
      2. Find and click the provider button
      3. Capture the share URL
      4. Extract the direct download URL + file size

    Returns (direct_url, size_bytes) or (None, None) on failure.
    """
    provider = cfg.preferred_provider

    # Load page with ad-redirect protection
    loaded = site.load_episode_page(driver, ep_num)
    if not loaded:
        return None, None

    # Find the provider button
    button = site.find_provider_button(driver, provider)

    # Fallback: try other providers if preferred one not found
    if not button:
        fallback_providers = [p for p in ["mediafire", "mp4upload", "googledrive"] if p != provider]
        for fallback in fallback_providers:
            button = site.find_provider_button(driver, fallback)
            if button:
                print(f"  [!] {provider} not found, using {fallback} instead")
                provider = fallback
                break

    if not button:
        dump_debug(driver, ep_num)
        print(f"  [x] No provider button found for episode {ep_num}")
        return None, None

    # Click and capture share URL
    share_url = click_provider_button(driver, button)
    if not share_url:
        print(f"  [x] Could not capture share URL for episode {ep_num}")
        return None, None

    print(f"  -> {provider}: {share_url}")

    # Extract direct URL from share page
    direct_url, size_bytes = get_direct_url(provider, share_url)
    return direct_url, size_bytes
