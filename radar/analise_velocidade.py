# -*- coding: utf-8 -*-
r"""Velocidade radial em torno do Aeroporto de Chapecó, 04/11/2026, 13:12–13:48 UTC.

1. Corrige o aliasing por regiões contíguas: une gates vizinhos com |dV| <= LIMIAR e escolhe o múltiplo de
   2*Vn que minimiza o salto na fronteira com as regiões já resolvidas. O salto restante é registrado:
   salto pequeno após a correção indica aliasing; salto grande indica descontinuidade real ou erro de dual-PRF.
   Regiões com menos de MIN_GATES gates ficam mascaradas, não são "corrigidas".
2. Subtrai um vento uniforme ajustado no entorno, pois perto do radar a geometria gera cisalhamento aparente.
3. Mede, em janelas de JANELA_KM, o par (Vmin, Vmax): orientação azimutal (rotação) ou radial (divergência).

Convenção: V < 0 aproxima-se do radar.
"""
import csv
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from leitor_vol_chapeco import ler_volume_rainbow  # noqa: E402

VOL = AQUI / "dados_chp_vol"
FIG = AQUI / "figuras"
RADAR = (-52.60374, -27.04879)
AERO = (-52.6496, -27.1338)
COS = np.cos(np.radians(RADAR[1]))
AX, AY = (AERO[0] - RADAR[0]) * 111.32 * COS, (AERO[1] - RADAR[1]) * 111.132
HORAS = ["131205", "131804", "132404", "133004", "133604", "134204", "134804"]
ELEV_IDX = [0, 1, 2, 3, 4]
RMAX_KM = 45.0
LIMIAR = 10.0
MIN_GATES = 12
RAIO_BUSCA_KM = 12.0
JANELA_KM = 3.0


def nome(h, var):
    return VOL / f"20261104{h}00{var}.vol"


def nyquist(arq, idx):
    """Lê o intervalo de V de cada fatia direto do XML."""
    import re
    raw = arq.read_bytes()
    x = raw[:raw.find(b"<!-- END XML -->")].decode("utf-8", "replace")
    return float(re.findall(r'<dynv min="[^"]+" max="([^"]+)"', x)[idx])


def dealias(V, vn):
    ny, nx = V.shape
    ok = np.isfinite(V)
    ids = -np.ones(V.shape, int)
    ids[ok] = np.arange(ok.sum())
    # vizinhos em alcance
    ia, ib = ids[:, :-1].ravel(), ids[:, 1:].ravel()
    va, vb = V[:, :-1].ravel(), V[:, 1:].ravel()
    # vizinhos em azimute, com volta em 360°
    ic, id_ = ids.ravel(), np.roll(ids, -1, axis=0).ravel()
    vc, vd = V.ravel(), np.roll(V, -1, axis=0).ravel()
    A = np.r_[ia, ic]
    B = np.r_[ib, id_]
    VA = np.r_[va, vc]
    VB = np.r_[vb, vd]
    val = (A >= 0) & (B >= 0)
    A, B, VA, VB = A[val], B[val], VA[val], VB[val]
    liga = np.abs(VA - VB) <= LIMIAR
    n = int(ok.sum())
    g = coo_matrix((np.ones(liga.sum()), (A[liga], B[liga])), shape=(n, n))
    _, rot = connected_components(g, directed=False)
    tam = np.bincount(rot)
    offs = {int(np.argmax(tam)): 0.0}
    RA, RB = rot[A], rot[B]
    dif = RA != RB
    RA, RB, VA, VB = RA[dif], RB[dif], VA[dif], VB[dif]
    log = []
    pendentes = {int(r) for r in np.nonzero(tam >= MIN_GATES)[0]} - set(offs)
    while pendentes:
        melhor, cont = None, 0
        res = np.array(sorted(offs))
        a_res, b_res = np.isin(RA, res), np.isin(RB, res)
        # conta fronteiras entre regiões pendentes e resolvidas
        c1 = RB[a_res & ~b_res]
        c2 = RA[b_res & ~a_res]
        cands, conts = np.unique(np.r_[c1, c2], return_counts=True)
        for r, c in zip(cands, conts):
            if int(r) in pendentes and c > cont:
                melhor, cont = int(r), int(c)
        if melhor is None:
            break
        m1 = (RB == melhor) & a_res
        m2 = (RA == melhor) & b_res
        ref = np.r_[VA[m1] + np.array([offs[int(x)] for x in RA[m1]]), VB[m2] + np.array([offs[int(x)] for x in RB[m2]])]
        ali = np.r_[VB[m1], VA[m2]]
        k = int(np.round(np.median(ref - ali) / (2 * vn)))
        offs[melhor] = k * 2 * vn
        log.append((melhor, int(tam[melhor]), k, float(np.median(np.abs(ref - ali))), float(np.median(np.abs(ref - ali - k * 2 * vn))), int(cont)))
        pendentes.discard(melhor)
    saida = np.full(V.shape, np.nan, dtype="f4")
    rots = -np.ones(V.shape, int)
    rots[ok] = rot
    for r, o in offs.items():
        m = rots == r
        saida[m] = V[m] + o
    return saida, rots, log


def carregar(h, idx):
    out = {}
    for var in ("V", "dBZ", "RhoHV", "ZDR", "W", "KDP"):
        s = ler_volume_rainbow(nome(h, var))["slices"][idx]
        out[var] = s
    return out


def cortar(s):
    nb = int(RMAX_KM / s["rstep_km"])
    return s["data"][:, :nb].astype("f8")


def xy(s, n_bins):
    az = np.radians(s["azimuths"])[:, None]
    r = s["ranges_km"][:n_bins][None, :] * np.cos(np.radians(s["ele_deg"]))
    x, y = r * np.sin(az), r * np.cos(az)
    return x, y, np.broadcast_to(r, x.shape)


def vento_uniforme(x, y, r, Vd):
    """Ajuste V = u*sin(az) + v*cos(az) (em termos de x/r e y/r) a menos de 25 km, fora de 5 km do aeroporto."""
    m = np.isfinite(Vd) & (r > 3) & (r < 25) & (np.hypot(x - AX, y - AY) > 5)
    A = np.c_[(x[m] / r[m]), (y[m] / r[m])]
    co, *_ = np.linalg.lstsq(A, Vd[m], rcond=None)
    res = Vd - (co[0] * x / r + co[1] * y / r)
    return co, res


def pares(V, x, y, r, s):
    """Procura o maior par (Vmax - Vmin) em janela de JANELA_KM, nas duas orientações, perto do aeroporto."""
    daz = np.median(np.diff(s["azimuths"]))
    drr = s["rstep_km"]
    nrad = max(1, int(round(JANELA_KM / drr)))
    perto = np.hypot(x - AX, y - AY) <= RAIO_BUSCA_KM
    melhor = {"azimutal": (0, None), "radial": (0, None)}
    for (i, j) in zip(*np.nonzero(perto & np.isfinite(V))):
        naz = max(1, int(round(JANELA_KM / max(.1, r[i, j] * np.radians(daz)))))
        v0 = V[i, j]
        for sinal, orient in ((naz, "azimutal"), (nrad, "radial")):
            for k in range(1, sinal + 1):
                if orient == "azimutal":
                    ii, jj = (i + k) % V.shape[0], j
                else:
                    ii, jj = i, j + k
                    if jj >= V.shape[1]:
                        break
                v1 = V[ii, jj]
                if not np.isfinite(v1):
                    continue
                d = abs(v1 - v0)
                if d > melhor[orient][0]:
                    dist = float(np.hypot(x[i, j] - x[ii, jj], y[i, j] - y[ii, jj]))
                    melhor[orient] = (float(d), {"v0": float(v0), "v1": float(v1), "dist": dist,
                                                 "x": float(x[i, j]), "y": float(y[i, j]),
                                                 "km_aero": float(np.hypot(x[i, j] - AX, y[i, j] - AY)),
                                                 "sinal": float(np.sign(v1 - v0))})
    return melhor


def amostra_aeroporto(campo, x, y, raio=1.5):
    m = np.hypot(x - AX, y - AY) <= raio
    return campo[m]


def main():
    FIG.mkdir(exist_ok=True)
    linhas = []
    guardar = {}
    for h in HORAS:
        for idx in ELEV_IDX:
            c = carregar(h, idx)
            vn = nyquist(nome(h, "V"), idx)
            V = cortar(c["V"])
            Vd, rots, log = dealias(V, vn)
            x, y, r = xy(c["V"], V.shape[1])
            co, res = vento_uniforme(x, y, r, Vd)
            p = pares(res, x, y, r, c["V"])
            perto = np.hypot(x - AX, y - AY) <= RAIO_BUSCA_KM
            ele = c["V"]["ele_deg"]
            alt = float(np.hypot(AX, AY) * np.sin(np.radians(ele)) + np.hypot(AX, AY) ** 2 / (2 * 8495))
            viz = {v: amostra_aeroporto(cortar(c[v]), x, y) for v in ("dBZ", "RhoHV", "ZDR", "W")}
            vz = amostra_aeroporto(V, x, y)
            dobr = [l for l in log if l[2] != 0]
            saltos = [l for l in log if l[4] > LIMIAR and l[1] >= MIN_GATES]
            az, rd = p["azimutal"], p["radial"]
            linhas.append({
                "hora": f"{h[:2]}:{h[2:4]}", "ele": ele, "alt_km": round(alt, 2), "vn": round(vn, 1),
                "u": round(float(co[0]), 1), "v": round(float(co[1]), 1),
                "V_min_12km": round(float(np.nanmin(Vd[perto])), 1), "V_max_12km": round(float(np.nanmax(Vd[perto])), 1),
                "n_dobradas": len(dobr), "n_saltos": len(saltos),
                "dV_azim": round(az[0], 1), "dist_azim": round(az[1]["dist"], 2) if az[1] else None,
                "sinal_azim": az[1]["sinal"] if az[1] else None, "km_azim": round(az[1]["km_aero"], 1) if az[1] else None,
                "dV_rad": round(rd[0], 1), "dist_rad": round(rd[1]["dist"], 2) if rd[1] else None,
                "sinal_rad": rd[1]["sinal"] if rd[1] else None, "km_rad": round(rd[1]["km_aero"], 1) if rd[1] else None,
                "frac_sem_V_1.5km": round(float(np.mean(~np.isfinite(vz))), 2),
                "Z_max": round(float(np.nanmax(viz["dBZ"])), 1), "CC_min": round(float(np.nanmin(viz["RhoHV"])), 2),
                "CC_med": round(float(np.nanmedian(viz["RhoHV"])), 2), "ZDR_med": round(float(np.nanmedian(viz["ZDR"])), 2),
                "W_max": round(float(np.nanmax(viz["W"])), 1),
            })
            print(*linhas[-1].values(), sep="\t", flush=True)
            if idx in (0, 1):
                guardar[(h, idx)] = dict(c=c, V=V, Vd=Vd, res=res, x=x, y=y, log=log, rots=rots, vn=vn)
            if h == "133004" and idx == 0:
                print("  regioes dobradas/saltos 13:30 0,5°:")
                for reg, n, k, antes, depois, cont in sorted(log, key=lambda l: -l[1])[:25]:
                    m = rots == reg
                    print(f"   n={n} k={k} salto_antes={antes:.1f} salto_depois={depois:.1f} fronteira={cont} "
                          f"km_aero={np.hypot(x[m].mean() - AX, y[m].mean() - AY):.1f} V={np.nanmedian(V[m]):.1f}")

    with open(FIG / "velocidade_tabela.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    # figura: 3 horários x 5 campos, a 0,5°
    hs = ["132404", "133004", "133604"]
    fig, eixos = plt.subplots(3, 5, figsize=(22, 13), constrained_layout=True)
    for lin, h in enumerate(hs):
        g = guardar[(h, 0)]
        c = g["c"]
        x, y = g["x"], g["y"]
        campos = [("dBZ", cortar(c["dBZ"]), "turbo", 10, 70), ("V bruta", g["V"], "RdBu_r", -32, 32),
                  ("V corrigida", g["Vd"], "RdBu_r", -50, 50), ("Resíduo sem vento uniforme", g["res"], "RdBu_r", -35, 35),
                  ("RhoHV", cortar(c["RhoHV"]), "viridis", .6, 1)]
        for ax, (tit, dado, cm, a, b) in zip(eixos[lin], campos):
            pc = ax.pcolormesh(x, y, np.ma.masked_invalid(dado)[:-1, :-1], cmap=cm, vmin=a, vmax=b, shading="flat")
            ax.plot(AX, AY, "*", color="yellow", mec="black", ms=14)
            ax.plot(0, 0, "^", color="black", ms=8)
            ax.set_xlim(AX - 14, AX + 14)
            ax.set_ylim(AY - 14, AY + 14)
            ax.set_aspect("equal")
            ax.set_title(f"{h[:2]}:{h[2:4]} UTC, 0,5°: {tit}", fontsize=11, fontweight="bold")
            fig.colorbar(pc, ax=ax, shrink=.8)
    fig.savefig(FIG / "velocidade_painel.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
