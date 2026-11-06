# -*- coding: utf-8 -*-
r"""Composição GOES-19 (canal 13) + echomax do radar de Chapecó, 04/11/2026, 12–15 UTC.

Echomax: máximo de dBZ na coluna, entre as 14 elevações de cada volume .vol, em grade de 0,01°.
Gera em satelite/figuras:
  composicao_1330.png      satélite, echomax e composição no volume de 13:30 UTC
  composicao_painel.png    composição em 6 horários
  composicao/c_NN.png      quadros da animação
  composicao_pareamento.csv  pares radar/satélite e estatísticas do echomax
Limitações: sem correção de paralaxe; perto do radar a elevação máxima (19,5°) limita a altura amostrada.
"""
import csv
import datetime as dt
import math
import pathlib
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path[:0] = [str(AQUI), str(RAIZ / "radar")]
from leitor_vol_chapeco import ler_volume_rainbow  # noqa: E402
import plotar_goes19 as g  # noqa: E402

VOL = RAIZ / "radar" / "dados_chp_vol"
FIG = AQUI / "figuras"
JAN = (-55.1, -50.1, -29.25, -25.0)
RADAR = (-52.60374, -27.04879)
ALCANCE_KM = 240
NIVEIS = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70]
CORES = ["#0ea5e9", "#22c55e", "#16a34a", "#15803d", "#fde047", "#f59e0b", "#f97316", "#ef4444", "#b91c1c", "#d946ef", "#ffffff"]
CMAP_Z = ListedColormap(CORES)
NORM_Z = BoundaryNorm(NIVEIS, CMAP_Z.N)


def grade():
    lons = np.arange(JAN[0], JAN[1] + 1e-6, .01)
    lats = np.arange(JAN[2], JAN[3] + 1e-6, .01)
    mlon, mlat = np.meshgrid(lons, lats)
    dx = (mlon - RADAR[0]) * 111.32 * math.cos(math.radians(RADAR[1]))
    dy = (mlat - RADAR[1]) * 111.132
    return lons, lats, np.hypot(dx, dy), np.degrees(np.arctan2(dx, dy)) % 360


def echomax(arq, dist, az):
    vol = ler_volume_rainbow(arq)
    saida = np.full(dist.shape, np.nan, dtype="f4")
    for s in vol["slices"]:
        r = dist / math.cos(math.radians(s["ele_deg"]))
        ib = np.floor(r / s["rstep_km"]).astype(int)
        azs = s["azimuths"]
        ir = np.searchsorted(azs, az) % len(azs)
        ant = (ir - 1) % len(azs)
        dif_d = np.abs((azs[ir] - az + 180) % 360 - 180)
        dif_a = np.abs((azs[ant] - az + 180) % 360 - 180)
        ir = np.where(dif_a < dif_d, ant, ir)
        ok = ib < s["data"].shape[1]
        val = np.full(dist.shape, np.nan, dtype="f4")
        val[ok] = s["data"][ir[ok], ib[ok]]
        saida = np.fmax(saida, val)
    saida[dist > ALCANCE_KM] = np.nan
    return saida


def t_radar(arq):
    return dt.datetime.strptime(arq.name[:14], "%Y%m%d%H%M%S")


def mapa(ax, lons, lats, tb=None, z=None, cinza=True, legendas=False):
    im_z = None
    if tb is not None:
        ext = (g_lons[0], g_lons[-1], g_lats[0], g_lats[-1])
        if cinza:
            ax.imshow(tb, extent=ext, origin="lower", cmap="Greys", vmin=-90, vmax=-30, interpolation="nearest", zorder=1)
        else:
            ax.imshow(tb, extent=ext, origin="lower", cmap=g.ESCALA, vmin=-90, vmax=-30, interpolation="nearest", zorder=1)
    if z is not None:
        im_z = ax.imshow(np.ma.masked_less(z, 20 if tb is not None else 15), extent=(lons[0], lons[-1], lats[0], lats[-1]),
                         origin="lower", cmap=CMAP_Z, norm=NORM_Z, interpolation="nearest", zorder=2,
                         alpha=.82 if tb is not None else 1)
    if tb is not None and z is not None:
        ax.contour(g_lons, g_lats, tb, levels=[-80], colors="#22d3ee", linewidths=.9, zorder=3)
    g.contornos(ax)
    th = np.linspace(0, 2 * np.pi, 361)
    ax.plot(RADAR[0] + ALCANCE_KM * np.sin(th) / (111.32 * math.cos(math.radians(RADAR[1]))),
            RADAR[1] + ALCANCE_KM * np.cos(th) / 111.132, color="black", lw=.7, ls="--", zorder=4)
    ax.plot(*g.AERO, "^", color="white", mec="black", ms=8, zorder=6)
    if legendas:
        ax.annotate("Chapecó", g.AERO, xytext=(7, 5), textcoords="offset points", fontsize=10, fontweight="bold", color="white",
                    bbox=dict(boxstyle="round,pad=.2", fc="#be123c", ec="none"), zorder=7)
    ax.set_xlim(JAN[:2])
    ax.set_ylim(JAN[2:])
    ax.set_aspect(1 / math.cos(math.radians(27)))
    ax.tick_params(labelsize=7)
    return im_z


def main():
    global g_lons, g_lats
    lons, lats, dist, az = grade()
    goes = []
    for a in sorted(g.DADOS.glob("OR_ABI-L2-CMIPF-M6C13_*.nc")):
        g_lons, g_lats, tb = g.ler(a)
        goes.append((g.horario(a.name), tb))
    pares = []
    (FIG / "composicao").mkdir(parents=True, exist_ok=True)
    arqs = sorted(VOL.glob("*dBZ.vol"))
    with open(FIG / "composicao_pareamento.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["radar_utc", "goes_inicio_utc", "area_ge45dBZ_km2", "Zmax_dBZ", "Zmax_aeroporto_5km"])
        ix = np.hypot((np.meshgrid(lons, lats)[0] - g.AERO[0]) * 99, (np.meshgrid(lons, lats)[1] - g.AERO[1]) * 111) <= 5
        for n, arq in enumerate(arqs):
            tr = t_radar(arq)
            # a −27° a varredura do disco passa cerca de 6 min após o início; o volume dura 6 min
            tg, tb = min(goes, key=lambda c: abs(c[0] + dt.timedelta(minutes=6) - tr - dt.timedelta(minutes=3)))
            z = echomax(arq, dist, az)
            area = float(np.nansum(z >= 45) * (.01 * 99) * (.01 * 111))
            w.writerow([f"{tr:%H:%M:%S}", f"{tg:%H:%M}", round(area), round(float(np.nanmax(z)), 1), round(float(np.nanmax(z[ix])), 1)])
            pares.append((tr, tg, tb, z))
            fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=150, constrained_layout=True)
            im = mapa(ax, lons, lats, tb, z, legendas=True)
            brt = tr - dt.timedelta(hours=3)
            ax.set_title(f"Echomax Chapecó {tr:%H:%M} UTC ({brt:%H:%M} BRT) sobre GOES-19 canal 13 ({tg:%H:%M} UTC)  |  ciano: topo −80 °C",
                         fontsize=12, fontweight="bold")
            fig.colorbar(im, ax=ax, shrink=.85, label="Refletividade máxima na coluna (dBZ)", ticks=NIVEIS)
            fig.savefig(FIG / "composicao" / f"c_{n:02d}.png")
            plt.close(fig)
            print(f"{tr:%H:%M}", flush=True)

    alvo = dt.datetime(2026, 11, 4, 13, 30)
    tr, tg, tb, z = min(pares, key=lambda p: abs(p[0] - alvo))
    fig, eixos = plt.subplots(1, 3, figsize=(18, 6.6), constrained_layout=True)
    mapa(eixos[0], lons, lats, tb=tb, cinza=False)
    eixos[0].set_title(f"GOES-19 canal 13, {tg:%H:%M} UTC", fontweight="bold")
    im = mapa(eixos[1], lons, lats, z=z, legendas=True)
    eixos[1].set_title(f"Echomax, radar de Chapecó, {tr:%H:%M} UTC", fontweight="bold")
    mapa(eixos[2], lons, lats, tb, z)
    eixos[2].set_title("Composição (ciano: topo −80 °C)", fontweight="bold")
    fig.colorbar(im, ax=eixos, shrink=.8, label="dBZ", ticks=NIVEIS)
    fig.savefig(FIG / "composicao_1330.png", dpi=140)
    plt.close(fig)

    sel = [min(pares, key=lambda p: abs(p[0] - dt.datetime(2026, 11, 4, h, m))) for h, m in
           [(12, 30), (13, 0), (13, 18), (13, 30), (13, 54), (14, 30)]]
    fig, eixos = plt.subplots(2, 3, figsize=(17, 10), constrained_layout=True)
    for ax, (tr, tg, tb, z) in zip(eixos.flat, sel):
        im = mapa(ax, lons, lats, tb, z)
        ax.set_title(f"Radar {tr:%H:%M} / GOES {tg:%H:%M} UTC ({tr - dt.timedelta(hours=3):%H:%M} BRT)", fontweight="bold", fontsize=11)
    fig.colorbar(im, ax=eixos, shrink=.8, label="Refletividade máxima na coluna (dBZ)", ticks=NIVEIS)
    fig.savefig(FIG / "composicao_painel.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
