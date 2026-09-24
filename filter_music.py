"""
Module de filtrage et nettoyage intelligent pour isoler les morceaux de musique.
Nettoie les titres YouTube (suppression de [Clip Officiel], (Official Video), 4K, etc.)
et extrait les noms d'artiste et de titre.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# Mots-clés indiquant du contenu musical
MUSIC_KEYWORDS = [
    "music", "musique", "audio", "soundtrack", "ost", "remix", "feat", "ft.",
    "prod.", "official video", "clip officiel", "clip", "lyrics", "paroles",
    "album", "single", "ep", "acoustic", "live", "cover", "instrumental",
    "official audio", "visualizer", "remastered", "extended mix", "original mix"
]

# Mots-clés indiquant du contenu non musical (tutos, vlogs, let's play, etc.)
NON_MUSIC_KEYWORDS = [
    "tutoriel", "tutorial", "how to", "comment faire", "gameplay", "let's play",
    "walkthrough", "vlog", "unboxing", "review", "critique", "podcast", "conférence",
    "news", "actualités", "journal", "reportage", "documentaire", "cours", "lesson",
    "speedrun", "highlights", "interview", "react", "reaction"
]

# Motifs regex pour nettoyer les artefacts de titres YouTube
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
    r"\|.*$",  # Supprime les suffixes après un pipe ex: "| Official Music Video"
    r"-\s*official\s+video.*$",
    r"-\s*clip\s+officiel.*$",
]


def clean_title(title: str) -> str:
    """Nettoie le titre YouTube pour ne garder que l'essentiel."""
    cleaned = title
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    # Nettoie les espaces multiples et les tirets orphelins
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^[-–—]\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*[-–—]$", "", cleaned).strip()
    return cleaned


def split_artist_title(title: str, uploader: Optional[str] = None) -> Tuple[str, str]:
    """
    Extrait l'artiste et le titre du morceau depuis le titre YouTube nettoyé.
    Exemples:
      "Daft Punk - Get Lucky" -> ("Daft Punk", "Get Lucky")
      "Booba - DKR (Clip)" -> ("Booba", "DKR")
      "Get Lucky" (avec uploader="Daft Punk - Topic") -> ("Daft Punk", "Get Lucky")
    """
    cleaned = clean_title(title)
    
    # Détecte les séparateurs classiques: " - ", " – ", " — ", " : ", " // "
    separators = [" - ", " – ", " — ", " : ", " // "]
    for sep in separators:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)
            artist = parts[0].strip()
            track_title = parts[1].strip()
            # Nettoie d'éventuels guillemets
            track_title = track_title.strip('"\'')
            return artist, track_title
            
    # Si pas de séparateur mais que l'uploader ressemble à un nom d'artiste (ex: "Artiste - Topic" ou chaîne officielle)
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
    Détermine si une vidéo est très probablement un morceau de musique.
    
    :param video: Métadonnées de la vidéo
    :param max_duration_seconds: Durée maximale par défaut (ex: 20 min) pour exclure les longues vidéos
    :return: Tuple (est_musique, raison)
    """
    title = video.get("title", "")
    duration = video.get("duration") or 0
    uploader = video.get("uploader") or ""
    categories = video.get("categories") or []
    
    title_lower = title.lower()
    uploader_lower = uploader.lower()
    
    # 1. Filtre par catégorie officielle YouTube si disponible
    if any(cat.lower() in ["music", "musique"] for cat in categories):
        return True, "Catégorie YouTube 'Musique'"

    # 2. Détection chaîne automatique "Topic" / "VEVO"
    if " - topic" in uploader_lower or uploader_lower.endswith("vevo"):
        return True, "Chaîne officielle d'artiste (Topic / VEVO)"

    # 3. Métadonnées YouTube Music explicites
    if video.get("track") or video.get("artist"):
        return True, "Métadonnées piste/artiste YouTube Music"

    # 4. Exclusions de mots-clés évidents non musicaux
    for keyword in NON_MUSIC_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return False, f"Mot-clé non musical détecté ('{keyword}')"

    # 5. Si la vidéo est trop longue (sauf si taggée musique explicitement)
    if duration > max_duration_seconds and duration > 0:
        return False, f"Durée trop longue ({duration // 60} min > {max_duration_seconds // 60} min)"

    # 6. Présence d'un séparateur "Artiste - Titre"
    if any(sep in title for sep in [" - ", " – ", " — "]):
        return True, "Format standard 'Artiste - Titre'"

    # 7. Présence de mots-clés musicaux
    for keyword in MUSIC_KEYWORDS:
        if keyword in title_lower:
            return True, f"Mot-clé musical détecté ('{keyword}')"

    # Par défaut, si courte et pas de mot-clé excluant
    if 30 <= duration <= 600:
        return True, "Durée typique de morceau (0:30 - 10:00)"

    return False, "Non identifié avec certitude comme musique"


def filter_and_process_playlist(
    entries: List[Dict[str, Any]],
    filter_music_only: bool = True,
    max_duration_seconds: int = 1200
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Traite toutes les entrées de la playlist et les sépare en musique / non-musique.
    """
    music_items = []
    other_items = []

    for entry in entries:
        if not entry:
            continue

        raw_title = entry.get("title") or "Sans titre"
        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
        duration = entry.get("duration")
        uploader = entry.get("uploader") or entry.get("channel") or ""

        # Test musique
        is_music, reason = is_music_track(entry, max_duration_seconds=max_duration_seconds)
        
        artist, track_name = split_artist_title(raw_title, uploader)

        item = {
            "id": entry.get("id"),
            "raw_title": raw_title,
            "clean_artist": artist,
            "clean_title": track_name,
            "uploader": uploader,
            "duration": duration,
            "duration_str": f"{int(duration)//60}:{int(duration)%60:02d}" if duration else "Inconnue",
            "url": url,
            "detection_reason": reason,
            "is_music": is_music,
        }

        if is_music or not filter_music_only:
            music_items.append(item)
        else:
            other_items.append(item)

    return music_items, other_items
