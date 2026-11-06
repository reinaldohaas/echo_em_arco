# -*- coding: utf-8 -*-
r"""Textura do canal visível (recortes npz) e sua posição em relação à trilha do núcleo do radar.

Textura: desvio-padrão da refletância após remover a média em 15 km, em janela de 5 km. Topos borbulhantes de overshoot
têm textura alta; bigorna lisa, baixa. Horário: a varredura passa em -27° cerca de 6 min após o início do disco.
Trilha: X0, Y0 em 13:30:06 e 40,4 m/s, de analise_rotacao_checagens.py.
Saídas: figuras/visivel_textura_saida.txt e assets/radar_v2/visivel_1330.png.
"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import label, uniform_filter

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import plotar_goes19 as g  # noqa: E402
from teste_overshoot import paralaxe  # noqa: E402

DEST = AQUI / "dados_goes19_vis"
RADAR = (-52.60374, -27.04879)
COS = math.cos(math.radians(RADAR[1]))
UX, UY, X0, Y0 = .0404 * .9987, -.0404 * .05, -4.9, -9.2
LAG_S = 360
FUNDO, TEXTO = "#0b1220", "#f1f5f9"


def nucleo(hhmm):
    seg = (int(hhmm[:2]) * 3600 + int(hhmm[2:]) * 60 + LAG_S) - (13 * 3600 + 30 * 60 + 6)
    x, y = X0 + UX * seg, Y0 + UY * seg
    return RADAR[0] + x / (111.32 * COS), RADAR[1] + y / 111.132


def main():
    dlon, dlat = paralaxe(*g.AERO)
    saida = open(AQUI / "figuras" / "visivel_textura_saida.txt", "w", encoding="utf-8")

    def pr(*a):
        print(*a, sep="\t", flush=True)
        print(*a, sep="\t", file=saida, flush=True)

    pr("início_UTC", "núcleo_lon", "núcleo_lat", "aglomerado", "lon", "lat", "área_km2", "km_ao_núcleo", "textura_máx", "p99_recorte")
    for alvo in ("1320", "1330", "1340"):
        q = np.load(DEST / f"recorte_{alvo}.npz")
        lons, lats, v = q["lons"] + dlon, q["lats"] + dlat, np.nan_to_num(q["v"], nan=float(np.nanmedian(q["v"])))
        dx = (lons[1] - lons[0]) * 111.2 * COS
        dy = (lats[1] - lats[0]) * 111.2
        hp = v - uniform_filter(v, size=(int(15 / dy), int(15 / dx)))
        n = (int(5 / dy), int(5 / dx))
        tex = np.sqrt(np.maximum(uniform_filter(hp ** 2, size=n) - uniform_filter(hp, size=n) ** 2, 0))
        lim = np.percentile(tex, 97)
        rot, k = label(tex >= lim)
        nx, ny = nucleo(alvo)
        ml, mla = np.meshgrid(lons, lats)
        grupos = []
        for r in range(1, k + 1):
            m = rot == r
            area = m.sum() * dx * dy
            if area < 30:
                continue
            cx, cy = float(ml[m].mean()), float(mla[m].mean())
            grupos.append((math.hypot((cx - nx) * 111.2 * COS, (cy - ny) * 111.2), cx, cy, area, float(tex[m].max())))
        for i, (dist, cx, cy, area, tm) in enumerate(sorted(grupos)):
            pr(alvo, round(nx, 3), round(ny, 3), i + 1, round(cx, 3), round(cy, 3), round(area), round(dist, 1), round(tm, 3), round(float(np.percentile(tex, 99)), 3))

    q = np.load(DEST / "recorte_1330.npz")
    lons, lats, v = q["lons"] + dlon, q["lats"] + dlat, q["v"]
    plt.rcParams.update({"figure.facecolor": FUNDO, "text.color": TEXTO, "axes.labelcolor": TEXTO, "xtick.color": TEXTO, "ytick.color": TEXTO, "font.size": 14})
    fig, ax = plt.subplots(figsize=(11.8, 6.64), dpi=100, constrained_layout=True)
    ax.imshow(v, extent=(lons[0], lons[-1], lats[0], lats[-1]), origin="lower", cmap="gray", vmin=np.nanpercentile(v, 2), vmax=np.nanpercentile(v, 99.8), interpolation="bilinear")
    g.contornos(ax)
    ax.plot(*g.AERO, "^", color="#ef4444", mec="white", ms=15, zorder=8)
    ax.annotate("Aeroporto", g.AERO, xytext=(-12, -26), textcoords="offset points", ha="right", fontsize=15, fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=.2", fc="#be123c", ec="none"), zorder=9)
    nx, ny = nucleo("1330")
    ax.plot(nx, ny, "o", mfc="none", mec="#22d3ee", ms=30, mew=3, zorder=8)
    ax.annotate("núcleo do radar", (nx, ny), xytext=(24, 16), textcoords="offset points", fontsize=15, fontweight="bold", color="#22d3ee",
                bbox=dict(boxstyle="round,pad=.2", fc="black", ec="none", alpha=.75), zorder=9)
    ax.set_xlim(g.AERO[0] - .55, g.AERO[0] + .75)
    ax.set_ylim(g.AERO[1] - .36, g.AERO[1] + .37)
    ax.set_aspect(1 / COS)
    ax.set_title("GOES-19, visível de 0,5 km, início 13:30 UTC; paralaxe corrigida para 14 km", fontweight="bold", fontsize=17)
    fig.savefig(pathlib.Path(AQUI.parent, "assets", "radar_v2", "visivel_1330.png"))


if __name__ == "__main__":
    main()
