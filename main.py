#!/usr/bin/env python3
"""
YouTube Playlist Music Fetcher (TubePlaylistFetcher / YT-Playlist-Curator)
---------------------------------------------------------------------------
Extracts full YouTube playlists (including private ones like LL and WL),
filters for music, cleans video titles, and enriches track metadata via iTunes & Deezer.
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
    print("   Full extraction, music filtering, and track metadata enrichment")
    print("=" * 70)
    print()


def ask_choice(prompt: str, options: list, default_index: int = 0) -> str:
    print(f"\n{prompt}")
    for idx, opt in enumerate(options, 1):
        marker = " (default)" if idx - 1 == default_index else ""
        print(f"  [{idx}] {opt}{marker}")
    
    choice = input(f"Your choice [1-{len(options)}]: ").strip()
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

    print(f"\n[1/4] 📥 Extracting playlist: {playlist_url}")
    if browser:
        print(f"      Using browser session: {browser.capitalize()}")
    elif cookies_file:
        print(f"      Using cookies file: {cookies_file}")

    try:
        data = extract_playlist(
            playlist_url=playlist_url,
            browser_for_cookies=browser,
            cookies_file=cookies_file,
            flat_extraction=True,
            progress_callback=print,
        )
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        print("\n💡 Tip for private playlists ('LL' or 'WL'):")
        print("   Make sure you are logged into your YouTube account in the selected browser,")
        print("   and close the browser if access to the cookie database is locked.")
        return

    entries = data.get("entries", [])
    playlist_title = data.get("title") or "YouTube_Playlist"
    # Clean filename string
    safe_title = "".join(c for c in playlist_title if c.isalnum() or c in (" ", "_", "-")).rstrip()
    safe_title = safe_title.replace(" ", "_") if safe_title else "Playlist"

    total_count = len(entries)
    print(f"\n✅ Found {total_count} videos in '{playlist_title}'.")

    if total_count == 0:
        print("⚠️ No videos extracted. Please check the URL or permissions.")
        return

    print(f"\n[2/4] 🔍 Filtering & Music detection in progress...")
    music_items, other_items = filter_and_process_playlist(
        entries=entries,
        filter_music_only=filter_music,
        max_duration_seconds=1200,
    )

    print(f"      • Music tracks retained: {len(music_items)}")
    print(f"      • Non-music items filtered out: {len(other_items)}")

    if enrich_metadata and music_items:
        print(f"\n[3/4] 🏷️ Track identification & metadata enrichment (iTunes / Deezer)...")
        enriched_count = 0
        for idx, item in enumerate(music_items, 1):
            artist = item.get("clean_artist", "")
            title = item.get("clean_title", "")
            
            # Progress output
            if idx % 10 == 0 or idx == len(music_items):
                print(f"      Processing {idx}/{len(music_items)}...", end="\r")

            match_info = identify_track(artist, title)
            if match_info:
                item.update(match_info)
                enriched_count += 1
        print(f"\n      ✅ {enriched_count}/{len(music_items)} tracks accurately identified!")
    else:
        print(f"\n[3/4] ⏩ Enrichment step skipped.")

    print(f"\n[4/4] 💾 Exporting results to directory '{output_dir}'...")

    csv_path = os.path.join(output_dir, f"{safe_title}_music.csv")
    json_path = os.path.join(output_dir, f"{safe_title}_music.json")
    txt_path = os.path.join(output_dir, f"{safe_title}_spotify_import.txt")
    m3u_path = os.path.join(output_dir, f"{safe_title}.m3u8")

    export_to_csv(music_items, csv_path)
    export_to_json(music_items, json_path)
    export_to_spotify_txt(music_items, txt_path)
    export_to_m3u8(music_items, m3u_path, playlist_title=playlist_title)

    if other_items:
        other_csv = os.path.join(output_dir, f"{safe_title}_non_music.csv")
        export_to_csv(other_items, other_csv)

    print("\n" + "=" * 70)
    print("   ✨ EXTRACTION AND PROCESSING COMPLETED SUCCESSFULLY! ✨")
    print("=" * 70)
    print(f"📁 Generated files:")
    print(f"  • CSV (Excel)          : {csv_path}")
    print(f"  • Text (Spotify import): {txt_path}")
    print(f"  • Playlist (M3U8)      : {m3u_path}")
    print(f"  • Raw JSON data        : {json_path}")
    if other_items:
        print(f"  • Non-music items CSV  : {os.path.join(output_dir, f'{safe_title}_non_music.csv')}")
    print()


def interactive_menu():
    print_banner()

    playlists_presets = [
        ("Liked Videos ('LL')", "https://www.youtube.com/playlist?list=LL"),
        ("Watch Later ('WL')", "https://www.youtube.com/playlist?list=WL"),
        ("Enter custom playlist URL", "CUSTOM"),
    ]

    print("Which playlist would you like to fetch?")
    for i, (label, _) in enumerate(playlists_presets, 1):
        print(f"  [{i}] {label}")

    p_choice = input(f"Your choice [1-{len(playlists_presets)}]: ").strip()
    idx = 0
    if p_choice.isdigit() and 1 <= int(p_choice) <= len(playlists_presets):
        idx = int(p_choice) - 1

    selected_label, selected_url = playlists_presets[idx]
    if selected_url == "CUSTOM":
        selected_url = input("\nPaste your YouTube playlist URL: ").strip()
        while not selected_url:
            selected_url = input("Please enter a valid URL: ").strip()

    is_private_preset = "list=LL" in selected_url or "list=WL" in selected_url

    browser = None
    if is_private_preset or "list=" in selected_url:
        print("\n🔑 To access private playlists ('Liked Videos' or 'Watch Later'), authentication is required.")
        browsers = ["edge", "chrome", "firefox", "brave", "opera", "None (public playlist)"]
        b_choice = ask_choice("Which browser are you logged into YouTube with?", browsers, default_index=0)
        if b_choice != "None (public playlist)":
            browser = b_choice

    enrich_choice = ask_choice("Do you want to automatically identify tracks via iTunes/Deezer?", ["Yes", "No"], default_index=0)
    enrich = (enrich_choice == "Yes")

    run_pipeline(
        playlist_url=selected_url,
        browser=browser,
        filter_music=True,
        enrich_metadata=enrich,
    )


def main():
    parser = argparse.ArgumentParser(description="YouTube Playlist Fetcher & Music Curator")
    parser.add_argument("--url", "-u", type=str, help="YouTube playlist URL")
    parser.add_argument("--browser", "-b", type=str, choices=get_available_browsers(), help="Browser to extract session cookies from")
    parser.add_argument("--cookies", "-c", type=str, help="Path to cookies.txt file")
    parser.add_argument("--all", action="store_true", help="Keep all videos without filtering for music")
    parser.add_argument("--no-enrich", action="store_true", help="Disable iTunes/Deezer track identification")
    parser.add_argument("--output", "-o", default="exports", help="Output directory")

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
