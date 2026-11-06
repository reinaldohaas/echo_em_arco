# -*- coding: utf-8 -*-
r"""Testes que poderiam derrubar o resultado de analise_rotacao.py.

 A. Rotação seguindo o núcleo em todas as elevações de 13:30 e 13:36.
 B. Granizo em altitude: Z >= 55 e 60 dBZ acima de 2,5 km antes e durante a passagem.
 C. Profundidade dos núcleos de CC baixo: quantas elevações o mesmo objeto ocupa, em cada volume.
 D. Controle de granizo: núcleos de Z >= 60 dBZ até 120 km, a 0,5° e 0,9°, 12–15 UTC.
"""
import csv
import datetime as dt
import pathlib
import sys
import warnings

import numpy as np
from scipy.ndimage import label

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)
FIG = ar.FIG
AX, AY = ar.AX, ar.AY
T0 = dt.datetime(2026, 11, 4, 13, 30, 6)
UX, UY = .0404 * .9987, -.0404 * .05  # km/s, ajuste em analise_rotacao (40,4 m/s, quase para leste)
X0, Y0 = -4.9, -9.2


def pos_nucleo(h, idx):
    xc, yc = X0, Y0
    for _ in range(4):
        tt = (ar.t_gate(h, idx, xc, yc) - T0).total_seconds()
        xc, yc = X0 + UX * tt, Y0 + UY * tt
    return xc, yc, tt


def arco_no_nucleo(Vs, s, xc, yc, arco):
    rc = float(np.hypot(xc, yc))
    azc = float(np.degrees(np.arctan2(xc, yc)) % 360)
    pf = ar.perfil_arco(Vs, s, arco, setor=(azc - 12, azc + 12), rs=np.array([rc]))
    return pf[0] if pf else None


def teste_a():
    print("[A] hora ele r az_nucleo | arco 1 km: dV a b | arco 2 km: dV a b | controle da mesma varredura em 2 km: mediana p90 max (fora de 3 km do núcleo) | Vbruta min max no disco 2 km | sem V")
    linhas = []
    for h in ("133004", "133604"):
        for idx in range(8):
            s, V, Vq, vn, log, rots = ar.v_qc(h, idx)
            Vs = ar.mediana(Vq, 3)
            xc, yc, tt = pos_nucleo(h, idx)
            # refina pelo centroide do núcleo, se houver
            cs = [c for c in ar.nucleos(h, idx, min_g=6) if np.hypot(c["x"] - xc, c["y"] - yc) < 3]
            if cs:
                c = max(cs, key=lambda q: q["n"])
                xc, yc = c["x"], c["y"]
            a1, a2 = arco_no_nucleo(Vs, s, xc, yc, 1.0), arco_no_nucleo(Vs, s, xc, yc, 2.0)
            pf = ar.perfil_arco(Vs, s, 2.0)
            rc = np.hypot(xc, yc)
            out = np.array([p[1] for p in pf if abs(p[0] - rc) >= 3])
            x, y, r = ar.geom(s, V.shape[1])
            d = np.hypot(x - xc, y - yc) <= 2
            lin = {"hora": h[:4], "ele": s["ele_deg"], "n_nucleo": cs and c["n"] or 0, "r": round(float(rc), 1), "az": round(float(np.degrees(np.arctan2(xc, yc)) % 360), 1),
                   "dV1": a1 and round(a1[1], 1), "a1": a1 and a1[3] and round(a1[3], 1), "b1": a1 and a1[4] and round(a1[4], 1),
                   "dV2": a2 and round(a2[1], 1), "a2": a2 and a2[3] and round(a2[3], 1), "b2": a2 and a2[4] and round(a2[4], 1),
                   "ctl_med": round(float(np.median(out)), 1), "ctl_p90": round(float(np.percentile(out, 90)), 1), "ctl_max": round(float(np.max(out)), 1),
                   "Vbr_min": round(float(np.nanmin(V[d])), 1), "Vbr_max": round(float(np.nanmax(V[d])), 1), "semV": round(float(np.mean(~np.isfinite(V[d]))), 2)}
            linhas.append(lin)
            print("   ", *lin.values(), sep="\t")
    with open(FIG / "rotacao_seguindo_nucleo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


def teste_b():
    print("[B] Z em altitude (acima do radar), até 35 km do aeroporto: hora faixa_km gates Z>=50 Z>=55 Z>=60 Zmax (x,y do máx)")
    for h in ("131205", "131804", "132404", "133004", "133604"):
        n_el = len(ar.volume(h, "dBZ"))
        for z0, z1 in ((1.5, 2.5), (2.5, 4.0), (4.0, 6.0), (6.0, 9.0)):
            n50 = n55 = n60 = tot = 0
            zm, pm = -99, (0, 0)
            for idx in range(n_el):
                s = ar.volume(h, "dBZ")[idx]
                Z = ar.campo(s)
                x, y, r = ar.geom(s, Z.shape[1])
                al = ar.alt_radar(s["ranges_km"][:Z.shape[1]], s["ele_deg"])[None, :]
                m = (al >= z0) & (al < z1) & (np.hypot(x - AX, y - AY) <= 35) & np.isfinite(Z)
                if not m.any():
                    continue
                v = Z[m]
                tot += v.size
                n50 += int((v >= 50).sum())
                n55 += int((v >= 55).sum())
                n60 += int((v >= 60).sum())
                if v.max() > zm:
                    zm = float(v.max())
                    k = np.argmax(v)
                    pm = (float(x[m][k]), float(y[m][k]))
            print(f"    {h[:2]}:{h[2:4]} {z0}-{z1} n={tot} >=50:{n50} >=55:{n55} >=60:{n60} Zmax={zm:.1f} em ({pm[0]:.1f},{pm[1]:.1f})")


def teste_c():
    print("[C] por volume: fatias com núcleo (Z>=45, CC<.85, >=20 gates, r>5 km); objetos que ocupam >=4 elevações, agrupados em 4 km após corrigir 40 m/s não se aplica aqui; agrupa em 6 km")
    hs = ar.horas()
    for h in hs[hs.index("130005"):hs.index("140004") + 1]:
        pts = []
        for idx in range(8):
            for c in ar.nucleos(h, idx, min_g=20):
                pts.append((idx, c["x"], c["y"], c["n"], c["Zmax"]))
        grupos = []
        for p in pts:
            for g in grupos:
                if any(np.hypot(p[1] - q[1], p[2] - q[2]) < 6 for q in g):
                    g.append(p)
                    break
            else:
                grupos.append([p])
        res = []
        for g in grupos:
            el = {q[0] for q in g}
            res.append((len(el), round(np.mean([q[1] for q in g]), 1), round(np.mean([q[2] for q in g]), 1), max(q[3] for q in g), max(q[4] for q in g)))
        res.sort(reverse=True)
        print(f"    {h[:2]}:{h[2:4]} " + " ".join(f"[{a} elev ({b},{c}) n={d} Z={e:.0f}]" for a, b, c, d, e in res[:6]))


def teste_d():
    ar.RMAX = 120.0
    print("[D] núcleos Z>=60 a 0,5° e 0,9°, 12–15 UTC, r de 20 a 120 km: (controle de núcleos intensos fora da região próxima do radar)")
    lin = []
    for h in ar.horas():
        for idx in (0, 1):
            sz = ar.volume(h, "dBZ")[idx]
            Z = ar.campo(sz)
            C, D, K, W = [ar.campo(ar.volume(h, v)[idx]) for v in ("RhoHV", "ZDR", "KDP", "W")]
            x, y, r = ar.geom(sz, Z.shape[1])
            rot, n = label((Z >= 60) & (r > 20), structure=np.ones((3, 3)))
            for k in range(1, n + 1):
                m = rot == k
                if m.sum() < 3:
                    continue
                lin.append({"hora": f"{h[:2]}:{h[2:4]}", "ele": sz["ele_deg"], "x": round(float(x[m].mean()), 1), "y": round(float(y[m].mean()), 1), "r": round(float(r[m].mean()), 1), "n": int(m.sum()),
                            "Zmax": float(np.nanmax(Z[m])), "CCmed": round(float(np.nanmedian(C[m])), 2), "fCC80": round(float(np.nanmean(C[m] < .8)), 2), "ZDRmed": round(float(np.nanmedian(D[m])), 2),
                            "KDPmed": round(float(np.nanmedian(K[m])), 2), "Wmed": round(float(np.nanmedian(W[m])), 1)})
        for v in ("dBZ", "RhoHV", "ZDR", "KDP", "W", "V"):
            ar._cache.pop((h, v), None)
    with open(FIG / "rotacao_controle_z60.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lin[0]))
        w.writeheader()
        w.writerows(lin)
    print(f"    total {len(lin)}; por faixa de alcance: CCmed mediana, fCC80 mediana, ZDR mediana, KDP mediana")
    for r0, r1 in ((20, 60), (60, 90), (90, 120)):
        q = [l for l in lin if r0 <= l["r"] < r1]
        if q:
            print(f"    {r0}-{r1} km: n={len(q)} CC={np.median([l['CCmed'] for l in q]):.2f} fCC<.8={np.median([l['fCC80'] for l in q]):.2f} ZDR={np.median([l['ZDRmed'] for l in q]):.2f} KDP={np.median([l['KDPmed'] for l in q]):.2f} W={np.median([l['Wmed'] for l in q]):.1f}")
    baixos = sorted([l for l in lin if l["CCmed"] < .85], key=lambda l: l["r"])
    print(f"    com CC mediano < 0,85: {len(baixos)}")
    for l in baixos[:40]:
        print("     ", *l.values(), sep="\t")


if __name__ == "__main__":
    teste_a()
    teste_b()
    teste_c()
    teste_d()
