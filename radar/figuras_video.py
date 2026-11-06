# -*- coding: utf-8 -*-
r"""Figuras do vídeo v3, em fundo escuro: campos reais de 13:30 UTC a 0,5° e mapa da trilha.

Saídas em radar/figuras/video: campo_Z.png, campo_V.png, campo_CC.png, campo_ZDR.png, mapa.png e mapa.json
(posição em pixels dos pontos da trilha, para animar sobre o mapa).
"""
import json
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402

SAIDA = AQUI / "figuras" / "video"
BG = "#0b1220"
FG = "#f1f5f9"
AX, AY = ar.AX, ar.AY
ALCANCE = 7.0
plt.rcParams.update({"text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG, "axes.edgecolor": "#64748b", "font.size": 13})


def campo(nome, dado, x, y, cmap, a, b, rotulo, Z, C):
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=150, facecolor=BG, constrained_layout=True)
    ax.set_facecolor("#1e293b")
    pc = ax.pcolormesh(x, y, np.ma.masked_invalid(dado)[:-1, :-1], cmap=cmap, vmin=a, vmax=b, shading="flat")
    ax.contour(x, y, np.where((Z >= 45) & (C < .85), 1.0, 0.0), levels=[.5], colors="white" if nome != "CC" else "black", linewidths=1.2)
    ax.plot(AX, AY, "*", color="yellow", mec="black", ms=20, zorder=5)
    ax.set_xlim(AX - ALCANCE * 1.9, AX + ALCANCE * 1.9)
    ax.set_ylim(AY - ALCANCE, AY + ALCANCE)
    ax.set_aspect("equal")
    ax.set_xlabel("km a leste do radar")
    ax.set_ylabel("km ao norte do radar")
    cb = fig.colorbar(pc, ax=ax, shrink=.9, pad=.01)
    cb.set_label(rotulo)
    fig.savefig(SAIDA / f"campo_{nome}.png", facecolor=BG)
    plt.close(fig)


def mapa():
    RAD = ar.RAD_LON, ar.RAD_LAT
    KX = 111.32 * math.cos(math.radians(RAD[1]))
    ll = lambda x, y: (RAD[0] + x / KX, RAD[1] + y / 111.132)
    E = json.load(open(AQUI / "dados_osm" / "osm.json", encoding="utf-8"))["elements"]
    B = json.load(open(AQUI / "dados_osm" / "bairros.json", encoding="utf-8"))["elements"]
    fig, ax = plt.subplots(figsize=(12.0, 8.2), dpi=150, facecolor=BG)
    fig.subplots_adjust(left=.07, right=.99, top=.99, bottom=.07)
    ax.set_facecolor("#0f1a2e")
    for e in E:
        t = e.get("tags", {})
        if t.get("waterway") in ("river", "stream") and e.get("geometry"):
            nom = t.get("name", "")
            uru = "Uruguai" in nom
            ax.plot([p["lon"] for p in e["geometry"]], [p["lat"] for p in e["geometry"]], color="#3b82f6" if uru or t["waterway"] == "river" else "#1e4a7a",
                    lw=4 if uru else (1.5 if nom else .6), zorder=1)
        if t.get("aeroway") == "runway":
            ax.plot([p["lon"] for p in e["geometry"]], [p["lat"] for p in e["geometry"]], color="#f1f5f9", lw=4.5, zorder=4)
    for e in B:
        n = e["tags"].get("name")
        for m in e["members"]:
            if m.get("geometry") and m.get("role") in ("outer", ""):
                ax.plot([p["lon"] for p in m["geometry"]], [p["lat"] for p in m["geometry"]], color="#f97316" if n != "Esplanada" else "#a16207", lw=2, zorder=2)
    ax.plot(*RAD, "^", color="#f1f5f9", ms=11, zorder=6)
    ax.annotate("Radar", RAD, xytext=(9, 4), textcoords="offset points", fontweight="bold", fontsize=14)
    ax.annotate("Rio Uruguai", (-52.745, -27.245), fontsize=15, fontweight="bold", color="#93c5fd")
    ax.annotate("Aeroporto", (-52.667, -27.1325), xytext=(-40, 22), textcoords="offset points", fontweight="bold", fontsize=14, zorder=7)
    ax.annotate("Bairros citados\npela Defesa Civil", (-52.606, -27.118), xytext=(-20, 42), textcoords="offset points", fontweight="bold", fontsize=13, color="#fdba74", zorder=7, ha="center")
    ax.set_xlim(-52.82, -52.48)
    ax.set_ylim(-27.26, -27.03)
    ax.set_aspect(1 / math.cos(math.radians(27.13)))
    ax.tick_params(labelsize=11)
    ax.grid(alpha=.12)
    pts = {h: ll(x, y) for h, x, y in (("13:24", -15.5, -10.1), ("13:30", -4.51, -9.55), ("13:36", 8.7, -10.2))}
    fig.canvas.draw()
    W, H = fig.canvas.get_width_height()
    px = {h: (float(ax.transData.transform(p)[0]) / W, 1 - float(ax.transData.transform(p)[1]) / H) for h, p in pts.items()}
    json.dump(px, open(SAIDA / "mapa.json", "w", encoding="utf-8"))
    fig.savefig(SAIDA / "mapa.png", facecolor=BG)
    plt.close(fig)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    s, V, Vq, vn, log, rots = ar.v_qc("133004", 0)
    Z, C, D = [ar.campo(ar.volume("133004", v)[0]) for v in ("dBZ", "RhoHV", "ZDR")]
    x, y, r = ar.geom(s, V.shape[1])
    campo("Z", Z, x, y, "turbo", 20, 70, "Refletividade (dBZ)", Z, C)
    campo("V", Vq, x, y, "RdBu_r", -50, 50, "Velocidade radial corrigida (m/s)", Z, C)
    campo("CC", C, x, y, "viridis", .5, 1, "Correlação copolar", Z, C)
    campo("ZDR", D, x, y, "coolwarm", -2, 4, "Refletividade diferencial (dB)", Z, C)
    mapa()
    print(sorted(p.name for p in SAIDA.iterdir()))


if __name__ == "__main__":
    main()
