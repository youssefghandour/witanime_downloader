"""
AnimeSlayer site plugin — example plugin showing how to add a new site.

AnimeSlayer (animeslayer.eu) is a popular Arabic anime site with a
different URL structure and button layout than witanime.

To activate: it's already registered in sites/__init__.py.
The scraper will auto-detect which plugin to use based on the URL you provide.
"""

import re
from witanime_dl.sites.base import BaseSite


class AnimeSlayerSite(BaseSite):

    NAME    = "AnimeSlayer"
    DOMAINS = ["animeslayer.eu", "animeslayer.com", "animeslayer"]

    # AnimeSlayer uses a different URL pattern
    # e.g. https://animeslayer.eu/anime/naruto-shippuden/ep-61/
    _URL_BASE = "https://animeslayer.eu/anime/{anime_slug}/ep-{ep}/"

    def __init__(self, anime_slug: str = "naruto-shippuden"):
        self._anime_slug = anime_slug

    def episode_url(self, ep_num: int) -> str:
        return self._URL_BASE.format(anime_slug=self._anime_slug, ep=ep_num)

    def ep_num_from_url(self, url: str) -> int | None:
        m = re.search(r"/ep-(\d+)/?$", url)
        return int(m.group(1)) if m else None

    def find_provider_button(self, driver, provider: str):
        # AnimeSlayer uses different class names — adjust to what you see
        # on the actual site (check a debug_epXXX.txt file)
        keywords = {
            "mediafire":   ["mediafire", "\u0645\u064a\u062f\u064a\u0627 \u0641\u0627\u064a\u0631"],
            "googledrive": ["google", "drive"],
            "mp4upload":   ["mp4upload"],
        }.get(provider, [provider])

        el = self._find_by_keywords(driver, keywords)
        if el:
            return el

        el = self._find_by_href_fragment(driver, provider)
        if el:
            return el

        return None

    # NOTE: AnimeSlayer has an episode list page — override find_max_episode
    # to use it instead of probing one by one (faster and more reliable)
    # Uncomment and implement when you have access to the site:
    #
    # def find_max_episode(self, driver) -> int:
    #     list_url = f"https://animeslayer.eu/anime/{self._anime_slug}/"
    #     driver.get(list_url)
    #     time.sleep(3)
    #     # parse episode list and return the highest number
    #     ...
