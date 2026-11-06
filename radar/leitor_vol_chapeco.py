# -*- coding: utf-8 -*-
"""
leitor_vol_chapeco.py
=====================
Leitor nativo de volumes polarimétricos Rainbow5 (.vol — Leonardo/Selex Gematronik)
do Radar Meteorológico Banda-S de Chapecó (217BRS).

Extrai:
- Metadados do sensor (lat=-27.048790, lon=-52.603740, alt=822 m, lambda=10.417 cm)
- Todas as 14 elevações (0.5° a 19.5°)
- Matrizes polares (azimute × alcance) convertidas para unidades físicas (dBZ, m/s, RhoHV, ZDR, KDP)
- Coordenadas geográficas (lat, lon, altura AGL/MSL do feixe com curvatura efetiva 4/3 da Terra)
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
import numpy as np


def ler_volume_rainbow(filepath: str | Path) -> dict:
    raw = Path(filepath).read_bytes()
    end_marker = b"<!-- END XML -->"
    idx = raw.find(end_marker)
    if idx < 0:
        raise ValueError(f"Marcador XML não encontrado em {filepath}")

    xml_bytes = raw[:idx]
    bin_bytes = raw[idx + len(end_marker):]
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))

    blobs: dict[int, bytes] = {}
    pattern = re.compile(rb'<BLOB\s+blobid="(\d+)"\s+size="(\d+)"\s+compression="(\w+)"\s*>')
    for m in pattern.finditer(bin_bytes):
        bid = int(m.group(1))
        sz = int(m.group(2))
        comp = m.group(3).decode("ascii")
        start = m.end()
        if bin_bytes[start : start + 1] == b"\n":
            start += 1
        elif bin_bytes[start : start + 2] == b"\r\n":
            start += 2
        chunk = bin_bytes[start : start + sz]
        if comp == "qt":
            blobs[bid] = zlib.decompress(chunk[4:])
        else:
            blobs[bid] = chunk

    sensor = root.find("sensorinfo")
    lat0 = float(sensor.findtext("lat")) if sensor is not None else -27.048790
    lon0 = float(sensor.findtext("lon")) if sensor is not None else -52.603740
    alt0 = float(sensor.findtext("alt")) if sensor is not None else 822.0

    # Parâmetros herdados da primeira fatia (slice 0) caso omitidos nas seguintes
    default_rstep = 0.25
    default_posangle = 0.5
    slices_out = []

    for s in root.findall(".//slice"):
        refid = int(s.attrib.get("refid", "0"))
        pos_txt = s.findtext("posangle")
        if pos_txt is not None:
            ele_deg = float(pos_txt)
            default_posangle = ele_deg
        else:
            ele_deg = default_posangle

        rs_txt = s.findtext("rangestep")
        if rs_txt is not None:
            rstep_km = float(rs_txt)
            default_rstep = rstep_km
        else:
            rstep_km = default_rstep

        sdata = s.find("slicedata")
        if sdata is None:
            continue
        rayinfo = sdata.find("rayinfo")
        rawdata = sdata.find("rawdata")
        if rayinfo is None or rawdata is None:
            continue

        ang_bid = int(rayinfo.attrib["blobid"])
        ang_depth = int(rayinfo.attrib["depth"])
        ang_rays = int(rayinfo.attrib["rays"])
        ang_buf = blobs[ang_bid]
        if ang_depth == 16:
            arr_ang = np.frombuffer(ang_buf, dtype=">u2").astype(np.float64)
            azimuths = arr_ang * 360.0 / 65536.0
        else:
            arr_ang = np.frombuffer(ang_buf, dtype=np.uint8).astype(np.float64)
            azimuths = arr_ang * 360.0 / 256.0

        dat_bid = int(rawdata.attrib["blobid"])
        dat_depth = int(rawdata.attrib["depth"])
        dat_rays = int(rawdata.attrib["rays"])
        dat_bins = int(rawdata.attrib["bins"])
        vmin = float(rawdata.attrib["min"])
        vmax = float(rawdata.attrib["max"])
        vtype = rawdata.attrib.get("type", "")

        dat_buf = blobs[dat_bid]
        if dat_depth == 16:
            raw_mat = np.frombuffer(dat_buf, dtype=">u2").reshape((dat_rays, dat_bins))
            max_int = 65535.0
        else:
            raw_mat = np.frombuffer(dat_buf, dtype=np.uint8).reshape((dat_rays, dat_bins))
            max_int = 255.0

        # 0 = sem eco (nodata) no padrão Rainbow5; valores válidos de 1..max_int mapeados para [vmin, vmax]
        phys = np.full((dat_rays, dat_bins), np.nan, dtype=np.float32)
        valid = raw_mat > 0
        phys[valid] = vmin + (raw_mat[valid].astype(np.float32) - 1.0) * (vmax - vmin) / (max_int - 1.0)

        # Reordena os raios em ordem crescente de azimute (0..360°)
        order = np.argsort(azimuths)
        azimuths_sorted = azimuths[order]
        phys_sorted = phys[order, :]
        ranges_km = (np.arange(dat_bins, dtype=np.float32) + 0.5) * rstep_km

        slices_out.append({
            "refid": refid,
            "ele_deg": ele_deg,
            "rstep_km": rstep_km,
            "azimuths": azimuths_sorted,
            "ranges_km": ranges_km,
            "data": phys_sorted,
            "type": vtype,
            "time": sdata.attrib.get("time", ""),
            "date": sdata.attrib.get("date", ""),
        })

    return {
        "lat0": lat0,
        "lon0": lon0,
        "alt0": alt0,
        "slices": slices_out,
    }


def polar_para_latlon(lat0: float, lon0: float, azimuths_deg: np.ndarray, ranges_km: np.ndarray, ele_deg: float = 0.5):
    """Converte grade (rays, bins) em matrizes (lat, lon, altura_agl_km)."""
    az_rad = np.deg2rad(azimuths_deg)[:, None]
    el_rad = np.deg2rad(ele_deg)
    r_ground = ranges_km[None, :] * np.cos(el_rad)

    x_km = r_ground * np.sin(az_rad)
    y_km = r_ground * np.cos(az_rad)

    dlat = y_km / 111.132
    dlon = x_km / (111.320 * np.cos(np.deg2rad(lat0)))
    lat = lat0 + dlat
    lon = lon0 + dlon

    # Altura do feixe acima do nível do radar (curvatura 4/3 da Terra, R_eff = 8495 km)
    r_slant = ranges_km[None, :]
    h_agl_km = r_slant * np.sin(el_rad) + (r_slant ** 2) / (2.0 * 8495.0)
    return lat, lon, h_agl_km


if __name__ == "__main__":
    base = Path(__file__).resolve().parent / "dados_chp_vol"
    for var in ("dBZ", "V", "RhoHV", "ZDR", "KDP", "W"):
        f = base / f"2026110413300400{var}.vol"
        vol = ler_volume_rainbow(f)
        s0 = vol["slices"][0]
        # Ponto do Aeroporto de Chapecó (-27.1338, -52.6496 -> azimute ~206°, alcance ~10.5 km)
        az_idx = int(np.argmin(np.abs(s0["azimuths"] - 206.0)))
        r_idx = int(np.argmin(np.abs(s0["ranges_km"] - 10.5)))
        patch = s0["data"][max(0, az_idx - 3) : az_idx + 4, max(0, r_idx - 4) : r_idx + 5]
        val_pt = s0["data"][az_idx, r_idx]
        val_max = np.nanmax(patch) if not np.all(np.isnan(patch)) else np.nan
        val_min = np.nanmin(patch) if not np.all(np.isnan(patch)) else np.nan
        print(
            f"{var:5s} (13:30 UTC, ele={s0['ele_deg']}°, slices={len(vol['slices'])}): "
            f"ponto(206°,10.5km)={val_pt:.2f} | min_viz={val_min:.2f} | max_viz={val_max:.2f}"
        )
