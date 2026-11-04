# Luftbildatlas Lärz

Interaktiver Kartenvergleich des ehemaligen Fliegerhorsts Lärz (heute Müritz Airpark) in Mecklenburg-Vorpommern. Historische und aktuelle Karten übereinander gelegt – von der Preußischen Landesaufnahme über die Luftaufklärung 1945 bis zu aktuellen Satellitenbildern.

## Ansehen

```bash
cd app
python3 -m http.server 8080
# → http://localhost:8080
```

## Ebenen

### Aktuelle Referenzkarten
| Ebene | Quelle | Auflösung | Lizenz |
|---|---|---|---|
| Google Satellite | Google Maps Tiles (live) | ~0,5 m/px | (C) Google |
| Luftbild heute | DOP, GeoBasis-DE/M-V | 0,6 m/px | CC BY 4.0 |
| Sentinel-2 (2018-2024) | BKG Jahresmosaike | 10 m/px | dl-de/by-2-0 |
| basemap.de / OSM | BKG / OSM-Mitwirkende | Vektorkarte | dl-de/by-2-0 |
| Topographische Karte | BKG TopPlusOpen | 1:25.000 | dl-de/by-2-0 |
| DTK25 aktuell | GeoBasis-DE/M-V | 1:25.000 | CC BY 4.0 |

### Historische Luftbilder
| Ebene | Quelle | Auflösung | Lizenz |
|---|---|---|---|
| Luftbild 1991 | DOP CIR-Infrarot, GeoBasis-DE/M-V | 0,6 m/px | CC BY 4.0 |
| Luftbild 1953 | DOP, GeoBasis-DE/M-V | 1,0 m/px | CC BY 4.0 |
| 11.04.1945 Frames 3054, 4071, 4053 | NCAP, Sortie US7/0094/C, **hochaufgelöster Scan (gekauft)** | 0,18-0,20 m/px | (C) NCAP |
| Luftbild 08.04.1945 | LAiV M-V, RAF 106G/5234, Mosaik aus 13 **Vorschaubildern** | ~1,7 m/px | CC BY 4.0 |
| Luftbild 24.12.1944 | LAiV M-V, Flug 44_009, 2 **Vorschaubilder**, kleiner Maßstab | ~7 m/px | CC BY 4.0 |
| Luftbild 13.09.1944 | LAiV M-V, Flug 44_090, 1 **Vorschaubild**, kleiner Maßstab | ~9 m/px | CC BY 4.0 |
| Luftbild 04.08.1944 | LAiV M-V, Flug 44_023, 2 **Vorschaubilder**, kleiner Maßstab | ~9 m/px | CC BY 4.0 |
| Luftbild 28.05.1944 | LAiV M-V, US 7GR Sortie 1619, Mosaik aus 9 **Vorschaubildern** | ~1,8 m/px | CC BY 4.0 |
| Luftbild 10.05.1944 | LAiV M-V, Flug 44_080, 4 **Vorschaubilder**, nur Nordostrand | ~2 m/px | CC BY 4.0 |

### Historische Karten
| Ebene | Quelle | Zeitraum | Lizenz |
|---|---|---|---|
| TK25 DDR-Ausgabe | GeoBasis-DE/M-V | 1981-1987 | CC BY 4.0 |
| Messtischblatt | Preuß. Landesaufnahme, GeoBasis-DE/M-V | 1877-1943 | CC BY 4.0 |

### Overlay-Ebenen
| Ebene | Quelle | Lizenz |
|---|---|---|
| Geländemodell (DGM) | GeoBasis-DE/M-V, LiDAR-Schummerung | CC BY 4.0 |
| ALKIS Flurstücke + Gebäude | GeoBasis-DE/M-V | CC BY 4.0 |

## Georeferenzierung der 1945er Aufnahmen

Die drei hochauflösenden Luftaufklärungsbilder vom 11.04.1945 (einen Tag nach dem Angriff der 8th Air Force) wurden per automatischer Bildkorrelation gegen das amtliche DOP 1953 georeferenziert:

- **Methode**: Template-Korrelation auf Gradientenbildern, iterativ, mit projektiver Homographie (RANSAC)
- **Passpunkte**: Bahnen, Rollwege, Straßen, Kanal (1953 noch identisch mit 1945)
- **Verknüpfungspunkte**: SIFT-Matching zwischen den Frames desselben Flugs
- **Ausgleich**: Gemeinsamer Bundle-Adjustment aller drei Frames

| Bild | Passpunkte | Restfehler | m/px (Original) |
|---|---|---|---|
| Frame 3054 | 71 + Verknüpfung | 1,8 m | 0,195 |
| Frame 4071 | 29 + Verknüpfung | 2,9 m | 0,183 |
| Frame 4053 | 105 + 1.280 | 2,5 m | 0,194 |

Die heutige Startbahn wurde nach 1945 umgebaut und passt deshalb nicht exakt.

### Luftbilder 1944 und 08.04.1945 (LAiV M-V)

Das LAiV M-V stellt im [Downloadportal](https://laiv.geodaten-mv.de/afgvk/Luftbilder/Vorschau?produkt=LB) Vorschauen alliierter Kriegsluftbilder frei bereit (1536 px breit, CC BY 4.0). Die Vorschauen und der Katalog liegen in `rohdaten/laiv_vorschau/`.

```bash
python3 skripte/laiv_reg.py      # Georeferenzierung -> georeferenz_parameter/LAiV_*.json
python3 skripte/laiv_mosaik.py   # Mosaik je Flugtag -> app/luftbild_<Datum>.webp
```

Start per SIFT gegen ein Mosaik der NCAP-Frames 1945 (für 1944 aus drei Handpasspunkten an Bild 2008), weitere Bilder über SIFT-Verknüpfung mit schon registrierten Bildern (auch anderer Flugtage), danach Template-Korrelation gegen DOP 1953. Die Bilder vom 10.05.1944 und Bild 7022 (24.12.1944) treffen das Arbeitsgebiet nur am Rand und sind allein über die Verknüpfung eingepasst. Restfehler je Bild 1,4-2,5 m.

### Hochaufgelöste Scans: Bestand und Kosten

Im Atlas sind nur die drei NCAP-Frames vom 11.04.1945 hochaufgelöst (0,18-0,20 m/px). Alle LAiV-Ebenen beruhen auf den freien Vorschaubildern (1536 px Kantenlänge). Ein Vollscan wäre voraussichtlich rund zehnmal feiner: etwa 0,2 m/px statt 1,7-2 m/px bei den großmaßstäbigen Flügen und etwa 1 m/px statt 7-9 m/px bei den Übersichtsaufnahmen von August bis Dezember 1944.

**Bereits bezahlt:** 3 Scans bei der NCAP (3054, 4053, 4071) zu je 35 £, zusammen **105 £** (ca. 120 €).

**Beim LAiV M-V kaufbar** (25 € je Bild, Mindestentgelt 60 € je Auftrag; Entgeltvorschrift ab 01.01.2026):

| Flugtag | Bilder, die das Arbeitsgebiet zeigen | Anzahl | Kosten | Sparsatz (deckt ≥ 98 % ab) |
|---|---|---:|---:|---|
| 11.04.1945 | 3053, 3055, 4054 (Lücken neben den NCAP-Frames) | 3 | 75 € | alle 3 – 75 € |
| 08.04.1945 | 3075-3080, 3093, 3094, 4079, 4091-4097 | 16 | 400 € | 3075, 3078, 3094 – 75 € |
| 24.12.1944 | 7022-7024 | 3 | 75 € | 7023 – 25 € |
| 13.09.1944 | 8016 | 1 | 25 € | 8016 – 25 € |
| 04.08.1944 | 7005, 7006 | 2 | 50 € | 7005 – 25 € |
| 28.05.1944 | 2005-2009, 2063-2066 | 9 | 225 € | 2007, 2008 – 50 € |
| 10.05.1944 | 2028-2031 (nur Nordostrand) | 4 | 100 € | 2028, 2031 – 50 € |
| **Summe** | | **38** | **950 €** | **13 Bilder – 325 €** |

Der Sparsatz wurde aus den Bildumrissen berechnet. Er deckt das Gebiet ab, liegt dann aber stellenweise am Bildrand. Den ganzen LAiV-Katalog für Lärz 1944/45 zu kaufen (83 Bilder, abzüglich der drei schon vorhandenen Frames vom 11.04.1945), kostet 80 × 25 € = **2.000 €**. Dabei sind auch Bilder ohne Anteil am Arbeitsgebiet.

Mögliche Zuschläge:

- Muss ein Bild erst gescannt werden, kommen 13-14 € je Bild hinzu, bei schwierigen Vorlagen 50 % mehr.
- Gekaufte Daten unterliegen den AGNB. Für eine öffentliche Weitergabe bearbeiteter Folgeprodukte kann eine jährliche Lizenzgebühr anfallen (100-300 % des Entgelts). Das sollte vor einem Kauf mit dem LAiV geklärt werden.

Die Frames 3053, 3055 und 4054 bietet auch die NCAP an (35 £ je Bild). Das LAiV ist günstiger.

## Koordinatensystem

- ETRS89 / UTM Zone 33N (EPSG:25833)
- Arbeitsgebiet: E 348.600-351.000, N 5.906.700-5.909.100 (2.400 x 2.400 m)
- Interne Karten-Koordinaten: x = E - 348.600, y = 5.909.100 - N (y nach unten, 1 Einheit = 1 m)

## Bilder aktualisieren

```bash
python3 skripte/fetch_geobasis.py           # Alle Ebenen herunterladen (~15 MB)
python3 skripte/fetch_geobasis.py --update   # Nur Sentinel-2 Satellitenbilder aktualisieren
```

Benötigt nur `curl` und Python 3. Die WMS-Dienste sind frei zugänglich.

## Funktionen

- Ebenen ein/ausblenden, Deckkraft anpassen, Reihenfolge ändern
- Ebenen manuell verschieben (Ost/West, Nord/Süd, Drehung, Maßstab)
- Entfernungen messen (Klick-Klick-Doppelklick)
- Punkte markieren mit UTM-Koordinaten
- Koordinatenanzeige: UTM + WGS84 Lat/Lon
- Export als PNG/JPG mit den sichtbaren Ebenen und Messungen (ohne Google Satellite)
- Voreinstellungen: "1945 über heute", "1945 gegen 1953", "1991 (Wende)", "Messtischblatt + 1945"
- Tastatur: H = 1945-Bilder ausblenden, M = Messen, P = Markieren, ESC = zurück

## Entstehung

Dieses Projekt entstand als Werkzeug zur Untersuchung der historischen Nutzung des Fliegerhorsts Lärz anhand georeferenzierter Luftbilder. Die Georeferenzierung der 1945er Aufnahmen wurde mit Python (OpenCV, NumPy, SciPy) durchgeführt (siehe `skripte/`). Der Ebenen-Viewer ist eine einzelne HTML-Datei. Externe Abhängigkeiten zur Laufzeit: Google Fonts (Barlow, JetBrains Mono) und optional Google Maps Satellite Tiles.

Erstellt von soenke.bartling@gmail.com mit Claude, Cursor und Grok.

## Lizenz

Der Code dieses Projekts ist frei verwendbar. Die eingebundenen Kartenbilder unterliegen den jeweiligen Lizenzen ihrer Anbieter (siehe Tabellen oben). Die 1945er Luftbilder stammen von NCAP (National Collection of Aerial Photography).
