# -*- coding: utf-8 -*-
r"""Há rotação colocalizada com o núcleo de CC baixo do Aeroporto de Chapecó (04/11/2026, 13:30 UTC)?

Etapas (saídas em radar/figuras, prefixo rotacao_):
 1. Clutter: gates de CC baixo recorrentes nos 31 volumes, a 0,5°.
 2. Movimento: centroide do núcleo x horário real da fatia e do raio, no volume de 13:30 e nos seguintes.
 3. Perfil vertical: as 14 elevações, seguindo o núcleo com o movimento ajustado.
 4. Rotação: V corrigida, sem regiões com salto residual na fronteira, em arcos de 1 e 2 km.
    Controle: a mesma medida nos outros alcances da mesma fronteira e no mesmo alcance em outros horários.
 5. Robustez: LIMIAR do dealias, filtro de mediana, dados sem correção, erros de dual-PRF.
 6. Granizo x detritos: compara o núcleo com os demais núcleos de Z >= 55 dBZ, fora do clutter, 13:00–14:00 UTC.

Convenção: V < 0 aproxima-se do radar; sentido horário (ciclônico no HS) quando V diminui com o azimute.
Como a fronteira é quase radial neste trecho, o radar vê a componente ao longo dela: rotação e cisalhamento
linear produzem o mesmo sinal azimutal, e a convergência através dela não é observável.
"""
import csv
import datetime as dt
import pathlib
import re
import struct
import sys
import warnings
import zlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import binary_dilation, label

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analise_velocidade as av  # noqa: E402
from leitor_vol_chapeco import ler_volume_rainbow  # noqa: E402

VOL = AQUI / "dados_chp_vol"
FIG = AQUI / "figuras"
AX, AY = av.AX, av.AY
RAD_LON, RAD_LAT = av.RADAR
RMAX = 60.0
warnings.simplefilter("ignore", RuntimeWarning)
_cache = {}


def horas():
    return sorted({p.name[8:14] for p in VOL.glob("*dBZ.vol")})


def volume(h, var):
    k = (h, var)
    if k not in _cache:
        _cache[k] = ler_volume_rainbow(VOL / f"20261104{h}00{var}.vol")["slices"]
    return _cache[k]


def campo(s):
    return s["data"][:, :int(RMAX / s["rstep_km"])].astype("f8")


def geom(s, nb):
    az = np.radians(s["azimuths"])[:, None]
    r = (s["ranges_km"][:nb] * np.cos(np.radians(s["ele_deg"])))[None, :]
    x, y = r * np.sin(az), r * np.cos(az)
    return x, y, np.broadcast_to(r, x.shape)


def tempos_fatias(h):
    """Devolve, por fatia, (início, duração estimada, azimute do primeiro raio)."""
    raw = (VOL / f"20261104{h}00V.vol").read_bytes()
    fim = raw.find(b"<!-- END XML -->")
    x, b = raw[:fim].decode("utf-8", "replace"), raw[fim:]
    t = [dt.datetime.fromisoformat(s) for s in re.findall(r'<slicedata datetimehighaccuracy="([^"]+)"', x)]
    ids = [int(i) for i in re.findall(r'<rayinfo refid="startangle" blobid="(\d+)"', x)]
    saida = []
    for k, (ti, bid) in enumerate(zip(t, ids)):
        m = re.search(rb'<BLOB\s+blobid="%d"\s+size="(\d+)"\s+compression="(\w+)"\s*>\r?\n?' % bid, b)
        ch = b[m.end():m.end() + int(m.group(1))]
        dec = zlib.decompress(ch[4:]) if m.group(2) == b"qt" else ch
        az0 = struct.unpack(">H", dec[:2])[0] * 360 / 65536
        dur = (t[k + 1] - ti).total_seconds() if k + 1 < len(t) else (ti - t[k - 1]).total_seconds()
        saida.append((ti, dur, az0))
    return saida


def t_gate(h, idx, xc, yc):
    ti, dur, az0 = tempos_fatias(h)[idx]
    az = np.degrees(np.arctan2(xc, yc)) % 360
    return ti + dt.timedelta(seconds=((az - az0) % 360) / 360 * dur)


def alt_radar(r_km, ele):
    return r_km * np.sin(np.radians(ele)) + r_km ** 2 / (2 * 8495)


def mediana(V, n=3):
    if n <= 1:
        return V.copy()
    k = n // 2
    p = np.pad(V, ((k, k), (k, k)), mode="wrap")
    jan = sliding_window_view(p, (n, n))
    q = np.isfinite(jan).sum(axis=(2, 3))
    m = np.nanmedian(jan, axis=(2, 3))
    m[q < (n * n) // 2 + 1] = np.nan
    return m


def v_qc(h, idx, limiar=10.0):
    """V corrigida, sem as regiões cuja fronteira continua com salto acima do limiar após o melhor múltiplo de 2*Vn."""
    s = volume(h, "V")[idx]
    V = campo(s)
    vn = av.nyquist(VOL / f"20261104{h}00V.vol", idx)
    av.LIMIAR = limiar
    Vd, rots, log = av.dealias(V, vn)
    ruins = [l[0] for l in log if l[4] > limiar]
    Vq = Vd.copy()
    Vq[np.isin(rots, ruins)] = np.nan
    return s, V, Vq, vn, log, rots


def mascara_clutter():
    conta, n = None, 0
    for h in horas():
        Z, C = campo(volume(h, "dBZ")[0]), campo(volume(h, "RhoHV")[0])
        ruim = (Z >= 30) & (C < .85)
        conta = ruim.astype(int) if conta is None else conta + ruim
        n += 1
        del _cache[(h, "dBZ")], _cache[(h, "RhoHV")]
    frac = conta / n
    return binary_dilation(frac >= .25, iterations=2), frac


def nucleos(h, idx, clutter=None, zlim=45, cclim=.85, min_g=8, rmin=5):
    sz, sc = volume(h, "dBZ")[idx], volume(h, "RhoHV")[idx]
    Z, C = campo(sz), campo(sc)
    x, y, r = geom(sz, Z.shape[1])
    mas = (Z >= zlim) & (C < cclim) & (r > rmin)
    if clutter is not None and idx == 0:
        mas &= ~clutter[:mas.shape[0], :mas.shape[1]] if clutter.shape == mas.shape else mas
    rot, n = label(mas, structure=np.ones((3, 3)))
    saida = []
    for k in range(1, n + 1):
        m = rot == k
        if m.sum() >= min_g:
            saida.append({"n": int(m.sum()), "x": float(x[m].mean()), "y": float(y[m].mean()), "mask": m, "Zmax": float(np.nanmax(Z[m]))})
    return saida


def stats_disco(h, idx, xc, yc, raio=1.5):
    sz = volume(h, "dBZ")[idx]
    Z = campo(sz)
    x, y, r = geom(sz, Z.shape[1])
    d = np.hypot(x - xc, y - yc)
    m = d <= raio
    an = (d > 3) & (d <= 6)
    S = {v: campo(volume(h, v)[idx]) for v in ("RhoHV", "ZDR", "KDP", "W", "V")}
    C = S["RhoHV"]
    return {"Zmax": np.nanmax(Z[m]), "Zp90": np.nanpercentile(Z[m], 90), "CCmed": np.nanmedian(C[m]), "fCC85": np.nanmean(C[m] < .85),
            "ZDRmed": np.nanmedian(S["ZDR"][m]), "KDPmed": np.nanmedian(S["KDP"][m]), "Wmed": np.nanmedian(S["W"][m]),
            "fsemV": float(np.mean(~np.isfinite(S["V"][m]))), "gates": int(m.sum()),
            "Zanel": np.nanpercentile(Z[an], 90), "CCanel": np.nanmedian(C[an]), "Wanel": np.nanmedian(S["W"][an])}


def perfil_arco(Vs, s, arco_km, setor=(120, 300), rs=np.arange(3, 31, 1.0)):
    """Em cada alcance: maior (P95-P5) de V em arco de arco_km, numa faixa de ±0,5 km em alcance."""
    azs = s["azimuths"]
    rr = s["ranges_km"][:Vs.shape[1]]
    saida = []
    for r0 in rs:
        jj = np.nonzero(np.abs(rr - r0) <= .5)[0]
        if not len(jj):
            continue
        nr = max(2, int(round(arco_km / (r0 * np.radians(1.0)))))
        melhor = (0, None, None, None)
        for i in np.nonzero((azs >= setor[0]) & (azs <= setor[1]))[0]:
            ii = np.arange(i, i + nr + 1) % len(azs)
            bloco = Vs[np.ix_(ii, jj)]
            ini, fim = bloco[:2].ravel(), bloco[-2:].ravel()
            if np.isfinite(bloco).mean() < .4 or np.isfinite(ini).sum() < 3 or np.isfinite(fim).sum() < 3:
                continue
            a, b = np.nanmedian(ini), np.nanmedian(fim)
            d = abs(b - a)
            if d > melhor[0]:
                melhor = (float(d), float(azs[i]), float(a), float(b))
        saida.append((float(r0),) + melhor)
    return saida


def par_no_alcance(perfil, r0):
    return min(perfil, key=lambda p: abs(p[0] - r0))


def main():
    FIG.mkdir(exist_ok=True)
    H = horas()
    # 1. clutter
    clutter, frac = mascara_clutter()
    sz = volume("133004", "dBZ")[0]
    Z = campo(sz)
    x, y, r = geom(sz, Z.shape[1])
    dA = np.hypot(x - AX, y - AY) <= 1.5
    print(f"[clutter] fração máx. de volumes com CC baixo a 1,5 km do aeroporto: {np.nanmax(frac[dA]):.2f}; mediana {np.nanmedian(frac[dA]):.2f}; clutter marcado no disco: {clutter[dA].mean():.2f}")

    # 2. movimento no volume de 13:30
    pos = []
    for idx in range(8):
        cs = nucleos("133004", idx, clutter)
        perto = [c for c in cs if np.hypot(c["x"] - (-4.6 + idx * 1.1), c["y"] + 9.4) < 3.5]
        c = max(perto, key=lambda q: q["n"])
        t = t_gate("133004", idx, c["x"], c["y"])
        pos.append((idx, volume("133004", "dBZ")[idx]["ele_deg"], t, c["x"], c["y"], c["n"], c["Zmax"]))
    t0 = pos[0][2]
    ts = np.array([(p[2] - t0).total_seconds() for p in pos])
    xs, ys = np.array([p[3] for p in pos]), np.array([p[4] for p in pos])
    ux, x0 = np.polyfit(ts, xs, 1)
    uy, y0 = np.polyfit(ts, ys, 1)
    rms = float(np.sqrt(np.mean((xs - (ux * ts + x0)) ** 2 + (ys - (uy * ts + y0)) ** 2)))
    print(f"[movimento 13:30] u={ux:.1f} v={uy:.1f} m/s*1e-3 km/s => {np.hypot(ux, uy) * 1000:.1f} m/s, resíduo {rms:.2f} km, t0={t0:%H:%M:%S}")
    for p, tt in zip(pos, ts):
        print(f"   {p[1]:>4}° t+{tt:5.0f}s x={p[3]:6.2f} y={p[4]:6.2f} gates={p[5]:3d} Zmax={p[6]:.1f}")

    # 3. perfil vertical, seguindo o núcleo
    print("[perfil vertical] ele alt_rad t x y | Zmax Zp90 CCmed fCC<.85 ZDR KDP W semV | anel: Zp90 CC W")
    perfil = []
    n_el = len(volume("133004", "dBZ"))
    for idx in range(n_el):
        s = volume("133004", "dBZ")[idx]
        xc, yc = x0, y0
        for _ in range(3):
            tt = (t_gate("133004", idx, xc, yc) - t0).total_seconds()
            xc, yc = x0 + ux * tt, y0 + uy * tt
        e = stats_disco("133004", idx, xc, yc)
        al = float(alt_radar(np.hypot(xc, yc), s["ele_deg"]))
        perfil.append((s["ele_deg"], al, e))
        print(f"   {s['ele_deg']:>4}° {al:5.2f} {tt:5.0f}s {xc:6.1f} {yc:6.1f} | {e['Zmax']:5.1f} {e['Zp90']:5.1f} {e['CCmed']:.2f} {e['fCC85']:.2f} {e['ZDRmed']:5.2f} {e['KDPmed']:5.2f} {e['Wmed']:4.1f} {e['fsemV']:.2f} | {e['Zanel']:5.1f} {e['CCanel']:.2f} {e['Wanel']:.1f}")

    # 4. rastreamento entre volumes, sem forçar: todos os núcleos a 0,5° a menos de 15 km da posição prevista
    print("[rastreio 0,5°] hora: núcleos fora do clutter, a menos de 15 km da previsão")
    trilha = []
    i0 = H.index("133004")
    for h in H[i0 - 3:i0 + 6]:
        tv = dt.datetime.strptime("20261104" + h, "%Y%m%d%H%M%S")
        dtt = (tv - t0.replace(microsecond=0)).total_seconds()
        px, py = x0 + ux * dtt, y0 + uy * dtt
        cs = nucleos(h, 0, clutter, min_g=6, rmin=3)
        cs = sorted([c for c in cs if np.hypot(c["x"] - px, c["y"] - py) < 15], key=lambda c: -c["n"])
        txt = "; ".join(f"({c['x']:.1f},{c['y']:.1f}) n={c['n']} Z={c['Zmax']:.0f}" for c in cs[:5])
        print(f"   {h[:2]}:{h[2:4]} prev=({px:.1f},{py:.1f}) {txt or 'nenhum'}")
        trilha.append((h, px, py, cs))

    # 5. rotação: perfil ao longo da fronteira
    print("[rotação] por volume e elevação: dV em arco de 1 e 2 km no alcance do núcleo x outros alcances da fronteira")
    linhas = []
    hov = {}
    for h in H[i0 - 2:i0 + 3]:
        for idx in range(0, 3):
            s, V, Vq, vn, log, rots = v_qc(h, idx)
            Vs = mediana(Vq, 3)
            for arco in (1.0, 2.0):
                pf = perfil_arco(Vs, s, arco)
                if idx == 0 and arco == 1.0:
                    hov[h] = pf
                if h == "133004":
                    cx, cy = pos[idx][3], pos[idx][4]
                else:
                    cx, cy = None, None
                r0 = float(np.hypot(cx, cy)) if cx is not None else 10.5
                alvo = par_no_alcance(pf, r0)
                outros = np.array([p[1] for p in pf if abs(p[0] - r0) >= 3])
                linhas.append({"hora": f"{h[:2]}:{h[2:4]}", "ele": s["ele_deg"], "arco_km": arco, "r_km": alvo[0], "az": alvo[2], "dV": round(alvo[1], 1),
                               "a": alvo[3], "b": alvo[4], "ctl_med": round(float(np.median(outros)), 1), "ctl_p90": round(float(np.percentile(outros, 90)), 1),
                               "ctl_max": round(float(np.max(outros)), 1), "perc_no_perfil": round(float(np.mean(outros < alvo[1]) * 100))})
    with open(FIG / "rotacao_perfil_fronteira.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    for l in linhas:
        print("   ", *l.values(), sep="\t")

    # 6. robustez no núcleo de 13:30
    print("[robustez] 13:30, disco de 2,5 km do centroide. LIMIAR, mediana -> Vmin Vmax dV dist sentido")
    rob = []
    for idx in (0, 1):
        cx, cy = pos[idx][3], pos[idx][4]
        for lim in (6., 8., 10., 14.):
            for nm in (1, 3, 5):
                s, V, Vq, vn, log, rots = v_qc("133004", idx, lim)
                Vs = mediana(Vq, nm)
                x, y, r = geom(s, V.shape[1])
                m = (np.hypot(x - cx, y - cy) <= 2.5) & np.isfinite(Vs)
                ii, jj = np.nonzero(m)
                v = Vs[ii, jj]
                a, b = int(np.argmin(v)), int(np.argmax(v))
                dif = (s["azimuths"][ii[b]] - s["azimuths"][ii[a]] + 180) % 360 - 180
                dist = float(np.hypot(x[ii[a], jj[a]] - x[ii[b], jj[b]], y[ii[a], jj[a]] - y[ii[b], jj[b]]))
                rob.append((s["ele_deg"], lim, nm, v[a], v[b], v[b] - v[a], dist, "horário" if dif < 0 else "anti-horário"))
                print(f"   {s['ele_deg']}° lim={lim:.0f} med={nm} Vmin={v[a]:.1f} Vmax={v[b]:.1f} dV={v[b] - v[a]:.1f} dist={dist:.2f} {rob[-1][-1]}")
    # dados sem correção
    for idx in (0, 1):
        s = volume("133004", "V")[idx]
        V = campo(s)
        x, y, r = geom(s, V.shape[1])
        m = (np.hypot(x - pos[idx][3], y - pos[idx][4]) <= 2.5) & np.isfinite(V)
        print(f"   bruto {s['ele_deg']}°: min={V[m].min():.1f} max={V[m].max():.1f}; fração de V>15 (dobrada?)={np.mean(V[m] > 15):.2f}; fração V<-15={np.mean(V[m] < -15):.2f}")

    # 7. erros de dual-PRF
    print("[dual-PRF] fração de gates cujo desvio da mediana 5x5 cai em 20,8±3 ou 31,25±3 m/s")
    for idx in (0, 1):
        s, V, Vq, vn, log, rots = v_qc("133004", idx)
        M = mediana(Vq, 5)
        d = np.abs(Vq - M)
        x, y, r = geom(s, V.shape[1])
        for nome, m in (("disco 3 km", np.hypot(x - pos[idx][3], y - pos[idx][4]) <= 3),
                        ("controle 5-25 km", (r > 5) & (r < 25) & (np.hypot(x - pos[idx][3], y - pos[idx][4]) > 6))):
            q = d[m & np.isfinite(d)]
            print(f"   {s['ele_deg']}° {nome}: n={len(q)} 20,8={np.mean(np.abs(q - 20.83) < 3):.3f} 31,25={np.mean(np.abs(q - 31.25) < 3):.3f} |d|>10={np.mean(q > 10):.3f}")

    # 8. núcleo x outros núcleos intensos
    print("[Z>=55] núcleos 13:00–14:00, 0,5°, fora do clutter e a mais de 5 km do radar: hora x y n Zmax CCmed fCC<.8 ZDRmed KDPmed Wmed fTDS")
    comp = []
    for h in H[H.index("130005"):H.index("140004") + 1]:
        sz = volume(h, "dBZ")[0]
        Z = campo(sz)
        C, D, K, W = [campo(volume(h, v)[0]) for v in ("RhoHV", "ZDR", "KDP", "W")]
        x, y, r = geom(sz, Z.shape[1])
        mas = (Z >= 55) & (r > 5) & ~clutter[:Z.shape[0], :Z.shape[1]]
        rot, n = label(mas, structure=np.ones((3, 3)))
        for k in range(1, n + 1):
            m = rot == k
            if m.sum() < 5:
                continue
            viz = binary_dilation(m, iterations=1)
            ftds = float(np.nanmean((Z[viz] > 45) & (C[viz] < .8) & (D[viz] < .5)))
            comp.append({"hora": f"{h[:2]}:{h[2:4]}", "x": round(float(x[m].mean()), 1), "y": round(float(y[m].mean()), 1), "r": round(float(r[m].mean()), 1), "n": int(m.sum()), "Zmax": float(np.nanmax(Z[m])),
                         "CCmed": round(float(np.nanmedian(C[viz])), 2), "fCC80": round(float(np.nanmean(C[viz] < .8)), 2), "ZDRmed": round(float(np.nanmedian(D[viz])), 2),
                         "KDPmed": round(float(np.nanmedian(K[viz])), 2), "Wmed": round(float(np.nanmedian(W[viz])), 1), "fTDS": round(ftds, 2),
                         "km_aero": round(float(np.hypot(x[m].mean() - AX, y[m].mean() - AY)), 1)})
    comp.sort(key=lambda c: -c["n"])
    with open(FIG / "rotacao_nucleos_z55.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(comp[0]))
        w.writeheader()
        w.writerows(comp)
    print(f"   total {len(comp)} núcleos; CCmed quartis {np.percentile([c['CCmed'] for c in comp], [25, 50, 75])}; fTDS quartis {np.percentile([c['fTDS'] for c in comp], [25, 50, 75])}")
    for c in comp[:30]:
        print("   ", *c.values(), sep="\t")

    # figura: evolução seguindo o núcleo
    hs = [h for h in H[i0 - 1:i0 + 3]]
    fig, eixos = plt.subplots(4, 4, figsize=(18, 17), constrained_layout=True)
    for col, h in enumerate(hs):
        s, V, Vq, vn, log, rots = v_qc(h, 0)
        Zc, Cc, Dc = [campo(volume(h, v)[0]) for v in ("dBZ", "RhoHV", "ZDR")]
        x, y, r = geom(s, V.shape[1])
        tv = dt.datetime.strptime("20261104" + h, "%Y%m%d%H%M%S")
        dtt = (tv - t0.replace(microsecond=0)).total_seconds()
        px, py = x0 + ux * dtt, y0 + uy * dtt
        for lin, (tit, dado, cm, a, b) in enumerate([("Z (dBZ)", Zc, "turbo", 20, 70), ("V corrigida (m/s)", Vq, "RdBu_r", -50, 50), ("V bruta (m/s)", V, "RdBu_r", -32, 32), ("RhoHV", Cc, "viridis", .5, 1)]):
            ax = eixos[lin, col]
            pc = ax.pcolormesh(x, y, np.ma.masked_invalid(dado)[:-1, :-1], cmap=cm, vmin=a, vmax=b, shading="flat")
            ax.contour(x, y, np.where((Zc >= 45) & (Cc < .85), 1.0, 0.0), levels=[.5], colors="k", linewidths=.6)
            ax.plot(AX, AY, "*", color="yellow", mec="black", ms=13)
            ax.plot(px, py, "+", color="magenta", ms=14, mew=2)
            ax.set_xlim(px - 10, px + 10)
            ax.set_ylim(py - 10, py + 10)
            ax.set_aspect("equal")
            ax.tick_params(labelsize=7)
            ax.set_title(f"{h[:2]}:{h[2:4]} UTC, 0,5°: {tit}", fontsize=10, fontweight="bold")
            if col == 3:
                fig.colorbar(pc, ax=ax, shrink=.8)
    fig.suptitle("+ posição prevista por movimento constante; contorno: Z ≥ 45 e CC < 0,85; ★ aeroporto; km a partir do radar", fontweight="bold")
    fig.savefig(FIG / "rotacao_evolucao.png", dpi=105)
    plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(17, 5.6), constrained_layout=True)
    al = [p[1] for p in perfil]
    ax[0].plot([p[2]["Zmax"] for p in perfil], al, "o-", color="#b91c1c", label="Z máx. no núcleo")
    ax[0].plot([p[2]["Zanel"] for p in perfil], al, "s--", color="0.5", label="Z p90 no anel 3–6 km")
    ax[0].set_xlabel("dBZ")
    ax[1].plot([p[2]["CCmed"] for p in perfil], al, "o-", color="#1d4ed8", label="CC mediano no núcleo")
    ax[1].plot([p[2]["CCanel"] for p in perfil], al, "s--", color="0.5", label="CC mediano no anel")
    ax[1].set_xlabel("RhoHV")
    ax[2].plot([p[2]["ZDRmed"] for p in perfil], al, "o-", color="#059669", label="ZDR mediano (dB)")
    ax[2].plot([p[2]["Wmed"] for p in perfil], al, "^-", color="#7c3aed", label="W mediano (m/s)")
    ax[2].plot([p[2]["Wanel"] for p in perfil], al, "s--", color="0.5", label="W no anel")
    for a in ax:
        a.set_ylabel("Altura acima do radar (km)")
        a.grid(alpha=.3)
        a.legend(fontsize=8)
    fig.suptitle("13:30 UTC: perfil vertical seguindo o núcleo (disco de 1,5 km); a altura acima do solo do aeroporto é cerca de 0,17 km maior", fontweight="bold")
    fig.savefig(FIG / "rotacao_perfil_vertical.png", dpi=110)
    plt.close(fig)

    with open(FIG / "rotacao_trilha.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hora_utc", "x_prev_km", "y_prev_km", "lat_prev", "lon_prev", "x_nucleo_km", "y_nucleo_km", "lat_nucleo", "lon_nucleo", "gates", "Zmax"])
        for h, px, py, cs in trilha:
            lat = lambda v: RAD_LAT + v / 111.132
            lon = lambda u: RAD_LON + u / (111.32 * np.cos(np.radians(RAD_LAT)))
            if cs:
                c = cs[0]
                w.writerow([f"{h[:2]}:{h[2:4]}", round(px, 1), round(py, 1), round(lat(py), 3), round(lon(px), 3), round(c["x"], 1), round(c["y"], 1), round(lat(c["y"]), 3), round(lon(c["x"]), 3), c["n"], c["Zmax"]])
            else:
                w.writerow([f"{h[:2]}:{h[2:4]}", round(px, 1), round(py, 1), round(lat(py), 3), round(lon(px), 3), "", "", "", "", 0, ""])


if __name__ == "__main__":
    main()
