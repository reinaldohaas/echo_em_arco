# -*- coding: utf-8 -*-
r"""Rastreia núcleos de CC baixo dentro de Z alto e mede a velocidade ao redor deles.

Núcleo: gates contíguos com Z >= 45 dBZ e RhoHV < 0,85, com ao menos MIN_GATES gates e a mais de 5 km do radar.
Em cada núcleo: Z, CC, ZDR, KDP, W e o par (Vmax, Vmin) da V corrigida, suavizada por mediana 3x3, em raio de 2 km.
Controle: a mesma medida em pontos da mesma fronteira de vento, a 5–15 km do núcleo.
O sentido é horário (ciclônico no HS) quando V diminui com o aumento do azimute.
"""
import csv
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import label

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from analise_velocidade import AX, AY, carregar, cortar, dealias, nome, nyquist, xy  # noqa: E402

FIG = AQUI / "figuras"
HORAS = ["130605", "131205", "131804", "132404", "133004", "133604", "134204", "134804", "135404"]
ELEVS = list(range(8))
MIN_GATES = 5
R_PAR = 2.0


def mediana3(V):
    p = np.pad(V, ((1, 1), (1, 1)), mode="wrap")
    # exige ao menos 5 de 9 valores válidos para não fabricar vento em lacunas
    jan = sliding_window_view(p, (3, 3))
    n = np.isfinite(jan).sum(axis=(2, 3))
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = np.nanmedian(jan, axis=(2, 3))
    m[n < 5] = np.nan
    return m


def par_em(Vs, x, y, azs, cx, cy, raio=R_PAR):
    m = (np.hypot(x - cx, y - cy) <= raio) & np.isfinite(Vs)
    if m.sum() < 8:
        return None
    ii, jj = np.nonzero(m)
    v = Vs[ii, jj]
    a, b = int(np.argmin(v)), int(np.argmax(v))
    xa, ya, xb, yb = x[ii[a], jj[a]], y[ii[a], jj[a]], x[ii[b], jj[b]], y[ii[b], jj[b]]
    dist = float(np.hypot(xb - xa, yb - ya))
    dif_az = (azs[ii[b]] - azs[ii[a]] + 180) % 360 - 180
    r_med = float(np.hypot((xa + xb) / 2, (ya + yb) / 2))
    sep_az = abs(np.radians(dif_az)) * r_med
    return {"vmin": float(v[a]), "vmax": float(v[b]), "dv": float(v[b] - v[a]), "dist": dist,
            "frac_azimutal": float(sep_az / max(dist, .01)),
            "sentido": "horário" if dif_az < 0 else "anti-horário"}


def controle(Vs, x, y, azs, cx, cy):
    d = np.hypot(x - cx, y - cy)
    cand = (d >= 5) & (d <= 15) & (np.abs(Vs) < 6)
    ii, jj = np.nonzero(cand)
    if not len(ii):
        return []
    saida = []
    for i, j in list(zip(ii, jj))[::max(1, len(ii) // 120)]:
        p = par_em(Vs, x, y, azs, x[i, j], y[i, j])
        if p and p["vmin"] < -5 and p["vmax"] > 5:
            saida.append(p["dv"])
    return saida


def main():
    linhas = []
    guardar = {}
    for h in HORAS:
        for idx in ELEVS:
            c = carregar(h, idx)
            vn = nyquist(nome(h, "V"), idx)
            V = cortar(c["V"])
            Vd, _, _ = dealias(V, vn)
            Vs = mediana3(Vd)
            x, y, r = xy(c["V"], V.shape[1])
            azs = c["V"]["azimuths"]
            Z, CC, ZDR, KDP, W = [cortar(c[k]) for k in ("dBZ", "RhoHV", "ZDR", "KDP", "W")]
            mas = (Z >= 45) & (CC < .85) & (r > 5)
            rot, n = label(mas, structure=np.ones((3, 3)))
            if h == "133004":
                guardar[idx] = dict(Z=Z, CC=CC, ZDR=ZDR, Vd=Vd, Vr=V, x=x, y=y, ele=c["V"]["ele_deg"])
            for k in range(1, n + 1):
                m = rot == k
                if m.sum() < MIN_GATES:
                    continue
                cx, cy = float(x[m].mean()), float(y[m].mean())
                p = par_em(Vs, x, y, azs, cx, cy)
                ctl = controle(Vs, x, y, azs, cx, cy) if p else []
                rc = float(np.hypot(cx, cy))
                ele = c["V"]["ele_deg"]
                ganho = 0.25 * np.radians(np.median(np.diff(azs)))
                area = float(np.sum(r[m] * ganho))
                linhas.append({
                    "hora": f"{h[:2]}:{h[2:4]}", "ele": ele, "x_km": round(cx, 1), "y_km": round(cy, 1), "km_aero": round(float(np.hypot(cx - AX, cy - AY)), 1),
                    "alt_rad_km": round(float(rc * np.sin(np.radians(ele)) + rc ** 2 / (2 * 8495)), 2),
                    "gates": int(m.sum()), "area_km2": round(area, 2), "Zmax": float(np.nanmax(Z[m])), "CCmin": round(float(np.nanmin(CC[m])), 2),
                    "CCmed": round(float(np.nanmedian(CC[m])), 2), "ZDRmed": round(float(np.nanmedian(ZDR[m])), 2), "KDPmed": round(float(np.nanmedian(KDP[m])), 2),
                    "Wmed": round(float(np.nanmedian(W[m])), 1), "fracsemV": round(float(np.mean(~np.isfinite(V[m]))), 2),
                    "Vmin": round(p["vmin"], 1) if p else "", "Vmax": round(p["vmax"], 1) if p else "", "dV": round(p["dv"], 1) if p else "",
                    "dist_par": round(p["dist"], 2) if p else "", "frac_az": round(p["frac_azimutal"], 2) if p else "", "sentido": p["sentido"] if p else "",
                    "ctl_med": round(float(np.median(ctl)), 1) if ctl else "", "ctl_p90": round(float(np.percentile(ctl, 90)), 1) if ctl else "", "ctl_n": len(ctl)})
    with open(FIG / "nucleos_cc_baixo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    cab = list(linhas[0])
    print(*cab, sep="\t")
    for l in sorted(linhas, key=lambda q: (q["hora"], q["ele"], -q["gates"])):
        if l["gates"] >= 8 or l["km_aero"] < 4:
            print(*l.values(), sep="\t")

    fig, eixos = plt.subplots(4, 6, figsize=(21, 13.4), constrained_layout=True)
    for col, idx in enumerate(range(6)):
        g = guardar[idx]
        for lin, (tit, dado, cm, a, b) in enumerate([("Z (dBZ)", g["Z"], "turbo", 20, 70), ("V corrigida (m/s)", g["Vd"], "RdBu_r", -50, 50),
                                                       ("RhoHV", g["CC"], "viridis", .5, 1), ("ZDR (dB)", g["ZDR"], "coolwarm", -2, 4)]):
            ax = eixos[lin, col]
            pc = ax.pcolormesh(g["x"], g["y"], np.ma.masked_invalid(dado)[:-1, :-1], cmap=cm, vmin=a, vmax=b, shading="flat")
            ax.plot(AX, AY, "*", color="yellow", mec="black", ms=13)
            ax.set_xlim(AX - 4, AX + 4)
            ax.set_ylim(AY - 4, AY + 4)
            ax.set_aspect("equal")
            ax.tick_params(labelsize=7)
            ax.set_title(f"{g['ele']}°: {tit}", fontsize=10, fontweight="bold")
            if col == 5:
                fig.colorbar(pc, ax=ax, shrink=.85)
    fig.suptitle("13:30 UTC: ±4 km do Aeroporto de Chapecó (★), coordenadas em km a partir do radar", fontweight="bold", fontsize=14)
    fig.savefig(FIG / "aeroporto_1330_elevacoes.png", dpi=110)


if __name__ == "__main__":
    main()
