"""
Witanime site plugin — supports witanime.life (and mirror domains).

This is the reference implementation. Read this file if you want to
understand how to write a plugin for a new site.
"""

import re
from witanime_dl.sites.base import BaseSite

# Provider button keywords in Arabic and English
PROVIDER_KEYWORDS = {
    "mediafire":   ["mediafire", "\u0645\u064a\u062f\u064a\u0627 \u0641\u0627\u064a\u0631", "\u0645\u064a\u062f\u064a\u0627\u0641\u0627\u064a\u0631"],
    "googledrive": ["google drive", "\u062c\u0648\u062c\u0644 \u062f\u0631\u0627\u064a\u0641", "gdrive"],
    "mp4upload":   ["mp4upload", "mp4 upload"],
    "mega":        ["mega", "\u0645\u064a\u062c\u0627"],
}


class WitanimeSite(BaseSite):

    NAME    = "Witanime"
    DOMAINS = ["witanime.life", "witanime.cyou", "witanime.com", "witanime"]

    # Witanime uses Arabic URL-encoded episode slugs
    # e.g. https://witanime.life/episode/naruto-shippuuden-الحلقة-61/
    _URL_BASE = (
        "https://witanime.life/episode/"
        "naruto-shippuuden-%d8%a7%d9%84%d8%ad%d9%84%d9%82%d8%a9-{}/"
    )

    def __init__(self, base_url: str = None):
        """
        base_url: optional custom episode URL template with {} as episode number placeholder.
        If not provided, defaults to Naruto Shippuden.
        """
        self._url_template = base_url or self._URL_BASE

    def episode_url(self, ep_num: int) -> str:
        return self._url_template.format(ep_num)

    def ep_num_from_url(self, url: str) -> int | None:
        m = re.search(r"-(\d+)/?$", url)
        return int(m.group(1)) if m else None

    def find_provider_button(self, driver, provider: str):
        keywords = PROVIDER_KEYWORDS.get(provider, [provider])

        # 1. By button/link text
        el = self._find_by_keywords(driver, keywords)
        if el:
            return el

        # 2. By href containing the provider domain
        el = self._find_by_href_fragment(driver, provider)
        if el:
            return el

        # 3. By CSS class / data attributes
        css_selectors = [
            f"a[class*='{provider}']",
            f"a[data-url*='{provider}']",
            f"a[href*='{provider}']",
            f"li[class*='{provider}'] a",
            f"[data-link*='{provider}']",
        ]
        el = self._find_by_css(driver, css_selectors)
        if el:
            return el

        return None
