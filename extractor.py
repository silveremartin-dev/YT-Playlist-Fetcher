"""
Module for extracting YouTube playlists using yt-dlp.
Supports public, unlisted, and private playlists (LL, WL) via browser cookies or cookies.txt.
"""

import os
import glob
from typing import Any, Dict, List, Optional
import yt_dlp


def find_local_cookie_file() -> Optional[str]:
    """Automatically search for a local cookies.txt or youtube_cookies.txt file in the project folder."""
    patterns = ["*cookie*.txt", "cookies.txt", "youtube_cookies.txt", "*.cookies"]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return os.path.abspath(matches[0])
    return None


def extract_playlist(
    playlist_url: str,
    browser_for_cookies: Optional[str] = None,
    cookies_file: Optional[str] = None,
    flat_extraction: bool = True,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Extract all metadata from a YouTube playlist.
    """
    ydl_opts: Dict[str, Any] = {
        "extract_flat": "in_playlist" if flat_extraction else False,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }

    # 1. Check if a cookies file exists locally
    detected_cookie_file = cookies_file or find_local_cookie_file()
    if detected_cookie_file and os.path.exists(detected_cookie_file):
        if progress_callback:
            progress_callback(f"Using detected cookies file: {os.path.basename(detected_cookie_file)}")
        ydl_opts["cookiefile"] = detected_cookie_file
    elif browser_for_cookies:
        ydl_opts["cookiesfrombrowser"] = (browser_for_cookies,)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if progress_callback:
            progress_callback("Connecting and extracting playlist...")
        info = ydl.extract_info(playlist_url, download=False)
        return info or {}


def get_available_browsers() -> List[str]:
    """Return the list of supported browsers for cookie extraction."""
    return ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]
