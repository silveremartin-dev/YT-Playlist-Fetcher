"""
Playlist export module supporting multiple formats:
- CSV (Excel compatible with UTF-8-SIG encoding)
- JSON (Structured raw & enriched data)
- M3U8 (Compatible with media players like VLC)
- TXT (Direct format for Spotify / Soundiiz / Spotlistr / TuneMyMusic import)
"""

import csv
import json
import os
from typing import Any, Dict, List


def export_to_csv(items: List[Dict[str, Any]], output_filepath: str):
    """Export track list to a CSV file encoded in UTF-8-SIG (direct opening in Excel)."""
    fieldnames = [
        "Index",
        "Artist",
        "Title",
        "Album",
        "Genre",
        "Year",
        "Duration",
        "Raw YouTube Title",
        "Channel / Uploader",
        "YouTube URL",
        "Music Link",
        "Identification Source",
    ]

    with open(output_filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for idx, item in enumerate(items, 1):
            writer.writerow({
                "Index": idx,
                "Artist": item.get("clean_artist") or item.get("matched_artist") or "",
                "Title": item.get("clean_title") or item.get("matched_title") or "",
                "Album": item.get("album") or "",
                "Genre": item.get("genre") or "",
                "Year": item.get("release_year") or "",
                "Duration": item.get("duration_str") or "",
                "Raw YouTube Title": item.get("raw_title") or "",
                "Channel / Uploader": item.get("uploader") or "",
                "YouTube URL": item.get("url") or "",
                "Music Link": item.get("service_url") or "",
                "Identification Source": item.get("source") or item.get("detection_reason") or "",
            })


def export_to_json(items: List[Dict[str, Any]], output_filepath: str):
    """Export raw and enriched items to JSON format."""
    with open(output_filepath, mode="w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def export_to_spotify_txt(items: List[Dict[str, Any]], output_filepath: str):
    """
    Export simple 'Artist - Title' format (1 line per track),
    ideal for copy-pasting into Spotlistr, TuneMyMusic, or Soundiiz.
    """
    with open(output_filepath, mode="w", encoding="utf-8") as f:
        for item in items:
            artist = item.get("clean_artist") or item.get("matched_artist") or ""
            title = item.get("clean_title") or item.get("matched_title") or item.get("raw_title") or ""
            if artist:
                f.write(f"{artist} - {title}\n")
            else:
                f.write(f"{title}\n")


def export_to_m3u8(items: List[Dict[str, Any]], output_filepath: str, playlist_title: str = "YouTube Music"):
    """Export an M3U8 playlist with direct YouTube URLs."""
    with open(output_filepath, mode="w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#PLAYLIST:{playlist_title}\n\n")
        for item in items:
            duration = item.get("duration") or -1
            artist = item.get("clean_artist") or item.get("matched_artist") or item.get("uploader") or "Unknown"
            title = item.get("clean_title") or item.get("matched_title") or item.get("raw_title") or "Unknown"
            url = item.get("url") or ""
            
            f.write(f"#EXTINF:{duration},{artist} - {title}\n")
            f.write(f"{url}\n\n")
