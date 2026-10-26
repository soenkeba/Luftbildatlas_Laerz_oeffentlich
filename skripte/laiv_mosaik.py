"""Mosaik je Flugtag aus den registrierten LAiV-Vorschaubildern.

Eingabe:  georeferenz_parameter/LAiV_Homographien_Vorschau_px_auf_Karte_m.json (laiv_reg.py)
          rohdaten/laiv_vorschau/*.jpg
Ausgabe:  app/luftbild_<Datum>.webp (2400 × 2400 px, 1 m/px, Ursprung wie DOP 1953)

Je Kartenpixel wird das Bild genommen, in dem der Punkt am nächsten zur Bildmitte
liegt (geringste Verkippung/Verzeichnung). Nicht abgedeckte Flächen sind transparent.

Nutzung (aus dem Projektordner):  python3 skripte/laiv_mosaik.py
"""
import numpy as np, cv2, json

SRC = "rohdaten/laiv_vorschau"
W = 2400
res = json.load(open("georeferenz_parameter/LAiV_Homographien_Vorschau_px_auf_Karte_m.json"))
cl = cv2.createCLAHE(1.5, (8, 8))
yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)

for datum in sorted({n[:10] for n in res}):
    mos = np.zeros((W, W), np.uint8); best = np.full((W, W), np.inf, np.float32); teile = []
    for name, r in sorted(res.items()):
        if name[:10] != datum: continue
        im = cl.apply(cv2.imread(f"{SRC}/{name}.jpg", 0))
        H = np.array(r["H"]); x0, y0, x1, y1 = r["clip"]
        # Karten-m -> Bild-px, normierter Abstand zur Bildmitte (Chebyshev)
        Hi = np.linalg.inv(H)
        d = Hi[2, 0] * xx + Hi[2, 1] * yy + Hi[2, 2]
        u = (Hi[0, 0] * xx + Hi[0, 1] * yy + Hi[0, 2]) / d
        v = (Hi[1, 0] * xx + Hi[1, 1] * yy + Hi[1, 2]) / d
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dist = np.maximum(np.abs(u - cx) / ((x1 - x0) / 2), np.abs(v - cy) / ((y1 - y0) / 2))
        sel = (dist < 1) & (dist < best)
        if not sel.any(): continue
        w = cv2.remap(im, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR)
        mos[sel] = w[sel]; best[sel] = dist[sel]; teile.append(name.split("_")[4])
    cov = np.isfinite(best).mean() * 100
    alpha = np.where(np.isfinite(best), 255, 0).astype(np.uint8)
    bgra = cv2.merge([mos, mos, mos, alpha])
    cv2.imwrite(f"app/luftbild_{datum}.webp", bgra, [cv2.IMWRITE_WEBP_QUALITY, 82])
    print(f"{datum}: Bilder {' '.join(teile)}, Abdeckung {cov:.1f} %")
