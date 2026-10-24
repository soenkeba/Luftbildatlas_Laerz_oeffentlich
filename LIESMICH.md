# Luftbildatlas Lärz

Ehemaliger Fliegerhorst Lärz (heute Müritz Airpark). Alliierte Aufklärungsfotos vom 11.04.1945 (NCAP, Sortie US7/0094/C, Frames 3054, 4053, 4071), einen Tag nach dem Angriff der 8th Air Force (Mission 938), entzerrt und vergleichbar mit den amtlichen Luftbildern von 1953, 1991 und heute, mit historischen Karten und mit aktuellen Satellitenbildern.

- `app/index.html` im Browser öffnen. Die `index.html` im Wurzelverzeichnis leitet dorthin weiter (für GitHub Pages).
- Ebenen, Deckkraft, Reihenfolge, Feinjustierung, Messen, Markieren, Sitzung als JSON, Bild-Export. Die Ebenenliste steht in der README.
- `georeferenziert/`: die drei Frames in ETRS89/UTM 33N (EPSG:25833), 0,3 m/Pixel, mit World-File – direkt in QGIS ladbar.
- `rohdaten/`: Original-Scans, Vorschauen, Geobasisdaten M-V mit World-Files.
- `skripte/`: Pipeline. Kartenebenen neu laden, aus dem Projektordner: `python3 skripte/fetch_geobasis.py`.

Genauigkeit: Restfehler der Entzerrung 1,8–2,9 m gegenüber dem Luftbild 1953.
Die heutige Startbahn wurde nach 1945 umgebaut und deckt sich deshalb nicht mit der Kriegsanlage.

**Keine Kampfmittelauskunft.** Für Bauvorhaben gilt allein die Auskunft des Munitionsbergungsdienstes M-V (LPBK).

Quellen und Lizenzen: NCAP / Historic Environment Scotland (Nutzungsbedingungen der NCAP beachten) · DOP, DOP 1953, DOP 1991, ALKIS, TK25, DTK25, DGM © GeoBasis-DE/M-V, CC BY 4.0 · TopPlusOpen, Sentinel-2, basemap.de © BKG bzw. BKG/OSM-Mitwirkende, dl-de/by-2-0 · Google Satellite © Google.
