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
| 1945 Frames 3054, 4071, 4053 | NCAP, Sortie US7/0094/C | 0,18-0,20 m/px | (C) NCAP |

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

Die drei Luftaufklärungsbilder vom 11.04.1945 (einen Tag nach dem Angriff der 8th Air Force) wurden per automatischer Bildkorrelation gegen das amtliche DOP 1953 georeferenziert:

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
- Export als PNG/JPG mit allen sichtbaren Ebenen und Messungen
- Voreinstellungen: "1945 über heute", "1945 gegen 1953", "1991 (Wende)", "Messtischblatt + 1945"
- Tastatur: H = 1945-Bilder ausblenden, M = Messen, P = Markieren, ESC = zurück

## Entstehung

Dieses Projekt entstand als Werkzeug zur Untersuchung der historischen Nutzung des Fliegerhorsts Lärz anhand georeferenzierter Luftbilder. Die Georeferenzierung der 1945er Aufnahmen wurde mit Python (OpenCV, NumPy, SciPy) durchgeführt (siehe `skripte/`). Der Ebenen-Viewer ist eine einzelne HTML-Datei. Externe Abhängigkeiten zur Laufzeit: Google Fonts (Barlow, JetBrains Mono) und optional Google Maps Satellite Tiles.

Erstellt von soenke.bartling@gmail.com mit Claude, Cursor und Grok.

## Lizenz

Der Code dieses Projekts ist frei verwendbar. Die eingebundenen Kartenbilder unterliegen den jeweiligen Lizenzen ihrer Anbieter (siehe Tabellen oben). Die 1945er Luftbilder stammen von NCAP (National Collection of Aerial Photography).
