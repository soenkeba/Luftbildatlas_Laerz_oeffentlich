"""Lädt Kartenebenen für den Luftbildatlas Lärz per WMS.
Arbeitsgebiet: E 348600–351000, N 5906700–5909100 (EPSG:25833), 2400 × 2400 m.
Ausgabe nach app/. Alle Dienste sind frei nutzbar (CC BY 4.0 bzw. dl-de/by-2-0).

Nutzung:
  python3 fetch_geobasis.py          # Alles herunterladen
  python3 fetch_geobasis.py --update  # Nur Satellitenbilder aktualisieren (Sentinel-2)
"""
import subprocess, os, sys

os.makedirs("app", exist_ok=True)
B = "348600,5906700,351000,5909100"
UPDATE_ONLY = "--update" in sys.argv

def get(url, out):
    path = f"app/{out}"
    print(f"  {out} ...", end=" ", flush=True)
    r = subprocess.run(["curl", "-s", "-m", "300", "-o", path, url])
    if r.returncode == 0 and os.path.getsize(path) > 1000:
        print(f"OK ({os.path.getsize(path)//1024} kB)")
    else:
        print("FEHLER" if r.returncode else f"zu klein ({os.path.getsize(path)} B) – Layer evtl. leer?")

def mv(svc, layer, out, w=2400, fmt="image/jpeg", style="", extra=""):
    """WMS-Request an geodaten-mv.de."""
    get(f"https://www.geodaten-mv.de/dienste/{svc}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS={layer}&STYLES={style}&CRS=EPSG:25833&BBOX={B}&WIDTH={w}&HEIGHT={w}"
        f"&FORMAT={fmt}{extra}", out)

def ext(base, svc, layer, out, w=2400, fmt="image/jpeg", extra=""):
    """WMS-Request an externen Server (BKG, basemap.de)."""
    get(f"{base}/{svc}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS={layer}&STYLES=&CRS=EPSG:25833&BBOX={B}&WIDTH={w}&HEIGHT={w}"
        f"&FORMAT={fmt}{extra}", out)

BKG = "https://sgx.geodatenzentrum.de"

if not UPDATE_ONLY:
    # ── GeoBasis-DE/M-V  (© GeoBasis-DE/M-V, CC BY 4.0) ──────────────
    print("\n── GeoBasis-DE/M-V ──")
    mv("adv_dop",    "mv_dop",     "dop_heute.jpg", 4000)          # DOP aktuell, 0,6 m/px
    mv("dop1991_wms","mv_dop1991", "dop_1991.jpg",  4000)          # DOP 1991 (CIR), 0,6 m/px
    mv("dop1953_wms","mv_dop1953", "dop_1953.jpg")                 # DOP 1953, 1,0 m/px
    mv("alkis_wms",  "adv_alkis_flurstuecke,adv_alkis_gebaeude",
       "alkis.png", 4000, "image/png", "Gelb,Gelb", "&TRANSPARENT=TRUE")

    # Topographische Karten
    mv("tk25m_laiv_wms", "mv_tk25m",  "tk25_messtisch.jpg")        # Messtischblatt 1877–1943
    mv("tk25as_laiv_wms","mv_tk25as", "tk25_ddr.jpg")              # TK25 DDR-Ausgabe 1981–87
    mv("adv_dtk25",      "mv_dtk25",  "dtk25.jpg")                # DTK25 aktuell

    # Geländemodell (Schummerung)
    mv("dgm_wms", "schummerung_NW", "dgm.png", 2400, "image/png", "", "&TRANSPARENT=TRUE")

    # ── BKG  (© BKG, dl-de/by-2-0) ────────────────────────────────────
    print("\n── BKG ──")
    ext(BKG, "wms_topplus_open", "web", "topo_bkg.jpg")            # TopPlusOpen Topo-Karte
    ext(BKG, "wms_basemapde", "de_basemapde_web_raster_farbe", "osm.jpg")  # basemap.de/OSM

# ── Sentinel-2 Zeitreihe (© BKG, dl-de/by-2-0) ───────────────────────
# Verfügbare Jahre: 2018–2024. Werden bei --update immer neu geladen.
print("\n── Sentinel-2 Zeitreihe (BKG) ──")
S2_YEARS = [2018, 2020, 2022, 2024]  # Auswahl, alle 2 Jahre
for year in S2_YEARS:
    ext(BKG, "wms_sentinel2_de", "rgb", f"sentinel2_{year}.jpg",
        extra=f"&TIME={year}-01-01T00:00:00Z")

print("\nFertig. Bilder liegen in app/.")
if not UPDATE_ONLY:
    print("Tipp: 'python3 fetch_geobasis.py --update' lädt nur die Sentinel-2-Bilder neu.")
