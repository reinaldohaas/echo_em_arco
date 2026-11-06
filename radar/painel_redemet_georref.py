# -*- coding: utf-8 -*-
r"""Painel de MaxCAPPI REDEMET (Santiago e Morro da Igreja) com georreferência e horário reais.

Usa os limites e os horários UTC de quadros.csv, em vez da calibração manual e do
tempo interpolado do mosaico gravado em tela. Não converte cor em dBZ: mostra o produto como veio.
"""
import csv
import math
import pathlib
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapefile
from PIL import Image

AQUI = pathlib.Path(__file__).resolve().parent
SHP = pathlib.Path(r"C:\gis4wrf\projects\Floripa\shp_ibge")
JANELA = (-54.3, -51.2, -28.0, -26.0)
CHAPECO = (-52.6496, -27.1338)
ALVOS = [datetime(2026, 11, 4, h, m) for h, m in
         [(12, 16), (12, 36), (12, 56), (13, 16), (13, 36), (13, 56), (14, 16), (14, 36)]]
TOLERANCIA = timedelta(minutes=12)


def quadros(radar):
    pasta = AQUI / radar / "maxcappi"
    with open(pasta / "quadros.csv", encoding="utf-8") as f:
        return [dict(r, t=datetime.strptime(r["data_utc"], "%Y-%m-%d %H:%M:%S"), png=pasta / r["arquivo"])
                for r in csv.DictReader(f)]


def mais_proximo(lista, alvo):
    q = min(lista, key=lambda r: abs(r["t"] - alvo))
    return q if abs(q["t"] - alvo) <= TOLERANCIA else None


def contornos(ax, arquivo, **kw):
    for s in shapefile.Reader(str(SHP / arquivo)).shapes():
        p = np.array(s.points)
        for a, b in zip(s.parts, list(s.parts[1:]) + [len(p)]):
            ax.plot(p[a:b, 0], p[a:b, 1], **kw)


def main():
    fontes = {r: quadros(r) for r in ("sg", "mi")}
    fig, eixos = plt.subplots(2, 4, figsize=(17, 8.6), constrained_layout=True)
    for ax, alvo in zip(eixos.flat, ALVOS):
        rotulos = []
        for radar, lista in fontes.items():
            q = mais_proximo(lista, alvo)
            if not q or not q["png"].exists():
                continue
            ext = [float(q[k]) for k in ("lon_min", "lon_max", "lat_min", "lat_max")]
            ax.imshow(np.array(Image.open(q["png"]).convert("RGBA")), extent=ext, origin="upper",
                      interpolation="nearest", zorder=2 if radar == "sg" else 1)
            rotulos.append(f"{radar.upper()} {q['t']:%H:%M}")
        contornos(ax, "SC_Municipios_2022.shp", color="0.55", lw=0.3, zorder=3)
        contornos(ax, "BR_Estados.shp", color="black", lw=0.9, zorder=3)
        ax.plot(*CHAPECO, "^", color="#e11d48", mec="white", ms=8, zorder=5)
        ax.set_xlim(JANELA[:2])
        ax.set_ylim(JANELA[2:])
        ax.set_aspect(1 / math.cos(math.radians(-27)))
        brt = alvo - timedelta(hours=3)
        ax.set_title(f"{alvo:%H:%M} UTC ({brt:%H:%M} BRT)\n{' | '.join(rotulos) or 'sem quadro'}", fontsize=10)
        ax.tick_params(labelsize=7)
    fig.suptitle("MaxCAPPI REDEMET/DECEA, Santiago sobre Morro da Igreja, 04/11/2026. ▲ Aeroporto de Chapecó", fontweight="bold")
    saida = AQUI / "figuras" / "chapeco_redemet_georref.png"
    fig.savefig(saida, dpi=130)
    print(saida)


if __name__ == "__main__":
    main()
