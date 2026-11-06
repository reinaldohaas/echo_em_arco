# -*- coding: utf-8 -*-
r"""Complementos de teste_microexplosao.py.

 A. O salto de 0,5° e 0,9° às 13:30: posição, V bruta e V corrigida do maior par em 1 km; quantas dobras cada lado recebeu.
 B. Perfil do vento atrás da linha: V na caixa 2 a 8 km a oeste do núcleo, por elevação. Um máximo raso indica saída de ar
    junto ao solo. A caixa é grande para reduzir o peso de gates isolados.
Saída: radar/figuras/teste_microexplosao_2_saida.txt
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
SAIDA = open(AQUI / "figuras" / "teste_microexplosao_2_saida.txt", "w", encoding="utf-8")


def pr(*a):
    print(*a, sep="\t", flush=True)
    print(*a, sep="\t", file=SAIDA, flush=True)


def main():
    pr("[A. maior par em ~1 km até 3 km do núcleo, 13:30] ele | az1 az2 r_km | Vbruta1 Vbruta2 | Vcorr1 Vcorr2 | dobras1 dobras2 | 2Vn | n_regiao1 n_regiao2")
    for idx in (0, 1, 2):
        s, V, Vq, vn, log, rots = ar.v_qc("133004", idx)
        x, y, r = ar.geom(s, V.shape[1])
        xc, yc, _ = ck.pos_nucleo("133004", idx)
        d = np.hypot(x - xc, y - yc)
        dv = Vq - np.roll(Vq, -6, axis=0)
        m = (d <= 3) & np.isfinite(dv)
        ii, jj = np.nonzero(m)
        for o in np.argsort(-np.abs(dv[m]))[:6:2]:
            i, j = ii[o], jj[o]
            i2 = (i + 6) % V.shape[0]
            k1, k2 = (Vq[i, j] - V[i, j]) / (2 * vn), (Vq[i2, j] - V[i2, j]) / (2 * vn)
            n1, n2 = int((rots == rots[i, j]).sum()), int((rots == rots[i2, j]).sum())
            pr(s["ele_deg"], round(float(s["azimuths"][i]), 1), round(float(s["azimuths"][i2]), 1), round(float(r[i, j]), 2),
               round(float(V[i, j]), 1), round(float(V[i2, j]), 1), round(float(Vq[i, j]), 1), round(float(Vq[i2, j]), 1),
               round(float(k1), 1), round(float(k2), 1), round(2 * vn, 1), n1, n2)

    pr("[B. vento atrás da linha: caixa de 2 a 8 km a oeste do núcleo, ±4 km N-S] hora ele alt_km n | V_mediana p10 p90 | frac_semV")
    for h in ("132404", "133004", "133604", "134204"):
        for idx in range(8):
            s, V, Vq, vn, log, rots = ar.v_qc(h, idx)
            x, y, r = ar.geom(s, V.shape[1])
            xc, yc, _ = ck.pos_nucleo(h, idx)
            cx = (x - xc >= -8) & (x - xc <= -2) & (np.abs(y - yc) <= 4)
            v = Vq[cx & np.isfinite(Vq)]
            if len(v) < 30:
                continue
            rm = float(np.median(r[cx]))
            pr(h[:4], s["ele_deg"], round(float(ar.alt_radar(rm, s["ele_deg"])), 2), len(v), round(float(np.median(v)), 1),
               round(float(np.percentile(v, 10)), 1), round(float(np.percentile(v, 90)), 1), round(float(np.mean(~np.isfinite(Vq[cx]))), 2))


if __name__ == "__main__":
    main()
