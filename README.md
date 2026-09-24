# 🎵 YouTube Playlist Fetcher & Music Curator

Outil intelligent en Python pour extraire **100% du contenu** d'une playlist YouTube (y compris les playlists privées comme vos **Vidéos « J'aime » (`LL`)** et **« À regarder plus tard » (`WL`)**), filtrer les vidéos pour ne garder que la musique, et identifier automatiquement les vrais morceaux (Artiste, Titre, Album, Année, Pochette) via iTunes & Deezer.

---

## ✨ Fonctionnalités

1. **Extraction complète sans limite :**
   - Récupère toutes les vidéos (même les playlists de plusieurs milliers de titres).
   - Accès aux playlists privées (`list=LL`, `list=WL`) grâce à la lecture sécurisée de la session de votre navigateur (Edge, Chrome, Firefox, Brave, Opera).

2. **Filtrage Musique & Détection intelligente :**
   - Détecte et isole la musique en éliminant les tutoriels, podcasts, vlogs, gameplays, etc.
   - Nettoie les pollutions de titres YouTube (`[Clip Officiel]`, `(Official Video)`, `4K`, `[Paroles]`, `(Audio)`, etc.).

3. **Identification des morceaux :**
   - Interroge les bases de données musicales (iTunes & Deezer) sans nécessiter de clé d'API.
   - Retrouve le vrai nom de l'artiste officiel, le titre exact, l'album, le genre et l'année de sortie.

4. **Multi-formats d'exportation :**
   - 📊 **CSV / Excel** : Tableau complet prêt pour tableur (`exports/*_musique.csv`).
   - 🎧 **TXT Spotify** : Fichier `Artiste - Titre` prêt à être importé en 1 clic dans Spotify via [Spotlistr](https://www.spotlistr.com/) ou [TuneMyMusic](https://www.tunemymusic.com/).
   - 📻 **Playlist M3U8** : Compatible VLC, foobar2000, etc.
   - 📦 **JSON** : Données brutes et métadonnées enrichies.

---

## 🚀 Utilisation

### Méthode 1 : Double-clic direct (Windows)
Double-cliquez simplement sur le fichier **`launch.bat`** à la racine du projet.

### Méthode 2 : Ligne de commande
Dans le terminal :
```powershell
.\.venv\Scripts\python main.py
```

### Options en ligne de commande :
```powershell
# Extraire les vidéos J'aime avec cookies du navigateur Edge
.\.venv\Scripts\python main.py --url "https://www.youtube.com/playlist?list=LL" --browser edge

# Extraire une playlist publique sans enrichissement iTunes
.\.venv\Scripts\python main.py --url "https://www.youtube.com/playlist?list=PL..." --no-enrich
```
