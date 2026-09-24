#!/usr/bin/env python3
"""
YouTube Playlist Music Fetcher (TubePlaylistFetcher / YT-Playlist-Curator)
---------------------------------------------------------------------------
Extrait l'intégralité d'une playlist YouTube (y compris privées comme LL et WL),
filtre pour ne conserver que la musique, nettoie les titres et enrichit
les métadonnées via iTunes/Deezer.
"""

import argparse
import os
import sys
from typing import Optional

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from extractor import extract_playlist, get_available_browsers

from filter_music import filter_and_process_playlist
from enricher import identify_track
from exporter import export_to_csv, export_to_json, export_to_m3u8, export_to_spotify_txt


def print_banner():
    print("=" * 70)
    print("   🎵  YOUTUBE PLAYLIST FETCHER & MUSIC CURATOR  🎵")
    print("   Extraction complète, filtrage et identification musicale")
    print("=" * 70)
    print()


def ask_choice(prompt: str, options: list, default_index: int = 0) -> str:
    print(f"\n{prompt}")
    for idx, opt in enumerate(options, 1):
        marker = " (par défaut)" if idx - 1 == default_index else ""
        print(f"  [{idx}] {opt}{marker}")
    
    choice = input(f"Votre choix [1-{len(options)}]: ").strip()
    if not choice:
        return options[default_index]
    try:
        val = int(choice)
        if 1 <= val <= len(options):
            return options[val - 1]
    except ValueError:
        pass
    return options[default_index]


def run_pipeline(
    playlist_url: str,
    browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
    filter_music: bool = True,
    enrich_metadata: bool = True,
    output_dir: str = "exports",
):
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[1/4] 📥 Extraction de la playlist : {playlist_url}")
    if browser:
        print(f"      Utilisation de la session du navigateur : {browser.capitalize()}")
    elif cookies_file:
        print(f"      Utilisation du fichier de cookies : {cookies_file}")

    try:
        data = extract_playlist(
            playlist_url=playlist_url,
            browser_for_cookies=browser,
            cookies_file=cookies_file,
            flat_extraction=True,
            progress_callback=print,
        )
    except Exception as e:
        print(f"\n❌ Erreur lors de l'extraction : {e}")
        print("\n💡 Conseil pour les playlists privées ('LL' ou 'WL') :")
        print("   Assurez-vous d'être connecté à votre compte YouTube sur le navigateur sélectionné,")
        print("   et que le navigateur est fermé si l'accès à la base de cookies est verrouillé.")
        return

    entries = data.get("entries", [])
    playlist_title = data.get("title") or "YouTube_Playlist"
    # Nettoyage du nom pour le dossier/fichier
    safe_title = "".join(c for c in playlist_title if c.isalnum() or c in (" ", "_", "-")).rstrip()
    safe_title = safe_title.replace(" ", "_") if safe_title else "Playlist"

    total_count = len(entries)
    print(f"\n✅ {total_count} vidéos trouvées dans '{playlist_title}'.")

    if total_count == 0:
        print("⚠️ Aucune vidéo extraite. Vérifiez l'URL ou les autorisations.")
        return

    print(f"\n[2/4] 🔍 Filtrage & Détection musicale en cours...")
    music_items, other_items = filter_and_process_playlist(
        entries=entries,
        filter_music_only=filter_music,
        max_duration_seconds=1200,
    )

    print(f"      • Morceaux de musique retenus : {len(music_items)}")
    print(f"      • Autres contenus écartés : {len(other_items)}")

    if enrich_metadata and music_items:
        print(f"\n[3/4] 🏷️ Identification et enrichissement des morceaux (iTunes / Deezer)...")
        enriched_count = 0
        for idx, item in enumerate(music_items, 1):
            artist = item.get("clean_artist", "")
            title = item.get("clean_title", "")
            
            # Affichage de progression
            if idx % 10 == 0 or idx == len(music_items):
                print(f"      Traitement {idx}/{len(music_items)}...", end="\r")

            match_info = identify_track(artist, title)
            if match_info:
                item.update(match_info)
                enriched_count += 1
        print(f"\n      ✅ {enriched_count}/{len(music_items)} morceaux identifiés avec précision !")
    else:
        print(f"\n[3/4] ⏩ Étape d'enrichissement ignorée.")

    print(f"\n[4/4] 💾 Exportation des résultats dans le dossier '{output_dir}'...")

    csv_path = os.path.join(output_dir, f"{safe_title}_musique.csv")
    json_path = os.path.join(output_dir, f"{safe_title}_musique.json")
    txt_path = os.path.join(output_dir, f"{safe_title}_spotify_import.txt")
    m3u_path = os.path.join(output_dir, f"{safe_title}.m3u8")

    export_to_csv(music_items, csv_path)
    export_to_json(music_items, json_path)
    export_to_spotify_txt(music_items, txt_path)
    export_to_m3u8(music_items, m3u_path, playlist_title=playlist_title)

    if other_items:
        other_csv = os.path.join(output_dir, f"{safe_title}_non_musique.csv")
        export_to_csv(other_items, other_csv)

    print("\n" + "=" * 70)
    print("   ✨ EXTRACTION ET TRAITEMENT TERMINÉS AVEC SUCCÈS ! ✨")
    print("=" * 70)
    print(f"📁 Fichiers générés :")
    print(f"  • CSV (Excel)      : {csv_path}")
    print(f"  • Texte (Spotify)  : {txt_path}")
    print(f"  • Playlist (M3U8)  : {m3u_path}")
    print(f"  • Données brutes   : {json_path}")
    if other_items:
        print(f"  • Vidéos non-musique : {os.path.join(output_dir, f'{safe_title}_non_musique.csv')}")
    print()


def interactive_menu():
    print_banner()

    playlists_presets = [
        ("Vidéos 'J'aime' (Liked Videos)", "https://www.youtube.com/playlist?list=LL"),
        ("À regarder plus tard (Watch Later)", "https://www.youtube.com/playlist?list=WL"),
        ("Entrer une autre URL de playlist", "CUSTOM"),
    ]

    print("Quelle playlist souhaitez-vous récupérer ?")
    for i, (label, _) in enumerate(playlists_presets, 1):
        print(f"  [{i}] {label}")

    p_choice = input(f"Votre choix [1-{len(playlists_presets)}]: ").strip()
    idx = 0
    if p_choice.isdigit() and 1 <= int(p_choice) <= len(playlists_presets):
        idx = int(p_choice) - 1

    selected_label, selected_url = playlists_presets[idx]
    if selected_url == "CUSTOM":
        selected_url = input("\nCollez l'URL de votre playlist YouTube : ").strip()
        while not selected_url:
            selected_url = input("Veuillez entrer une URL valide : ").strip()

    is_private_preset = "list=LL" in selected_url or "list=WL" in selected_url

    browser = None
    if is_private_preset or "list=" in selected_url:
        print("\n🔑 Pour accéder aux vidéos 'J'aime' ou 'À regarder plus tard', une connexion est requise.")
        browsers = ["edge", "chrome", "firefox", "brave", "opera", "Aucun (playlist publique)"]
        b_choice = ask_choice("Sur quel navigateur êtes-vous connecté à votre compte YouTube ?", browsers, default_index=0)
        if b_choice != "Aucun (playlist publique)":
            browser = b_choice

    enrich_choice = ask_choice("Voulez-vous identifier automatiquement les morceaux via iTunes/Deezer ?", ["Oui", "Non"], default_index=0)
    enrich = (enrich_choice == "Oui")

    run_pipeline(
        playlist_url=selected_url,
        browser=browser,
        filter_music=True,
        enrich_metadata=enrich,
    )


def main():
    parser = argparse.ArgumentParser(description="YouTube Playlist Fetcher & Music Curator")
    parser.add_argument("--url", "-u", type=str, help="URL de la playlist YouTube")
    parser.add_argument("--browser", "-b", type=str, choices=get_available_browsers(), help="Navigateur pour extraire les cookies de session")
    parser.add_argument("--cookies", "-c", type=str, help="Fichier cookies.txt")
    parser.add_argument("--all", action="store_true", help="Garder toutes les vidéos sans filtrer uniquement la musique")
    parser.add_argument("--no-enrich", action="store_true", help="Désactiver l'identification iTunes/Deezer")
    parser.add_argument("--output", "-o", default="exports", help="Dossier de sortie")

    args = parser.parse_args()

    if not args.url:
        interactive_menu()
    else:
        run_pipeline(
            playlist_url=args.url,
            browser=args.browser,
            cookies_file=args.cookies,
            filter_music=not args.all,
            enrich_metadata=not args.no_enrich,
            output_dir=args.output,
        )


if __name__ == "__main__":
    main()
