# -*- coding: utf-8 -*-
r"""Mapas de temperatura de topo de nuvem (GOES-19, canal 13) do evento de Chapecó, 04/11/2026.

Gera em satelite/figuras:
  goes19_painel.png        evolução 12–15 UTC
  goes19_1330.png          imagem mais próxima de 13:30 UTC, com o entorno de Chapecó
  quadros/q_NN.png         quadros para a animação
  goes19_estatisticas.csv  temperaturas por horário
A temperatura é a de brilho a 10,3 µm, sem correção de paralaxe.
"""
import csv
import datetime as dt
import math
import pathlib
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import netCDF4
import shapefile
from matplotlib.colors import LinearSegmentedColormap

AQUI = pathlib.Path(__file__).resolve().parent
DADOS = AQUI / "dados_goes19"
FIG = AQUI / "figuras"
SHP = pathlib.Path(r"C:\gis4wrf\projects\Floripa\shp_ibge")
JANELA = (-56.5, -49.5, -29.5, -25.0)  # lon0, lon1, lat0, lat1
AERO = (-52.6496, -27.1338)
RAIO_KM = 25
CIDADES = [("Chapecó", -52.6496, -27.1338), ("S. Miguel do Oeste", -53.518, -26.7253), ("Xanxerê", -52.4036, -26.8747),
           ("Concórdia", -52.0278, -27.2342), ("Erechim", -52.274, -27.634), ("Passo Fundo", -52.407, -28.263)]
VMIN, VMAX = -90, -30
# Escala concentrada nos topos frios, onde está a estrutura do sistema; acima de -30 °C, cinza.
ESCALA = LinearSegmentedColormap.from_list("topo", [
    (0.00, "#ffffff"), (0.10, "#f0abfc"), (0.20, "#a21caf"), (0.30, "#b91c1c"), (0.40, "#f97316"),
    (0.50, "#fde047"), (0.60, "#22c55e"), (0.70, "#06b6d4"), (0.82, "#1d4ed8"), (1.00, "#1e293b")])
ESCALA.set_over("#94a3b8")


def latlon_para_fixa(lon, lat, p):
    """Grade fixa do ABI (GOES-R PUG, vol. 3): devolve os ângulos x, y em radianos para lat/lon em graus."""
    rq, rp, h, lon0 = p["rq"], p["rp"], p["h"], p["lon0"]
    la, lo = np.radians(lat), np.radians(lon)
    e2 = 1 - (rp / rq) ** 2
    lc = np.arctan((rp / rq) ** 2 * np.tan(la))
    rc = rp / np.sqrt(1 - e2 * np.cos(lc) ** 2)
    sx = h - rc * np.cos(lc) * np.cos(lo - lon0)
    sy = -rc * np.cos(lc) * np.sin(lo - lon0)
    sz = rc * np.sin(lc)
    return np.arcsin(-sy / np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)), np.arctan(sz / sx)


def ler(arq):
    with netCDF4.Dataset(arq) as ds:
        g = ds["goes_imager_projection"]
        h = float(g.perspective_point_height) + float(g.semi_major_axis)
        p = {"rq": float(g.semi_major_axis), "rp": float(g.semi_minor_axis), "h": h,
             "lon0": math.radians(float(g.longitude_of_projection_origin))}
        x = ds["x"][:].astype("f8")
        y = ds["y"][:].astype("f8")
        lons = np.linspace(JANELA[0], JANELA[1], 900)
        lats = np.linspace(JANELA[2], JANELA[3], 620)
        mlon, mlat = np.meshgrid(lons, lats)
        fx, fy = latlon_para_fixa(mlon, mlat, p)
        dx, dy = x[1] - x[0], y[1] - y[0]
        ix = np.rint((fx - x[0]) / dx).astype(int)
        iy = np.rint((fy - y[0]) / dy).astype(int)
        i0, i1, j0, j1 = iy.min(), iy.max() + 1, ix.min(), ix.max() + 1
        tk = ds["CMI"][i0:i1, j0:j1]
        tc = np.ma.filled(tk.astype("f8"), np.nan) - 273.15
        return lons, lats, tc[iy - i0, ix - j0]


def horario(nome):
    s = re.search(r"_s(\d{4})(\d{3})(\d{2})(\d{2})", nome)
    return dt.datetime(int(s[1]), 1, 1) + dt.timedelta(days=int(s[2]) - 1, hours=int(s[3]), minutes=int(s[4]))


def contornos(ax):
    for arq, cor, lw in (("SC_Municipios_2022.shp", "#0f172a", .22), ("BR_Estados.shp", "black", 1.0), ("America_do_Sul.shp", "black", 1.0)):
        for s in shapefile.Reader(str(SHP / arq)).shapes():
            pts = np.array(s.points)
            for a, b in zip(s.parts, list(s.parts[1:]) + [len(pts)]):
                ax.plot(pts[a:b, 0], pts[a:b, 1], color=cor, lw=lw, zorder=3)


def base(ax, lons, lats, tc):
    im = ax.imshow(tc, extent=(lons[0], lons[-1], lats[0], lats[-1]), origin="lower", cmap=ESCALA, vmin=VMIN, vmax=VMAX,
                   interpolation="nearest", zorder=1)
    contornos(ax)
    ax.set_xlim(JANELA[:2])
    ax.set_ylim(JANELA[2:])
    ax.set_aspect(1 / math.cos(math.radians(27)))
    ax.plot(*AERO, "^", color="white", mec="black", ms=8, zorder=5)
    return im


def mascara_raio(lons, lats):
    mlon, mlat = np.meshgrid(lons, lats)
    dx = (mlon - AERO[0]) * 111.2 * math.cos(math.radians(AERO[1]))
    dy = (mlat - AERO[1]) * 111.2
    return np.hypot(dx, dy) <= RAIO_KM


def main():
    FIG.mkdir(exist_ok=True)
    (FIG / "quadros").mkdir(exist_ok=True)
    arqs = sorted(DADOS.glob("OR_ABI-L2-CMIPF-M6C13_*.nc"))
    if not arqs:
        raise SystemExit("sem dados em " + str(DADOS))
    series, campos = [], []
    for arq in arqs:
        lons, lats, tc = ler(arq)
        t = horario(arq.name)
        campos.append((t, tc))
        m = mascara_raio(lons, lats)
        i = int(np.argmin(np.abs(lons - AERO[0])))
        j = int(np.argmin(np.abs(lats - AERO[1])))
        series.append([t.strftime("%H:%M"), round(float(tc[j, i]), 1), round(float(np.nanmin(tc[m])), 1), round(float(np.nanmin(tc)), 1)])
    with open(FIG / "goes19_estatisticas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["inicio_varredura_utc", "T_aeroporto_C", f"T_min_{RAIO_KM}km_C", "T_min_janela_C"])
        w.writerows(series)
    for s in series:
        print(*s, sep="\t")

    # painel: 6 horários igualmente espaçados
    sel = campos[1::3][:6]
    fig, eixos = plt.subplots(2, 3, figsize=(16, 9.2), constrained_layout=True)
    for ax, (t, tc) in zip(eixos.flat, sel):
        im = base(ax, lons, lats, tc)
        brt = t - dt.timedelta(hours=3)
        ax.set_title(f"{t:%H:%M} UTC ({brt:%H:%M} BRT)", fontweight="bold")
        ax.tick_params(labelsize=7)
    fig.colorbar(im, ax=eixos, shrink=.8, label="Temperatura de brilho, 10,3 µm (°C)")
    fig.suptitle("GOES-19, canal 13, 04/11/2026. ▲ Aeroporto de Chapecó", fontweight="bold", fontsize=14)
    fig.savefig(FIG / "goes19_painel.png", dpi=130)
    plt.close(fig)

    # imagem principal e quadros
    alvo = dt.datetime(2026, 11, 4, 13, 30)
    t, tc = min(campos, key=lambda c: abs(c[0] - alvo))
    desenhar(lons, lats, t, tc, FIG / "goes19_1330.png")
    for n, (t, tc) in enumerate(campos):
        desenhar(lons, lats, t, tc, FIG / "quadros" / f"q_{n:02d}.png")


def desenhar(lons, lats, t, tc, saida):
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=150, constrained_layout=True)
    im = base(ax, lons, lats, tc)
    for nome, lo, la in CIDADES[1:]:
        ax.plot(lo, la, "o", color="white", mec="black", ms=4, zorder=5)
        ax.annotate(nome, (lo, la), xytext=(5, 4), textcoords="offset points", fontsize=9, color="white", zorder=6,
                    bbox=dict(boxstyle="round,pad=.15", fc="black", ec="none", alpha=.65))
    ax.annotate("Chapecó", AERO, xytext=(7, 5), textcoords="offset points", fontsize=11, fontweight="bold", color="white", zorder=6,
                bbox=dict(boxstyle="round,pad=.2", fc="#be123c", ec="none"))
    brt = t - dt.timedelta(hours=3)
    ax.set_title(f"GOES-19, canal 13: início da varredura {t:%H:%M} UTC ({brt:%H:%M} BRT), 04/11/2026", fontweight="bold", fontsize=13)
    fig.colorbar(im, ax=ax, shrink=.85, label="Temperatura de brilho, 10,3 µm (°C)")
    fig.savefig(saida)
    plt.close(fig)


if __name__ == "__main__":
    main()
