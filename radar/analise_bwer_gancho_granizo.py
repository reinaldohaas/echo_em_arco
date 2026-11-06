# -*- coding: utf-8 -*-
r"""BWER, eco em gancho e granizo, 04/11/2026, 13:00–14:00 UTC.

Grade de 1 km em até 80 km do radar. Cada fatia é deslocada pelo movimento do núcleo (40,4 m/s para leste), para reduzir a
inclinação falsa de um volume que leva 6 min. Níveis de 1 a 10 km acima do radar, por interpolação entre elevações.

BWER (candidato): região com Z < 30 dBZ ou sem eco num nível de 2 a 6 km, de 1 a 100 km², com ao menos 90% do entorno
com Z >= 40 dBZ e mediana de Z máximo acima dela >= 45 dBZ. É um critério simples, não um algoritmo validado.
Gancho: não há critério automático; a figura mostra Z em baixos níveis para exame visual.
Granizo:
  HDR (Aydin et al. 1986): Z - f(ZDR), com f = 27 se ZDR <= 0; 19*ZDR + 27 se 0 < ZDR <= 1,74; 60 se ZDR > 1,74.
  MESH (Witt et al. 1998): usa níveis de 0 °C e -20 °C ASSUMIDOS, pois não há sondagem do dia.
Limites: a menos de ~25 km do radar a coluna é truncada, e o MESH é subestimado (por isso só vale onde a elevação máxima
alcança o nível de -20 °C). Saídas em figuras: bwer_candidatos.csv, granizo_indicadores.csv, gancho_baixos_niveis.png.
"""
import csv
import datetime as dt
import math
import pathlib
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import binary_dilation, label

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from leitor_vol_chapeco import ler_volume_rainbow  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)
VOL = AQUI / "dados_chp_vol"
FIG = AQUI / "figuras"
UX, UY = .0404 * .9987, -.0404 * .05  # km/s
X0, Y0 = -4.9, -9.2
T0 = dt.datetime(2026, 11, 4, 13, 30, 6)
ALT_RADAR = .822
ALC = 80
XS = np.arange(-ALC, ALC + 1, 1.0)
GX, GY = np.meshgrid(XS, XS)
NIVEIS = np.arange(1, 11, .5)
ISO = [(4.0, 7.1), (3.6, 6.7), (4.4, 7.5)]  # 0 °C e -20 °C (km MSL), central e sensibilidade


def amostrar(s, dado, gx, gy):
    r = np.hypot(gx, gy) / math.cos(math.radians(s["ele_deg"]))
    az = np.degrees(np.arctan2(gx, gy)) % 360
    azs = s["azimuths"]
    ir = np.searchsorted(azs, az) % len(azs)
    ant = (ir - 1) % len(azs)
    ir = np.where(np.abs((azs[ant] - az + 180) % 360 - 180) < np.abs((azs[ir] - az + 180) % 360 - 180), ant, ir)
    ib = np.floor(r / s["rstep_km"]).astype(int)
    ok = ib < dado.shape[1]
    out = np.full(gx.shape, np.nan, dtype="f4")
    out[ok] = dado[ir[ok], ib[ok]]
    alt = r * np.sin(np.radians(s["ele_deg"])) + r ** 2 / (2 * 8495)
    alt[~ok] = np.nan
    return out, alt


def cappi(arq, t0):
    fat = sorted(ler_volume_rainbow(arq)["slices"], key=lambda q: q["ele_deg"])
    Zs, Hs = [], []
    for s in fat:
        ts = dt.datetime.fromisoformat(f"{s['date']}T{s['time']}")
        d = (ts - t0).total_seconds()
        z, h = amostrar(s, s["data"], GX + UX * d, GY + UY * d)
        Zs.append(z)
        Hs.append(h)
    Z, H = np.array(Zs), np.array(Hs)
    C = np.full((len(NIVEIS),) + GX.shape, np.nan, dtype="f4")
    amostrado = np.zeros(C.shape, bool)
    for k, nv in enumerate(NIVEIS):
        for i in range(len(fat) - 1):
            m = (H[i] <= nv) & (H[i + 1] > nv)
            if not m.any():
                continue
            amostrado[k][m] = True
            f = (nv - H[i][m]) / (H[i + 1][m] - H[i][m])
            C[k][m] = (Z[i][m] * (1 - f) + Z[i + 1][m] * f)
            # se só um feixe tem eco, usa-o
            a, b = Z[i][m], Z[i + 1][m]
            so = np.where(np.isnan(a), b, np.where(np.isnan(b), a, np.nan))
            cc = C[k][m]
            cc[np.isnan(cc)] = so[np.isnan(cc)]
            C[k][m] = cc
    return C, amostrado


def pos_trilha(tv):
    d = (tv + dt.timedelta(seconds=150) - T0).total_seconds()
    return X0 + UX * d, Y0 + UY * d


def candidatos_bwer(C, amostrado, tv):
    saida = []
    px, py = pos_trilha(tv)
    r = np.hypot(GX, GY)
    for k, nv in enumerate(NIVEIS):
        if not 2 <= nv <= 6:
            continue
        z = C[k]
        fraco = (np.isnan(z) | (z < 30)) & amostrado[k] & (r > 10)
        rot, n = label(fraco)
        for j in range(1, n + 1):
            m = rot == j
            area = int(m.sum())
            if not 1 <= area <= 100:
                continue
            ii, jj = np.nonzero(m)
            if ii.min() == 0 or jj.min() == 0 or ii.max() == len(XS) - 1 or jj.max() == len(XS) - 1:
                continue
            anel = binary_dilation(m, iterations=2) & ~m
            if np.nanmean(np.nan_to_num(z[anel], nan=-99) >= 40) < .9:
                continue
            acima = np.nanmax(C[k + 1:], axis=0)[m] if k + 1 < len(NIVEIS) else np.array([np.nan])
            cap = float(np.nanmedian(acima))
            if not cap >= 45:
                continue
            baixo = np.nanmax(C[:k], axis=0)[m] if k else np.array([np.nan])
            saida.append({"hora": f"{tv:%H:%M}", "nivel_km": nv, "x": round(float(GX[m].mean()), 1), "y": round(float(GY[m].mean()), 1), "r": round(float(r[m].mean()), 1),
                          "area_km2": area, "anel_ge40": round(float(np.mean(np.nan_to_num(z[anel], nan=-99) >= 40)), 2), "Zacima": round(cap, 1),
                          "Zabaixo_mediana": round(float(np.nanmedian(baixo)), 1) if np.isfinite(baixo).any() else "", "dist_trilha": round(float(np.hypot(GX[m].mean() - px, GY[m].mean() - py)), 1)})
    return saida


def mesh(C, h0, h20):
    Hm = (NIVEIS + ALT_RADAR)[:, None, None]
    z = np.nan_to_num(C, nan=-99)
    W = np.clip((z - 40) / 10, 0, 1)
    E = 5e-6 * 10 ** (.084 * np.clip(z, None, 75)) * W
    WT = np.clip((Hm - h0) / (h20 - h0), 0, 1)
    SHI = .1 * np.sum(WT * E * (Hm >= h0) * 500.0, axis=0)
    return 2.54 * np.sqrt(np.maximum(SHI, 0))


def hdr_baixo(arq, tv):
    px, py = pos_trilha(tv)
    h = arq.name[:14]
    sz = ler_volume_rainbow(arq)["slices"]
    sd = ler_volume_rainbow(VOL / f"{h}00ZDR.vol")["slices"]
    sc = ler_volume_rainbow(VOL / f"{h}00RhoHV.vol")["slices"]
    out = []
    for idx in (0, 1, 2):
        nb = int(ALC / sz[idx]["rstep_km"])
        Z, D, C = sz[idx]["data"][:, :nb], sd[idx]["data"][:, :nb], sc[idx]["data"][:, :nb]
        az = np.radians(sz[idx]["azimuths"])[:, None]
        r = sz[idx]["ranges_km"][:nb][None, :]
        x, y = r * np.sin(az), r * np.cos(az)
        f = np.where(D <= 0, 27, np.where(D <= 1.74, 19 * D + 27, 60))
        HDR = Z - f
        m = (Z >= 55) & (r > 5) & np.isfinite(D)
        if not m.any():
            continue
        perto = m & (np.hypot(x - px, y - py) <= 6)
        out.append({"hora": f"{tv:%H:%M}", "ele": sz[idx]["ele_deg"], "n_Z55": int(m.sum()), "frac_ZDR_lt1": round(float(np.mean(D[m] < 1)), 2), "CCmed": round(float(np.nanmedian(C[m])), 2),
                    "HDRmax": round(float(np.nanmax(HDR[m])), 1), "n_HDR_ge15": int((HDR[m] >= 15).sum()), "n_HDR_ge15_CCge90": int(((HDR >= 15) & m & (C >= .9)).sum()),
                    "perto_n": int(perto.sum()), "perto_ZDRmed": round(float(np.nanmedian(D[perto])), 2) if perto.any() else "", "perto_CCmed": round(float(np.nanmedian(C[perto])), 2) if perto.any() else "",
                    "perto_HDRmax": round(float(np.nanmax(HDR[perto])), 1) if perto.any() else ""})
    return out


def main():
    arqs = [a for a in sorted(VOL.glob("*dBZ.vol")) if dt.datetime(2026, 11, 4, 13, 0) <= dt.datetime.strptime(a.name[:14], "%Y%m%d%H%M%S") <= dt.datetime(2026, 11, 4, 14, 0, 30)]
    bw, gr, ms = [], [], []
    baixos = {}
    for a in arqs:
        tv = dt.datetime.strptime(a.name[:14], "%Y%m%d%H%M%S")
        C, am = cappi(a, tv)
        c = candidatos_bwer(C, am, tv)
        bw += c
        gr += hdr_baixo(a, tv)
        px, py = pos_trilha(tv)
        perto = np.hypot(GX - px, GY - py) <= 10
        r = np.hypot(GX, GY)
        lin = [f"{tv:%H:%M}", round(float(np.hypot(px, py)), 1)]
        for h0, h20 in ISO:
            M = mesh(C, h0, h20)
            valido = (r * math.tan(math.radians(19.5)) + r ** 2 / (2 * 8495) + ALT_RADAR) >= h20
            lin += [round(float(np.max(M[valido])), 1), round(float(np.max(M[perto & valido])), 1) if (perto & valido).any() else "sem coluna válida"]
        ms.append(lin)
        print("MESH", *lin, f"| BWER candidatos: {len(c)}", flush=True)
        if tv.strftime("%H%M") in ("1312", "1318", "1324", "1330", "1336"):
            baixos[tv] = (a, px, py)
    with open(FIG / "bwer_candidatos.csv", "w", newline="", encoding="utf-8") as f:
        ch = list(bw[0]) if bw else ["hora"]
        w = csv.DictWriter(f, fieldnames=ch)
        w.writeheader()
        w.writerows(bw)
    print("[BWER] hora nivel x y r area anel Zacima Zabaixo dist_trilha")
    for q in sorted(bw, key=lambda q: q["dist_trilha"])[:30]:
        print("   ", *q.values(), sep="\t")
    print("total candidatos", len(bw), "; a menos de 10 km da trilha:", sum(q["dist_trilha"] <= 10 for q in bw))
    with open(FIG / "granizo_indicadores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gr[0]))
        w.writeheader()
        w.writerows(gr)
    print("[HDR] " + " ".join(gr[0]))
    for q in gr:
        print("   ", *q.values(), sep="\t")
    with open(FIG / "granizo_mesh.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hora_utc", "r_trilha_km", "MESHmm_dominio_iso4.0", "MESHmm_10km_trilha_iso4.0", "dominio_iso3.6", "trilha_iso3.6", "dominio_iso4.4", "trilha_iso4.4"])
        w.writerows(ms)

    fig, eixos = plt.subplots(2, 5, figsize=(21, 9), constrained_layout=True)
    for col, (tv, (a, px, py)) in enumerate(sorted(baixos.items())):
        fat = ler_volume_rainbow(a)["slices"]
        for lin, idx in enumerate((0, 2)):
            s = fat[idx]
            nb = int(ALC / s["rstep_km"])
            az = np.radians(s["azimuths"])[:, None]
            r = s["ranges_km"][:nb][None, :] * math.cos(math.radians(s["ele_deg"]))
            x, y = r * np.sin(az), r * np.cos(az)
            ax = eixos[lin, col]
            pc = ax.pcolormesh(x, y, np.ma.masked_invalid(s["data"][:, :nb])[:-1, :-1], cmap="turbo", vmin=10, vmax=70, shading="flat")
            d = (dt.datetime.fromisoformat(f"{s['date']}T{s['time']}") - T0).total_seconds()
            ax.plot(X0 + UX * d, Y0 + UY * d, "+", color="white", ms=16, mew=2.5)
            ax.plot(-4.54, -9.45, "*", color="yellow", mec="black", ms=12)
            ax.set_xlim(X0 + UX * d - 18, X0 + UX * d + 18)
            ax.set_ylim(Y0 + UY * d - 18, Y0 + UY * d + 18)
            ax.set_aspect("equal")
            ax.set_title(f"{tv:%H:%M} UTC, {s['ele_deg']}°", fontweight="bold")
            ax.tick_params(labelsize=7)
    fig.colorbar(pc, ax=eixos, shrink=.7, label="Z (dBZ)")
    fig.suptitle("Z em baixos níveis seguindo o núcleo (+), para exame de eco em gancho. ★ aeroporto", fontweight="bold")
    fig.savefig(FIG / "gancho_baixos_niveis.png", dpi=105)


if __name__ == "__main__":
    main()
