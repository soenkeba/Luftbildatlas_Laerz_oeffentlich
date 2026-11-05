"""Blockausgleich der LAiV-Vorschaubilder je Gruppe von Flugtagen.

Einzeln gegen DOP 1953 eingepasste Bilder können auf dem Flugfeld (wenig Passpunkte) und an den
Nähten mehrere Dutzend Meter auseinanderliegen. Hier werden alle überlappenden Bilder direkt
miteinander verknüpft (Gitter-Korrelation der entzerrten Bilder); die NCAP-Frames und DOP 1953
gehen als feste Bilder ein. 15 % der Punkte bleiben aus dem Ausgleich heraus und dienen der Kontrolle.

Nutzung (aus dem Projektordner):
  python3 skripte/laiv_block.py 1945-04-08,1945-04-11 [Ausgabe.json]
  python3 skripte/laiv_block.py 1944-05-10,1944-05-28 [Ausgabe.json]
Ohne Ausgabe wird die Homographien-Datei überschrieben. Danach laiv_mosaik.py starten.
Bilder mit "nutzen": false werden mitgerechnet; das Feld bleibt unverändert und wird von Hand entschieden.
Laufzeit: je nach Bildzahl bis über eine Stunde.
"""
import sys, json, itertools
import numpy as np, cv2
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix

HF = "georeferenz_parameter/LAiV_Homographien_Vorschau_px_auf_Karte_m.json"
NCAP = "georeferenz_parameter/Homographien_Frame_px_auf_Karte_m.json"
SRC = "rohdaten/laiv_vorschau"
X0, Y0, N = -1200, -2200, 5400            # Rechengebiet, größer als das Kartengebiet
STUFEN = [(2, 70), (2, 25), (1.25, 12)]   # (m/px, Suchradius m)
W_FEST = {"DOP1953": 1.0, "NCAP": 1.5}    # Gewichte der festen Bilder
cl = cv2.createCLAHE(1.5, (8, 8))


def pr(H, p):
    q = np.c_[p, np.ones(len(p))] @ H.T
    return q[:, :2] / q[:, 2:]


def verknuepfen(res, tage, RES, SUCH):
    """Alle überlappenden Bildpaare: Gitter-NCC, je Paar Ausreißer per RANSAC entfernen."""
    W = int(N / RES)
    A = np.array([[RES, 0, X0], [0, RES, Y0], [0, 0, 1.0]])
    Ai = np.linalg.inv(A)
    PAT, STEP, S = int(120 / RES) | 1, int(70 / RES), int(SUCH / RES)

    def hp(g):
        g = g.astype(np.float32)
        return g - cv2.GaussianBlur(g, (0, 0), 30 / RES)

    def eintrag(g, H, clip, fest):
        m = np.zeros(g.shape, np.uint8)
        x0, y0, x1, y1 = clip
        m[y0:y1, x0:x1] = 255
        M = Ai @ H
        return dict(w=hp(cv2.warpPerspective(g, M, (W, W), flags=cv2.INTER_LINEAR)),
                    m=cv2.warpPerspective(m, M, (W, W), flags=cv2.INTER_NEAREST) > 0, H=H, fest=fest)

    bilder = {}
    for n, r in res.items():
        if n[:10] in tage:
            g = cl.apply(cv2.imread(f"{SRC}/{n}.jpg", 0))
            g = cv2.GaussianBlur(g, (0, 0), max(0.5, 0.5 * RES / r["mpx"]))
            e = eintrag(g, np.array(r["H"]), r["clip"], False)
            if e["m"].mean() > 1e-3:
                bilder[n] = e
    for k, H in json.load(open(NCAP)).items():      # app/f*.jpg haben halbe Auflösung
        g = cv2.imread(f"app/f{k}.jpg", 0)
        h, w = g.shape
        g = cv2.GaussianBlur(cl.apply(g), (0, 0), max(0.5, RES / 1.6))
        clip = [int(.02 * w), int(.02 * h), int(.98 * w), int(.98 * h)]
        bilder["NCAP" + k] = eintrag(g, np.array(H) @ np.diag([2.0, 2.0, 1.0]), clip, True)
    g = cv2.imread("app/dop_1953.jpg", 0)
    bilder["DOP1953"] = eintrag(cl.apply(g), np.array([[1, 0, -400], [0, 1, -1400], [0, 0, 1.0]]),
                                [0, 0, g.shape[1], g.shape[0]], True)

    paare = []
    for a, b in itertools.combinations(bilder, 2):
        Ba, Bb = bilder[a], bilder[b]
        if Ba["fest"] and Bb["fest"]:
            continue
        ov = Ba["m"] & Bb["m"]
        if ov.mean() < 2e-3:
            continue
        pts = []
        for y in range(S + PAT // 2, W - S - PAT // 2, STEP):
            for x in range(S + PAT // 2, W - S - PAT // 2, STEP):
                y0, x0 = y - PAT // 2, x - PAT // 2
                if not ov[y0:y0 + PAT, x0:x0 + PAT].all():
                    continue
                t = Ba["w"][y0:y0 + PAT, x0:x0 + PAT]
                if t.std() < 3:
                    continue
                c = cv2.matchTemplate(Bb["w"][y0 - S:y0 + PAT + S, x0 - S:x0 + PAT + S], t, cv2.TM_CCOEFF_NORMED)
                _, mx, _, lo = cv2.minMaxLoc(c)
                if not (0 < lo[0] < c.shape[1] - 1 and 0 < lo[1] < c.shape[0] - 1):
                    continue
                c2 = c.copy()
                r = max(3, int(10 / RES))
                c2[max(0, lo[1] - r):lo[1] + r + 1, max(0, lo[0] - r):lo[0] + r + 1] = -1

                def sp(l, m, h):
                    d = 2 * m - l - h
                    return 0 if abs(d) < 1e-6 else .5 * (h - l) / d
                pts.append((x, y, lo[0] - S + sp(c[lo[1], lo[0] - 1], mx, c[lo[1], lo[0] + 1]),
                            lo[1] - S + sp(c[lo[1] - 1, lo[0]], mx, c[lo[1] + 1, lo[0]]), mx, c2.max()))
        if len(pts) < 8:
            continue
        P = np.array(pts)
        # Gegen 1953 hat sich das Gelände verändert, daher dort mildere Schwellen
        dop = "DOP1953" in (a, b)
        P = P[(P[:, 4] > (.35 if dop else .45)) & (P[:, 4] - P[:, 5] > (.05 if dop else .06))]
        if len(P) < 8:
            continue
        src, dst = P[:, :2], P[:, :2] + P[:, 2:4]
        Hm, inl = cv2.findHomography(src.astype(np.float32), dst.astype(np.float32), cv2.RANSAC, 4.0 / RES,
                                     maxIters=5000, confidence=.999)
        if Hm is None or inl.sum() < 8:
            continue
        I = inl.ravel() > 0
        paare.append(dict(a=a, b=b, pa=pr(np.linalg.inv(Ba["H"]) @ A, src[I]), pb=pr(np.linalg.inv(Bb["H"]) @ A, dst[I])))
    return paare, {k: v["H"] for k, v in bilder.items() if v["fest"]}


def hm(s, d):
    M, r = [], []
    for (x, y), (u, v) in zip(s, d):
        M += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        r += [u, v]
    return np.append(np.linalg.solve(np.array(M, float), np.array(r, float)), 1).reshape(3, 3)


def ausgleichen(res, paare, fest):
    """Je Bild die vier Ecken in Karten-Metern als Unbekannte; robuste Kleinste Quadrate."""
    frei = sorted({n for p in paare for n in (p["a"], p["b"]) if n not in fest})
    ix = {n: i for i, n in enumerate(frei)}
    ecke = {n: np.array([[res[n]["clip"][i], res[n]["clip"][j]] for i, j in ((0, 1), (2, 1), (2, 3), (0, 3))], float) for n in frei}
    start = np.concatenate([pr(np.array(res[n]["H"]), ecke[n]).ravel() for n in frei])
    rng = np.random.default_rng(1)
    A, B, W_ = [], [], []
    for p in paare:
        w = 1.0
        for x in (p["a"], p["b"]):
            if x in fest:
                w = W_FEST["DOP1953"] if x == "DOP1953" else W_FEST["NCAP"]
        A += [p["a"]] * len(p["pa"]); B += [p["b"]] * len(p["pa"]); W_ += [w] * len(p["pa"])
    A, B, W_ = np.array(A), np.array(B), np.array(W_)
    PA, PB = np.vstack([p["pa"] for p in paare]), np.vstack([p["pb"] for p in paare])
    kontrolle = rng.random(len(A)) < .15
    QA, QB = np.zeros_like(PA), np.zeros_like(PB)
    for n, H in fest.items():
        if (A == n).any(): QA[A == n] = pr(H, PA[A == n])
        if (B == n).any(): QB[B == n] = pr(H, PB[B == n])
    gr = {n: (np.where(A == n)[0], np.where(B == n)[0]) for n in frei}

    def proj(v):
        v = v.reshape(-1, 4, 2)
        a, b = QA.copy(), QB.copy()
        for n in frei:
            H = hm(ecke[n], v[ix[n]])
            i, j = gr[n]
            if len(i): a[i] = pr(H, PA[i])
            if len(j): b[j] = pr(H, PB[j])
        return a, b

    TR = np.where(~kontrolle)[0]
    PRI = .015                                 # schwach zum Startwert, stabilisiert Bilder mit wenig Punkten

    def f(v):
        a, b = proj(v)
        return np.r_[((a - b)[TR] * W_[TR, None]).ravel(), PRI * (v - start)]
    nt = len(TR) * 2
    Sp = lil_matrix((nt + len(start), len(start)), dtype=int)
    for k, t in enumerate(TR):
        for n in (A[t], B[t]):
            if n in ix:
                Sp[2 * k:2 * k + 2, 8 * ix[n]:8 * ix[n] + 8] = 1
    for i in range(len(start)):
        Sp[nt + i, i] = 1
    r = least_squares(f, start, jac_sparsity=Sp, loss="soft_l1", f_scale=3., max_nfev=25, x_scale=10.)
    a0, b0 = proj(start); a1, b1 = proj(r.x)
    e0, e1 = np.hypot(*(a0 - b0).T), np.hypot(*(a1 - b1).T)
    fm = lambda e: f"Median {np.median(e[kontrolle]):.1f} m, p90 {np.percentile(e[kontrolle], 90):.1f} m"
    print(f"  {len(e1)} Punkte. Kontrollpunkte vorher: {fm(e0)}; nachher: {fm(e1)}", flush=True)
    v = r.x.reshape(-1, 4, 2)
    for n in frei:
        m = (A == n) | (B == n)
        res[n]["H"] = hm(ecke[n], v[ix[n]]).tolist()
        res[n]["korr"] = "block"
        res[n]["blk"] = dict(n=int(m.sum()), med=round(float(np.median(e1[m])), 2), p90=round(float(np.percentile(e1[m], 90)), 2))


if __name__ == "__main__":
    tage = sys.argv[1].split(",")
    aus = sys.argv[2] if len(sys.argv) > 2 else HF
    res = json.load(open(HF))
    for RES, SUCH in STUFEN:
        print(f"Stufe {RES} m/px, Suche ±{SUCH} m", flush=True)
        paare, fest = verknuepfen(res, tage, RES, SUCH)
        print(f"  {len(paare)} Bildpaare", flush=True)
        ausgleichen(res, paare, fest)
    json.dump(res, open(aus, "w"), indent=1)
