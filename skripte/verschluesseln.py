"""Verschlüsselt vertrauliche Ebenen für den Luftbildatlas Lärz.

Die Originale liegen in vertraulich/ (per .gitignore ausgeschlossen), beschrieben in
vertraulich/ebenen.json (Vorlage: skripte/ebenen_vertraulich.beispiel.json).
Ausgabe nach app/airparkinternal/: index.json (Schlüsselparameter + verschlüsselte Ebenenliste)
und je Ebene eine .bin-Datei. Nur diese verschlüsselten Dateien kommen ins Repo.

Verfahren: PBKDF2-HMAC-SHA256 (600.000 Runden) → AES-256-GCM. Jede Datei: 12 Byte IV + Chiffrat.
Die App entschlüsselt mit WebCrypto im Browser. Der Passwort-Bereich erscheint nur über den Link
…/app/?airparkinternal (danach mit „Auf diesem Gerät merken“ auch ohne Parameter).

Einmalig: pip3 install cryptography numpy pillow   (falls der Build scheitert: --only-binary=:all:)

Nutzung (aus dem Projektordner):
  python3 skripte/verschluesseln.py                       # Passwort wird abgefragt
  LAERZ_PASSWORT='...' python3 skripte/verschluesseln.py   # Passwort aus Umgebungsvariable

Georeferenz je Ebene ("georef"):
  "auto"      GeoTIFF-Tags, sonst World-File (.jgw/.pgw/.tfw/.wld) neben dem Bild – Standard
  "voll"      Bild deckt genau das Arbeitsgebiet ab (E 348600–351000, N 5906700–5909100)
  {"ecken": [[E,N],[E,N],[E,N],[E,N]]}   Bildecken oben links, oben rechts, unten rechts, unten links
  {"H": [[...],[...],[...]]}             Homographie Bildpixel → Karten-Meter (wie die 1945er Frames)
Koordinaten in ETRS89 / UTM 33N (EPSG:25833); EPSG:5650 (Ostwert mit „33“ davor) wird erkannt.
"""
import base64, getpass, hashlib, hmac, io, json, os, secrets, sys

import numpy as np
from PIL import Image
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

QUELLE = "vertraulich"
ZIEL = "app/airparkinternal"
E0, N0, W = 348600, 5909100, 2400
ITER = 600_000
Image.MAX_IMAGE_PIXELS = None


def fehler(msg):
    sys.exit(f"FEHLER: {msg}")


def utm(e, n):
    """EPSG:5650 (Zonenpräfix 33) auf EPSG:25833 bringen und Plausibilität prüfen."""
    if e > 3e7:
        e -= 33e6
    if not (1e5 < e < 1e6 and 5e6 < n < 7e6):
        fehler(f"Koordinate E {e:.0f} / N {n:.0f} ist nicht UTM 33N – bitte umprojizieren "
               "(gdalwarp -t_srs EPSG:25833 ...).")
    return e, n


def affin_zu_H(a, b, c, d, e, f):
    """E = a·col + b·row + c, N = d·col + e·row + f (Pixelecke) → Karten-Meter."""
    c, f = utm(c, f)
    return np.array([[a, b, c - E0], [-d, -e, N0 - f], [0, 0, 1.0]])


def georef_auto(pfad, img):
    tags = getattr(img, "tag_v2", None)
    if tags and 33922 in tags and 33550 in tags:
        i, j, _, x, y, _ = tags[33922][:6]
        sx, sy = tags[33550][:2]
        geokeys = tags.get(34735)
        if geokeys:
            keys = {geokeys[k]: geokeys[k + 3] for k in range(4, len(geokeys), 4)}
            if keys.get(3072) not in (None, 25833, 5650):
                fehler(f"{pfad}: GeoTIFF in EPSG:{keys[3072]} – bitte nach EPSG:25833 umprojizieren.")
        return affin_zu_H(sx, 0, x - i * sx, 0, -sy, y + j * sy)
    stamm = os.path.splitext(pfad)[0]
    endung = os.path.splitext(pfad)[1].lower()
    kandidaten = [endung[:2] + endung[-1] + "w", ".wld", ".jgw", ".pgw", ".tfw"]
    for k in kandidaten:
        for p in (stamm + k, stamm + k.upper(), pfad + "w"):
            if os.path.exists(p):
                a, d, b, e, c, f = [float(z) for z in open(p).read().split()[:6]]
                # World-File bezieht sich auf die Pixelmitte, CSS/Canvas auf die Pixelecke
                return affin_zu_H(a, b, c - a / 2 - b / 2, d, e, f - d / 2 - e / 2)
    fehler(f"{pfad}: keine Georeferenz gefunden (GeoTIFF-Tags oder World-File).")


def georef_ecken(ecken, w, h):
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = []
    for e, n in ecken:
        e, n = utm(e, n)
        dst.append((e - E0, N0 - n))
    A, rhs = [], []
    for (u, v), (x, y) in zip(src, dst):
        A.append([u, v, 1, 0, 0, 0, -u * x, -v * x]); rhs.append(x)
        A.append([0, 0, 0, u, v, 1, -u * y, -v * y]); rhs.append(y)
    h8 = np.linalg.solve(np.array(A, float), np.array(rhs, float))
    return np.append(h8, 1).reshape(3, 3)


def bild_kodieren(img):
    hat_alpha = img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info
    buf = io.BytesIO()
    if hat_alpha:
        img.convert("RGBA").save(buf, "PNG", optimize=True)
        return buf.getvalue(), "image/png"
    img.convert("RGB").save(buf, "JPEG", quality=85, optimize=True)
    return buf.getvalue(), "image/jpeg"


def verschluesseln(key, daten):
    iv = secrets.token_bytes(12)
    return iv + AESGCM(key).encrypt(iv, daten, None)


def main():
    cfg_pfad = os.path.join(QUELLE, "ebenen.json")
    if not os.path.exists(cfg_pfad):
        fehler(f"{cfg_pfad} fehlt. Vorlage: skripte/ebenen_vertraulich.beispiel.json "
               f"nach {cfg_pfad} kopieren und anpassen.")
    cfg = json.load(open(cfg_pfad, encoding="utf-8"))

    pw = os.environ.get("LAERZ_PASSWORT") or getpass.getpass("Passwort: ")
    if "LAERZ_PASSWORT" not in os.environ and getpass.getpass("Wiederholen: ") != pw:
        fehler("Passwörter stimmen nicht überein.")
    if len(pw) < 12:
        print("WARNUNG: Passwort kürzer als 12 Zeichen – die verschlüsselten Dateien sind öffentlich "
              "und können offline durchprobiert werden.")
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER, 32)

    os.makedirs(ZIEL, exist_ok=True)
    for alt in os.listdir(ZIEL):
        if alt.endswith(".bin") or alt == "index.json":
            os.remove(os.path.join(ZIEL, alt))

    ebenen = []
    for e in cfg["ebenen"]:
        pfad = os.path.join(QUELLE, e["datei"])
        img = Image.open(pfad)
        w, h = img.size
        g = e.get("georef", "auto")
        if g == "auto":
            H = georef_auto(pfad, img)
        elif g == "voll":
            H = np.array([[W / w, 0, 0], [0, W / h, 0], [0, 0, 1.0]])
        elif "ecken" in g:
            H = georef_ecken(g["ecken"], w, h)
        elif "H" in g:
            H = np.array(g["H"], float)
        else:
            fehler(f"{e['id']}: unbekannte Georeferenz {g!r}")
        clip = e.get("clip", [0, 0, w, h])

        # Verkleinern, Homographie und Clip mitskalieren
        s = max(w, h) / e.get("max_px", 4000)
        if s > 1:
            w2, h2 = round(w / s), round(h / s)
            img = img.resize((w2, h2), Image.LANCZOS)
            H = H @ np.diag([w / w2, h / h2, 1])
            clip = [clip[0] * w2 / w, clip[1] * h2 / h, clip[2] * w2 / w, clip[3] * h2 / h]
            w, h = w2, h2
        H = H / H[2, 2]

        daten, mime = bild_kodieren(img)
        datei = hmac.new(key, e["id"].encode(), "sha256").hexdigest()[:16] + ".bin"
        open(os.path.join(ZIEL, datei), "wb").write(verschluesseln(key, daten))

        def pt(u, v):
            q = H @ [u, v, 1]
            return q[:2] / q[2]
        ecken = np.array([pt(clip[0], clip[1]), pt(clip[2], clip[1]), pt(clip[2], clip[3]), pt(clip[0], clip[3])])
        mpx = np.linalg.norm(pt(w / 2 + 1, h / 2) - pt(w / 2, h / 2))
        lo, hi = ecken.min(0), ecken.max(0)
        print(f"  {e['id']}: {w}×{h} px, {mpx:.2f} m/px, Karte x {lo[0]:.0f}…{hi[0]:.0f}, "
              f"y {lo[1]:.0f}…{hi[1]:.0f}, {len(daten)//1024} kB → {datei}")
        if hi[0] < 0 or hi[1] < 0 or lo[0] > W or lo[1] > W:
            print("    WARNUNG: Bild liegt vollständig außerhalb des Arbeitsgebiets.")

        ebenen.append({
            "id": e["id"], "name": e["name"], "sub": e.get("sub", "Airpark intern"),
            "desc": e.get("desc", ""), "datei": datei, "mime": mime, "w": w, "h": h,
            "H": H.tolist(), "clip": [round(c, 1) for c in clip],
            "op": e.get("deckkraft", 0.85), "sw": e.get("farbe", "#c0392b"),
        })

    manifest = json.dumps({"ebenen": ebenen}, ensure_ascii=False).encode()
    index = {
        "version": 1,
        "kdf": {"name": "PBKDF2", "hash": "SHA-256", "iter": ITER, "salt": base64.b64encode(salt).decode()},
        "manifest": base64.b64encode(verschluesseln(key, manifest)).decode(),
    }
    json.dump(index, open(os.path.join(ZIEL, "index.json"), "w"), indent=1)
    print(f"{len(ebenen)} Ebene(n) verschlüsselt nach {ZIEL}/")


if __name__ == "__main__":
    main()
