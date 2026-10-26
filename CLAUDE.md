# CLAUDE.md – Luftbildatlas Lärz

## Zweck
Georeferenzierung historischer Luftbilder (NCAP US7/0094/C, 11.04.1945) des Fliegerhorsts Lärz und ein Ebenen-Viewer (`app/index.html`).
Projekt ist für eine Weitergabe vorbereitet: **keine personenbezogenen Daten, keine Flurstücks-, Haus- oder Behördendaten zu einem bestimmten Grundstück** in dieses Repo aufnehmen. Private Auswertungen bleiben außerhalb (Ordner `_arbeit/` ist ignoriert).

## Sprache
Deutsch für Texte, UI und Doku.

## Koordinaten
- Bezugssystem überall ETRS89 / UTM Zone 33N (EPSG:25833).
- Interne „Karten-Meter": `x = E − 348600`, `y = 5909100 − N` (y nach unten). Arbeitsgebiet 2400 × 2400 m.
- `r53.jpg` (DOP 1953) hat 1 m/px mit Ursprung genau dort → Pixel = Karten-Meter.
- `rnow.jpg`/`alkis.png`: 0,6 m/px, gleicher Ursprung.

## Pipeline (skripte/)
1. `fetch_geobasis.py` – DOP heute, DOP 1953, ALKIS per WMS laden.
2. `reg.py` – Frames 4071 und 3054 per Template-Korrelation (Gradientenbilder) gegen DOP 1953, iterativ, projektive Homographie (RANSAC). Benötigt Start-Ähnlichkeitstransformationen (aus Handpasspunkten; derzeit in `o53a.jpg.M.npy`/`o54a.jpg.M.npy`, nicht im Repo – bei Neuaufbau zwei Passpunkte je Frame setzen).
3. `sift.py` – Verknüpfungspunkte 4053↔4071 und 3054↔4071 (SIFT, Halbauflösung).
4. `bundle.py` – gemeinsamer Ausgleich 4071/3054 aus Passpunkten + Verknüpfungspunkten → `Hfinal.json`.
5. `ref53.py` – 4053 aus Verknüpfungspunkten zu 4071 + eigenen Passpunkten gegen 1953 verfeinern.
6. `mosaic45.py` – Mosaik der drei Frames.
7. `laiv_reg.py` + `laiv_mosaik.py` – LAiV-Vorschaubilder 28.05.1944 und 08.04.1945 (`rohdaten/laiv_vorschau/`, mit `katalog.tsv`) registrieren und je Flugtag zu `app/luftbild_<Datum>.webp` (1 m/px, Alpha) mosaikieren. Feste Pfade, aus dem Projektordner starten.
Ergebnis-Homographien: `georeferenz_parameter/Homographien_Frame_px_auf_Karte_m.json` (Frame-Pixel des Original-Scans → Karten-Meter).
Restfehler: 3054 1,8 m · 4071 2,9 m · 4053 2,5 m; Maßstab 0,18–0,195 m/px.

Die Skripte sind Arbeitsstand (Pfade relativ zum Arbeitsverzeichnis, Dateinamen wie `frame_full.jpg` = 4071, `f4053.jpg`, `f3054.jpg`). Erste sinnvolle Aufgabe: zu einer Pipeline mit festen Ein-/Ausgabepfaden aufräumen.

## App
- Eine HTML-Datei, Daten (Homographien, Bildgrößen, Clip-Rechtecke) inline in `const D`. Bilder relativ (`f4071.jpg` usw. mit halber Auflösung).
- Frames werden per CSS `matrix3d` aus der Homographie gezeichnet.
- „Airpark intern": verschlüsselte Zusatzebenen in `app/airparkinternal/` (nur `index.json` + `*.bin` im Repo). Originale + `ebenen.json` lokal in `vertraulich/` (ignoriert), Verschlüsselung mit `skripte/verschluesseln.py`. Der Passwort-Bereich erscheint nur über `app/?airparkinternal` oder mit gemerktem Schlüssel; in README/UI der normalen Version nicht erwähnen.
- Online-Version existiert als claude.ai-Artifact „Luftbildatlas Lärz" (enthält dort private Ebenen – nicht diese Fassung).

## Offene Ideen
- Weitere Frames (3055, 3053, 4054) hochauflösend beschaffen und einbinden. Das LAiV M-V hat sie (Flüge 45_149/45_150), ebenso 1944/45-Flüge über Lärz: 10.05.44, 28.05.44, 04.08.44, 13.09.44, 24.12.44, 08.04.45. Vollscans 25 €/Bild (Mindestens 60 €/Auftrag); Vorschau-API: `laiv.geodaten-mv.de/afgvk/_apps/dladownload/_ajax/overview.php` und `preview.php?type=lb&id=<bild_id>`.
- Trichterkartierung des gesamten Platzes, Bombenreihen-Analyse (Anflugrichtung aus Mission Reports der 458th/466th/467th BG).
- GeoTIFF statt JPG+World-File erzeugen (gdal).
