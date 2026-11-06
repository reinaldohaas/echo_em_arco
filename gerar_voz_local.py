# -*- coding: utf-8 -*-
r"""Gera a narração com a voz clonada (Chatterbox) nesta máquina, a partir de video_v2/falas.json.

Usa os mesmos parâmetros de videoaula/gerador_de_video_e_som.py. Cada frase fica em cache, identificada pelo
texto; refazer uma cena só sintetiza as frases alteradas. Saída em video_work/echo_em_arco_v2/audio:
  slide_00N.wav   áudio normalizado
  slide_00N.json  {"texto", "palavras": [[palavra, início, fim], ...]}
  checagem.txt    transcrição automática e fração de palavras reconhecidas, por cena

  python -P gerar_voz_local.py            todas as cenas
  python -P gerar_voz_local.py --cena 5   só a cena 5
"""
import argparse
import difflib
import hashlib
import json
import os
import pathlib
import re
import subprocess
import time
import unicodedata

os.environ["HF_HUB_OFFLINE"] = os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import torchaudio

BASE = pathlib.Path(__file__).resolve().parent
FALAS = BASE / "video_v2" / "falas.json"
AUDIO = BASE / "video_work" / "echo_em_arco_v2" / "audio"
CACHE = BASE / "video_work" / "echo_em_arco_v2" / "frases"
REF = pathlib.Path(r"C:\Users\haas\github\videoaula\voz_referencia\amostra_nova_ref24k.wav")
CB_CFG, CB_EXAG, CB_TEMP = 0.4, 0.45, 0.7
PAUSA = 0.35
SEMENTE = 2026


def frases_de(texto, max_chars=220):
    saida = []
    partes = re.split(r"(?<=[.!?;:])\s+", texto.strip())
    # "Segundo:" sozinho faz o Chatterbox inventar sílabas: fica junto da frase seguinte
    unidas = []
    for p in partes:
        if unidas and unidas[-1].endswith(":") and len(unidas[-1]) <= 10:
            unidas[-1] += " " + p
        else:
            unidas.append(p)
    for p in unidas:
        if len(p) <= max_chars:
            saida.append(p)
            continue
        buf = ""
        for s in re.split(r"(?<=,)\s+", p):
            if buf and len(buf) + len(s) > max_chars:
                saida.append(buf.strip())
                buf = s
            else:
                buf = (buf + " " + s).strip()
        if buf:
            saida.append(buf.strip())
    return saida


def simples(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if not unicodedata.combining(c))).split()


def tempos(toks, alinhados, total):
    """Associa os tokens do texto aos tempos do alinhador; preenche por interpolação os que vierem sem tempo."""
    out = [[t, None, None] for t in toks]
    if len(alinhados) == len(toks):
        for o, (_, s, e) in zip(out, alinhados):
            o[1], o[2] = s, e
    else:
        print(f"  alinhador devolveu {len(alinhados)} palavras para {len(toks)}; usando o casamento por texto", flush=True)
        a = [" ".join(simples(p[0])) for p in alinhados]
        b = [" ".join(simples(t)) for t in toks]
        for bl in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
            for k in range(bl.size):
                out[bl.b + k][1], out[bl.b + k][2] = alinhados[bl.a + k][1], alinhados[bl.a + k][2]
    n = len(out)
    i = 0
    while i < n:
        if out[i][1] is not None:
            i += 1
            continue
        j = i
        while j < n and out[j][1] is None:
            j += 1
        ini = out[i - 1][2] if i else 0.0
        fim = out[j][1] if j < n else total
        passo = (fim - ini) / (j - i)
        for k in range(i, j):
            out[k][1], out[k][2] = ini + passo * (k - i), ini + passo * (k - i + 1)
        i = j
    return [[t, round(float(s), 3), round(float(e), 3)] for t, s, e in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cena", type=int)
    a = ap.parse_args()
    falas = json.loads(FALAS.read_text(encoding="utf-8"))
    AUDIO.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    cenas = [(i, t) for i, t in enumerate(falas, 1) if a.cena in (None, i)]

    pend = [f for _, t in cenas for f in frases_de(t) if not (CACHE / (hashlib.sha1(f.encode()).hexdigest()[:16] + ".wav")).exists()]
    print(f"{len(pend)} frases a sintetizar", flush=True)
    tts = None
    if pend:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        tts = ChatterboxMultilingualTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
        tts.prepare_conditionals(str(REF), exaggeration=CB_EXAG)
    feitas, t0, gerado = 0, time.time(), 0.0
    for i, texto in cenas:
        pedacos, sr = [], 24000
        for f in frases_de(texto):
            arq = CACHE / (hashlib.sha1(f.encode()).hexdigest()[:16] + ".wav")
            if not arq.exists():
                torch.manual_seed(SEMENTE)
                with torch.inference_mode():
                    w = tts.generate(f, language_id="pt", exaggeration=CB_EXAG, cfg_weight=CB_CFG, temperature=CB_TEMP).cpu()
                torchaudio.save(str(arq), w, tts.sr)
                feitas += 1
                gerado += w.shape[1] / tts.sr
                print(f"  [{feitas}/{len(pend)}] {w.shape[1] / tts.sr:.1f} s de áudio; {time.time() - t0:.0f} s decorridos: {f[:60]}", flush=True)
            w, sr = torchaudio.load(str(arq))
            pedacos += [w, torch.zeros(1, int(PAUSA * sr))]
        audio = torch.cat(pedacos[:-1], dim=1)
        bruto = AUDIO / f"slide_{i:03d}_bruto.wav"
        torchaudio.save(str(bruto), audio / audio.abs().max().clamp(min=1e-6) * .9, sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(bruto), "-ar", "48000", "-ac", "1",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(AUDIO / f"slide_{i:03d}.wav")], check=True)
        bruto.unlink()
        print(f"cena {i}: {audio.shape[1] / sr:.1f} s", flush=True)

    # alinhamento das palavras e checagem por transcrição, pois o texto é conhecido
    import whisperx
    from faster_whisper import WhisperModel
    modelo, meta = whisperx.load_align_model(language_code="pt", device="cpu")
    transc = WhisperModel("small", device="cpu", compute_type="int8")
    rel = []
    for i, texto in cenas:
        wav = AUDIO / f"slide_{i:03d}.wav"
        au = whisperx.load_audio(str(wav))
        total = len(au) / 16000
        res = whisperx.align([{"text": texto, "start": 0.0, "end": total}], modelo, meta, au, "cpu", return_char_alignments=False)
        al = [(p.get("word", "").strip(), p.get("start"), p.get("end")) for p in res.get("word_segments", []) if p.get("word", "").strip()]
        pal = tempos(texto.split(), al, total)
        (AUDIO / f"slide_{i:03d}.json").write_text(json.dumps({"texto": texto, "palavras": pal}, ensure_ascii=False), encoding="utf-8")
        segs, _ = transc.transcribe(str(wav), language="pt")
        ouvido = " ".join(s.text.strip() for s in segs)
        x, y = simples(texto), simples(ouvido)
        taxa = difflib.SequenceMatcher(None, x, y, autojunk=False).ratio()
        rel.append(f"cena {i}: {total:.1f} s, concordância {taxa:.2f}\n  texto:   {texto}\n  ouvido:  {ouvido}\n")
        print(f"cena {i}: alinhada; concordância com a transcrição {taxa:.2f}", flush=True)
    (AUDIO / ("checagem.txt" if a.cena is None else f"checagem_{a.cena}.txt")).write_text("\n".join(rel), encoding="utf-8")
    if feitas:
        print(f"fator CPU: {(time.time() - t0) / max(gerado, .1):.1f}x", flush=True)


if __name__ == "__main__":
    main()
