# -*- coding: utf-8 -*-
"""Baixa imagens MaxCAPPI/CAPPI dos radares do DECEA (API REDEMET) para o evento de 04/11/2026 (Chapecó / Oeste de SC).

Radares do DECEA que cobrem o Oeste e Meio-Oeste de SC:
  sg = Santiago (RS)
  mi = Morro da Igreja (SC)
  ct = Curitiba / Teixeira Soares (PR) / cascavel
"""
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

CURL = r"C:\Windows\System32\curl.exe"
API = "https://api-redemet.decea.mil.br/produtos/radar/{tipo}?api_key={key}&data={data}&area={area}&anima=15"
INICIO, FIM = datetime(2026, 11, 4, 10), datetime(2026, 11, 4, 17)
AQUI = os.path.dirname(os.path.abspath(__file__))


def obter_chave():
    if os.environ.get("REDEMET_KEY"):
        return os.environ["REDEMET_KEY"]
    raise RuntimeError("Defina a variavel de ambiente REDEMET_KEY")


def baixar(url, destino=None):
    cmd = [CURL, "-s", "-f", "-m", "120", "-A", "Mozilla/5.0", url]
    if destino:
        cmd[1:1] = ["-o", destino]
    for _ in range(4):
        r = subprocess.run(cmd, capture_output=True)
        if not r.returncode:
            return r.stdout
    return None


def main():
    key = obter_chave()
    tipo = sys.argv[1] if len(sys.argv) > 1 else "maxcappi"
    radares = sys.argv[2:] or ["sg", "mi"]
    for area in radares:
        pasta = os.path.join(AQUI, area, tipo)
        os.makedirs(pasta, exist_ok=True)
        quadros = {}
        h = INICIO
        while h <= FIM:
            raw = baixar(API.format(tipo=tipo, key=key, data=h.strftime("%Y%m%d%H"), area=area))
            if raw:
                try:
                    resp = json.loads(raw)
                    for grupo in resp.get("data", {}).get("radar", []):
                        for r in grupo:
                            if r.get("localidade") == area and r.get("path"):
                                quadros[r["data"]] = r
                except Exception:
                    pass
            h += timedelta(hours=1)
        with open(os.path.join(pasta, "quadros.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["data_utc", "arquivo", "lon_min", "lon_max", "lat_min", "lat_max", "lat_center", "lon_center", "url"])
            for data in sorted(quadros):
                r = quadros[data]
                nome = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d_%H%M%S") + ".png"
                destino = os.path.join(pasta, nome)
                if not os.path.exists(destino):
                    baixar(r["path"], destino)
                w.writerow([data, nome, r["lon_min"], r["lon_max"], r["lat_min"], r["lat_max"],
                            r["lat_center"], r["lon_center"], r["path"]])
        print(f"{area} {tipo}: {len(quadros)} quadros baixados em {pasta}")


if __name__ == "__main__":
    main()
