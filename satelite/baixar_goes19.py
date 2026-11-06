# -*- coding: utf-8 -*-
r"""Baixa o canal 13 do GOES-19 (disco completo) de 04/11/2026, 12–15 UTC, do bucket público da NOAA.

Usa o curl.exe do Windows. Pula arquivos completos e confere o tamanho de cada um com a listagem.
"""
import pathlib
import re
import subprocess
import sys

CURL = r"C:\Windows\System32\curl.exe"
BUCKET = "https://noaa-goes19.s3.amazonaws.com"
DESTINO = pathlib.Path(__file__).resolve().parent / "dados_goes19"
DIA_JULIANO = 308  # 04/11/2026
HORAS = (12, 13, 14)


def listar(hora):
    pref = f"ABI-L2-CMIPF/2026/{DIA_JULIANO}/{hora:02d}/OR_ABI-L2-CMIPF-M6C13"
    r = subprocess.run([CURL, "-sS", "-f", "-m", "60", f"{BUCKET}/?list-type=2&prefix={pref}"],
                       capture_output=True, text=True, check=True)
    return [(k, int(s)) for k, s in re.findall(r"<Key>([^<]+)</Key>.*?<Size>(\d+)</Size>", r.stdout)]


def main():
    DESTINO.mkdir(exist_ok=True)
    alvos = [item for h in HORAS for item in listar(h)]
    print(f"{len(alvos)} arquivos, {sum(s for _, s in alvos) / 1e6:.0f} MB", flush=True)
    falhas = 0
    for n, (chave, tam) in enumerate(alvos, 1):
        arq = DESTINO / chave.rsplit("/", 1)[-1]
        if arq.exists() and arq.stat().st_size == tam:
            print(f"[{n}/{len(alvos)}] já existe", flush=True)
            continue
        parcial = arq.with_name(arq.name + ".parcial")
        r = subprocess.run([CURL, "-sS", "-f", "-m", "300", "--retry", "3", "-o", str(parcial), f"{BUCKET}/{chave}"])
        if r.returncode or parcial.stat().st_size != tam:
            falhas += 1
            print(f"[{n}/{len(alvos)}] FALHOU {arq.name}", flush=True)
            continue
        parcial.replace(arq)
        print(f"[{n}/{len(alvos)}] {arq.name}", flush=True)
    print(f"concluído: {falhas} falhas", flush=True)
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
