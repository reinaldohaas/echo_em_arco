# -*- coding: utf-8 -*-
r"""Reconcilia analise_rotacao.py (controle ao longo da fronteira) e teste_microexplosao.py (controle no resto da varredura).

Mesmo estimador no núcleo e em discos independentes de 3 km de raio, a cada 6 km, com alcance de 5 a 45 km:
maior dV entre gates separados de 1 ou 2 km em azimute, após mediana 3x3, só no sentido horário (ciclônico no HS).
Três versões: toda a V corrigida; só a região sem dobra (k = 0), que não depende do dealias; e controle apenas em discos
que têm V < -5 e V > +5 m/s, ou seja, fronteiras de vento.
"""
import pathlib
import sys
import warnings

import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_rotacao as ar  # noqa: E402
import analise_rotacao_checagens as ck  # noqa: E402
from analise_velocidade import dealias, nyquist  # noqa: E402,F401

warnings.simplefilter("ignore", RuntimeWarning)
SAIDA = open(AQUI / "figuras" / "teste_reconciliacao_saida.txt", "w", encoding="utf-8")


def pr(*a):
    print(*a, sep="\t", flush=True)
    print(*a, sep="\t", file=SAIDA, flush=True)


def sem_dobra(V, Vq):
    """Mantém só os gates em que a correção não alterou a velocidade bruta."""
    out = Vq.copy()
    out[~(np.isfinite(V) & np.isfinite(Vq) & (np.abs(V - Vq) < .01))] = np.nan
    return out


def disco_max(dv, Vs, x, y, cx, cy):
    m = np.hypot(x - cx, y - cy) <= 3
    if not m.any():
        return None
    q = dv[m]
    if np.isfinite(q).sum() < 15:
        return None
    return float(np.nanmax(q)), float(np.nanmin(Vs[m])), float(np.nanmax(Vs[m]))


def teste(h, idx, base):
    s, V, Vq, *_ = ar.v_qc(h, idx)
    campo = Vq if base == "corrigida" else sem_dobra(V, Vq)
    Vs = ar.mediana(campo, 3)
    x, y, r = ar.geom(s, V.shape[1])
    xc, yc, _ = ck.pos_nucleo(h, idx)
    cs = [c for c in ar.nucleos(h, idx, min_g=6) if np.hypot(c["x"] - xc, c["y"] - yc) < 3]
    if cs:
        c = max(cs, key=lambda q: q["n"])
        xc, yc = c["x"], c["y"]
    dphi = np.radians(np.median(np.diff(s["azimuths"])))
    out = []
    grade = [(a, b) for a in np.arange(-45, 45.1, 6) for b in np.arange(-45, 45.1, 6)
             if 5 <= np.hypot(a, b) <= 45 and np.hypot(a - xc, b - yc) >= 6]
    for sep in (1.0, 2.0):
        # separação em km no alcance de cada gate
        n = np.maximum(1, np.round(sep / np.maximum(r * dphi, .01)).astype(int))
        ii, jj = np.indices(Vs.shape)
        dv = Vs - Vs[(ii + n) % Vs.shape[0], jj]  # > 0: V diminui com o azimute, sentido horário
        nuc = disco_max(dv, Vs, x, y, xc, yc)
        todos, front = [], []
        for a, b in grade:
            q = disco_max(dv, Vs, x, y, a, b)
            if q:
                todos.append(q[0])
                if q[1] < -5 and q[2] > 5:
                    front.append(q[0])
        todos, front = np.array(todos), np.array(front)
        if nuc is None or not len(front):
            out.append((sep, None))
            continue
        out.append((sep, round(nuc[0], 1), round(nuc[1], 1), round(nuc[2], 1), len(todos), round(float(np.median(todos)), 1), round(float(np.percentile(todos, 90)), 1), round(float(todos.max()), 1),
                    int((todos >= nuc[0]).sum()), len(front), round(float(np.median(front)), 1), round(float(np.percentile(front, 90)), 1), round(float(front.max()), 1), int((front >= nuc[0]).sum())))
    return s["ele_deg"], out


def main():
    pr("hora base ele sep_km | dV_nucleo Vmin Vmax | todos: n med p90 max discos>=nucleo | fronteiras: n med p90 max discos>=nucleo")
    for h in ("132404", "133004", "133604"):
        for base in ("corrigida", "sem_dobra"):
            for idx in range(7):
                e, out = teste(h, idx, base)
                for o in out:
                    pr(h[:4], base, e, *o)


if __name__ == "__main__":
    main()
