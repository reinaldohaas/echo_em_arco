# -*- coding: utf-8 -*-
r"""Mapa: bairros com danos relatados, trilha do radar e hidrografia. Mede extensão e retilinidade.

Limite principal: a Defesa Civil divulgou bairros, não pontos de dano. Por isso, centroides e polígonos dão
um ENVELOPE da área, não a faixa real de destruição.
Fontes: geometria OpenStreetMap (radar/dados_osm/osm.json, © colaboradores do OSM); trilha em analise_rotacao.py.
Saídas: figuras/mapa_danos_trilha.png, figuras/mapa_danos_medidas.csv.
"""
import csv
import json
import math
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
OSM = AQUI / "dados_osm" / "osm.json"
FIG = AQUI / "figuras"
RAD = (-52.60374, -27.04879)
KX = 111.32 * math.cos(math.radians(RAD[1]))
KY = 111.132
SEVEROS = ["Quedas do Palmital", "Palmital", "Palmital dos Fundos", "Seminário", "Universitário"]
OUTROS = ["Esplanada"]
# posições medidas pelo radar (km a partir do radar), com horário UTC
TRILHA = [("13:24", -15.5, -10.1, "cisalhamento"), ("13:30", -4.51, -9.55, "núcleo de CC baixo"), ("13:36", 8.7, -10.2, "núcleo de CC baixo")]


def ll(x, y):
    return RAD[0] + x / KX, RAD[1] + y / KY


def km(lon, lat):
    return (lon - RAD[0]) * KX, (lat - RAD[1]) * KY


def centro(e):
    if "lat" in e:
        return e["lon"], e["lat"]
    if "center" in e:
        return e["center"]["lon"], e["center"]["lat"]
    return None


def aneis(e):
    if e["type"] == "way" and "geometry" in e:
        return [[(p["lon"], p["lat"]) for p in e["geometry"]]]
    if e["type"] == "relation":
        return [[(p["lon"], p["lat"]) for p in m["geometry"]] for m in e.get("members", []) if m.get("geometry") and m.get("role") in ("outer", "")]
    return []


def main():
    E = json.load(open(OSM, encoding="utf-8"))["elements"]
    E += json.load(open(OSM.with_name("bairros.json"), encoding="utf-8"))["elements"]
    pontos, poli = {}, {}
    for e in E:
        n = e.get("tags", {}).get("name")
        if not n or n not in SEVEROS + OUTROS:
            continue
        t = e["tags"]
        if t.get("place") or t.get("admin_level") == "10":
            c = centro(e)
            if c and n not in pontos:
                pontos[n] = c
            if e["type"] == "relation" and aneis(e):
                poli[n] = aneis(e)

    # eixo da trilha do radar
    xs = np.array([p[1] for p in TRILHA])
    ys = np.array([p[2] for p in TRILHA])
    b, a = np.polyfit(xs, ys, 1)
    azim = math.degrees(math.atan2(1, b)) % 360
    res = ys - (a + b * xs)
    print(f"[trilha radar] {TRILHA[0][0]}–{TRILHA[-1][0]}: {np.hypot(xs[-1] - xs[0], ys[-1] - ys[0]):.1f} km, rumo {azim:.0f}°, desvio máx. da reta {np.max(np.abs(res)) / math.hypot(1, b):.2f} km")

    # eixo dos centroides dos bairros
    cx = np.array([km(*pontos[n])[0] for n in SEVEROS])
    cy = np.array([km(*pontos[n])[1] for n in SEVEROS])
    b2, a2 = np.polyfit(cx, cy, 1)
    az2 = math.degrees(math.atan2(1, b2)) % 360
    d2 = (cy - (a2 + b2 * cx)) / math.hypot(1, b2)
    d1 = (cy - (a + b * cx)) / math.hypot(1, b)
    print(f"[bairros] extensão O–L dos centroides {cx.max() - cx.min():.1f} km; rumo do eixo {az2:.0f}°; desvio rms da própria reta {np.sqrt(np.mean(d2 ** 2)):.2f} km, máx. {np.abs(d2).max():.2f} km")
    linhas = []
    for n, x, y, d in zip(SEVEROS, cx, cy, d1):
        pol = poli.get(n)
        ext = ""
        if pol:
            pts = np.array([km(*p) for r in pol for p in r])
            ext = f"{pts[:, 0].max() - pts[:, 0].min():.1f} x {pts[:, 1].max() - pts[:, 1].min():.1f}"
        print(f"   {n}: lon={pontos[n][0]:.4f} lat={pontos[n][1]:.4f} desvio da trilha {d:+.2f} km (+ = norte); polígono O-L x N-S km: {ext or 'sem polígono'}")
        linhas.append({"bairro": n, "lon": round(pontos[n][0], 4), "lat": round(pontos[n][1], 4), "desvio_trilha_km": round(float(d), 2), "poligono_km": ext})
    with open(FIG / "mapa_danos_medidas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    # hidrografia: cursos nomeados que cruzam a trilha, e os mais próximos do aeroporto ao sul dela
    print("[hidrografia] curso: ponto mais próximo do aeroporto; km; cruza a reta da trilha entre x=-25 e x=+15? onde")
    ax0, ay0 = km(-52.6496, -27.1338)
    por_nome = {}
    for e in E:
        t = e.get("tags", {})
        if t.get("waterway") in ("river", "stream") and e.get("geometry"):
            n = t.get("name", "(sem nome)")
            por_nome.setdefault(n, []).append(np.array([km(p["lon"], p["lat"]) for p in e["geometry"]]))
    saida = []
    for n, segs in por_nome.items():
        if n == "(sem nome)":
            continue
        P = np.vstack(segs)
        d = np.hypot(P[:, 0] - ax0, P[:, 1] - ay0)
        k = int(np.argmin(d))
        cruz = []
        for s in segs:
            f = s[:, 1] - (a + b * s[:, 0])
            for i in np.nonzero(np.sign(f[:-1]) * np.sign(f[1:]) < 0)[0]:
                if -25 < s[i, 0] < 15:
                    cruz.append(float(s[i, 0]))
        tcr = ", ".join(f"x={c:.1f} km (~{13.5 + (c + 4.51) / 2.4 / 60:.3f}h)" for c in sorted(set(round(c, 1) for c in cruz)))
        saida.append((float(d[k]), n, *ll(*P[k]), P[k, 1] < ay0, tcr))
    for q in sorted(saida)[:16]:
        print(f"   {q[1]}: {q[0]:.1f} km do aeroporto em ({q[3]:.3f}, {q[2]:.3f}) {'ao sul' if q[4] else 'ao norte'}; cruza: {q[5] or 'não'}")

    # quantos cursos d'água a trilha cruza, e qual passa logo ao sul do aeroporto
    cruz_tot, cruz_nom = [], []
    for e in E:
        t = e.get("tags", {})
        if t.get("waterway") in ("river", "stream") and e.get("geometry"):
            s = np.array([km(p["lon"], p["lat"]) for p in e["geometry"]])
            f = s[:, 1] - (a + b * s[:, 0])
            for i in np.nonzero(np.sign(f[:-1]) * np.sign(f[1:]) < 0)[0]:
                if xs[0] <= s[i, 0] <= xs[-1]:
                    cruz_tot.append(float(s[i, 0]))
                    cruz_nom.append(t.get("name", "(sem nome)") + "/" + t["waterway"])
    print(f"[cruzamentos] {len(cruz_tot)} entre 13:24 e 13:36 ({xs[-1] - xs[0]:.0f} km):")
    for c, n in sorted(zip(cruz_tot, cruz_nom)):
        lo_c, la_c = ll(c, a + b * c)
        print(f"   x={c:6.1f} km ({la_c:.3f}, {lo_c:.3f}) {n}")

    fig, eixos = plt.subplots(1, 2, figsize=(19, 8.8), constrained_layout=True, gridspec_kw=dict(width_ratios=[1, 1.08]))
    OFF = {"Palmital dos Fundos": (-8, 12), "Quedas do Palmital": (-40, -22), "Palmital": (-60, 12), "Universitário": (8, 6), "Seminário": (8, -16), "Esplanada": (14, 12)}
    for ax, xlim, ylim, zoom in ((eixos[0], (-52.82, -52.48), (-27.26, -27.03), False), (eixos[1], (-52.685, -52.575), (-27.165, -27.10), True)):
        for e in E:
            t = e.get("tags", {})
            if t.get("waterway") in ("river", "stream") and e.get("geometry"):
                g = e["geometry"]
                nome = t.get("name", "")
                uru = "Uruguai" in nome
                ax.plot([p["lon"] for p in g], [p["lat"] for p in g], color="#1d4ed8" if uru or t["waterway"] == "river" else "#60a5fa", lw=3.5 if uru else (1.6 if nome or t["waterway"] == "river" else .6), zorder=1)
            if t.get("aeroway") == "runway":
                g = e["geometry"]
                ax.plot([p["lon"] for p in g], [p["lat"] for p in g], color="black", lw=5, zorder=4)
        for n, pol in poli.items():
            for r in pol:
                arr = np.array(r)
                ax.plot(arr[:, 0], arr[:, 1], color="#ea580c" if n in SEVEROS else "#a16207", zorder=2, lw=1.8)
        xl = np.array([-30, 22])
        lo, la = ll(xl, a + b * xl)
        ax.plot(lo, la, "--", color="#be123c", lw=1.4, zorder=5, label=f"Reta ajustada à trilha do radar (rumo {azim:.0f}°)")
        for h, x, y, tipo in TRILHA:
            lo, la = ll(x, y)
            ax.plot(lo, la, "D", color="#be123c", ms=10, mec="white", zorder=8)
            if xlim[0] < lo < xlim[1]:
                ax.annotate(f"{h} UTC\n{tipo}", (lo, la), xytext=(0, -36), textcoords="offset points", ha="center", fontsize=10, color="#881337", fontweight="bold", zorder=9,
                            bbox=dict(boxstyle="round,pad=.15", fc="white", ec="#be123c", alpha=.92))
        if zoom:
            for n, (lo, la) in pontos.items():
                ax.plot(lo, la, "o", color="#7c2d12", ms=6, zorder=6)
                ax.annotate(n, (lo, la), xytext=OFF.get(n, (4, 6)), textcoords="offset points", fontsize=10, fontweight="bold", zorder=7,
                            bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.85))
            ax.annotate("Pista do aeroporto", (-52.665, -27.1328), xytext=(-40, 34), textcoords="offset points", fontsize=10, fontweight="bold", zorder=8,
                        arrowprops=dict(arrowstyle="-", lw=.8), bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.85))
            ax.annotate("Lajeado Ferreira", (-52.654, -27.141), xytext=(-110, -42), textcoords="offset points", fontsize=10, fontweight="bold", color="#1d4ed8", zorder=8,
                        arrowprops=dict(arrowstyle="-", lw=.8, color="#1d4ed8"), bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.85))
            ax.set_title("Zoom: área dos danos relatados", fontweight="bold")
        else:
            ax.plot(*RAD, "^", color="black", ms=11, zorder=8)
            ax.annotate("Radar", RAD, xytext=(7, 4), textcoords="offset points", fontsize=10, fontweight="bold")
            ax.annotate("Rio Uruguai", (-52.74, -27.243), fontsize=11, fontweight="bold", color="#1d4ed8", zorder=8, bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.85))
            ax.plot([], [], color="#60a5fa", lw=1.6, label="Rios, córregos e lajeados")
            ax.plot([], [], color="#ea580c", lw=1.8, label="Limites de bairros com danos mais severos (Defesa Civil)")
            ax.plot([], [], color="#a16207", lw=1.8, label="Esplanada: antenas derrubadas (fonte não atribuída)")
            ax.legend(loc="lower right", fontsize=9, framealpha=.95)
            ax.set_title("Região: trilha medida pelo radar", fontweight="bold")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect(1 / math.cos(math.radians(27.13)))
        ax.grid(alpha=.25)
    fig.suptitle("Chapecó, 04/11/2026: bairros indicam área aproximada, não a faixa real de destruição. Geometria © OpenStreetMap", fontweight="bold", fontsize=13)
    fig.savefig(FIG / "mapa_danos_trilha.png", dpi=115)


if __name__ == "__main__":
    main()
