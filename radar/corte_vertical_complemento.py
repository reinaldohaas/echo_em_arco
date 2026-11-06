# -*- coding: utf-8 -*-
r"""Complemento do corte vertical: a chuva e o CC anômalo são o mesmo objeto?

 A. Por hora e camada, em caixa seguindo o núcleo (-10 a +4 km ao longo do movimento, ±4 km através):
    Z máximo com todos os gates e só com CC >= 0,90; KDP p95 (CC >= 0,90); ZDR mediano em Z >= 50; fração de CC < 0,85 em Z >= 45.
 B. Às 13:30 e 13:36, por elevação: centro do CC anômalo (Z >= 45, CC < 0,85) e da chuva intensa (KDP >= 2,5, CC >= 0,90),
    em km relativos ao núcleo, e Z, ZDR e KDP medianos em cada um.
 C. Coerência Z-KDP: KDP esperado de chuva para o mesmo Z, ajustado nos gates de 13:12 a 13:24 abaixo da fusão.
Saída: radar/figuras/corte_vertical_complemento.txt
"""
import pathlib
import sys
import warnings

import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402
import analise_rotacao_checagens as ck  # noqa: E402

warnings.simplefilter("ignore", RuntimeWarning)
SAIDA = open(AQUI / "figuras" / "corte_vertical_complemento.txt", "w", encoding="utf-8")
HORAS = ("130605", "131205", "131804", "132404", "133004", "133604", "134204")
BANDAS = [(0, .3), (.3, .7), (.7, 1.2), (1.2, 2), (2, 3), (3, 5), (5, 8)]
UX, UY = ck.UX, ck.UY
NU = np.hypot(UX, UY)
EX, EY = UX / NU, UY / NU


def pr(*a):
    print(*a, sep="\t", flush=True)
    print(*a, sep="\t", file=SAIDA, flush=True)


def fatia(h, idx):
    s = ar.volume(h, "dBZ")[idx]
    Z = ar.campo(s)
    C = ar.campo(ar.volume(h, "RhoHV")[idx])
    D = ar.campo(ar.volume(h, "ZDR")[idx])
    K = ar.campo(ar.volume(h, "KDP")[idx])
    x, y, r = ar.geom(s, Z.shape[1])
    xc, yc, _ = ck.pos_nucleo(h, idx)
    su, sv = (x - xc) * EX + (y - yc) * EY, -(x - xc) * EY + (y - yc) * EX
    al = ar.alt_radar(r, s["ele_deg"])
    return s, Z, C, D, K, su, sv, al


def r1(v, n=1):
    return round(float(v), n) if np.isfinite(v) else "nd"


def teste_a():
    pr("[A] hora camada_km n | Zmax Zmax_CC>=.9 | KDPp95 s_do_KDPmax | ZDR_med(Z>=50, CC>=.9) | frac_CC<.85 em Z>=45 | n_Z>=45")
    for h in HORAS:
        acc = {b: [] for b in BANDAS}
        for idx in range(len(ar.volume(h, "dBZ"))):
            s, Z, C, D, K, su, sv, al = fatia(h, idx)
            cx = (su >= -10) & (su <= 4) & (np.abs(sv) <= 4) & np.isfinite(Z)
            for b in BANDAS:
                m = cx & (al >= b[0]) & (al < b[1])
                if m.any():
                    acc[b].append(np.column_stack([Z[m], C[m], D[m], K[m], su[m]]))
        for b in BANDAS:
            if not acc[b]:
                continue
            A = np.vstack(acc[b])
            Z, C, D, K, su = A.T
            lim = C >= .9
            kk = np.where(lim, K, np.nan)
            z50 = lim & (Z >= 50)
            z45 = Z >= 45
            i = np.nanargmax(kk) if np.isfinite(kk).any() else None
            pr(h[:4], f"{b[0]}-{b[1]}", len(Z), r1(np.nanmax(Z)), r1(np.nanmax(Z[lim])) if lim.any() else "nd", r1(np.nanpercentile(K[lim], 95), 2) if lim.any() else "nd",
               r1(su[i]) if i is not None else "nd", r1(np.nanmedian(D[z50]), 2) if z50.any() else "nd",
               r1(np.mean(C[z45] < .85), 2) if z45.sum() >= 5 else "nd", int(z45.sum()))


def teste_b():
    pr("[B] hora ele alt_km | anômalo: n s n_trav Z ZDR KDP Zmax | chuva intensa: n s n_trav Z ZDR KDP")
    for h in ("132404", "133004", "133604", "134204"):
        for idx in range(9):
            s, Z, C, D, K, su, sv, al = fatia(h, idx)
            cx = (su >= -12) & (su <= 6) & (np.abs(sv) <= 6)
            a = cx & (Z >= 45) & (C < .85)
            b = cx & (K >= 2.5) & (C >= .9) & (Z >= 40)
            alt = float(np.nanmedian(al[cx]))
            f = lambda q: [int(q.sum()), r1(np.nanmedian(su[q])), r1(np.nanmedian(sv[q])), r1(np.nanmedian(Z[q])), r1(np.nanmedian(D[q]), 2), r1(np.nanmedian(K[q]), 2)] if q.sum() >= 5 else [int(q.sum())] + ["nd"] * 5
            pr(h[:4], s["ele_deg"], round(alt, 2), *f(a), r1(np.nanmax(Z[a])) if a.any() else "nd", "|", *f(b))


def teste_c():
    zs, ks = [], []
    for h in ("131205", "131804", "132404"):
        for idx in range(6):
            s, Z, C, D, K, su, sv, al = fatia(h, idx)
            m = (su >= -12) & (su <= 6) & (np.abs(sv) <= 6) & (C >= .95) & (Z >= 40) & (Z <= 62) & (al < 2.5) & np.isfinite(K)
            zs.append(Z[m])
            ks.append(K[m])
    zs, ks = np.concatenate(zs), np.concatenate(ks)
    pr("[C] Z | KDP mediano p10 p90 em chuva (13:12 a 13:24, CC>=.95, abaixo de 2,5 km) | n")
    faixas = {}
    for z0 in range(40, 62, 4):
        m = (zs >= z0) & (zs < z0 + 4)
        if m.sum() > 30:
            faixas[z0] = float(np.median(ks[m]))
            pr(f"{z0}-{z0 + 4}", r1(np.median(ks[m]), 2), r1(np.percentile(ks[m], 10), 2), r1(np.percentile(ks[m], 90), 2), int(m.sum()))
    pr("[C2] gates de 13:30 com Z>=55, seguindo o núcleo até 1,5 km do centro do CC anômalo: ele | n Z ZDR CC KDP medianos")
    for idx in range(4):
        s, Z, C, D, K, su, sv, al = fatia("133004", idx)
        a = (su >= -12) & (su <= 6) & (np.abs(sv) <= 6) & (Z >= 45) & (C < .85)
        sc, nc = np.nanmedian(su[a]), np.nanmedian(sv[a])
        m = (np.hypot(su - sc, sv - nc) <= 1.5) & (Z >= 55)
        pr(s["ele_deg"], int(m.sum()), r1(np.nanmedian(Z[m])), r1(np.nanmedian(D[m]), 2), r1(np.nanmedian(C[m]), 3), r1(np.nanmedian(K[m]), 2))


def main():
    teste_a()
    teste_b()
    teste_c()


if __name__ == "__main__":
    main()
