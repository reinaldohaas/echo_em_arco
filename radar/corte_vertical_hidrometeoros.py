# -*- coding: utf-8 -*-
r"""Corte vertical e hidrometeoros no núcleo do Aeroporto de Chapecó (04/11/2026).

 A. Nível de fusão estimado pelo próprio radar: perfis (QVP) em elevações altas, com o mínimo de CC e o máximo de Z e ZDR.
 B. Viés de ZDR: mediana em chuva fraca, abaixo do nível de fusão.
 C. Coluna seguindo o núcleo, por volume e elevação: Z, ZDR, CC e KDP nos gates de Z alto, em disco de 2 km.
 D. Corte ao longo do movimento, relativo ao núcleo, em cada elevação no horário dela. Classes por regras simples.

A posição do núcleo é a do ajuste de 13:30 (40 m/s para leste); longe de 13:30 ela é extrapolação, assim como supor
o mesmo movimento em todas as alturas. Alturas são acima do radar (822 m); o aeroporto está cerca de 180 m abaixo dele.
As classes são limiares escolhidos aqui para leitura, não um classificador validado.
Saídas: radar/figuras/corte_vertical_saida.txt, corte_vertical_coluna.csv, corte_vertical_hidrometeoros.png
"""
import csv
import pathlib
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402
import analise_rotacao_checagens as ck  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)
FIG = AQUI / "figuras"
SAIDA = open(FIG / "corte_vertical_saida.txt", "w", encoding="utf-8")
HORAS = ("131205", "131804", "132404", "133004", "133604", "134204")
VARS = ("dBZ", "ZDR", "RhoHV", "KDP")
ZF_PADRAO = 3.8


def pr(*a):
    print(*a, sep="\t", flush=True)
    print(*a, sep="\t", file=SAIDA, flush=True)


def amostra(s, x, y):
    e = np.radians(s["ele_deg"])
    r = np.hypot(x, y) / np.cos(e)
    az = np.degrees(np.arctan2(x, y)) % 360
    azs = s["azimuths"]
    i = np.abs(((azs[None, :] - az[:, None] + 180) % 360) - 180).argmin(axis=1)
    j = np.floor(r / s["rstep_km"]).astype(int)
    ok = j < s["data"].shape[1]
    v = np.full(x.shape, np.nan)
    v[ok] = s["data"][i[ok], j[ok]]
    return v


def teste_a():
    pr("[A. QVP] hora ele | alt_km do CC mínimo, CC | alt do Z máximo, Z | alt do ZDR máximo, ZDR (2 a 7 km, r até 40 km)")
    achados = []
    for h in ("120004", "124804", "143004", "144804", "150004"):
        for var in VARS[:3]:
            ar.volume(h, var)
        sl = {v: ar.volume(h, v) for v in VARS[:3]}
        for idx, s in enumerate(sl["dBZ"]):
            if s["ele_deg"] < 6 or s["ele_deg"] > 13:
                continue
            nb = min(int(40 / s["rstep_km"]), s["data"].shape[1])
            Z = s["data"][:, :nb]
            C = sl["RhoHV"][idx]["data"][:, :nb]
            D = sl["ZDR"][idx]["data"][:, :nb]
            bom = Z >= 10
            n = bom.sum(axis=0)
            def med(a):
                return np.nanmedian(np.where(bom, a, np.nan), axis=0)
            mZ, mC, mD = med(Z), med(C), med(D)
            alt = ar.alt_radar(s["ranges_km"][:nb] * np.cos(np.radians(s["ele_deg"])), s["ele_deg"])
            f = (alt >= 2) & (alt <= 7) & (n >= 0.3 * Z.shape[0])
            if f.sum() < 5:
                continue
            ic, iz, id_ = np.nanargmin(np.where(f, mC, np.nan)), np.nanargmax(np.where(f, mZ, np.nan)), np.nanargmax(np.where(f, mD, np.nan))
            pr(h[:4], s["ele_deg"], round(float(alt[ic]), 2), round(float(mC[ic]), 3), round(float(alt[iz]), 2), round(float(mZ[iz]), 1),
               round(float(alt[id_]), 2), round(float(mD[id_]), 2))
            achados.append((float(alt[ic]), float(mC[ic]), float(alt[iz]), float(alt[id_])))
    # Banda brilhante plausível: CC mínimo nítido, com Z e ZDR máximos à mesma altura.
    nit = [a for a in achados if a[1] < .975 and abs(a[0] - a[2]) < .8 and abs(a[0] - a[3]) < .8]
    if nit:
        zf = float(np.median([a[0] for a in nit]))
        pr("perfis com banda brilhante coerente", len(nit), "de", len(achados), "; altura mediana do CC mínimo", round(zf, 2), "km acima do radar")
        return zf + 0.25, True
    pr("nenhum perfil com banda brilhante coerente; uso", ZF_PADRAO, "km, da figura antiga e sem verificação")
    return ZF_PADRAO, False


def teste_b(zf):
    pr("[B. viés de ZDR] hora ele | n, mediana de ZDR em 20<=Z<=28 dBZ, CC>=0.97, alt<", round(zf - 1, 1), "km, 10<r<60 km")
    for h in ("120004", "133004", "143004"):
        tot = []
        for idx in range(0, 6):
            s, d, c = ar.volume(h, "dBZ")[idx], ar.volume(h, "ZDR")[idx], ar.volume(h, "RhoHV")[idx]
            Z, D, C = ar.campo(s), ar.campo(d), ar.campo(c)
            nb = Z.shape[1]
            rg = s["ranges_km"][:nb]
            al = ar.alt_radar(rg, s["ele_deg"])[None, :]
            m = (Z >= 20) & (Z <= 28) & (C >= .97) & (al < zf - 1) & (rg[None, :] > 10)
            if m.sum() > 50:
                tot.append(D[m])
                pr(h[:4], s["ele_deg"], int(m.sum()), round(float(np.nanmedian(D[m])), 2))
        if tot:
            pr(h[:4], "todas", sum(map(len, tot)), round(float(np.nanmedian(np.concatenate(tot))), 2))


def teste_c(zf):
    pr("[C. coluna, disco de 2 km seguindo o núcleo; gates com Z>=p90 do disco] hora ele alt_km r_km n Zmax Zp90 | ZDR CC KDP medianos | frac_CC<.85 entre Z>=45 | CC p10 | ZDR p10 p90")
    linhas = []
    for h in HORAS:
        for idx, s in enumerate(ar.volume(h, "dBZ")):
            xc, yc, _ = ck.pos_nucleo(h, idx)
            Z = ar.campo(s)
            x, y, r = ar.geom(s, Z.shape[1])
            d = np.hypot(x - xc, y - yc)
            m = (d <= 2) & np.isfinite(Z)
            if m.sum() < 8:
                continue
            al = float(ar.alt_radar(np.hypot(xc, yc), s["ele_deg"]))
            if al > 9:
                continue
            C = ar.campo(ar.volume(h, "RhoHV")[idx])
            D = ar.campo(ar.volume(h, "ZDR")[idx])
            K = ar.campo(ar.volume(h, "KDP")[idx])
            p90 = np.nanpercentile(Z[m], 90)
            q = m & (Z >= p90)
            z45 = m & (Z >= 45)
            f = float(np.mean(C[z45] < .85)) if z45.sum() >= 5 else np.nan
            ln = [h[:4], s["ele_deg"], round(al, 2), round(float(np.hypot(xc, yc)), 1), int(m.sum()), round(float(np.nanmax(Z[m])), 1), round(float(p90), 1),
                  round(float(np.nanmedian(D[q])), 2), round(float(np.nanmedian(C[q])), 3), round(float(np.nanmedian(K[q])), 2), round(f, 2),
                  round(float(np.nanpercentile(C[m], 10)), 3), round(float(np.nanpercentile(D[m], 10)), 2), round(float(np.nanpercentile(D[m], 90)), 2)]
            pr(*ln)
            linhas.append(ln)
    with open(FIG / "corte_vertical_coluna.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow("hora_UTC ele_graus alt_km_acima_radar r_km n Zmax Zp90 ZDR_med CC_med KDP_med frac_CC_baixo CC_p10 ZDR_p10 ZDR_p90".split())
        w.writerows(linhas)


CLASSES = ["sem eco", "neve/agregados", "gelo denso/graupel", "granizo acima da fusão", "chuva", "chuva forte, gotas grandes",
           "chuva com granizo", "CC anômalo"]
CORES = ["#0b1220", "#7dd3fc", "#2563eb", "#e879f9", "#4ade80", "#facc15", "#f97316", "#ffffff"]


def classifica(Z, D, C, al, zf):
    c = np.zeros(Z.shape, int)
    eco = np.isfinite(Z) & (Z >= 10)
    gelo = al >= zf
    c[eco & gelo] = 1
    c[eco & gelo & (Z >= 35)] = 2
    c[eco & gelo & (Z >= 50)] = 3
    c[eco & ~gelo] = 4
    c[eco & ~gelo & (Z >= 45) & (D >= 2)] = 5
    c[eco & ~gelo & (Z >= 50) & (D < 2)] = 6
    c[eco & ~gelo & (Z >= 45) & (C < .85)] = 7
    return c


def figura(zf):
    S = np.arange(-15, 10.01, .25)
    ux, uy = ck.UX, ck.UY
    nu = np.hypot(ux, uy)
    ex, ey = ux / nu, uy / nu
    nx, ny = -ey, ex
    cmaps = {"dBZ": ("turbo", 20, 70, "Z (dBZ)"), "ZDR": ("RdYlBu_r", -1, 4, "ZDR (dB)"), "RhoHV": ("viridis", .65, 1, "CC"), "KDP": ("magma", -1, 5, "KDP (°/km)")}
    fig, axs = plt.subplots(5, len(HORAS), figsize=(4.0 * len(HORAS), 15), sharex=True, sharey=True, constrained_layout=True)
    fig.patch.set_facecolor("#0b1220")
    plt.rcParams["text.color"] = "white"
    cm_cl = ListedColormap(CORES)
    nm_cl = BoundaryNorm(np.arange(-.5, len(CORES)), len(CORES))
    pcm = {}
    for c, h in enumerate(HORAS):
        sl = {v: ar.volume(h, v) for v in VARS}
        for idx in range(len(sl["dBZ"])):
            ele = sl["dBZ"][idx]["ele_deg"]
            xc, yc, _ = ck.pos_nucleo(h, idx)
            x, y = xc + S * ex, yc + S * ey
            rg = np.hypot(x, y)
            al = ar.alt_radar(rg, ele)
            if al.min() > 9:
                continue
            campos = {}
            for v in VARS:
                pilha = [amostra(sl[v][idx], x + o * nx, y + o * ny) for o in (-.5, 0, .5)]
                campos[v] = np.nanmedian(np.array(pilha), axis=0)
            mei = rg * np.radians(.5)
            z2 = np.vstack([al - mei, al + mei])
            s2 = np.vstack([S, S])
            for lin, v in enumerate(VARS):
                nome, a, b, _ = cmaps[v]
                pcm[v] = axs[lin, c].pcolormesh(s2, z2, np.ma.masked_invalid(campos[v][None, :-1]), cmap=nome, vmin=a, vmax=b, shading="flat")
            cl = classifica(campos["dBZ"], campos["ZDR"], campos["RhoHV"], al, zf)
            pcm["cl"] = axs[4, c].pcolormesh(s2, z2, cl[None, :-1], cmap=cm_cl, norm=nm_cl, shading="flat")
        axs[0, c].set_title(f"{h[:2]}:{h[2:4]} UTC ({int(h[:2]) - 3}:{h[2:4]} local)", color="white", fontweight="bold")
        for lin in range(5):
            a = axs[lin, c]
            a.set_facecolor("#111a2e")
            a.axhline(zf, color="white", ls="--", lw=.9)
            a.axvline(0, color="white", ls=":", lw=.8)
            a.set_xlim(-15, 10)
            a.set_ylim(0, 9)
            a.tick_params(colors="white")
            for sp in a.spines.values():
                sp.set_color("#475569")
        axs[4, c].set_xlabel("km relativos ao núcleo (leste →)", color="white")
    for lin, v in enumerate(VARS):
        axs[lin, 0].set_ylabel("km acima do radar", color="white")
        cb = fig.colorbar(pcm[v], ax=axs[lin, :], shrink=.9, pad=.008)
        cb.set_label(cmaps[v][3], color="white")
        cb.ax.tick_params(colors="white")
    axs[4, 0].set_ylabel("km acima do radar", color="white")
    cb = fig.colorbar(pcm["cl"], ax=axs[4, :], shrink=.95, pad=.008, ticks=range(len(CLASSES)))
    cb.ax.set_yticklabels(CLASSES, fontsize=8, color="white")
    fig.suptitle(f"Corte ao longo do movimento, seguindo o núcleo. Tracejado: fusão estimada ({zf:.1f} km). Classes por regras simples, não validadas.", color="white", fontsize=15, fontweight="bold")
    fig.savefig(FIG / "corte_vertical_hidrometeoros.png", dpi=110, facecolor=fig.get_facecolor())
    pr("figura", FIG / "corte_vertical_hidrometeoros.png")


def main():
    pr("ajuste do núcleo: UX UY (km/s)", ck.UX, ck.UY)
    pr("aeroporto: x y (km), r, altura do feixe a 0,5° acima do radar", ar.AX, ar.AY, round(float(np.hypot(ar.AX, ar.AY)), 2), round(float(ar.alt_radar(np.hypot(ar.AX, ar.AY), .5)), 3))
    zf, _ = teste_a()
    teste_b(zf)
    teste_c(zf)
    figura(zf)


if __name__ == "__main__":
    main()
