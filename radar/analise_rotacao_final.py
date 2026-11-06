# -*- coding: utf-8 -*-
r"""Etapa final: descida de precipitação, velocidade relativa ao núcleo, largura espectral e figura-resumo.

 1. Altura x tempo: Z ao longo da trilha do núcleo, 13:18–13:36 UTC, em disco de 4 km.
 2. Velocidade relativa ao núcleo: V - U·r, com U ajustado (40,4 m/s para leste).
 3. Largura espectral e lacunas: a filtragem pode ocultar justamente os gates mais turbulentos.
 4. Figura rotacao_resumo.png e tabela rotacao_resumo.csv.
"""
import csv
import datetime as dt
import pathlib
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
FIG = ar.FIG
AX, AY = ar.AX, ar.AY
UX, UY, X0, Y0, T0 = ck.UX, ck.UY, ck.X0, ck.Y0, ck.T0


def altura_tempo():
    pts = []
    print("[altura x tempo] hora ele alt_km seg_rel | Zmax Zp90 gates>=55 CCmed | distância do máx à trilha")
    for h in ("131804", "132404", "133004", "133604"):
        for idx in range(len(ar.volume(h, "dBZ"))):
            s = ar.volume(h, "dBZ")[idx]
            xc, yc = X0, Y0
            for _ in range(4):
                tt = (ar.t_gate(h, idx, xc, yc) - T0).total_seconds()
                xc, yc = X0 + UX * tt, Y0 + UY * tt
            Z = ar.campo(s)
            C = ar.campo(ar.volume(h, "RhoHV")[idx])
            x, y, r = ar.geom(s, Z.shape[1])
            d = np.hypot(x - xc, y - yc)
            m = (d <= 4) & np.isfinite(Z)
            if m.sum() < 10:
                continue
            al = float(ar.alt_radar(np.hypot(xc, yc), s["ele_deg"]))
            v = Z[m]
            k = np.argmax(v)
            pts.append({"hora": h[:4], "ele": s["ele_deg"], "alt": round(al, 2), "t": round(tt), "Zmax": float(v.max()), "Zp90": float(np.percentile(v, 90)),
                        "n55": int((v >= 55).sum()), "CCmed": round(float(np.nanmedian(C[m])), 2), "dist": round(float(d[m][k]), 1)})
            print("   ", *pts[-1].values(), sep="\t")
    return pts


def relativa():
    print("[velocidade relativa ao núcleo] 13:30: ele az | Vmin Vmax (disco 2,5 km, mediana 3x3) | SRmin SRmax | razão")
    saida = []
    guard = {}
    for idx in range(7):
        s, V, Vq, vn, log, rots = ar.v_qc("133004", idx)
        Vs = ar.mediana(Vq, 3)
        x, y, r = ar.geom(s, V.shape[1])
        rr = np.hypot(x, y)
        SR = Vs - (UX * 1000 * x / rr + UY * 1000 * y / rr)
        cs = [c for c in ar.nucleos("133004", idx, min_g=6)]
        xc, yc, _ = ck.pos_nucleo("133004", idx)
        cs = [c for c in cs if np.hypot(c["x"] - xc, c["y"] - yc) < 3]
        if cs:
            c = max(cs, key=lambda q: q["n"])
            xc, yc = c["x"], c["y"]
        m = (np.hypot(x - xc, y - yc) <= 2.5) & np.isfinite(SR)
        a, b = float(np.min(SR[m])), float(np.max(SR[m]))
        saida.append({"ele": s["ele_deg"], "xc": round(xc, 1), "yc": round(yc, 1), "Vmin": round(float(np.min(Vs[m])), 1), "Vmax": round(float(np.max(Vs[m])), 1),
                      "SRmin": round(a, 1), "SRmax": round(b, 1), "Vrot": round((b - a) / 2, 1)})
        print("   ", *saida[-1].values(), sep="\t")
        Zc, Cc = ar.campo(ar.volume("133004", "dBZ")[idx]), ar.campo(ar.volume("133004", "RhoHV")[idx])
        guard[idx] = dict(x=x, y=y, SR=SR, Z=Zc, C=Cc, xc=xc, yc=yc, ele=s["ele_deg"])
    return saida, guard


def largura():
    print("[W e lacunas no núcleo de 13:30] ele gates | fração sem V, sem W, sem Z, sem CC | W mediana p90 máx | anel 3–6 km W mediana p90")
    for idx in range(4):
        h = "133004"
        xc, yc, _ = ck.pos_nucleo(h, idx)
        sz = ar.volume(h, "dBZ")[idx]
        Z, C, V, W = [ar.campo(ar.volume(h, v)[idx]) for v in ("dBZ", "RhoHV", "V", "W")]
        x, y, r = ar.geom(sz, Z.shape[1])
        d = np.hypot(x - xc, y - yc)
        nuc = (d <= 2.5) & (Z >= 45) & (C < .85)
        an = (d > 3) & (d <= 6)
        print(f"    {sz['ele_deg']}° n={nuc.sum()} semV={np.mean(~np.isfinite(V[nuc])):.2f} semW={np.mean(~np.isfinite(W[nuc])):.2f} "
              f"W={np.nanmedian(W[nuc]):.1f}/{np.nanpercentile(W[nuc], 90):.1f}/{np.nanmax(W[nuc]):.1f} anel={np.nanmedian(W[an]):.1f}/{np.nanpercentile(W[an], 90):.1f}")


def main():
    pts = altura_tempo()
    rel, g = relativa()
    largura()
    with open(FIG / "rotacao_resumo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rel[0]))
        w.writeheader()
        w.writerows(rel)
    # perfil ao longo da fronteira, para o painel de controle
    s, V, Vq, vn, log, rots = ar.v_qc("133004", 0)
    pf = ar.perfil_arco(ar.mediana(Vq, 3), s, 2.0)
    comp = list(csv.DictReader(open(FIG / "rotacao_nucleos_z55.csv", encoding="utf-8")))

    fig = plt.figure(figsize=(19, 11.5), constrained_layout=True)
    gs = fig.add_gridspec(2, 4)
    for k, idx in enumerate((0, 1, 2, 3)):
        q = g[idx]
        ax = fig.add_subplot(gs[0, k])
        pc = ax.pcolormesh(q["x"], q["y"], np.ma.masked_invalid(q["SR"])[:-1, :-1], cmap="RdBu_r", vmin=-40, vmax=40, shading="flat")
        ax.contour(q["x"], q["y"], np.where((q["Z"] >= 45) & (q["C"] < .85), 1.0, 0.0), levels=[.5], colors="k", linewidths=.8)
        ax.plot(q["xc"], q["yc"], "+", color="magenta", ms=14, mew=2)
        ax.set_xlim(q["xc"] - 6, q["xc"] + 6)
        ax.set_ylim(q["yc"] - 6, q["yc"] + 6)
        ax.set_aspect("equal")
        ax.set_title(f"13:30 UTC, {q['ele']}°: V relativa ao núcleo (m/s)", fontweight="bold", fontsize=11)
        ax.set_xlabel("km a leste do radar")
        if k == 0:
            ax.set_ylabel("km ao norte do radar")
        if k == 3:
            fig.colorbar(pc, ax=ax, shrink=.8)
    ax = fig.add_subplot(gs[1, 0])
    rs = [p[0] for p in pf]
    ax.plot(rs, [p[1] for p in pf], "o-", color="0.35")
    al = min(pf, key=lambda p: abs(p[0] - 10.6))
    ax.plot(al[0], al[1], "o", color="#dc2626", ms=11, label="alcance do núcleo")
    ax.set_xlabel("Alcance (km)")
    ax.set_ylabel("dV em arco de 2 km (m/s)")
    ax.set_title("13:30, 0,5°: cisalhamento ao longo da fronteira", fontweight="bold", fontsize=11)
    ax.legend()
    ax.grid(alpha=.3)
    ax = fig.add_subplot(gs[1, 1])
    zz = [float(c["Zmax"]) for c in comp]
    cc = [float(c["CCmed"]) for c in comp]
    ax.scatter(zz, cc, c="0.45", s=38, label="outros núcleos Z ≥ 55 (13:00–14:00)")
    n = [c for c in comp if c["hora"] == "13:30" and abs(float(c["km_aero"])) < 1]
    if n:
        ax.scatter([float(n[0]["Zmax"])], [float(n[0]["CCmed"])], c="#dc2626", s=120, zorder=5, label="núcleo do aeroporto")
    ax.set_xlabel("Z máx (dBZ)")
    ax.set_ylabel("CC mediano")
    ax.set_title("Único núcleo intenso com CC baixo", fontweight="bold", fontsize=11)
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=.3)
    ax = fig.add_subplot(gs[1, 2])
    sc = ax.scatter([p["t"] / 60 for p in pts], [p["alt"] for p in pts], c=[p["Zmax"] for p in pts], cmap="turbo", vmin=45, vmax=66, s=75, edgecolors="k", linewidths=.3)
    fig.colorbar(sc, ax=ax, label="Z máx em 4 km da trilha (dBZ)")
    ax.axvline(0, color="k", ls="--", lw=.8)
    ax.set_xlabel("Minutos em relação à passagem pelo aeroporto")
    ax.set_ylabel("Altura acima do radar (km)")
    ax.set_title("Z ao longo da trilha do núcleo", fontweight="bold", fontsize=11)
    ax.grid(alpha=.3)
    ax = fig.add_subplot(gs[1, 3])
    el = [r["ele"] for r in rel]
    ax.plot([r["SRmax"] for r in rel], el, "o-", color="#dc2626", label="máx. (afastando)")
    ax.plot([-r["SRmin"] for r in rel], el, "o-", color="#2563eb", label="|mín.| (aproximando)")
    ax.set_xlabel("V relativa ao núcleo em 2,5 km (m/s)")
    ax.set_ylabel("Elevação (°)")
    ax.set_title("Simetria do par relativo ao núcleo", fontweight="bold", fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    fig.suptitle("Núcleo de CC baixo do Aeroporto de Chapecó, 04/11/2026: rotação colocalizada? Contorno: Z ≥ 45 e CC < 0,85", fontweight="bold", fontsize=14)
    fig.savefig(FIG / "rotacao_resumo.png", dpi=105)
    plt.close(fig)


if __name__ == "__main__":
    main()
