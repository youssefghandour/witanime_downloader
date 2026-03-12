"""
Site registry — maps domains to site plugin classes.

To add a new site:
  1. Create witanime_dl/sites/yoursite.py
  2. Import it here and add it to SITE_REGISTRY

The scraper auto-detects which plugin to use based on the URL provided.
"""

from witanime_dl.sites.witanime import WitanimeSite
from witanime_dl.sites.animeslayer import AnimeSlayerSite

# Maps domain fragments → plugin class
SITE_REGISTRY = {
    "witanime":    WitanimeSite,
    "animeslayer": AnimeSlayerSite,
}


def detect_site(url: str):
    """
    Given a URL, return the appropriate site plugin instance.
    Falls back to WitanimeSite if no domain matches.
    """
    url_lower = url.lower()
    for domain, cls in SITE_REGISTRY.items():
        if domain in url_lower:
            return cls()
    # Default
    return WitanimeSite()


__all__ = ["BaseSite", "WitanimeSite", "AnimeSlayerSite", "SITE_REGISTRY", "detect_site"]
