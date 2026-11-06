# -*- coding: utf-8 -*-
r"""Segunda checagem da narração: transcreve cada frase em cache com o Whisper large-v3-turbo e lista as diferenças.

Números por extenso e por algarismos aparecem como diferença: é só escrita, a ser ignorada na leitura do relatório.
Saída: video_work/echo_em_arco_v2/audio/checagem_turbo.txt
"""
import difflib
import hashlib
import json
import os
import pathlib
import sys

os.environ["HF_HUB_OFFLINE"] = os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import torchaudio
from transformers import WhisperForConditionalGeneration, WhisperProcessor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gerar_voz_local import AUDIO, CACHE, FALAS, frases_de, simples  # noqa: E402


def main():
    nome = "openai/whisper-large-v3-turbo"
    proc = WhisperProcessor.from_pretrained(nome)
    modelo = WhisperForConditionalGeneration.from_pretrained(nome, torch_dtype=torch.float32).eval()
    falas = json.loads(FALAS.read_text(encoding="utf-8"))
    rel = []
    for i, texto in enumerate(falas, 1):
        rel.append(f"=== cena {i}")
        for f in frases_de(texto):
            arq = CACHE / (hashlib.sha1(f.encode()).hexdigest()[:16] + ".wav")
            w, sr = torchaudio.load(str(arq))
            w16 = torchaudio.functional.resample(w, sr, 16000)[0].numpy()
            ent = proc(w16, sampling_rate=16000, return_tensors="pt").input_features
            with torch.inference_mode():
                ids = modelo.generate(ent, language="pt", task="transcribe")
            ouvido = proc.batch_decode(ids, skip_special_tokens=True)[0].strip()
            x, y = simples(f), simples(ouvido)
            m = difflib.SequenceMatcher(None, x, y, autojunk=False)
            dif = [f"{' '.join(x[a0:a1])} -> {' '.join(y[b0:b1])}" for op, a0, a1, b0, b1 in m.get_opcodes() if op != "equal"]
            rel.append(f"[{m.ratio():.2f}] {w.shape[1] / sr:.1f} s | {f}\n     ouvido: {ouvido}" + ("\n     dif: " + " | ".join(dif) if dif else ""))
            print(rel[-1], flush=True)
    (AUDIO / "checagem_turbo.txt").write_text("\n".join(rel), encoding="utf-8")


if __name__ == "__main__":
    main()
