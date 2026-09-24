"""
Smart filtering and cleaning module to isolate music tracks.
Cleans YouTube titles (removes [Official Video], (Audio HD), 4K, etc.)
and extracts artist and song titles.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# Keywords indicating musical content
MUSIC_KEYWORDS = [
    "music", "musique", "audio", "soundtrack", "ost", "remix", "feat", "ft.",
    "prod.", "official video", "clip officiel", "clip", "lyrics", "paroles",
    "album", "single", "ep", "acoustic", "live", "cover", "instrumental",
    "official audio", "visualizer", "remastered", "extended mix", "original mix"
]

# Keywords indicating non-musical content (tutorials, vlogs, let's play, etc.)
NON_MUSIC_KEYWORDS = [
    "tutoriel", "tutorial", "how to", "comment faire", "gameplay", "let's play",
    "walkthrough", "vlog", "unboxing", "review", "critique", "podcast", "conférence",
    "news", "actualités", "journal", "reportage", "documentaire", "cours", "lesson",
    "speedrun", "highlights", "interview", "react", "reaction"
]

# Regex patterns to clean noise from YouTube titles
NOISE_PATTERNS = [
    r"\[\s*(?:official\s+)?(?:music\s+)?(?:video|audio|clip|hd|4k|lyric video|lyrics|paroles|visualizer|remastered|explicit)?\s*\]",
    r"\(\s*(?:official\s+)?(?:music\s+)?(?:video|audio|clip|hd|4k|lyric video|lyrics|paroles|visualizer|remastered|explicit)?\s*\)",
    r"\[\s*clip\s+officiel\s*\]",
    r"\(\s*clip\s+officiel\s*\)",
    r"\[\s*audio\s*\]",
    r"\(\s*audio\s*\)",
    r"\[\s*visualizer\s*\]",
    r"\(\s*visualizer\s*\)",
    r"\[\s*hd\s*\]",
    r"\[\s*4k\s*\]",
    r"\[\s*lyrics\s*\]",
    r"\(\s*lyrics\s*\)",
    r"\[\s*paroles\s*\]",
    r"\(\s*paroles\s*\)",
    r"\|.*$",  # Remove suffixes after pipe e.g.: "| Official Music Video"
    r"-\s*official\s+video.*$",
    r"-\s*clip\s+officiel.*$",
]


def clean_title(title: str) -> str:
    """Clean the YouTube title to retain only the essential track info."""
    cleaned = title
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    # Clean whitespace and orphan hyphens
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^[-–—]\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*[-–—]$", "", cleaned).strip()
    return cleaned


def split_artist_title(title: str, uploader: Optional[str] = None) -> Tuple[str, str]:
    """
    Extract artist and track title from the cleaned YouTube title.
    Examples:
      "Daft Punk - Get Lucky" -> ("Daft Punk", "Get Lucky")
      "Booba - DKR (Clip)" -> ("Booba", "DKR")
      "Get Lucky" (with uploader="Daft Punk - Topic") -> ("Daft Punk", "Get Lucky")
    """
    cleaned = clean_title(title)
    
    # Detect common separators: " - ", " – ", " — ", " : ", " // "
    separators = [" - ", " – ", " — ", " : ", " // "]
    for sep in separators:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)
            artist = parts[0].strip()
            track_title = parts[1].strip()
            # Strip surrounding quotes
            track_title = track_title.strip('"\'')
            return artist, track_title
            
    # If no separator found, inspect if uploader looks like an artist channel
    if uploader:
        clean_uploader = re.sub(r"\s*-\s*topic$", "", uploader, flags=re.IGNORECASE)
        clean_uploader = re.sub(r"\s*vevo$", "", clean_uploader, flags=re.IGNORECASE).strip()
        if clean_uploader and clean_uploader.lower() not in cleaned.lower():
            return clean_uploader, cleaned
        elif clean_uploader:
            return clean_uploader, cleaned

    return "", cleaned


def is_music_track(video: Dict[str, Any], max_duration_seconds: int = 1200) -> Tuple[bool, str]:
    """
    Determine if a video is likely to be a music track.
    
    :param video: Video metadata dictionary
    :param max_duration_seconds: Maximum duration threshold (e.g. 20 min) to exclude long videos
    :return: Tuple (is_music, reason)
    """
    title = video.get("title") or ""
    duration = video.get("duration") or 0
    uploader = video.get("uploader") or ""
    categories = video.get("categories") or []
    
    title_lower = title.lower()
    uploader_lower = uploader.lower()
    
    # 0. Skip deleted or empty titles
    if not title:
        return False, "Deleted or private video (no title)"

    # 1. Check official YouTube category
    if any((cat or "").lower() in ["music", "musique"] for cat in categories):
        return True, "YouTube 'Music' category"

    # 2. Topic / VEVO channel detection
    if " - topic" in uploader_lower or uploader_lower.endswith("vevo"):
        return True, "Official artist channel (Topic / VEVO)"

    # 3. Explicit YouTube Music metadata
    if video.get("track") or video.get("artist"):
        return True, "YouTube Music track/artist metadata"

    # 4. Non-music keyword exclusion
    for keyword in NON_MUSIC_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return False, f"Non-music keyword detected ('{keyword}')"

    # 5. Length exclusion (unless explicitly music tagged)
    if duration > max_duration_seconds and duration > 0:
        return False, f"Duration exceeds threshold ({duration // 60} min > {max_duration_seconds // 60} min)"

    # 6. Standard 'Artist - Title' separator presence
    if any(sep in title for sep in [" - ", " – ", " — "]):
        return True, "Standard 'Artist - Title' format"

    # 7. Music keywords presence (with word boundaries)
    for keyword in MUSIC_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return True, f"Music keyword detected ('{keyword}')"

    return False, "Not identified as music with certainty"


def filter_and_process_playlist(
    entries: List[Dict[str, Any]],
    filter_music_only: bool = True,
    max_duration_seconds: int = 1200
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process all playlist entries and split them into music and non-music items.
    """
    music_items = []
    other_items = []

    for entry in entries:
        if not entry:
            continue

        raw_title = entry.get("title") or "Untitled"
        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
        duration = entry.get("duration")
        uploader = entry.get("uploader") or entry.get("channel") or ""

        # Test music
        is_music, reason = is_music_track(entry, max_duration_seconds=max_duration_seconds)
        
        artist, track_name = split_artist_title(raw_title, uploader)

        item = {
            "id": entry.get("id"),
            "raw_title": raw_title,
            "clean_artist": artist,
            "clean_title": track_name,
            "uploader": uploader,
            "duration": duration,
            "duration_str": f"{int(duration)//60}:{int(duration)%60:02d}" if duration else "Unknown",
            "url": url,
            "detection_reason": reason,
            "is_music": is_music,
        }

        if is_music or not filter_music_only:
            music_items.append(item)
        else:
            other_items.append(item)

    return music_items, other_items
