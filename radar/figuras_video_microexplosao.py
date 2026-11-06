# -*- coding: utf-8 -*-
r"""Painéis da cena de radar do vídeo, a partir dos testes de microexplosão.

Lê radar/figuras/teste_microexplosao_saida.txt e teste_microexplosao_2_saida.txt. Gera em assets/radar_v2:
  chuva.png     Z máximo por altura e horário, só com CC >= 0,90
  vento.png     V atrás da linha, por altura, às 13:30 UTC
  cisalhamento.png  V e cisalhamento em 2 km, sem dobra: núcleo x outros discos
descida() e linha() geram os painéis da versão anterior do vídeo. divergencia_sem_dobra() gera
radar/figuras/teste_divergencia_sem_dobra.txt.
"""
import pathlib
import re
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402
import analise_rotacao_checagens as ck  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)
SAIDA = AQUI.parent / "assets" / "radar_v2"
FUNDO, TEXTO = "#0b1220", "#f1f5f9"
plt.rcParams.update({"figure.facecolor": FUNDO, "axes.facecolor": "#151f33", "text.color": TEXTO, "axes.labelcolor": TEXTO,
                     "xtick.color": TEXTO, "ytick.color": TEXTO, "axes.edgecolor": "#64748b", "font.size": 14})
T1 = (AQUI / "figuras" / "teste_microexplosao_saida.txt").read_text(encoding="utf-8")
T2 = (AQUI / "figuras" / "teste_microexplosao_2_saida.txt").read_text(encoding="utf-8")


def secao(texto, marca):
    s = texto[texto.index(marca):].split("\n")[1:]
    out = []
    for l in s:
        if l.startswith("["):
            break
        if l.strip():
            out.append(l.split("\t"))
    return out


def descida():
    linhas = secao(T1, "[4. Z POR ALTURA")
    horas = ["1306", "1312", "1318", "1324", "1330", "1336", "1342"]
    bandas = ["0-0.3", "0.3-0.7", "0.7-1.2", "1.2-2", "2-3", "3-5", "5-8"]
    M = np.full((len(bandas), len(horas)), np.nan)
    for h, b, zmax, *_ in linhas:
        M[bandas.index(b), horas.index(h)] = float(zmax)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=100, constrained_layout=True)
    ax.set_facecolor("#7c8798")
    im = ax.imshow(np.ma.masked_invalid(M), origin="lower", aspect="auto", cmap="turbo", vmin=50, vmax=66)
    for j, i in np.ndindex(M.shape):
        if np.isfinite(M[j, i]):
            ax.text(i, j, f"{M[j, i]:.0f}", ha="center", va="center", fontsize=15, fontweight="bold", color="black" if 53 < M[j, i] < 62 else "white")
    ax.set_xticks(range(len(horas)), [f"{int(h[:2]) - 3}:{h[2:]}" for h in horas])
    ax.set_yticks(range(len(bandas)), [b.replace(".", ",").replace("-", " a ") for b in bandas])
    ax.set_xlabel("Hora local, seguindo o núcleo")
    ax.set_ylabel("Altura acima do radar (km)")
    ax.set_title("Refletividade máxima (dBZ): o núcleo desce e chega ao solo às 10:30", fontweight="bold", fontsize=17)
    fig.colorbar(im, ax=ax, label="dBZ", shrink=.9)
    fig.savefig(SAIDA / "descida.png")
    plt.close(fig)


def vento():
    ls = [l for l in secao(T2, "[B. vento") if l[0] == "1330"]
    alt = [float(l[2]) * 1000 for l in ls]
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=100, constrained_layout=True)
    med, p10, p90 = [np.array([float(l[k]) for l in ls]) for k in (4, 5, 6)]
    ax.fill_betweenx(alt, -p10, -p90, color="#3ecbe8", alpha=.25, label="10% a 90% dos gates")
    ax.plot(-med, alt, "o-", color="#3ecbe8", lw=4, ms=11, label="mediana")
    for a, m in zip(alt, med):
        ax.annotate(f"{-m:.0f}", (-m, a), xytext=(10, -4), textcoords="offset points", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 35)
    ax.set_ylim(0, 900)
    ax.set_xlabel("Componente do vento em direção ao radar (m/s)")
    ax.set_ylabel("Altura acima do radar (m)")
    ax.set_title("Atrás da linha, às 10:30: o vento mais forte está na camada mais baixa", fontweight="bold", fontsize=17)
    ax.grid(alpha=.25)
    ax.legend(loc="upper left", frameon=False)
    fig.savefig(SAIDA / "vento.png")
    plt.close(fig)


def linha():
    s, V, Vq, *_ = ar.v_qc("133004", 2)  # 1,3°: sem dobra junto ao núcleo
    x, y, r = ar.geom(s, V.shape[1])
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 5.8), dpi=100, constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.25]})
    a.set_facecolor("#7c8798")
    fx = lambda c: np.vstack([c, c[:1]])
    pc = a.pcolormesh(fx(x), fx(y), np.ma.masked_invalid(fx(Vq))[:-1, :-1], cmap="RdBu_r", vmin=-35, vmax=35, shading="flat")
    a.plot(ar.AX, ar.AY, "*", color="#fde047", mec="black", ms=20)
    a.set_xlim(-16, 8)
    a.set_ylim(-26, 2)
    a.set_aspect("equal")
    a.set_title("V, 1,3°: fronteira contínua", fontweight="bold", fontsize=15)
    a.set_xlabel("km a leste do radar")
    a.set_ylabel("km ao norte do radar")
    fig.colorbar(pc, ax=a, label="m/s", shrink=.8)
    eles, nuc, resto = [], [], []
    bloco = None
    for l in secao(T1, "[1. ESCALA"):
        if l[0].strip():
            bloco = float(l[0])
        elif float(l[1]) == 1.0:
            eles.append(bloco)
            nuc.append(float(l[3]))
            resto.append(float(l[6]))
    pos = np.arange(1, len(eles))  # 0,5° fica fora: o par depende de uma região pequena desdobrada
    b.bar(pos - .2, nuc[1:], .4, color="#ef4444", label="junto ao aeroporto")
    b.bar(pos + .2, resto[1:], .4, color="#94a3b8", label="maior valor no resto da linha")
    b.set_xticks(pos, [f"{e:.1f}°".replace(".", ",") for e in eles[1:]])
    b.set_xlabel("Elevação")
    b.set_ylabel("Diferença de V em 1 km (m/s)")
    b.set_ylim(0, 62)
    b.set_title("O par não se destaca da linha", fontweight="bold", fontsize=15)
    b.legend(frameon=False, fontsize=12, loc="upper right")
    fig.savefig(SAIDA / "linha.png")
    plt.close(fig)


def chuva():
    """Z máximo por camada só com CC >= 0,90, de corte_vertical_complemento.txt: tira o sinal anômalo de 13:30."""
    texto = (AQUI / "figuras" / "corte_vertical_complemento.txt").read_text(encoding="utf-8")
    horas = ["1306", "1312", "1318", "1324", "1330", "1336", "1342"]
    bandas = ["0-0.3", "0.3-0.7", "0.7-1.2", "1.2-2", "2-3", "3-5", "5-8"]
    M = np.full((len(bandas), len(horas)), np.nan)
    for l in secao(texto, "[A]"):
        if l[4] != "nd":
            M[bandas.index(l[1]), horas.index(l[0])] = float(l[4])
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=100, constrained_layout=True)
    ax.set_facecolor("#7c8798")
    im = ax.imshow(np.ma.masked_invalid(M), origin="lower", aspect="auto", cmap="turbo", vmin=50, vmax=66)
    for j, i in np.ndindex(M.shape):
        if np.isfinite(M[j, i]):
            ax.text(i, j, f"{M[j, i]:.1f}".replace(".", ",").replace(",0", ""), ha="center", va="center", fontsize=15, fontweight="bold",
                    color="black" if 53 < M[j, i] < 62 else "white")
    ax.set_xticks(range(len(horas)), [f"{int(h[:2]) - 3}:{h[2:]}" for h in horas])
    ax.set_yticks(range(len(bandas)), [b.replace(".", ",").replace("-", " a ") for b in bandas])
    ax.set_xlabel("Hora local, seguindo o núcleo; cinza: sem amostragem")
    ax.set_ylabel("Altura acima do radar (km)")
    ax.set_title("Refletividade máxima (dBZ), só com CC ≥ 0,90: chuva intensa até a camada mais baixa", fontweight="bold", fontsize=15)
    fig.colorbar(im, ax=ax, label="dBZ", shrink=.9)
    fig.savefig(SAIDA / "chuva.png")
    plt.close(fig)


def cisalhamento():
    """Campo de V e dV em 2 km, sem gates dobrados: núcleo x outros discos (teste_reconciliacao_saida.txt, 13:30)."""
    s, V, Vq, *_ = ar.v_qc("133004", 2)
    x, y, r = ar.geom(s, V.shape[1])
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 5.8), dpi=100, constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.25]})
    a.set_facecolor("#7c8798")
    fx = lambda c: np.vstack([c, c[:1]])
    pc = a.pcolormesh(fx(x), fx(y), np.ma.masked_invalid(fx(Vq))[:-1, :-1], cmap="RdBu_r", vmin=-35, vmax=35, shading="flat")
    a.plot(ar.AX, ar.AY, "*", color="#fde047", mec="black", ms=20)
    a.set_xlim(-16, 8)
    a.set_ylim(-26, 2)
    a.set_aspect("equal")
    a.set_title("V, 1,3°, às 10:30", fontweight="bold", fontsize=15)
    a.set_xlabel("km a leste do radar")
    a.set_ylabel("km ao norte do radar")
    fig.colorbar(pc, ax=a, label="m/s", shrink=.8)
    eles, nuc, resto = [], [], []
    for l in (AQUI / "figuras" / "teste_reconciliacao_saida.txt").read_text(encoding="utf-8").splitlines():
        c = l.split("\t")
        if len(c) > 11 and c[0] == "1330" and c[1] == "sem_dobra" and c[3] == "2.0" and float(c[2]) <= 4:
            eles.append(float(c[2]))
            nuc.append(float(c[4]))
            resto.append(float(c[10]))
    print("cisalhamento:", eles, nuc, resto)
    pos = np.arange(len(eles))
    b.bar(pos - .2, nuc, .4, color="#ef4444", label="núcleo, junto ao aeroporto")
    b.bar(pos + .2, resto, .4, color="#94a3b8", label="maior valor nos outros discos")
    b.set_xticks(pos, [f"{e:.1f}°".replace(".", ",") for e in eles])
    b.set_xlabel("Elevação")
    b.set_ylabel("Diferença de V em 2 km (m/s)")
    b.set_ylim(0, 72)
    b.set_title("Sem dobra: maior no núcleo até 1,3°", fontweight="bold", fontsize=15)
    b.legend(frameon=False, fontsize=12, loc="upper left")
    fig.savefig(SAIDA / "cisalhamento.png")
    plt.close(fig)


def divergencia_sem_dobra():
    saida = ["hora ele km | dV máx em V bruta, mesmo sinal de fundo, região sem dobra, até 6 km do núcleo | p99,5 no resto"]
    for h in ("133004", "133604"):
        for idx in (0, 1, 2, 3):
            s, V, Vq, vn, log, rots = ar.v_qc(h, idx)
            Vs = ar.mediana(V, 3)
            x, y, r = ar.geom(s, V.shape[1])
            xc, yc, _ = ck.pos_nucleo(h, idx)
            d = np.hypot(x - xc, y - yc)
            sem = np.abs(Vq - V) < .01
            for km in (1, 2, 4):
                n = int(round(km / s["rstep_km"]))
                dv = np.roll(Vs, -n, axis=1) - Vs
                ok = sem & np.roll(sem, -n, axis=1) & (rots == np.roll(rots, -n, axis=1)) & np.isfinite(dv)
                ok[:, -n:] = False
                a, c = ok & (d <= 6), ok & (d > 8) & (r > 5) & (r < 45)
                saida.append(f"{h[:4]} {s['ele_deg']} {km} | {np.nanmax(dv[a]) if a.any() else float('nan'):.1f} | {np.nanpercentile(dv[c], 99.5):.1f}")
    texto = "\n".join(saida)
    (AQUI / "figuras" / "teste_divergencia_sem_dobra.txt").write_text(texto, encoding="utf-8")
    print(texto)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    chuva()
    vento()
    cisalhamento()


if __name__ == "__main__":
    main()
