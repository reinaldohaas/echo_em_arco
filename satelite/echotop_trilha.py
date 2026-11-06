# -*- coding: utf-8 -*-
r"""Echo Top ao longo da trilha do núcleo: separa queda real do topo do truncamento perto do radar.

Em cada volume, usa a posição prevista pelo movimento ajustado (40,4 m/s para leste; extrapolação fora de 13:30–13:36).
Compara o topo no disco de 5 km com a altura máxima alcançável ali. Se os dois coincidem, o topo está truncado e é só
um limite inferior. Saída: figuras/echotop_trilha.csv.
"""
import csv
import datetime as dt
import pathlib
import sys

import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI), str(AQUI.parent / "radar")]
import compor_echotop_satelite as ce  # noqa: E402
from compor_radar_satelite import RADAR, VOL, grade  # noqa: E402

UX, UY = .0404 * .9987, -.0404 * .05
X0, Y0 = -4.9, -9.2
T0 = dt.datetime(2026, 11, 4, 13, 30, 6)


def main():
    lons, lats, dist, az = grade()
    mlon, mlat = np.meshgrid(lons, lats)
    kx = 111.32 * np.cos(np.radians(RADAR[1]))
    x, y = (mlon - RADAR[0]) * kx, (mlat - RADAR[1]) * 111.132
    cab = ["radar_utc", "r_km", "alcance_km", "ET18_max", "ET40_max", "ET50_max_nao_calc", "truncado18", "truncado40"]
    linhas = []
    print(*[c for c in cab if "nao_calc" not in c], sep="\t")
    for arq in sorted(VOL.glob("*dBZ.vol")):
        tr = ce.t_radar(arq)
        if not dt.datetime(2026, 11, 4, 13, 0) <= tr <= dt.datetime(2026, 11, 4, 13, 54, 30):
            continue
        s = (tr - T0).total_seconds() + 150  # meio do volume
        px, py = X0 + UX * s, Y0 + UY * s
        m = np.hypot(x - px, y - py) <= 5
        tp, alc = ce.echo_top(arq, dist, az)
        amax = float(np.nanmax(alc[m]))
        e18, e40 = float(np.nanmax(tp[18][m])), float(np.nanmax(tp[40][m]))
        lin = [f"{tr:%H:%M}", round(float(np.hypot(px, py)), 1), round(amax, 1), round(e18, 1), round(e40, 1), e18 >= amax - .3, e40 >= amax - .3]
        linhas.append(lin)
        print(*lin, sep="\t", flush=True)
    with open(AQUI / "figuras" / "echotop_trilha.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([c for c in cab if "nao_calc" not in c])
        w.writerows(linhas)


if __name__ == "__main__":
    main()
