# -*- coding: utf-8 -*-
r"""A rotação desceu? Procura o maior cisalhamento em arco de 2 km perto da trilha, em todas as elevações, 13:06–13:36 UTC.

Em cada fatia, compara o máximo a menos de 6 km da posição prevista com o restante da mesma fatia.
Fatias em que o par não é horário ou não supera o p90 do restante não contam como rotação localizada.
A trilha antes de 13:30 é extrapolada com o movimento ajustado (40,4 m/s), então a posição é incerta.
Saída: figuras/descida_rotacao.csv e descida_rotacao.png.
"""
import csv
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
UX, UY, X0, Y0, T0 = ck.UX, ck.UY, ck.X0, ck.Y0, ck.T0
ar.RMAX = 60.0


def fatia(h, idx):
    s, V, Vq, vn, log, rots = ar.v_qc(h, idx)
    Vs = ar.mediana(Vq, 3)
    xc, yc = X0, Y0
    for _ in range(4):
        tt = (ar.t_gate(h, idx, xc, yc) - T0).total_seconds()
        xc, yc = X0 + UX * tt, Y0 + UY * tt
    rc = float(np.hypot(xc, yc))
    azc = float(np.degrees(np.arctan2(xc, yc)) % 360)
    if rc * np.cos(np.radians(s["ele_deg"])) > Vs.shape[1] * s["rstep_km"]:
        return None
    rs_loc = np.arange(max(3, rc - 6), rc + 6.01, 1.0)
    dang = np.degrees(6 / max(rc, 3))
    pf = ar.perfil_arco(Vs, s, 2.0, setor=(azc - dang, azc + dang), rs=rs_loc)
    pf = [p for p in pf if p[2] is not None]
    # só pares ciclônicos: V maior no azimute menor
    cic = [p for p in pf if p[3] > p[4]]
    ger = [p for p in ar.perfil_arco(Vs, s, 2.0, setor=(0, 359), rs=np.arange(3, 45, 1.0)) if p[2] is not None and abs(p[0] - rc) >= 6]
    fora = np.array([p[1] for p in ger])
    alt = float(ar.alt_radar(rc, s["ele_deg"]))
    q = {"hora": h[:4], "ele": s["ele_deg"], "alt_rad_km": round(alt, 2), "t_min": round(tt / 60, 1), "x_prev": round(xc, 1), "y_prev": round(yc, 1),
         "dV_cic": None, "r": None, "az": None, "a": None, "b": None, "dist_prev": None,
         "fora_med": round(float(np.median(fora)), 1) if len(fora) else None, "fora_p90": round(float(np.percentile(fora, 90)), 1) if len(fora) else None}
    if cic:
        m = max(cic, key=lambda p: p[1])
        arad = np.radians(m[2] + np.degrees(1.0 / m[0]))
        px, py = m[0] * np.sin(arad), m[0] * np.cos(arad)
        q.update(dV_cic=round(m[1], 1), r=m[0], az=round(m[2], 1), a=round(m[3], 1), b=round(m[4], 1), dist_prev=round(float(np.hypot(px - xc, py - yc)), 1))
    return q


def main():
    linhas = []
    for h in ("130605", "131205", "131804", "132404", "133004", "133604"):
        for idx in range(len(ar.volume(h, "V"))):
            q = fatia(h, idx)
            if q:
                linhas.append(q)
                print(*q.values(), sep="\t", flush=True)
    with open(FIG / "descida_rotacao.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    fig, ax = plt.subplots(figsize=(11, 6.2), constrained_layout=True)
    val = [l for l in linhas if l["dV_cic"] is not None]
    razao = [l["dV_cic"] / max(l["fora_p90"], 1) for l in val]
    sc = ax.scatter([l["t_min"] for l in val], [l["alt_rad_km"] for l in val], c=razao, cmap="RdYlBu_r", vmin=.5, vmax=1.5, s=[max(25, l["dV_cic"] * 3) for l in val], edgecolors="k", linewidths=.4)
    fig.colorbar(sc, ax=ax, label="dV ciclônico perto da trilha / p90 do restante da fatia")
    ax.axvline(0, color="k", ls="--")
    ax.set_xlabel("Minutos em relação à passagem pelo aeroporto (13:30:06 UTC)")
    ax.set_ylabel("Altura acima do radar (km)")
    ax.set_title("Rotação localizada descendo? Tamanho proporcional a dV em 2 km", fontweight="bold")
    ax.grid(alpha=.3)
    fig.savefig(FIG / "descida_rotacao.png", dpi=120)


if __name__ == "__main__":
    main()
