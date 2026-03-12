"""
BaseSite — the interface every site plugin must implement.

To add support for a new anime site:
  1. Create witanime_dl/sites/yoursite.py
  2. Subclass BaseSite
  3. Implement the three required methods
  4. Register it in witanime_dl/sites/__init__.py

That's it. Everything else (clicking, URL extraction, saving, size tracking)
is handled by the core engine.
"""

from __future__ import annotations
import re
import time
from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By

from witanime_dl.config import cfg


class BaseSite(ABC):
    """
    Abstract base class for anime site plugins.

    Each plugin represents one website and knows:
    - Which domains it handles
    - How to build an episode URL from a number
    - How to find the download provider buttons on its pages
    - How to extract the episode number from its URLs
    """

    # ── Required: override these in your plugin ────────────────────────────────

    # List of domains this plugin handles, e.g. ["witanime.life", "witanime.cyou"]
    DOMAINS: list[str] = []

    # Human-readable name shown in logs
    NAME: str = "Unknown Site"

    @abstractmethod
    def episode_url(self, ep_num: int) -> str:
        """Return the full URL for episode ep_num."""
        ...

    @abstractmethod
    def find_provider_button(self, driver, provider: str):
        """
        Find and return the Selenium element for the given provider's button.
        provider is a string like "mediafire", "googledrive", "mp4upload".
        Return None if the button is not found.
        """
        ...

    @abstractmethod
    def ep_num_from_url(self, url: str) -> int | None:
        """Extract and return the episode number from a witanime episode URL."""
        ...

    # ── Optional: override for custom behavior ─────────────────────────────────

    def is_valid_page(self, driver) -> bool:
        """
        Return True if the driver is currently on a valid episode page for this site.
        Default: checks that any of DOMAINS appears in the current URL.
        Override if your site uses redirects internally.
        """
        current = driver.current_url.lower()
        return any(domain.lower() in current for domain in self.DOMAINS)

    def load_episode_page(self, driver, ep_num: int) -> bool:
        """
        Load an episode page, retrying up to 3 times if redirected by ads.
        Returns True if the page loaded successfully.
        """
        url = self.episode_url(ep_num)
        for attempt in range(1, 4):
            try:
                driver.get(url)
            except Exception:
                pass
            time.sleep(cfg.js_wait)
            if self.is_valid_page(driver):
                return True
            print(f"  [!] Redirected to {driver.current_url[:60]}... retrying ({attempt}/3)")
            time.sleep(3)
        print(f"  [x] Could not load episode {ep_num} after 3 attempts")
        return False

    def find_max_episode(self, driver) -> int:
        """
        Find the highest episode number available on this site.
        Probes in steps of 25, then refines one-by-one.
        Override if your site has a better way (e.g. an episode list page).
        """
        print(f"  Probing {self.NAME} for latest episode...")
        max_ep   = cfg.start_episode
        step     = 25

        probe = cfg.start_episode
        while probe <= cfg.max_episode:
            url = self.episode_url(probe)
            try:
                driver.get(url)
                time.sleep(4)
            except Exception:
                break
            if self.is_valid_page(driver):
                max_ep = probe
                probe += step
            else:
                break

        # Refine: one-by-one from last confirmed good
        for ep in range(max_ep + 1, max_ep + step + 1):
            if ep > cfg.max_episode:
                break
            url = self.episode_url(ep)
            try:
                driver.get(url)
                time.sleep(4)
            except Exception:
                break
            if self.is_valid_page(driver):
                max_ep = ep
            else:
                break

        print(f"  Latest episode: {max_ep}")
        return max_ep

    # ── Helpers available to subclasses ───────────────────────────────────────

    def _find_by_keywords(self, driver, keywords: list[str]):
        """Find any <a> or <button> whose text contains one of the keywords."""
        for el in driver.find_elements(By.TAG_NAME, "a") + driver.find_elements(By.TAG_NAME, "button"):
            text = el.text.strip().lower()
            if any(kw.lower() in text for kw in keywords):
                return el
        return None

    def _find_by_href_fragment(self, driver, fragment: str):
        """Find any <a> whose href contains a given string."""
        for el in driver.find_elements(By.TAG_NAME, "a"):
            if fragment in (el.get_attribute("href") or ""):
                return el
        return None

    def _find_by_css(self, driver, selectors: list[str]):
        """Try a list of CSS selectors, return first match."""
        for sel in selectors:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                return els[0]
        return None
