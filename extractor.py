"""
Module d'extraction des playlists YouTube avec yt-dlp.
Supporte les playlists publiques, non répertoriées, et privées (LL, WL) via cookies de navigateur.
"""

from typing import Any, Dict, List, Optional
import yt_dlp


def extract_playlist(
    playlist_url: str,
    browser_for_cookies: Optional[str] = None,
    cookies_file: Optional[str] = None,
    flat_extraction: bool = True,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Extrait l'ensemble des métadonnées d'une playlist YouTube.
    
    :param playlist_url: URL de la playlist (ex: https://www.youtube.com/playlist?list=LL ou WL)
    :param browser_for_cookies: Nom du navigateur pour extraire la session ('chrome', 'firefox', 'edge', 'brave', etc.)
    :param cookies_file: Chemin vers un fichier cookies.txt (alternative au navigateur)
    :param flat_extraction: Si True, extraction ultra rapide sans télécharger les pages individuelles de chaque vidéo
    :param progress_callback: Fonction de callback optionnelle pour suivre la progression
    :return: Dictionnaire contenant les métadonnées de la playlist et la liste des vidéos
    """
    ydl_opts: Dict[str, Any] = {
        "extract_flat": "in_playlist" if flat_extraction else False,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }

    if browser_for_cookies:
        ydl_opts["cookiesfrombrowser"] = (browser_for_cookies,)
    elif cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if progress_callback:
            progress_callback("Connexion et extraction de la playlist en cours...")
        info = ydl.extract_info(playlist_url, download=False)
        return info or {}


def get_available_browsers() -> List[str]:
    """Retourne la liste des navigateurs supportés pour les cookies."""
    return ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]
