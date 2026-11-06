# -*- coding: utf-8 -*-
r"""Há overshoot sobre Chapecó? GOES-19 canal 13, 04/11/2026, 12–15 UTC.

Critério no estilo de Bedka et al. (2010): pixel com T <= -58 °C, mínimo local, ao menos 6,5 K mais frio que a média da
bigorna em um anel de 8 a 16 km (apenas pixels de bigorna, T <= -48 °C). Sem perfil de tropopausa, o critério é só o
contraste; ao menos 2/3 do anel precisam ser bigorna. Resolução nominal de 2 km: overshoots pequenos ficam suavizados.

Paralaxe: a posição aparente é deslocada para longe do ponto subsatélite. Corrigida aqui para topo em 14 km.
Saídas: satelite/figuras/overshoot.csv, overshoot_serie.csv, overshoot_saida.txt e overshoot_1330.png.
"""
import csv
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import convolve, minimum_filter

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import plotar_goes19 as g  # noqa: E402

FIG = AQUI / "figuras"
LON_SAT = -75.2
H_TOPO = 14.0
DT = 6.5
KM_LAT, R_T, H_SAT = 111.2, 6378.0, 35786.0


def paralaxe(lon, lat, h=H_TOPO):
    """Devolve (dlon, dlat): somar à posição aparente para obter a posição real."""
    def vetor(lo, la, raio):
        lo, la = math.radians(lo), math.radians(la)
        return np.array([raio * math.cos(la) * math.cos(lo), raio * math.cos(la) * math.sin(lo), raio * math.sin(la)])
    sat = vetor(LON_SAT, 0, R_T + H_SAT)
    p = vetor(lon, lat, R_T)
    # ponto no nível H_TOPO sobre a mesma linha de visada do pixel de superfície
    d = (p - sat)
    a, b, c = d @ d, 2 * sat @ d, sat @ sat - (R_T + h) ** 2
    k = (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)
    q = sat + k * d
    la2 = math.degrees(math.asin(q[2] / np.linalg.norm(q)))
    lo2 = math.degrees(math.atan2(q[1], q[0]))
    return lo2 - lon, la2 - lat


def anel(dx, dy, r0=8, r1=16):
    nx, ny = int(r1 / dx) + 1, int(r1 / dy) + 1
    yy, xx = np.mgrid[-ny:ny + 1, -nx:nx + 1]
    d = np.hypot(xx * dx, yy * dy)
    return ((d >= r0) & (d <= r1)).astype("f4")


def main():
    arqs = sorted(g.DADOS.glob("OR_ABI-L2-CMIPF-M6C13_*.nc"))
    dlon, dlat = paralaxe(*g.AERO)
    print(f"paralaxe para 14 km em Chapecó: real = aparente + ({dlon:+.3f}°, {dlat:+.3f}°) = {dlon * 99:+.1f} km E, {dlat * 111:+.1f} km N")
    linhas, serie, campos = [], [], {}
    for arq in arqs:
        lons, lats, tc = g.ler(arq)
        t = g.horario(arq.name)
        dx = (lons[1] - lons[0]) * KM_LAT * math.cos(math.radians(27))
        dy = (lats[1] - lats[0]) * KM_LAT
        A = anel(dx, dy)
        bigorna = (tc <= -48).astype("f4")
        soma = convolve(np.where(tc <= -48, tc, 0).astype("f4"), A, mode="constant")
        n = convolve(bigorna, A, mode="constant")
        media = np.where(n >= .67 * A.sum(), soma / np.maximum(n, 1), np.nan)
        contraste = media - tc
        minimos = tc == minimum_filter(tc, size=int(8 / dx) | 1)
        ot = minimos & (tc <= -58) & (contraste >= DT)
        ml, mla = np.meshgrid(lons + dlon, lats + dlat)  # posição corrigida
        dist = np.hypot((ml - g.AERO[0]) * KM_LAT * math.cos(math.radians(27)), (mla - g.AERO[1]) * KM_LAT)
        for j, i in zip(*np.nonzero(ot)):
            linhas.append([t.strftime("%H:%M"), round(float(ml[j, i]), 3), round(float(mla[j, i]), 3), round(float(tc[j, i]), 1),
                           round(float(contraste[j, i]), 1), round(float(dist[j, i]), 1)])
        perto = dist <= 40
        cand = np.where(minimos & perto & np.isfinite(contraste), contraste, np.nan)
        k = np.unravel_index(np.nanargmax(cand), cand.shape)
        serie.append([t.strftime("%H:%M"), round(float(np.nanmin(tc[perto])), 1), round(float(tc[k]), 1), round(float(cand[k]), 1),
                      round(float(dist[k]), 1), int(ot[perto].sum()), int(ot[dist <= 100].sum()), int(ot.sum())])
        campos[t.strftime("%H:%M")] = (lons, lats, tc, ml, mla, ot)
    with open(FIG / "overshoot.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["inicio_utc", "lon_corr", "lat_corr", "T_C", "contraste_K", "km_aeroporto"])
        w.writerows(linhas)
    cab = ["inicio_utc", "Tmin_40km_C", "T_do_maior_contraste", "maior_contraste_K", "km_aeroporto", "OT_40km", "OT_100km", "OT_janela"]
    with open(FIG / "overshoot_serie.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cab)
        w.writerows(serie)
    with open(FIG / "overshoot_saida.txt", "w", encoding="utf-8") as f:
        for l in [cab] + serie:
            print(*l, sep="\t")
            print(*l, sep="\t", file=f)
        print("OT até 60 km:", file=f)
        print("OT até 60 km:")
        for l in linhas:
            if l[5] <= 60:
                print(*l, sep="\t", file=f)
                print(*l, sep="\t")

    fig, eixos = plt.subplots(1, 3, figsize=(18, 6.6), constrained_layout=True)
    for ax, h in zip(eixos, ("13:20", "13:30", "13:40")):
        lons, lats, tc, ml, mla, ot = campos[h]
        im = ax.imshow(tc, extent=(lons[0] + dlon, lons[-1] + dlon, lats[0] + dlat, lats[-1] + dlat), origin="lower", cmap=g.ESCALA, vmin=-90, vmax=-50, interpolation="nearest")
        g.contornos(ax)
        ax.plot(ml[ot], mla[ot], "o", mfc="none", mec="black", ms=11, mew=1.5)
        ax.plot(*g.AERO, "^", color="white", mec="black", ms=10)
        ax.set_xlim(g.AERO[0] - 1.1, g.AERO[0] + 1.1)
        ax.set_ylim(g.AERO[1] - .9, g.AERO[1] + .9)
        ax.set_aspect(1 / math.cos(math.radians(27)))
        ax.set_title(f"Início da varredura {h} UTC", fontweight="bold")
    fig.colorbar(im, ax=eixos, shrink=.8, label="Temperatura de brilho, canal 13 (°C)")
    fig.suptitle(f"Candidatos a overshoot (○): mínimo local, T ≤ −58 °C, ≥ {DT} K abaixo da bigorna; paralaxe corrigida para 14 km; ▲ aeroporto", fontweight="bold")
    fig.savefig(FIG / "overshoot_1330.png", dpi=120)


if __name__ == "__main__":
    main()
