"""
Module d'exportation des données de playlist sous différents formats :
- CSV (compatible Excel avec encodage UTF-8-SIG)
- JSON
- M3U8 (compatible lecteurs multimédias)
- TXT (format direct pour import Spotify / Soundiiz / Spotlistr)
"""

import csv
import json
import os
from typing import Any, Dict, List


def export_to_csv(items: List[Dict[str, Any]], output_filepath: str):
    """Exporte la liste dans un fichier CSV encodé en UTF-8-SIG (ouverture directe dans Excel)."""
    fieldnames = [
        "Index",
        "Artiste Identifié",
        "Titre Identifié",
        "Album",
        "Genre",
        "Année",
        "Durée",
        "Titre Brut YouTube",
        "Chaine / Uploader",
        "URL YouTube",
        "Lien Musique",
        "Source Identification",
    ]

    with open(output_filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for idx, item in enumerate(items, 1):
            writer.writerow({
                "Index": idx,
                "Artiste Identifié": item.get("clean_artist") or item.get("matched_artist") or "",
                "Titre Identifié": item.get("clean_title") or item.get("matched_title") or "",
                "Album": item.get("album") or "",
                "Genre": item.get("genre") or "",
                "Année": item.get("release_year") or "",
                "Durée": item.get("duration_str") or "",
                "Titre Brut YouTube": item.get("raw_title") or "",
                "Chaine / Uploader": item.get("uploader") or "",
                "URL YouTube": item.get("url") or "",
                "Lien Musique": item.get("service_url") or "",
                "Source Identification": item.get("source") or item.get("detection_reason") or "",
            })


def export_to_json(items: List[Dict[str, Any]], output_filepath: str):
    """Exporte la liste brute et enrichie au format JSON."""
    with open(output_filepath, mode="w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def export_to_spotify_txt(items: List[Dict[str, Any]], output_filepath: str):
    """
    Exporte au format simple 'Artiste - Titre' (1 ligne par morceau),
    parfait pour le copier-coller dans Spotlistr, TuneMyMusic ou Soundiiz.
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
    """Exporte une playlist M3U8 avec liens directs."""
    with open(output_filepath, mode="w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#PLAYLIST:{playlist_title}\n\n")
        for item in items:
            duration = item.get("duration") or -1
            artist = item.get("clean_artist") or item.get("matched_artist") or item.get("uploader") or "Inconnu"
            title = item.get("clean_title") or item.get("matched_title") or item.get("raw_title") or "Inconnu"
            url = item.get("url") or ""
            
            f.write(f"#EXTINF:{duration},{artist} - {title}\n")
            f.write(f"{url}\n\n")
