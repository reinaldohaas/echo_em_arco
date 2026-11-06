# -*- coding: utf-8 -*-
r"""Composição GOES-19 (canal 13) + Echo Top do radar de Chapecó, 04/11/2026, 12–15 UTC.

Echo Top: altitude do centro do feixe mais alto com Z >= limiar em cada coluna, em grade de 0,01°, somada à altitude
do radar (822 m) e com Terra 4/3. Gates isolados são descartados: a coluna precisa de vizinhos com o mesmo limiar.
Limiares: 18 dBZ (topo do eco) e 40 dBZ (topo do núcleo convectivo).

Limitações:
- Perto do radar, a elevação máxima (19,5°) trunca o topo: a altura máxima alcançável é mostrada em `alcance_km`.
- Longe do radar, os feixes altos terminam em 130–187 km, e os baixos ficam altos e largos: o topo perde resolução.
- Sem interpolação entre elevações nem correção de paralaxe do satélite.
Saídas em satelite/figuras: echotop_1330.png, echotop_painel.png, echotop/e_NN.png, echotop_estatisticas.csv.
"""
import csv
import datetime as dt
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import uniform_filter

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path[:0] = [str(AQUI), str(RAIZ / "radar")]
from leitor_vol_chapeco import ler_volume_rainbow  # noqa: E402
import plotar_goes19 as g  # noqa: E402
from compor_radar_satelite import ALCANCE_KM, JAN, RADAR, VOL, grade  # noqa: E402

FIG = AQUI / "figuras"
ALT_RADAR = .822
RE = 8495.0
LIMIARES = (18, 40)
ZONA_TRUNC = 40  # km: dentro deste alcance, a 19,5° o feixe não passa de ~15 km de altitude


def alt_msl(r_inclinado, ele):
    return ALT_RADAR + r_inclinado * np.sin(np.radians(ele)) + r_inclinado ** 2 / (2 * RE)


def echo_top(arq, dist, az):
    vol = ler_volume_rainbow(arq)
    topos = {t: np.full(dist.shape, np.nan, dtype="f4") for t in LIMIARES}
    alcance = np.full(dist.shape, np.nan, dtype="f4")
    for s in sorted(vol["slices"], key=lambda q: q["ele_deg"]):
        ele = s["ele_deg"]
        r = dist / math.cos(math.radians(ele))
        ib = np.floor(r / s["rstep_km"]).astype(int)
        azs = s["azimuths"]
        ir = np.searchsorted(azs, az) % len(azs)
        ant = (ir - 1) % len(azs)
        dif_d = np.abs((azs[ir] - az + 180) % 360 - 180)
        dif_a = np.abs((azs[ant] - az + 180) % 360 - 180)
        ir = np.where(dif_a < dif_d, ant, ir)
        ok = ib < s["data"].shape[1]
        Z = np.full(dist.shape, np.nan, dtype="f4")
        Z[ok] = s["data"][ir[ok], ib[ok]]
        h = alt_msl(r, ele)
        alcance = np.where(ok, h, alcance)
        for t in LIMIARES:
            m = np.nan_to_num(Z) >= t
            # exige ao menos 3 de 9 vizinhos, para não tomar ruído como topo
            suporte = uniform_filter(m.astype("f4"), size=3) >= 3 / 9
            topos[t] = np.where(m & suporte, h, topos[t])
    for t in LIMIARES:
        topos[t][dist > ALCANCE_KM] = np.nan
    return topos, alcance


def t_radar(arq):
    return dt.datetime.strptime(arq.name[:14], "%Y%m%d%H%M%S")


def desenhar(ax, lons, lats, et, glo, gla, tb=None, legenda=False):
    if tb is not None:
        ax.imshow(tb, extent=(glo[0], glo[-1], gla[0], gla[-1]), origin="lower", cmap="Greys", vmin=-90, vmax=-30, interpolation="nearest", zorder=1)
    im = ax.imshow(np.ma.masked_invalid(et), extent=(lons[0], lons[-1], lats[0], lats[-1]), origin="lower", cmap="turbo", vmin=2, vmax=18,
                   interpolation="nearest", zorder=2, alpha=.85 if tb is not None else 1)
    g.contornos(ax)
    th = np.linspace(0, 2 * np.pi, 361)
    kx = 111.32 * math.cos(math.radians(RADAR[1]))
    for raio, ls, cor in ((ALCANCE_KM, "--", "black"), (ZONA_TRUNC, ":", "black")):
        ax.plot(RADAR[0] + raio * np.sin(th) / kx, RADAR[1] + raio * np.cos(th) / 111.132, color=cor, lw=.8, ls=ls, zorder=4)
    ax.plot(*g.AERO, "^", color="white", mec="black", ms=8, zorder=6)
    if legenda:
        ax.annotate("Chapecó", g.AERO, xytext=(7, 5), textcoords="offset points", fontsize=10, fontweight="bold", color="white",
                    bbox=dict(boxstyle="round,pad=.2", fc="#be123c", ec="none"), zorder=7)
    ax.set_xlim(JAN[:2])
    ax.set_ylim(JAN[2:])
    ax.set_aspect(1 / math.cos(math.radians(27)))
    ax.tick_params(labelsize=7)
    return im


def main():
    lons, lats, dist, az = grade()
    goes = []
    for a in sorted(g.DADOS.glob("OR_ABI-L2-CMIPF-M6C13_*.nc")):
        glo, gla, tb = g.ler(a)
        goes.append((g.horario(a.name), tb))
    (FIG / "echotop").mkdir(parents=True, exist_ok=True)
    mlon, mlat = np.meshgrid(lons, lats)
    perto = np.hypot((mlon - g.AERO[0]) * 99, (mlat - g.AERO[1]) * 111) <= 25
    faixa = (dist >= ZONA_TRUNC) & (dist <= 130)
    pares = []
    with open(FIG / "echotop_estatisticas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        cab = ["radar_utc", "goes_inicio_utc", "ET18_max_40a130km", "ET18_p99_40a130km", "ET40_max_40a130km", "ET40_p99_40a130km", "ET18_max_25km_aero", "ET40_max_25km_aero", "alcance_max_aero_km"]
        w.writerow(cab)
        print(*cab, sep="\t")
        ia = np.unravel_index(np.argmin(np.hypot((mlon - g.AERO[0]) * 99, (mlat - g.AERO[1]) * 111)), dist.shape)
        for n, arq in enumerate(sorted(VOL.glob("*dBZ.vol"))):
            tr = t_radar(arq)
            tg, tbp = min(goes, key=lambda c: abs(c[0] + dt.timedelta(minutes=6) - tr - dt.timedelta(minutes=3)))
            tp, alc = echo_top(arq, dist, az)
            e18, e40 = tp[18], tp[40]
            lin = [f"{tr:%H:%M:%S}", f"{tg:%H:%M}", round(float(np.nanmax(e18[faixa])), 1), round(float(np.nanpercentile(e18[faixa], 99)), 1),
                   round(float(np.nanmax(e40[faixa])), 1), round(float(np.nanpercentile(e40[faixa], 99)), 1),
                   round(float(np.nanmax(e18[perto])), 1), round(float(np.nanmax(e40[perto])), 1), round(float(alc[ia]), 1)]
            w.writerow(lin)
            print(*lin, sep="\t", flush=True)
            pares.append((tr, tg, tbp, e18, e40))
            fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=150, constrained_layout=True)
            im = desenhar(ax, lons, lats, e18, glo, gla, tbp, legenda=True)
            ax.set_title(f"Echo Top 18 dBZ, Chapecó, {tr:%H:%M} UTC ({tr - dt.timedelta(hours=3):%H:%M} BRT), sobre GOES-19 canal 13 ({tg:%H:%M} UTC)", fontsize=12, fontweight="bold")
            fig.colorbar(im, ax=ax, shrink=.85, label="Altitude do topo (km)")
            fig.savefig(FIG / "echotop" / f"e_{n:02d}.png")
            plt.close(fig)

    alvo = dt.datetime(2026, 11, 4, 13, 30)
    tr, tg, tbp, e18, e40 = min(pares, key=lambda p: abs(p[0] - alvo))
    fig, eixos = plt.subplots(1, 3, figsize=(18, 6.6), constrained_layout=True)
    desenhar(eixos[0], lons, lats, e18, glo, gla, legenda=True)
    eixos[0].set_title(f"Echo Top 18 dBZ, {tr:%H:%M} UTC", fontweight="bold")
    im = desenhar(eixos[1], lons, lats, e40, glo, gla)
    eixos[1].set_title(f"Echo Top 40 dBZ, {tr:%H:%M} UTC", fontweight="bold")
    desenhar(eixos[2], lons, lats, e18, glo, gla, tbp)
    eixos[2].set_title(f"18 dBZ sobre GOES-19 ({tg:%H:%M} UTC)", fontweight="bold")
    fig.colorbar(im, ax=eixos, shrink=.8, label="Altitude do topo (km)")
    fig.suptitle("Pontilhado: até 40 km do radar, o topo pode estar truncado pela elevação máxima de 19,5°", fontweight="bold")
    fig.savefig(FIG / "echotop_1330.png", dpi=140)
    plt.close(fig)

    sel = [min(pares, key=lambda p: abs(p[0] - dt.datetime(2026, 11, 4, h, m))) for h, m in [(12, 30), (13, 0), (13, 18), (13, 30), (13, 54), (14, 30)]]
    fig, eixos = plt.subplots(2, 3, figsize=(17, 10), constrained_layout=True)
    for ax, (tr, tg, tbp, e18, e40) in zip(eixos.flat, sel):
        im = desenhar(ax, lons, lats, e40, glo, gla, tbp)
        ax.set_title(f"Topo de 40 dBZ: radar {tr:%H:%M} / GOES {tg:%H:%M} UTC ({tr - dt.timedelta(hours=3):%H:%M} BRT)", fontweight="bold", fontsize=11)
    fig.colorbar(im, ax=eixos, shrink=.8, label="Altitude do topo de 40 dBZ (km)")
    fig.savefig(FIG / "echotop_painel.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
