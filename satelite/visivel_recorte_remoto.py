# -*- coding: utf-8 -*-
r"""Lê do bucket da NOAA apenas o recorte de Chapecó do canal 2 (0,5 km), com requisições por faixa de bytes.

Grava os recortes em satelite/dados_goes19_vis/recorte_HHMM.npz e o painel em figuras/visivel_overshoot.png.
Evita baixar os 382 MB de cada disco completo.
"""
import csv
import math
import pathlib
import re
import subprocess
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import plotar_goes19 as g  # noqa: E402
from teste_overshoot import paralaxe  # noqa: E402

CURL = r"C:\Windows\System32\curl.exe"
B = "https://noaa-goes19.s3.amazonaws.com"
DEST = AQUI / "dados_goes19_vis"
FIG = AQUI / "figuras"
ALVOS = ("1320", "1330", "1340")
RAIO = 0.75


def recorte(chave):
    lons = np.linspace(g.AERO[0] - RAIO * 1.2, g.AERO[0] + RAIO * 1.2, 800)
    lats = np.linspace(g.AERO[1] - RAIO, g.AERO[1] + RAIO, 600)
    mlon, mlat = np.meshgrid(lons, lats)
    with netCDF4.Dataset(f"{B}/{chave}#mode=bytes") as ds:
        p0 = ds["goes_imager_projection"]
        p = {"rq": float(p0.semi_major_axis), "rp": float(p0.semi_minor_axis), "h": float(p0.perspective_point_height) + float(p0.semi_major_axis),
             "lon0": math.radians(float(p0.longitude_of_projection_origin))}
        fx, fy = g.latlon_para_fixa(mlon, mlat, p)
        x, y = ds["x"], ds["y"]
        x0, dx = float(x[0]), float(x[1] - x[0])
        y0, dy = float(y[0]), float(y[1] - y[0])
        ix, iy = np.rint((fx - x0) / dx).astype(int), np.rint((fy - y0) / dy).astype(int)
        i0, i1, j0, j1 = iy.min(), iy.max() + 1, ix.min(), ix.max() + 1
        print("blocos:", ds["CMI"].chunking(), "janela", i1 - i0, j1 - j0, flush=True)
        d = np.ma.filled(ds["CMI"][i0:i1, j0:j1].astype("f8"), np.nan)
    return lons, lats, d[iy - i0, ix - j0]


def main():
    DEST.mkdir(exist_ok=True)
    r = subprocess.run([CURL, "-sS", "-f", "-m", "60", f"{B}/?list-type=2&prefix=ABI-L2-CMIPF/2026/308/13/OR_ABI-L2-CMIPF-M6C02"], capture_output=True, text=True, check=True)
    chaves = re.findall(r"<Key>([^<]+)</Key>", r.stdout)
    dados = []
    for alvo in ALVOS:
        arq = DEST / f"recorte_{alvo}.npz"
        if not arq.exists():
            t0 = time.time()
            lons, lats, v = recorte(next(k for k in chaves if f"_s2026308{alvo}" in k))
            np.savez_compressed(arq, lons=lons, lats=lats, v=v)
            print(alvo, f"{time.time() - t0:.0f} s; refletância {np.nanmin(v):.2f} a {np.nanmax(v):.2f}", flush=True)
        q = np.load(arq)
        dados.append((alvo, q["lons"], q["lats"], q["v"]))

    dlon, dlat = paralaxe(*g.AERO)
    print(f"paralaxe: {dlon * 99:+.1f} km E, {dlat * 111:+.1f} km N", flush=True)
    with open(FIG / "overshoot.csv", encoding="utf-8") as f:
        ots = list(csv.DictReader(f))
    fig, eixos = plt.subplots(1, 3, figsize=(19, 6.2), constrained_layout=True)
    for ax, (alvo, lons, lats, v) in zip(eixos, dados):
        ax.imshow(v, extent=(lons[0] + dlon, lons[-1] + dlon, lats[0] + dlat, lats[-1] + dlat), origin="lower", cmap="gray",
                  vmin=np.nanpercentile(v, 2), vmax=np.nanpercentile(v, 99.8), interpolation="bilinear")
        g.contornos(ax)
        h = f"{alvo[:2]}:{alvo[2:]}"
        o = [q for q in ots if q["inicio_utc"] == h]
        if o:
            ax.plot([float(q["lon_corr"]) for q in o], [float(q["lat_corr"]) for q in o], "o", mfc="none", mec="#22d3ee", ms=16, mew=1.4)
        ax.plot(*g.AERO, "^", color="#ef4444", mec="white", ms=11, zorder=8)
        ax.set_xlim(lons[0] + dlon, lons[-1] + dlon)
        ax.set_ylim(lats[0] + dlat, lats[-1] + dlat)
        ax.set_aspect(1 / math.cos(math.radians(27)))
        ax.set_title(f"Visível (0,64 µm), início {h} UTC", fontweight="bold")
    fig.suptitle("GOES-19 canal 2; paralaxe corrigida para 14 km; ○ candidatos do canal 13; ▲ aeroporto", fontweight="bold")
    fig.savefig(FIG / "visivel_overshoot.png", dpi=125)
    print("figura pronta", flush=True)


if __name__ == "__main__":
    main()
