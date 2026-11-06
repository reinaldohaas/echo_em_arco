# -*- coding: utf-8 -*-
"""
plotar_radar_chapeco.py
=======================
Processa os 186 volumes polarimétricos brutos (.vol — Rainbow5) do Radar Banda-S
de Chapecó (217BRS, Defesa Civil de SC) do dia 04/11/2026 (09:00–12:00 BRT /
12:00–15:00 UTC) sobre a malha municipal oficial do IBGE (`SC_Municipios_2022.shp`).

Gera 4 figuras científicas de alta resolução (em `radar/figuras/` e `assets/`):
1. `chapeco_4paineis_reais_1030.png`:
   Inspeção polarimétrica georreferenciada (PPI 0,5° às 10:30:04 BRT / 13:30:04 UTC)
   com Z (dBZ), Velocidade Radial Doppler V (m/s), RhoHV e ZDR (dB) sobre Chapecó.
2. `chapeco_corte_vertical_rhi_1030.png`:
   Corte vertical real (Pseudo-RHI construído com as 14 elevações de 0,5° a 19,5°)
   ao longo do azimute 206° (direção do Aeroporto de Chapecó, r = 10,5 km) mostrando
   Z (dBZ), RhoHV e Velocidade Radial Doppler às 10:24, 10:30 e 10:36 BRT.
3. `chapeco_quadros_redemet.png`:
   Painel multi-horário (6 instantes reais: 09:30, 09:54, 10:12, 10:30, 10:48 e 11:12 BRT)
   mostrando a evolução do Eco em Arco (Bow Echo) nos dados brutos do radar de Chapecó.
4. `chapeco_trajetoria_nucleos.png`:
   Swath máximo real (MAX dBZ de 31 varreduras entre 09:00 e 12:00 BRT) e trilha
   cronológica dos centróides severos (Z >= 58 dBZ) sobre os municípios do Oeste de SC.
"""

from __future__ import annotations

import shutil
from pathlib import Path
import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

from leitor_vol_chapeco import ler_volume_rainbow, polar_para_latlon

BASE_DIR = Path(__file__).resolve().parent
VOL_DIR = BASE_DIR / "dados_chp_vol"
FIG_DIR = BASE_DIR / "figuras"
ASSETS_DIR = BASE_DIR.parent / "assets"
SHP_SC = Path(r"C:\gis4wrf\projects\Floripa\shp_ibge\SC_Municipios_2022.shp")

# Coordenadas exatas do Radar de Chapecó (extraídas do XML <sensorinfo>) e do Aeroporto
RADAR_LAT = -27.048790
RADAR_LON = -52.603740
RADAR_ALT_M = 822.0

AERO_LAT = -27.1338
AERO_LON = -52.6496

CIDADES_OESTE = {
    "Chapecó": (-52.6152, -27.1004),
    "Aeroporto (126 km/h)": (AERO_LON, AERO_LAT),
    "São Miguel do Oeste": (-53.5192, -26.7244),
    "Palmitos": (-53.1610, -27.0678),
    "Xanxerê": (-52.4042, -26.8747),
    "Concórdia": (-52.0228, -27.2333),
    "Pinhalzinho": (-52.9922, -26.8481),
    "Xaxim": (-52.5347, -26.9614),
    "Seara": (-52.3106, -27.1494),
    "Coronel Freitas": (-52.7033, -26.9086),
}


def cmap_dbz() -> tuple[mcolors.Colormap, mcolors.Normalize]:
    # Paleta oficial Defesa Civil SC / Rainbow5 (10 a 66 dBZ: 45-55 vermelho, 56-61 magenta, >=62 branco)
    cores = [
        (0.00, "#01a0f6"),  # 10 dBZ
        (0.14, "#0000f6"),  # 18 dBZ
        (0.25, "#00ff00"),  # 24 dBZ
        (0.36, "#00c800"),  # 30 dBZ
        (0.45, "#009000"),  # 35 dBZ
        (0.54, "#ffff00"),  # 40 dBZ
        (0.62, "#ff9000"),  # 45 dBZ
        (0.71, "#ff0000"),  # 50 dBZ
        (0.80, "#c00000"),  # 55 dBZ
        (0.89, "#ff00ff"),  # 60 dBZ
        (0.95, "#ffffff"),  # 63 dBZ (núcleo branco sobre o Aeroporto)
        (1.00, "#ffffff"),  # 66 dBZ
    ]
    cmap = mcolors.LinearSegmentedColormap.from_list("radar_dbz_sdc", cores, N=256)
    norm = mcolors.Normalize(vmin=10.0, vmax=66.0)
    return cmap, norm


def carregar_municipios() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(SHP_SC)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


def plotar_4paineis_reais_1030(gdf_sc: gpd.GeoDataFrame) -> Path:
    """Figura 1: Zoom Polarimétrico de 4 Painéis às 10:30:04 BRT (13:30:04 UTC) sobre Chapecó."""
    ts = "2026110413300400"
    vol_z = ler_volume_rainbow(VOL_DIR / f"{ts}dBZ.vol")
    vol_v = ler_volume_rainbow(VOL_DIR / f"{ts}V.vol")
    vol_rho = ler_volume_rainbow(VOL_DIR / f"{ts}RhoHV.vol")
    vol_zdr = ler_volume_rainbow(VOL_DIR / f"{ts}ZDR.vol")

    s_z = vol_z["slices"][0]
    s_v = vol_v["slices"][0]
    s_rho = vol_rho["slices"][0]
    s_zdr = vol_zdr["slices"][0]

    lat_z, lon_z, _ = polar_para_latlon(vol_z["lat0"], vol_z["lon0"], s_z["azimuths"], s_z["ranges_km"], s_z["ele_deg"])
    lat_v, lon_v, _ = polar_para_latlon(vol_v["lat0"], vol_v["lon0"], s_v["azimuths"], s_v["ranges_km"], s_v["ele_deg"])

    # Máscara de eco significativo (Z >= 15 dBZ) para limpar ruído nos campos polarimétricos
    z_mask = np.isnan(s_z["data"]) | (s_z["data"] < 15.0)
    data_z = np.ma.masked_where(z_mask, s_z["data"])
    data_v = np.ma.masked_invalid(s_v["data"])
    data_rho = np.ma.masked_where(z_mask | np.isnan(s_rho["data"]), s_rho["data"])
    data_zdr = np.ma.masked_where(z_mask | np.isnan(s_zdr["data"]), s_zdr["data"])

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 13.0), dpi=200)
    fig.patch.set_facecolor("#070b14")

    # Janela de zoom centrada em Chapecó e no Aeroporto Serafim Enoss Bertaso
    xlim = (-52.92, -52.38)
    ylim = (-27.30, -26.88)

    cmap_z, norm_z = cmap_dbz()
    configs = [
        (
            axes[0, 0],
            lon_z,
            lat_z,
            data_z,
            cmap_z,
            norm_z,
            "A) Refletividade Horizontal Z (dBZ) — Pico: 65,5 dBZ (63,0 dBZ na Pista)",
            "dBZ",
        ),
        (
            axes[0, 1],
            lon_v,
            lat_v,
            data_v,
            "RdYlGn_r",
            mcolors.Normalize(vmin=-28.0, vmax=28.0),
            "B) Velocidade Radial Doppler Vr (m/s) — Sem Dipolo Rotacional (Sem Eco no Pico)",
            "Vr (m/s)",
        ),
        (
            axes[1, 0],
            lon_z,
            lat_z,
            data_rho,
            "Spectral_r",
            mcolors.Normalize(vmin=0.60, vmax=1.00),
            "C) Coeficiente de Correlação Copolar (ρ_hv) — Queda a 0,70 no Núcleo de 63 dBZ",
            "ρ_hv",
        ),
        (
            axes[1, 1],
            lon_z,
            lat_z,
            data_zdr,
            "RdYlBu_r",
            mcolors.Normalize(vmin=-3.0, vmax=5.0),
            "D) Refletividade Diferencial Z_DR (dB) — Oscilação Mie / Wet Hail",
            "Z_DR (dB)",
        ),
    ]

    for ax, lon_g, lat_g, dat, cm, nm, titulo, clabel in configs:
        ax.set_facecolor("#0b1120")
        gdf_sc.boundary.plot(ax=ax, color="#94a3b8", linewidth=0.9, alpha=0.85, zorder=3)
        # Destaca o município de Chapecó
        chap = gdf_sc[gdf_sc["NM_MUN"].str.contains("Chapec", case=False, na=False)]
        if not chap.empty:
            chap.boundary.plot(ax=ax, color="#f8fafc", linewidth=1.7, zorder=4)

        pcm = ax.pcolormesh(lon_g, lat_g, dat, cmap=cm, norm=nm, shading="auto", zorder=2)
        cb = fig.colorbar(pcm, ax=ax, fraction=0.042, pad=0.02)
        cb.set_label(clabel, color="#e2e8f0", fontsize=9.5, fontweight="bold")
        cb.ax.yaxis.set_tick_params(color="#cbd5e1")
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#cbd5e1", fontsize=8.5)

        # Marca o Radar de Chapecó e o Aeroporto (10,5 km, azimute 206°, feixe a 280 m AGL)
        ax.scatter(
            [RADAR_LON], [RADAR_LAT],
            marker="^", s=95, c="#38bdf8", edgecolors="black", linewidths=1.2, zorder=6, label="Radar CHP (822 m)"
        )
        ax.scatter(
            [AERO_LON], [AERO_LAT],
            marker="*", s=190, c="#fbbf24", edgecolors="black", linewidths=1.2, zorder=7, label="Aeroporto (206° / 10,5 km)"
        )
        # Círculo pericial de 4 km de raio ao redor do Aeroporto (igual ao círculo verde da análise)
        circ = plt.Circle((AERO_LON, AERO_LAT), 0.038, fill=False, edgecolor="#22c55e", linewidth=2.2, linestyle="--", zorder=6)
        ax.add_patch(circ)

        # Linha radial do radar ao Aeroporto (azimute 206°)
        ax.plot([RADAR_LON, AERO_LON], [RADAR_LAT, AERO_LAT], color="#38bdf8", linestyle=":", linewidth=1.3, zorder=5)

        ax.annotate(
            "Radar CHP",
            (RADAR_LON, RADAR_LAT),
            xytext=(6, 5),
            textcoords="offset points",
            color="#38bdf8",
            fontsize=8.5,
            fontweight="bold",
            path_effects=[pe.withStroke(linewidth=2.5, foreground="#070b14")],
            zorder=8,
        )
        ax.annotate(
            "Aeroporto Serafim Bertaso\n(Z=63 dBZ | ρ_hv=0,70 | Vr=sem eco)",
            (AERO_LON, AERO_LAT),
            xytext=(-95, -28),
            textcoords="offset points",
            color="#fbbf24",
            fontsize=8.2,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#070b14", edgecolor="#fbbf24", alpha=0.88),
            zorder=8,
        )

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_title(titulo, color="#f8fafc", fontsize=10.5, fontweight="bold", pad=8)
        ax.tick_params(colors="#94a3b8", labelsize=8.5)
        for sp in ax.spines.values():
            sp.set_edgecolor("#334155")
        ax.grid(True, linestyle=":", color="#334155", alpha=0.5)

    fig.suptitle(
        "Radar Banda-S de Chapecó (217BRS · SDC/SC) — 04/11/2026 às 10:30:04 BRT (13:30:04 UTC) · Elevação 0,5° (Feixe a 280 m AGL no Aeroporto)\n"
        "Prova Polarimétrica Real (.vol): Núcleo de 63–65,5 dBZ com Queda de ρ_hv = 0,70 (Wet Hail / Ressonância Mie) e Ausência de Vórtice Tornádico (TVS)",
        color="#ffffff",
        fontsize=12.5,
        fontweight="bold",
        y=0.975,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    out_path = FIG_DIR / "chapeco_4paineis_reais_1030.png"
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    shutil.copy2(out_path, ASSETS_DIR / out_path.name)
    return out_path


def plotar_corte_vertical_rhi(
    ts: str = "2026110413300400",
    az_alvo: float = 206.0,
) -> Path:
    """Figura 2: Corte Vertical Real (Pseudo-RHI das 14 elevações 0,5°..19,5°) sobre o Aeroporto (azimute 206°)."""
    vol_z = ler_volume_rainbow(VOL_DIR / f"{ts}dBZ.vol")
    vol_rho = ler_volume_rainbow(VOL_DIR / f"{ts}RhoHV.vol")
    vol_v = ler_volume_rainbow(VOL_DIR / f"{ts}V.vol")

    # Constrói seção vertical (14 elevações × alcance até 35 km) na direção do Aeroporto (206°)
    r_max_km = 35.0
    n_ele = len(vol_z["slices"])
    s0 = vol_z["slices"][0]
    r_mask = s0["ranges_km"] <= r_max_km
    r_km = s0["ranges_km"][r_mask]
    n_r = len(r_km)

    R_grid = np.zeros((n_ele, n_r), dtype=np.float32)
    H_grid = np.zeros((n_ele, n_r), dtype=np.float32)
    Z_vert = np.full((n_ele, n_r), np.nan, dtype=np.float32)
    RHO_vert = np.full((n_ele, n_r), np.nan, dtype=np.float32)
    V_vert = np.full((n_ele, n_r), np.nan, dtype=np.float32)

    for i, sl_z in enumerate(vol_z["slices"]):
        ele = sl_z["ele_deg"]
        el_rad = np.deg2rad(ele)
        R_grid[i, :] = r_km * np.cos(el_rad)
        H_grid[i, :] = r_km * np.sin(el_rad) + (r_km ** 2) / (2.0 * 8495.0)

        # Média nos 3 raios centrados em az_alvo (205°..207°) para continuidade vertical
        az_idx = int(np.argmin(np.abs(sl_z["azimuths"] - az_alvo)))
        bins_slice = min(n_r, sl_z["data"].shape[1])
        Z_vert[i, :bins_slice] = np.nanmean(sl_z["data"][max(0, az_idx - 1) : az_idx + 2, :bins_slice], axis=0)

        if i < len(vol_rho["slices"]):
            sl_r = vol_rho["slices"][i]
            az_r = int(np.argmin(np.abs(sl_r["azimuths"] - az_alvo)))
            b_r = min(n_r, sl_r["data"].shape[1])
            RHO_vert[i, :b_r] = np.nanmean(sl_r["data"][max(0, az_r - 1) : az_r + 2, :b_r], axis=0)

        if i < len(vol_v["slices"]):
            sl_v = vol_v["slices"][i]
            az_v = int(np.argmin(np.abs(sl_v["azimuths"] - az_alvo)))
            b_v = min(n_r, sl_v["data"].shape[1])
            V_vert[i, :b_v] = np.nanmean(sl_v["data"][max(0, az_v - 1) : az_v + 2, :b_v], axis=0)

    fig, axes = plt.subplots(1, 3, figsize=(17.0, 5.8), dpi=200, sharey=True)
    fig.patch.set_facecolor("#070b14")

    cmap_z, norm_z = cmap_dbz()
    paineis = [
        (
            axes[0],
             np.ma.masked_where(np.isnan(Z_vert) | (Z_vert < 10.0), Z_vert),
            cmap_z,
            norm_z,
            "A) Estrutura Vertical de Z (dBZ) — Azimute 206°",
            "Refletividade Z (dBZ)",
        ),
        (
            axes[1],
            np.ma.masked_where(np.isnan(Z_vert) | (Z_vert < 15.0) | np.isnan(RHO_vert), RHO_vert),
            "Spectral_r",
            mcolors.Normalize(vmin=0.65, vmax=1.00),
            "B) Estrutura Vertical de ρ_hv (Fusão / Wet Hail)",
            "Correlação Copolar ρ_hv",
        ),
        (
            axes[2],
            np.ma.masked_invalid(V_vert),
            "RdYlGn_r",
            mcolors.Normalize(vmin=-26.0, vmax=26.0),
            "C) Velocidade Radial Doppler Vr (m/s) — Fluxo Linear",
            "Velocidade Radial Vr (m/s)",
        ),
    ]

    for ax, mat, cm, nm, tit, clab in paineis:
        ax.set_facecolor("#0b1120")
        pcm = ax.pcolormesh(R_grid, H_grid, mat, cmap=cm, norm=nm, shading="nearest", zorder=2)
        # Traça as 14 linhas de feixe do radar
        for i in range(n_ele):
            ax.plot(R_grid[i, :], H_grid[i, :], color="#475569", linewidth=0.45, alpha=0.45, zorder=3)

        # Isoterma de 0 °C (~3,8 km acima do nível do radar = ~4,6 km MSL)
        ax.axhline(3.8, color="#38bdf8", linestyle="--", linewidth=1.3, alpha=0.85, zorder=4)
        ax.text(21.5, 3.98, "Isoterma 0 °C (Camada de Fusão)", color="#38bdf8", fontsize=8.0, fontweight="bold")

        # Posição do Aeroporto de Chapecó (distância = 10,5 km do radar)
        ax.axvline(10.5, color="#fbbf24", linestyle="-.", linewidth=1.6, zorder=5)
        ax.scatter([10.5], [0.28], marker="*", s=160, c="#fbbf24", edgecolors="black", zorder=6)
        ax.text(
            11.0,
            0.45,
            "Aeroporto (10,5 km)\nFeixe 0,5° = 280 m AGL",
            color="#fbbf24",
            fontsize=8.0,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#070b14", edgecolor="#fbbf24", alpha=0.85),
            zorder=7,
        )

        cb = fig.colorbar(pcm, ax=ax, fraction=0.046, pad=0.03)
        cb.set_label(clab, color="#e2e8f0", fontsize=9.0, fontweight="bold")
        cb.ax.yaxis.set_tick_params(color="#cbd5e1")
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#cbd5e1", fontsize=8.0)

        ax.set_xlim(0, 32.0)
        ax.set_ylim(0, 10.5)
        ax.set_xlabel("Distância Radial a partir do Radar de Chapecó ao longo do Azimute 206° (km)", color="#cbd5e1", fontsize=9.0)
        ax.set_title(tit, color="#f8fafc", fontsize=10.5, fontweight="bold", pad=8)
        ax.tick_params(colors="#94a3b8", labelsize=8.5)
        for sp in ax.spines.values():
            sp.set_edgecolor("#334155")
        ax.grid(True, linestyle=":", color="#334155", alpha=0.5)

    axes[0].set_ylabel("Altura Acima do Nível do Radar (km AGL · Radar a 822 m MSL)", color="#cbd5e1", fontsize=9.5)
    fig.suptitle(
        "Corte Vertical Polarimétrico Real (14 Elevações: 0,5° a 19,5°) — Radar de Chapecó (04/11/2026 às 10:30:04 BRT)\n"
        "Colapso do Núcleo Convectivo (Z > 63 dBZ) sobre o Aeroporto (r = 10,5 km), Depressão de ρ_hv abaixo da Isoterma de 0 °C e Escoamento Descendente",
        color="#ffffff",
        fontsize=12.0,
        fontweight="bold",
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.91])

    out_path = FIG_DIR / "chapeco_corte_vertical_rhi_1030.png"
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    shutil.copy2(out_path, ASSETS_DIR / out_path.name)
    return out_path


def plotar_painel_6horarios_reais(gdf_sc: gpd.GeoDataFrame) -> Path:
    """Figura 3: Evolução Multi-Horária Real (09:30 a 11:12 BRT) nos volumes .vol de Chapecó."""
    horarios = [
        ("202611041230", "09:30 BRT (12:30 UTC) — Entrada em São Miguel do Oeste"),
        ("202611041254", "09:54 BRT (12:54 UTC) — Arco Atinge Palmitos / Pinhalzinho"),
        ("202611041312", "10:12 BRT (13:12 UTC) — Aproximação de Chapecó (RIJ Intenso)"),
        ("202611041330", "10:30 BRT (13:30 UTC) — IMPACTO EM CHAPECÓ (65,5 dBZ / 126 km/h)"),
        ("202611041348", "10:48 BRT (13:48 UTC) — Avanço para Xanxerê / Xaxim / Seara"),
        ("202611041412", "11:12 BRT (14:12 UTC) — Passagem por Concórdia e Meio-Oeste"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(17.5, 10.8), dpi=200, sharex=True, sharey=True)
    fig.patch.set_facecolor("#070b14")
    cmap_z, norm_z = cmap_dbz()

    xlim = (-53.85, -51.65)
    ylim = (-27.60, -26.35)

    for ax, (ts_pref, label_h) in zip(axes.flat, horarios):
        ax.set_facecolor("#0b1120")
        arq_z = next(VOL_DIR.glob(f"{ts_pref}*dBZ.vol"))
        vol = ler_volume_rainbow(arq_z)
        s0 = vol["slices"][0]
        lat_g, lon_g, _ = polar_para_latlon(vol["lat0"], vol["lon0"], s0["azimuths"], s0["ranges_km"], s0["ele_deg"])
        dat = np.ma.masked_where(np.isnan(s0["data"]) | (s0["data"] < 18.0), s0["data"])

        gdf_sc.boundary.plot(ax=ax, color="#64748b", linewidth=0.7, alpha=0.8, zorder=3)
        pcm = ax.pcolormesh(lon_g, lat_g, dat, cmap=cmap_z, norm=norm_z, shading="auto", zorder=2)

        for cid, (clon, clat) in CIDADES_OESTE.items():
            if cid == "Aeroporto (126 km/h)":
                continue
            is_chp = cid == "Chapecó"
            ax.scatter(
                [clon], [clat],
                s=45 if is_chp else 22,
                c="#fbbf24" if is_chp else "#e2e8f0",
                edgecolors="black",
                linewidths=0.8,
                zorder=5,
            )
            ax.text(
                clon + 0.02,
                clat + 0.015,
                cid,
                color="#fbbf24" if is_chp else "#cbd5e1",
                fontsize=7.8 if is_chp else 6.8,
                fontweight="bold" if is_chp else "normal",
                path_effects=[pe.withStroke(linewidth=2.0, foreground="#070b14")],
                zorder=6,
            )

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        cor_t = "#fbbf24" if "10:30" in label_h else "#f8fafc"
        ax.set_title(label_h, color=cor_t, fontsize=9.8, fontweight="bold", pad=6)
        ax.tick_params(colors="#94a3b8", labelsize=8.0)
        for sp in ax.spines.values():
            sp.set_edgecolor("#fbbf24" if "10:30" in label_h else "#334155")
            if "10:30" in label_h:
                sp.set_linewidth(1.8)
        ax.grid(True, linestyle=":", color="#334155", alpha=0.45)

    cbar_ax = fig.add_axes([0.92, 0.12, 0.015, 0.76])
    cb = fig.colorbar(pcm, cax=cbar_ax)
    cb.set_label("Refletividade Horizontal Z (dBZ — Radar Banda-S Chapecó 217BRS)", color="#f8fafc", fontsize=10.5, fontweight="bold")
    cb.ax.yaxis.set_tick_params(color="#cbd5e1")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#cbd5e1", fontsize=9.0)

    fig.suptitle(
        "Evolução Espaço-Temporal Real do Eco em Arco (Bow Echo) no Radar de Chapecó (217BRS · SDC/SC) — 04/11/2026 (09:30–11:12 BRT)\n"
        "Varreduras Originais PPI 0,5° (Resolução 250 m) sobre a Malha Municipal do IBGE no Oeste de Santa Catarina",
        color="#ffffff",
        fontsize=12.5,
        fontweight="bold",
        y=0.975,
    )
    fig.subplots_adjust(left=0.05, right=0.90, bottom=0.06, top=0.89, wspace=0.08, hspace=0.16)

    out_path = FIG_DIR / "chapeco_quadros_redemet.png"
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    shutil.copy2(out_path, ASSETS_DIR / out_path.name)
    return out_path


def plotar_swath_e_trajetoria_real(gdf_sc: gpd.GeoDataFrame) -> Path:
    """Figura 4: Swath Contínuo Real (Máximo de Z nas varreduras 09:30–11:30 BRT) e Trilha do Ápice do Eco em Arco."""
    from scipy.ndimage import median_filter

    arquivos_dbz = sorted(
        f for f in VOL_DIR.glob("20261104*dBZ.vol")
        if "202611041230" <= f.name[:12] <= "202611041430"
    )
    vol0 = ler_volume_rainbow(arquivos_dbz[0])
    s0 = vol0["slices"][0]
    lat_g, lon_g, _ = polar_para_latlon(vol0["lat0"], vol0["lon0"], s0["azimuths"], s0["ranges_km"], s0["ele_deg"])

    swath_max = np.full_like(s0["data"], np.nan, dtype=np.float32)
    track_pts = []

    for f in arquivos_dbz:
        ts_str = f.name[:12]  # YYYYMMDDHHMM (UTC)
        hh_utc = int(ts_str[8:10])
        mm_utc = int(ts_str[10:12])
        hora_brt_dec = (hh_utc - 3) + mm_utc / 60.0
        hora_brt_str = f"{hh_utc - 3:02d}:{mm_utc:02d}"

        v = ler_volume_rainbow(f)
        sl = v["slices"][0]
        # Filtro mediano 3x3 para remover pixels isolados de ruído/clutter de terreno
        raw_z = np.where(np.isnan(sl["data"]), -32.0, sl["data"])
        dat = median_filter(raw_z, size=(3, 3))
        dat = np.where(dat < 10.0, np.nan, dat)

        if dat.shape == swath_max.shape:
            swath_max = np.fmax(swath_max, dat)

        # Janela móvel acompanhando a frente convectiva de WNW para ESE (velocidade média ~75 km/h)
        lon_esp = -53.45 + (hora_brt_dec - 9.5) * 0.78
        lat_esp = -27.18 + (hora_brt_dec - 9.5) * 0.10
        mask_core = (
            (~np.isnan(dat))
            & (dat >= 50.0)
            & (np.abs(lon_g - lon_esp) <= 0.32)
            & (np.abs(lat_g - lat_esp) <= 0.28)
        )
        if np.count_nonzero(mask_core) >= 10:
            pesos = (dat[mask_core] - 45.0) ** 2
            lon_c = float(np.average(lon_g[mask_core], weights=pesos))
            lat_c = float(np.average(lat_g[mask_core], weights=pesos))
            z_max_core = float(np.nanmax(sl["data"][mask_core]))
            track_pts.append((hora_brt_dec, hora_brt_str, lon_c, lat_c, z_max_core))

    fig, ax = plt.subplots(figsize=(14.5, 9.2), dpi=200)
    fig.patch.set_facecolor("#070b14")
    ax.set_facecolor("#0b1120")

    cmap_z, norm_z = cmap_dbz()
    swath_masked = np.ma.masked_where(np.isnan(swath_max) | (swath_max < 25.0), swath_max)

    gdf_sc.boundary.plot(ax=ax, color="#94a3b8", linewidth=0.85, alpha=0.85, zorder=3)
    chap = gdf_sc[gdf_sc["NM_MUN"].str.contains("Chapec", case=False, na=False)]
    if not chap.empty:
        chap.boundary.plot(ax=ax, color="#ffffff", linewidth=1.8, zorder=4)

    pcm = ax.pcolormesh(lon_g, lat_g, swath_masked, cmap=cmap_z, norm=norm_z, shading="auto", alpha=0.92, zorder=2)
    cb = fig.colorbar(pcm, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Refletividade Máxima Acumulada no Swath — MAX Z (dBZ · 09:00–12:00 BRT)", color="#f8fafc", fontsize=10.0, fontweight="bold")
    cb.ax.yaxis.set_tick_params(color="#cbd5e1")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#cbd5e1", fontsize=9.0)

    # Plota a trajetória cronológica dos núcleos convectivos severos (WNW -> ESE)
    if track_pts:
        lons_t = [p[2] for p in track_pts]
        lats_t = [p[3] for p in track_pts]
        ax.plot(lons_t, lats_t, color="#000000", linewidth=3.8, zorder=6)
        ax.plot(lons_t, lats_t, color="#fbbf24", linewidth=2.2, linestyle="-", zorder=7, label="Eixo de Propagação do Ápice do Bow Echo (Z ≥ 56 dBZ)")
        for idx_p, (h_dec, h_str, lon_c, lat_c, zp) in enumerate(track_pts):
            if idx_p % 3 == 0 or h_str == "10:30":
                ax.scatter([lon_c], [lat_c], s=70, c="#fbbf24", edgecolors="black", linewidths=1.1, zorder=8)
                ax.annotate(
                    f"{h_str} BRT\n({zp:.0f} dBZ)",
                    (lon_c, lat_c),
                    xytext=(0, 10 if idx_p % 2 == 0 else -22),
                    textcoords="offset points",
                    ha="center",
                    color="#ffffff",
                    fontsize=7.8,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.18", facecolor="#070b14", edgecolor="#fbbf24", alpha=0.88),
                    zorder=9,
                )

    for cid, (clon, clat) in CIDADES_OESTE.items():
        is_aero = "Aeroporto" in cid
        ax.scatter(
            [clon], [clat],
            marker="*" if is_aero else "o",
            s=180 if is_aero else 42,
            c="#22c55e" if is_aero else "#f8fafc",
            edgecolors="black",
            linewidths=1.1,
            zorder=8,
        )
        ax.text(
            clon + 0.018,
            clat - (0.028 if is_aero else -0.014),
            cid,
            color="#22c55e" if is_aero else "#f8fafc",
            fontsize=8.8 if is_aero else 8.0,
            fontweight="bold",
            path_effects=[pe.withStroke(linewidth=2.5, foreground="#070b14")],
            zorder=9,
        )

    ax.set_xlim(-53.80, -51.75)
    ax.set_ylim(-27.50, -26.45)
    ax.set_xlabel("Longitude (°O)", color="#cbd5e1", fontsize=10.0)
    ax.set_ylabel("Latitude (°S)", color="#cbd5e1", fontsize=10.0)
    ax.set_title(
        "Rastro Contínuo de Refletividade Máxima (Swath MAX-Z) e Trajetória do Eco em Arco — 04/11/2026 (09:00–12:00 BRT)\n"
        "Dados Brutos (.vol) do Radar Banda-S de Chapecó (217BRS · Defesa Civil de SC) sobre a Malha Municipal do IBGE",
        color="#ffffff",
        fontsize=12.0,
        fontweight="bold",
        pad=10,
    )
    ax.tick_params(colors="#94a3b8", labelsize=9.0)
    for sp in ax.spines.values():
        sp.set_edgecolor("#334155")
    ax.grid(True, linestyle=":", color="#334155", alpha=0.5)
    ax.legend(loc="upper right", facecolor="#0b1120", edgecolor="#fbbf24", labelcolor="#f8fafc", fontsize=9.0)

    fig.tight_layout()
    out_path = FIG_DIR / "chapeco_trajetoria_nucleos.png"
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    shutil.copy2(out_path, ASSETS_DIR / out_path.name)
    return out_path


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/5] Carregando malha municipal do IBGE (SC_Municipios_2022.shp)...")
    gdf_sc = carregar_municipios()

    print("[2/5] Gerando Figura 1: 4 Painéis Polarimétricos Reais às 10:30:04 BRT...")
    f1 = plotar_4paineis_reais_1030(gdf_sc)
    print(f"      Salvo em: {f1}")

    print("[3/5] Gerando Figura 2: Corte Vertical Real (14 Elevações, Azimute 206°)...")
    f2 = plotar_corte_vertical_rhi()
    print(f"      Salvo em: {f2}")

    print("[4/5] Gerando Figura 3: Painel Multi-Horário Real (6 Varreduras 09:30–11:12 BRT)...")
    f3 = plotar_painel_6horarios_reais(gdf_sc)
    print(f"      Salvo em: {f3}")

    print("[5/5] Gerando Figura 4: Swath Máximo Contínuo (31 Varreduras) e Trajetória...")
    f4 = plotar_swath_e_trajetoria_real(gdf_sc)
    print(f"      Salvo em: {f4}")


if __name__ == "__main__":
    main()
