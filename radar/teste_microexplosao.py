# -*- coding: utf-8 -*-
r"""Testes da crítica à rotação: a assinatura é vórtice ou deformação da linha? Há assinatura de microexplosão?

 1. Escala: cisalhamento azimutal em função da separação, no núcleo e no resto da varredura. A 10,6 km do radar um raio
    tem cerca de 0,2 km; um vórtice tornádico apareceria como salto grande em poucos raios.
 2. Divergência ao longo do radial: a fronteira é quase radial, logo a variação de V ao longo do alcance é a parte
    observável do espalhamento ao longo da linha. Critério usual: dV >= 10 m/s em até 4 km.
 3. CC por faixa de alcance: separa a queda de CC do núcleo de um efeito geral de proximidade do radar.
 4. Z por altura ao longo da trilha do núcleo, para ver se o máximo desce até o solo.
Saída: radar/figuras/teste_microexplosao_saida.txt. Convenção: V < 0 aproxima-se do radar.
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
SEPS = [.25, .5, 1, 1.5, 2, 3, 4]
SAIDA = open(AQUI / "figuras" / "teste_microexplosao_saida.txt", "w", encoding="utf-8")


def pr(*a):
    print(*a, sep="\t", flush=True)
    print(*a, sep="\t", file=SAIDA, flush=True)


def escala(h, idx):
    s, V, Vq, *_ = ar.v_qc(h, idx)
    x, y, r = ar.geom(s, V.shape[1])
    xc, yc, _ = ck.pos_nucleo(h, idx)
    d = np.hypot(x - xc, y - yc)
    dphi = np.radians(np.median(np.diff(s["azimuths"])))
    rc = np.hypot(xc, yc)
    linhas = []
    for sep in SEPS:
        n = max(1, int(round(sep / (rc * dphi))))
        dv = Vq - np.roll(Vq, -n, axis=0)  # > 0: V diminui com o azimute, sentido horário
        perto = (d <= 3) & np.isfinite(dv)
        fora = (d > 6) & (r > 5) & (r < 30) & np.isfinite(dv)
        linhas.append((sep, n, np.nanmax(np.abs(dv[perto])) if perto.any() else np.nan, np.nanpercentile(np.abs(dv[perto]), 95) if perto.any() else np.nan,
                       np.nanpercentile(np.abs(dv[fora]), 99.9), np.nanmax(np.abs(dv[fora]))))
    semv = float(np.mean(~np.isfinite(Vq[d <= 1.5])))
    return s["ele_deg"], rc, rc * dphi, semv, linhas


def divergencia(h, idx):
    s, V, Vq, *_ = ar.v_qc(h, idx)
    Vs = ar.mediana(Vq, 3)
    x, y, r = ar.geom(s, V.shape[1])
    xc, yc, _ = ck.pos_nucleo(h, idx)
    d = np.hypot(x - xc, y - yc)
    passo = s["rstep_km"]
    out = []
    for km in (1, 2, 4):
        n = int(round(km / passo))
        dv = np.roll(Vs, -n, axis=1) - Vs  # > 0: divergência ao longo do radial
        dv[:, -n:] = np.nan
        perto = (d <= 6) & np.isfinite(dv)
        fora = (d > 8) & (r > 5) & (r < 45) & np.isfinite(dv)
        if not perto.any():
            out.append((km, np.nan, np.nan, np.nan, np.nan))
            continue
        out.append((km, float(np.nanmax(dv[perto])), float(np.nanmin(dv[perto])), float(np.nanpercentile(dv[fora], 99.5)), float(np.nanpercentile(dv[fora], .5))))
    return s["ele_deg"], out


def main():
    pr("[1. ESCALA, 13:30] ele alcance_km km_por_raio frac_semV_1,5km | sep_km raios max_nucleo p95_nucleo p99,9_resto max_resto")
    for idx in range(7):
        e, rc, kmr, semv, ls = escala("133004", idx)
        pr(e, round(rc, 1), round(kmr, 3), round(semv, 2))
        for l in ls:
            pr("   ", *[round(float(q), 2) for q in l])

    pr("[2. DIVERGÊNCIA AO LONGO DO RADIAL, disco de 6 km do núcleo] hora ele km max_div max_conv | p99,5 e p0,5 do resto")
    for h in ("131804", "132404", "133004", "133604", "134204"):
        for idx in (0, 1, 2):
            e, out = divergencia(h, idx)
            for km, a, b, c, f in out:
                pr(h[:4], e, km, round(a, 1), round(b, 1), round(c, 1), round(f, 1))

    pr("[3. CC x ALCANCE, 0,5°, gates Z>=50] hora faixa_km n frac_CC<0,85 CC_mediana")
    faixas = [(5, 10), (10, 15), (15, 25), (25, 40), (40, 60)]
    for h in ar.horas()[::2] + ["133004", "133604"]:
        s = ar.volume(h, "dBZ")[0]
        Z, C = ar.campo(s), ar.campo(ar.volume(h, "RhoHV")[0])
        n = min(Z.shape[1], C.shape[1])
        Z, C = Z[:, :n], C[:, :n]
        _, _, r = ar.geom(s, n)
        for a, b in faixas:
            m = (Z >= 50) & (r >= a) & (r < b) & np.isfinite(C)
            if m.sum() >= 5:
                pr(h[:4], f"{a}-{b}", int(m.sum()), round(float(np.mean(C[m] < .85)), 2), round(float(np.median(C[m])), 2))
        for k in [("dBZ"), ("RhoHV")]:
            ar._cache.pop((h, k), None)

    pr("[4. Z POR ALTURA, disco de 5 km da trilha] hora faixa_km Zmax Zp95 n>=55 n>=60")
    bandas = [(0, .3), (.3, .7), (.7, 1.2), (1.2, 2), (2, 3), (3, 5), (5, 8)]
    for h in ("130605", "131205", "131804", "132404", "133004", "133604", "134204"):
        por = {b: [] for b in bandas}
        for idx in range(len(ar.volume(h, "dBZ"))):
            s = ar.volume(h, "dBZ")[idx]
            Z = ar.campo(s)
            x, y, r = ar.geom(s, Z.shape[1])
            xc, yc, _ = ck.pos_nucleo(h, idx)
            m = (np.hypot(x - xc, y - yc) <= 5) & np.isfinite(Z)
            al = ar.alt_radar(r, s["ele_deg"])
            for b in bandas:
                q = m & (al >= b[0]) & (al < b[1])
                por[b] += list(Z[q])
        for b in bandas:
            v = np.array(por[b])
            if len(v) >= 10:
                pr(h[:4], f"{b[0]}-{b[1]}", float(v.max()), round(float(np.percentile(v, 95)), 1), int((v >= 55).sum()), int((v >= 60).sum()))


if __name__ == "__main__":
    main()
