"""
Metadata enrichment and track identification module using iTunes and Deezer APIs.
Completely free, no API keys required.
"""

from typing import Any, Dict, Optional
import requests


def search_itunes_track(artist: str, title: str) -> Optional[Dict[str, Any]]:
    """
    Search for a song on the iTunes Search API.
    Returns official metadata (Artist, Title, Album, Genre, Year, Artwork, etc.).
    """
    query = f"{artist} {title}".strip()
    if not query:
        return None

    url = "https://itunes.apple.com/search"
    params = {
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("resultCount", 0) > 0:
                result = data["results"][0]
                return {
                    "matched_artist": result.get("artistName"),
                    "matched_title": result.get("trackName"),
                    "album": result.get("collectionName"),
                    "genre": result.get("primaryGenreName"),
                    "release_year": result.get("releaseDate", "")[:4] if result.get("releaseDate") else "",
                    "artwork_url": result.get("artworkUrl100"),
                    "preview_url": result.get("previewUrl"),
                    "service_url": result.get("trackViewUrl"),
                    "source": "iTunes",
                }
    except Exception:
        pass
    return None


def search_deezer_track(artist: str, title: str) -> Optional[Dict[str, Any]]:
    """
    Fallback search using Deezer API if iTunes does not return a match.
    """
    query = f"{artist} {title}".strip()
    if not query:
        return None

    url = "https://api.deezer.com/search"
    params = {
        "q": query,
        "limit": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                result = data["data"][0]
                return {
                    "matched_artist": result.get("artist", {}).get("name"),
                    "matched_title": result.get("title"),
                    "album": result.get("album", {}).get("title"),
                    "genre": "",
                    "release_year": "",
                    "artwork_url": result.get("album", {}).get("cover_medium"),
                    "preview_url": result.get("preview"),
                    "service_url": result.get("link"),
                    "source": "Deezer",
                }
    except Exception:
        pass
    return None


def identify_track(artist: str, title: str) -> Optional[Dict[str, Any]]:
    """
    Identify track by querying iTunes first, then Deezer as a fallback.
    """
    # 1. Try iTunes
    res = search_itunes_track(artist, title)
    if res:
        return res

    # 2. Try Deezer
    res = search_deezer_track(artist, title)
    if res:
        return res

    return None
