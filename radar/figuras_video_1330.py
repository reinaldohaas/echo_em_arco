# -*- coding: utf-8 -*-
r"""Painéis da cena de radar do vídeo: 13:30 UTC, 0,5°, em torno do Aeroporto de Chapecó.

Gera em assets/radar_v2: z.png, cc.png, v_rel.png e perfil.png (1100x580, fundo escuro).
A velocidade relativa ao núcleo segue analise_rotacao_final.py: V - U·r, mediana 3x3, sem regiões com salto residual.
O perfil lê rotacao_resumo.csv e as alturas de rotacao_final_saida.txt.
"""
import csv
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402
import analise_rotacao_checagens as ck  # noqa: E402

SAIDA = AQUI.parent / "assets" / "radar_v2"
HORA, IDX = "133004", 0
ALT_KM = [.10, .16, .22, .30, .40, .52, .69]  # alturas acima do radar, 13:30, 0,5° a 4,0°
FUNDO, TEXTO = "#0b1220", "#f1f5f9"
plt.rcParams.update({"figure.facecolor": FUNDO, "axes.facecolor": "#151f33", "text.color": TEXTO, "axes.labelcolor": TEXTO,
                     "xtick.color": TEXTO, "ytick.color": TEXTO, "axes.edgecolor": "#64748b", "font.size": 13})


def painel(nome, x, y, campo, cmap, a, b, rotulo, titulo, Z, C):
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=100, constrained_layout=True)
    # cinza médio: gates sem dado não podem parecer valores extremos da escala
    ax.set_facecolor("#7c8798")
    ax.text(.99, .02, "cinza: sem dado", transform=ax.transAxes, ha="right", va="bottom", fontsize=13, color="white", fontweight="bold",
            bbox=dict(boxstyle="round,pad=.2", fc="#334155", ec="none"), zorder=9)
    pc = ax.pcolormesh(x, y, np.ma.masked_invalid(campo)[:-1, :-1], cmap=cmap, vmin=a, vmax=b, shading="flat")
    if Z is not None:
        nuc = np.where((Z >= 45) & (C < .85), 1.0, 0.0)
        ax.contour(x, y, nuc, levels=[.5], colors="black", linewidths=1.0)
    ax.plot(ar.AX, ar.AY, "*", color="#fde047", mec="black", ms=20)
    ax.annotate("Aeroporto", (ar.AX, ar.AY), xytext=(14, -6), textcoords="offset points", fontsize=14, fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=.2", fc="black", ec="none", alpha=.7))
    ax.set_xlim(ar.AX - 9, ar.AX + 9)
    ax.set_ylim(ar.AY - 4.7, ar.AY + 4.7)
    ax.set_aspect("equal")
    ax.set_xlabel("km a leste do radar")
    ax.set_ylabel("km ao norte do radar")
    ax.set_title(titulo, fontweight="bold", fontsize=16)
    fig.colorbar(pc, ax=ax, label=rotulo, shrink=.92)
    fig.savefig(SAIDA / nome)
    plt.close(fig)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    s, V, Vq, vn, log, rots = ar.v_qc(HORA, IDX)
    x, y, r = ar.geom(s, V.shape[1])
    rr = np.hypot(x, y)
    Vs = ar.mediana(Vq, 3)
    SR = Vs - (ck.UX * 1000 * x / rr + ck.UY * 1000 * y / rr)
    Z = ar.campo(ar.volume(HORA, "dBZ")[IDX])
    C = ar.campo(ar.volume(HORA, "RhoHV")[IDX])
    # a grade de Z e CC pode ter mais gates que a de V
    n = min(Z.shape[1], x.shape[1])
    x, y, SR, Z, C = x[:, :n], y[:, :n], SR[:, :n], Z[:, :n], C[:, :n]
    # sem linha de corte em 0/360°: fecha a varredura repetindo o primeiro raio
    fechar = lambda a: np.vstack([a, a[:1]])
    x, y, SR, Z, C = map(fechar, (x, y, SR, Z, C))
    t = "13:30 UTC, elevação 0,5°: "
    painel("z.png", x, y, Z, "turbo", 20, 70, "dBZ", t + "refletividade", Z, C)
    painel("cc.png", x, y, C, "viridis", .5, 1, "RhoHV", t + "correlação copolar", Z, C)
    painel("v_rel.png", x, y, SR, "RdBu_r", -40, 40, "m/s (vermelho: afasta do radar)", t + "velocidade relativa ao núcleo", Z, C)

    with open(AQUI / "figuras" / "rotacao_resumo.csv", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=100, constrained_layout=True)
    alt = [a * 1000 for a in ALT_KM]
    ax.plot([float(l["SRmax"]) for l in linhas], alt, "o-", color="#ef4444", lw=3, ms=10, label="afasta do radar")
    ax.plot([float(l["SRmin"]) for l in linhas], alt, "o-", color="#3ecbe8", lw=3, ms=10, label="aproxima do radar")
    ax.axvline(0, color=TEXTO, lw=1)
    ax.set_xlim(-40, 40)
    ax.set_ylim(0, 800)
    ax.set_xlabel("Velocidade relativa ao núcleo, disco de 2,5 km (m/s)")
    ax.set_ylabel("Altura acima do radar (m)")
    ax.set_title("13:30 UTC: o par de ventos opostos em 7 elevações (0,5° a 4,0°)", fontweight="bold", fontsize=16)
    ax.grid(alpha=.25)
    ax.legend(loc="upper left", frameon=False, fontsize=14)
    fig.savefig(SAIDA / "perfil.png")
    plt.close(fig)
    print("gerado em", SAIDA)


if __name__ == "__main__":
    main()
