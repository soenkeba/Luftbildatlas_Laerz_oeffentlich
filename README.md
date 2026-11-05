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
| Luftbild 11.04.1945 (Vorschau) | LAiV M-V, Flüge 45_149/45_150, Mosaik aus 23 **Vorschaubildern**, ergänzt die NCAP-Frames | ~0,8 m/px | CC BY 4.0 |
| Luftbild 08.04.1945 | LAiV M-V, RAF 106G/5234, Mosaik aus 42 **Vorschaubildern** | ~1,7 m/px | CC BY 4.0 |
| Luftbild 24.12.1944 | LAiV M-V, Flug 44_009, 1 **Vorschaubild**, kleiner Maßstab | ~7 m/px | CC BY 4.0 |
| Luftbild 13.09.1944 | LAiV M-V, Flug 44_090, 1 **Vorschaubild**, kleiner Maßstab | ~8 m/px | CC BY 4.0 |
| Luftbild 04.08.1944 | LAiV M-V, Flug 44_023, 1 **Vorschaubild**, kleiner Maßstab | ~9 m/px | CC BY 4.0 |
| Luftbild 28.05.1944 | LAiV M-V, US 7GR Sortie 1619, Mosaik aus 16 **Vorschaubildern** | ~1,8 m/px | CC BY 4.0 |
| Luftbild 10.05.1944 | LAiV M-V, Flüge 44_080/44_082, 6 **Vorschaubilder**, Norden und Osten des Gebiets | ~2 m/px | CC BY 4.0 |

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
python3 skripte/laiv_block.py 1945-04-08,1945-04-11   # Blockausgleich, ebenso 1944-05-10,1944-05-28
python3 skripte/laiv_mosaik.py   # Mosaik je Flugtag -> app/luftbild_<Datum>.webp
```

Start per SIFT gegen ein Mosaik der NCAP-Frames 1945 (für 1944 aus drei Handpasspunkten an Bild 2008), weitere Bilder über SIFT-Verknüpfung mit schon registrierten Bildern (auch anderer Flugtage), danach Template-Korrelation gegen DOP 1953.

Anschließend wurden die Bilder von 1945 und Mai 1944 in einem gemeinsamen Blockausgleich neu eingepasst (`skripte/laiv_block.py`): Alle überlappenden Bilder werden direkt miteinander verknüpft, die NCAP-Frames und DOP 1953 gehen als feste Bilder ein. Das war nötig, weil die Einzelpassung gegen 1953 auf dem Flugfeld kaum Punkte fand und Nachbarbilder dort bis zu 50 m auseinanderlagen, ohne dass der Vergleich mit 1953 das zeigte. An 15 % zurückgehaltenen Punkten sank der Abstand im 90-%-Wert von 21,6 m auf 2,3 m (1945) und von 13,6 m auf 3,6 m (Mai 1944). Nachbarbilder liegen jetzt meist 1-4 m auseinander, gegen DOP 1953 meist 1-4 m. Die Übersichtsbilder von 1944 (Einzelbilder) liegen etwa 10-25 m genau. Bilder mit `"nutzen": false` in der JSON-Datei bleiben aus dem Mosaik heraus (14 von 111).

### Hochaufgelöste Scans: Bestand und Kosten

Im Atlas sind nur die drei NCAP-Frames vom 11.04.1945 hochaufgelöst (0,18-0,20 m/px). Alle LAiV-Ebenen beruhen auf freien Vorschaubildern. Das LAiV nennt keine Scanauflösung. Wären seine Scans so groß wie die NCAP-Scans (rund 8000 px), wären sie etwa fünfmal feiner als die Vorschauen.

**Bereits bezahlt:** 3 Scans bei der NCAP (3054, 4053, 4071) zu je 35 £, zusammen **105 £**. Die Frames decken den Airpark ganz ab, das Fusion-Gelände zu 62 % und das Gesamtgebiet zu 37 %.

**Vorschlag für den Kauf beim LAiV M-V** (25 € netto je Bild, Mindestentgelt 60 € je Auftrag, Entgeltvorschrift ab 01.01.2026):

| Stand | Bilder | Anzahl | Netto |
|---|---|---:|---:|
| 11.04.1945, nach dem Angriff | 4070, 3056, 4069 | 3 | 75 € |
| 08.04.1945, vor dem Angriff | 3094, 3079, 3098 | 3 | 75 € |
| 28.05.1944 | 2008, 2009 | 2 | 50 € |
| 26.08.1990 | 90_235_10_0012, 90_235_11_0037 | 2 | 50 € |
| 23.04.1995 | 95_04_18_0993 | 1 | 25 € |
| **Vorschlag** | | **11** | **275 €** (327,25 € brutto) |

Optional: 11.04.1945 Ostteil (3075, 4055), 08.04.1945 Umland (3076, 3091), Übersichten 1944 (7023, 8016, 7005), 1999 und 2002 (je 1 Bild), zusammen 9 Bilder für 225 € netto. Den ganzen Katalog über dem Gesamtgebiet zu kaufen (130 Kriegs- und 125 Nachkriegsbilder), kostet 6.375 € netto und wiederholt meist dieselbe Fläche.

Mögliche Zuschläge und offene Punkte:

- Muss ein Bild erst gescannt werden, kommen 13-14 € je Bild hinzu, bei schwierigen Vorlagen 50 % mehr.
- Die Entgeltvorschrift (Nr. 3.2.1) nennt die externe Nutzung als enthalten, die AGNB (Nr. 7.2.2) begrenzen Internet-Veröffentlichungen auf zehn Bilder mit je 1 Megapixel. Für Unterlizenzen fällt jährlich 100-300 % des Entgelts an (Nr. 3.2.3). Das ist vor dem Kauf mit dem LAiV zu klären.
- Die NCAP nennt für Scans auf Bestellung derzeit 55 £ netto je Bild plus 4 £ je Filmdose, dazu eine Lizenz (nicht kommerzielle Website: 11 £ für 5 Jahre).
- Orthophotos der Jahrgänge 1953, 1991 und ab 2002 sind über Download- und Darstellungsdienst des LAiV kostenlos (CC BY 4.0).

## Koordinatensystem

- ETRS89 / UTM Zone 33N (EPSG:25833)
- Gesamtgebiet: E 348.200-352.000, N 5.906.700-5.910.500 (3.800 x 3.800 m), umfasst den ganzen Flugplatz einschließlich Fusion-Gelände
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
