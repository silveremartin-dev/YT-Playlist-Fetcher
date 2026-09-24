"""
Module d'extraction des playlists YouTube avec yt-dlp.
Supporte les playlists publiques, non répertoriées, et privées (LL, WL) via cookies de navigateur.
"""

import os
import glob
from typing import Any, Dict, List, Optional
import yt_dlp


def find_local_cookie_file() -> Optional[str]:
    """Recherche automatiquement un fichier cookies.txt ou youtube_cookies.txt dans le dossier du projet."""
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
    Extrait l'ensemble des métadonnées d'une playlist YouTube.
    """
    ydl_opts: Dict[str, Any] = {
        "extract_flat": "in_playlist" if flat_extraction else False,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }

    # 1. Vérifie si un fichier cookies existe localement
    detected_cookie_file = cookies_file or find_local_cookie_file()
    if detected_cookie_file and os.path.exists(detected_cookie_file):
        if progress_callback:
            progress_callback(f"Utilisation du fichier cookies détecté : {os.path.basename(detected_cookie_file)}")
        ydl_opts["cookiefile"] = detected_cookie_file
    elif browser_for_cookies:
        ydl_opts["cookiesfrombrowser"] = (browser_for_cookies,)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if progress_callback:
            progress_callback("Connexion et extraction de la playlist en cours...")
        info = ydl.extract_info(playlist_url, download=False)
        return info or {}



def get_available_browsers() -> List[str]:
    """Retourne la liste des navigateurs supportés pour les cookies."""
    return ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]
