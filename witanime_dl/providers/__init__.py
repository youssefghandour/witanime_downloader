"""
Provider registry — maps provider names to their get_direct_url functions.

To add a new provider:
  1. Create witanime_dl/providers/myprovider.py
  2. Implement get_direct_url(share_url) -> (direct_url, size_bytes)
  3. Register it here
"""

from witanime_dl.providers import mediafire, mp4upload

PROVIDER_REGISTRY = {
    "mediafire": mediafire.get_direct_url,
    "mp4upload": mp4upload.get_direct_url,
}


def get_direct_url(provider: str, share_url: str) -> tuple[str | None, int | None]:
    """Dispatch to the correct provider. Returns (url, size_bytes) or (None, None)."""
    fn = PROVIDER_REGISTRY.get(provider)
    if not fn:
        print(f"  [provider] Unknown provider: {provider}")
        return None, None
    return fn(share_url)
