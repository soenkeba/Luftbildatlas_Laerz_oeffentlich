"""Georeferenzierung der LAiV-Vorschaubilder (historische Luftbilder 1944/45).

Eingabe:  rohdaten/laiv_vorschau/*.jpg  (Dateiname: <Datum>_<Bildname>.jpg)
          app/dop_1953.jpg               (1 m/px, Pixel = Karten-Meter)
          app/f3054.jpg, f4053.jpg, f4071.jpg + Homographien (NCAP 11.04.1945)
Ausgabe:  georeferenz_parameter/LAiV_Homographien_Vorschau_px_auf_Karte_m.json

Ablauf je Bild:
  1. Start-Homographie per SIFT gegen ein 1-m-Mosaik der NCAP-Frames 1945
     (zeitlich näher als 1953, deshalb viele Übereinstimmungen), sonst aus
     Handpasspunkten (HAND), sonst SIFT gegen ein bereits registriertes Bild
     desselben Flugtags.
  2. 3 Iterationen Template-Korrelation auf Gradientenbildern gegen DOP 1953
     (wie reg.py) mit RANSAC -> projektive Homographie.

Nutzung (aus dem Projektordner):  python3 skripte/laiv_reg.py [Muster]
"""
import numpy as np, cv2, json, glob, os, sys

SRC = "rohdaten/laiv_vorschau"
OUT = "georeferenz_parameter/LAiV_Homographien_Vorschau_px_auf_Karte_m.json"
pat = sys.argv[1] if len(sys.argv) > 1 else "*"

ref = cv2.imread("app/dop_1953.jpg", 0)
Hh, Ww = ref.shape
cl = cv2.createCLAHE(2.0, (16, 16))

def prep(im):
    im = cl.apply(im); g = cv2.GaussianBlur(im, (0, 0), 1.5)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    return cv2.GaussianBlur(np.sqrt(gx * gx + gy * gy), (0, 0), 1.0)

def bildmaske(im):
    """Bildinhalt ohne Filmrand/Beschriftung: 4 % Rand abschneiden."""
    h, w = im.shape; m = np.zeros_like(im)
    m[int(h * .04):int(h * .96), int(w * .04):int(w * .96)] = 255
    return m

R = prep(ref)

# Handpasspunkte (Vorschau-px -> Karten-m) für Bilder, bei denen SIFT gegen 1945 scheitert:
# Rollbahnkreuz, SO-Ende der NW-SO-Bahn, W-Ende der SW-NO-Bahn
HAND = {"1944-05-28_44_186_00_2008_L_2742": ([[515, 455], [940, 870], [165, 625]],
                                             [[1183, 504], [1764, 1392], [516, 648]])}

# ── Referenzmosaik NCAP 11.04.1945, 1 m/px (Homographien für Original-Scans, app-Bilder halb so groß)
HN = json.load(open("georeferenz_parameter/Homographien_Frame_px_auf_Karte_m.json"))
CLIP = {"4071": (320, 240, 3690, 3615), "4053": (235, 260, 3615, 3570), "3054": (260, 210, 3615, 3590)}
ref45 = np.zeros((Hh, Ww), np.uint8); m45 = np.zeros((Hh, Ww), np.uint8)
for n, c in CLIP.items():
    f = cv2.imread(f"app/f{n}.jpg", 0); fm = np.zeros_like(f); fm[c[1]:c[3], c[0]:c[2]] = 255
    H = np.array(HN[n]) @ np.diag([2., 2., 1.])
    w = cv2.warpPerspective(f, H, (Ww, Hh), flags=cv2.INTER_AREA)
    wm = cv2.warpPerspective(fm, H, (Ww, Hh), flags=cv2.INTER_NEAREST)
    sel = (wm > 0) & (m45 == 0); ref45[sel] = w[sel]; m45[sel] = 255

sift = cv2.SIFT_create(8000)
matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))

def merkmale(im, m):
    k, d = sift.detectAndCompute(cl.apply(im), m)
    return np.float32([p.pt for p in k]), d

sift.setNFeatures(30000)
K45 = merkmale(ref45, cv2.erode(m45, np.ones((15, 15), np.uint8)))
sift.setNFeatures(8000)

def sift_h(A, B):
    """Homographie A-px -> B-px, Anzahl Inlier."""
    (pa, da), (pb, db) = A, B
    g = [a for a, b in matcher.knnMatch(da, db, k=2) if a.distance < 0.75 * b.distance]
    if len(g) < 15: return None, 0
    P = pa[[a.queryIdx for a in g]]; Q = pb[[a.trainIdx for a in g]]
    H, inl = cv2.findHomography(P, Q, cv2.RANSAC, 8.0, maxIters=50000)
    return (H, int(inl.sum())) if H is not None else (None, 0)

def verfeinern(im, m, Hm):
    err, n = None, 0
    for it in range(3):
        w = cv2.warpPerspective(im, Hm, (Ww, Hh), flags=cv2.INTER_LINEAR)
        wm = cv2.warpPerspective(m, Hm, (Ww, Hh), flags=cv2.INTER_NEAREST)
        W = prep(w)
        src, dst = [], []
        win = 48 if it == 0 else 40; srch = 40 if it == 0 else 15
        for y in range(srch + win, Hh - srch - win, 40):
            for x in range(srch + win, Ww - srch - win, 40):
                if wm[y - win - srch:y + win + srch, x - win - srch:x + win + srch].min() == 0: continue
                t = W[y - win:y + win, x - win:x + win]
                if t.std() < 4: continue
                s = R[y - win - srch:y + win + srch, x - win - srch:x + win + srch]
                c = cv2.matchTemplate(s, t, cv2.TM_CCOEFF_NORMED)
                _, mx, _, ml = cv2.minMaxLoc(c)
                if mx < 0.35: continue
                c2 = c.copy(); cv2.circle(c2, ml, 8, -1, -1)
                if mx - c2.max() < 0.06: continue
                f = np.linalg.inv(Hm) @ np.array([x, y, 1.]); f /= f[2]
                src.append(f[:2]); dst.append([x + ml[0] - srch, y + ml[1] - srch])
        if len(src) < 15: return Hm, None, len(src)
        src = np.float32(src); dst = np.float32(dst)
        Hn, inl = cv2.findHomography(src, dst, cv2.RANSAC, 6.0 if it < 2 else 4.0, maxIters=20000)
        inl = inl.ravel().astype(bool)
        e = np.linalg.norm(cv2.perspectiveTransform(src[inl][None], Hn)[0] - dst[inl], axis=1)
        err = float(np.sqrt((e ** 2).mean())); n = int(inl.sum()); Hm = Hn
    return Hm, err, n

os.makedirs(os.path.dirname(OUT), exist_ok=True)
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
offen = {os.path.basename(f)[:-4]: f for f in sorted(glob.glob(f"{SRC}/{pat}.jpg"))}
bilder, feat = {}, {}
for name, fn in offen.items():
    im = cv2.imread(fn, 0); m = bildmaske(im)
    bilder[name] = (im, m); feat[name] = merkmale(im, m)

def annehmen(name, H, wie):
    im, m = bilder[name]
    H, rmse, n = verfeinern(im, m, H)
    if rmse is None or n < 25 or rmse > 4.0:
        print(f"{name}: verworfen ({wie}, {n} Passpunkte, Restfehler {rmse})"); return False
    h, w = im.shape; c = np.float32([[[w / 2, h / 2], [w / 2 + 100, h / 2], [w / 2, h / 2 + 100]]])
    p = cv2.perspectiveTransform(c, H)[0]
    mpx = (np.linalg.norm(p[1] - p[0]) + np.linalg.norm(p[2] - p[0])) / 200
    print(f"{name}: {wie}, {n} Passpunkte, Restfehler {rmse:.2f} m, {mpx:.2f} m/px")
    res[name] = dict(w=w, h=h, H=H.tolist(), n=n, rmse=round(rmse, 2), mpx=round(float(mpx), 3),
                     clip=[int(w * .04), int(h * .04), int(w * .96), int(h * .96)])
    json.dump(res, open(OUT, "w"), indent=1)
    return True

# Runde 1: gegen NCAP-Mosaik; Runde 2+: gegen schon registrierte Bilder desselben Tages
rest = []
for name in offen:
    H, n = sift_h(feat[name], K45)
    if H is not None and n >= 30 and annehmen(name, H, f"SIFT 1945 {n}"): continue
    if name in HAND:
        A, _ = cv2.estimateAffinePartial2D(np.float32(HAND[name][0]), np.float32(HAND[name][1]))
        if annehmen(name, np.vstack([A, [0, 0, 1]]), "Handpasspunkte"): continue
    rest.append(name)
paare = {}
fortschritt = True
while rest and fortschritt:
    fortschritt = False
    for name in list(rest):
        best = (0, None, None)
        for r in res:
            if r in feat and r[:10] == name[:10]:
                if (name, r) not in paare: paare[name, r] = sift_h(feat[name], feat[r])
                H, n = paare[name, r]
                if n > best[0]: best = (n, H, r)
        n, H, r = best
        if n >= 40 and annehmen(name, np.array(res[r]["H"]) @ H, f"SIFT über {r[-14:-7]} {n}"):
            rest.remove(name); fortschritt = True
for name in rest: print(f"{name}: nicht registriert")

