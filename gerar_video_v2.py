# -*- coding: utf-8 -*-
r"""Vídeo "Tornado ou microexplosão em Chapecó?" (versão 2, refeita do zero).

  python gerar_video_v2.py --quadros     só quadros de teste de cada cena (video_v2/teste_*.png)
  python gerar_video_v2.py               renderiza video_chapeco_v2.mp4
  python gerar_video_v2.py --vlab        gera echo_em_arco_v2-vlab.zip para a voz clonada

Se existirem video_work/echo_em_arco_v2/audio/slide_00N.wav e .json do mesmo texto (gerar_voz_local.py), eles
substituem a narração SAPI e as animações se ressincronizam, pois os eventos dependem do tempo das palavras.
  python gerar_video_v2.py --falas       grava video_v2/falas.json, a entrada de gerar_voz_local.py
"""
import argparse
import json
import math
import multiprocessing as mp
import pathlib
import random
import re
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

BASE = pathlib.Path(__file__).resolve().parent
A = BASE / "assets"
OUT = BASE / "video_v2"
VOZ = BASE / "video_work" / "echo_em_arco_v2" / "audio"
W, H, SS, FPS = 1920, 1080, 2, 24
FIM_MUDO = 0.7
SILENCIO_FINAL_SAPI = 0.76

BG = (11, 18, 32)
PAINEL = (21, 31, 51)
LINHA = (51, 65, 92)
BRANCO = (241, 245, 249)
CINZA = (160, 174, 192)
CORAL = (255, 107, 91)
CIANO = (62, 203, 232)
AMBAR = (251, 191, 36)
VERDE = (74, 222, 128)
VERMELHO = (239, 68, 68)

CENAS = [
    "Na manhã de quatro de novembro de dois mil e vinte e seis, ventos de cento e vinte e seis quilômetros por hora "
    "destruíram hangares e telhados em Chapecó. As reportagens falaram em tornado, confirmado pela Defesa Civil. "
    "Mas outro fenômeno causa danos parecidos: a microexplosão. Como saber qual foi?",

    "Os dois fenômenos movem o ar de formas opostas. No tornado, o ar converge e gira em torno de um eixo. "
    "Na microexplosão, uma coluna de ar frio despenca, bate no solo e se espalha em todas as direções. "
    "Por isso, o padrão de danos é a pista mais direta: convergente em um, divergente no outro.",

    "Por que o ar despenca? Dois efeitos se somam. O peso da chuva e do granizo arrasta o ar para baixo. "
    "E a evaporação e a fusão do gelo resfriam esse ar, que fica mais denso que o ambiente. "
    "Ao chegar ao solo, o fluxo se espalha e forma uma frente de rajada capaz de superar cento e vinte quilômetros por hora.",

    "Naquela manhã, uma linha de tempestades em forma de arco cruzou o oeste catarinense. "
    "O radar de Chapecó mostra esse arco com clareza, passando pela cidade perto das dez e meia. "
    "No satélite, os topos esfriaram de setenta e nove para oitenta e cinco graus negativos em vinte minutos, e depois voltaram a aquecer. "
    "No canal visível, topos borbulhantes, típicos de overshoot, acompanham o núcleo do radar e passam junto ao aeroporto. "
    "Esse formato de arco favorece ventos fortes em linha reta. Mas atenção: ele não exclui tornado. "
    "Sistemas lineares também geram tornados, em geral curtos e difíceis de detectar.",

    "Agora temos os dados brutos do radar. Duas pistas favorecem ar descendo e se espalhando, e uma fica em aberto. "
    "Primeiro, a chuva: a coluna é de chuva intensa, e chega à camada mais baixa com cerca de sessenta decibéis zê. "
    "Segundo, o vento: atrás da linha, o mais forte está na camada mais baixa e diminui com a altura, como numa saída de ar que desce e se espalha. "
    "Terceiro, o cisalhamento: às dez e meia, junto ao aeroporto, há um salto de vento localizado até cerca de setecentos metros. "
    "Mas um único radar não separa rotação de cisalhamento, e o sinal não se mantém seis minutos antes nem depois.",

    "Isso encerra o caso? Ainda não. Primeiro: o radar varre a cada seis minutos, e sobre o aeroporto o feixe mais baixo passa a quase trezentos metros do chão. "
    "Um vórtice curto e raso poderia escapar. "
    "Segundo: a correlação copolar cai a cerca de zero vírgula sete, mas isso não separa as hipóteses, pois granizo em fusão ou detritos erguidos pelo vento também a reduzem. "
    "Terceiro: falta o levantamento de campo, com a direção de queda de árvores e estruturas, e a medida do vento durante a passagem.",

    "Com os dados reais, a melhor hipótese continua sendo a microexplosão, dentro da linha em arco, mas ela não está provada. "
    "O tornado não está descartado, e só o levantamento de danos pode encerrar a questão. "
    "E, na próxima manchete sobre um vendaval, vale fazer uma pergunta simples: para que lado caíram as árvores? "
    "Uma ressalva: isto é ciência, não veredito. "
    "O código e os resultados estão no GitHub, para qualquer pessoa usar e refutar.",
]


# ---------------------------------------------------------------- utilitários
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def suave(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def mix(c, a, fundo=BG):
    return tuple(int(round(f + (k - f) * a)) for k, f in zip(c, fundo))


_fontes = {}


def fonte(tam, negrito=False):
    k = (tam, negrito)
    if k not in _fontes:
        _fontes[k] = ImageFont.truetype(rf"C:\Windows\Fonts\segoeui{'b' if negrito else ''}.ttf", tam * SS)
    return _fontes[k]


class Tela:
    def __init__(self):
        self.im = Image.new("RGB", (W * SS, H * SS), BG)
        self.d = ImageDraw.Draw(self.im)

    def txt(self, x, y, s, tam=36, cor=BRANCO, neg=False, anc="la", a=1.0, fundo=BG):
        if a > 0:
            self.d.text((x * SS, y * SS), s, font=fonte(tam, neg), fill=mix(cor, a, fundo), anchor=anc)

    def bloco(self, x, y, s, tam, larg, cor=BRANCO, neg=False, a=1.0, fundo=BG, entre=1.3):
        for lin in quebrar(s, tam, larg, neg):
            self.txt(x, y, lin, tam, cor, neg, a=a, fundo=fundo)
            y += tam * entre
        return y

    def caixa(self, x0, y0, x1, y1, fill=PAINEL, borda=None, r=18, w=2):
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], r * SS, fill=fill,
                                 outline=borda, width=w * SS if borda else 0)

    def linha(self, pts, cor, w=4):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=cor, width=int(w * SS), joint="curve")

    def disco(self, x, y, r, cor, borda=None, w=2):
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=cor, outline=borda,
                       width=w * SS if borda else 0)

    def anel(self, x, y, r, cor, w=4):
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], outline=cor, width=int(w * SS))

    def seta(self, x0, y0, x1, y1, cor, w=6, cab=20):
        ang = math.atan2(y1 - y0, x1 - x0)
        bx, by = x1 - cab * math.cos(ang), y1 - cab * math.sin(ang)
        self.linha([(x0, y0), (bx, by)], cor, w)
        p = [(x1, y1), (bx + cab * .6 * math.sin(ang), by - cab * .6 * math.cos(ang)),
             (bx - cab * .6 * math.sin(ang), by + cab * .6 * math.cos(ang))]
        self.d.polygon([(a * SS, b * SS) for a, b in p], fill=cor)

    def foto(self, img, caixa, zoom=1.0, cx=.5, cy=.5, a=1.0):
        """Preenche a caixa com a imagem (recorte central deslocável); a<1 esmaece sobre o fundo atual."""
        x0, y0, x1, y1 = caixa
        tw, th = int((x1 - x0) * SS), int((y1 - y0) * SS)
        iw, ih = img.size
        esc = max(tw / iw, th / ih) * zoom
        cw, ch = tw / esc, th / esc
        l = clamp(cx * iw - cw / 2, 0, iw - cw)
        t = clamp(cy * ih - ch / 2, 0, ih - ch)
        rec = img.resize((tw, th), Image.BILINEAR, box=(l, t, l + cw, t + ch))
        pos = (int(x0 * SS), int(y0 * SS))
        if a < 1:
            rec = Image.blend(self.im.crop((pos[0], pos[1], pos[0] + tw, pos[1] + th)), rec, clamp(a))
        self.im.paste(rec, pos)

    def fim(self, fade):
        out = self.im.reduce(SS)
        return Image.blend(Image.new("RGB", out.size, BG), out, fade) if fade < 1 else out


def quebrar(s, tam, larg, neg=False):
    f, linhas, cur = fonte(tam, neg), [], ""
    for p in s.split():
        t = f"{cur} {p}".strip()
        if f.getlength(t) <= larg * SS or not cur:
            cur = t
        else:
            linhas.append(cur)
            cur = p
    return linhas + ([cur] if cur else [])


def abrir(nome, caixa=None):
    im = Image.open(nome).convert("RGB")
    return im.crop(caixa) if caixa else im


# ---------------------------------------------------------------- narração
def duracao(wav):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def palavras_proporcionais(texto, dur):
    toks = texto.split()
    pesos = [len(t) + 2 for t in toks]
    tot, ac, saida = sum(pesos), 0, []
    for t, p in zip(toks, pesos):
        saida.append((t, dur * ac / tot, dur * (ac + p) / tot))
        ac += p
    return saida


def narracao_local(i, texto):
    wav, raw = OUT / f"cena_{i}.wav", OUT / f"cena_{i}_raw.wav"
    txt, js = OUT / f"cena_{i}.txt", OUT / f"cena_{i}.json"
    if not (wav.exists() and js.exists() and txt.exists() and txt.read_text(encoding="utf-8") == texto):
        txt.write_text(texto, encoding="utf-8")
        ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Maria Desktop')
$s.Rate = 1
$w = New-Object System.Collections.Generic.List[object]
$s.add_SpeakProgress({{ param($o,$e) $w.Add(@{{ text=$e.Text; offset=[double]$e.AudioPosition.TotalSeconds }}) }})
$s.SetOutputToWaveFile('{raw}')
$s.Speak([System.IO.File]::ReadAllText('{txt}', [System.Text.Encoding]::UTF8))
$s.Dispose()
[System.IO.File]::WriteAllText('{js}', ($w | ConvertTo-Json -Compress), [System.Text.Encoding]::UTF8)
"""
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ar", "48000", "-ac", "1",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(wav)], check=True)
    itens = json.loads(js.read_text(encoding="utf-8-sig"))
    dur = duracao(wav)
    toks = texto.split()
    if len(toks) != len(itens):
        print(f"cena {i}: {len(itens)} eventos de voz para {len(toks)} palavras; legenda sem pontuação", flush=True)
        toks = [it["text"] for it in itens]
    # Com Rate != 0, o SAPI informa AudioPosition sem aplicar a velocidade: reescala para o áudio real.
    fim_fala = dur - SILENCIO_FINAL_SAPI
    ultimo = float(itens[-1]["offset"]) + len(itens[-1]["text"]) * .11
    esc = fim_fala / ultimo
    pal = []
    for k, (it, tok) in enumerate(zip(itens, toks)):
        fim = float(itens[k + 1]["offset"]) * esc if k + 1 < len(itens) else fim_fala
        pal.append((tok, float(it["offset"]) * esc, fim))
    return wav, dur, pal


def _sem_pontuacao(texto):
    return re.sub(r"[,;:]", "", texto)


def preparar_narracao():
    OUT.mkdir(exist_ok=True)
    saida = []
    for i, texto in enumerate(CENAS, 1):
        clonada, tempos = VOZ / f"slide_{i:03d}.wav", VOZ / f"slide_{i:03d}.json"
        meta = json.loads(tempos.read_text(encoding="utf-8")) if tempos.exists() else {}
        # Pontuação não muda a fala: a voz clonada continua valendo, e a legenda usa a pontuação atual.
        if clonada.exists() and _sem_pontuacao(meta.get("texto", "")) == _sem_pontuacao(texto):
            pal = [tuple(q) for q in meta["palavras"]]
            toks = texto.split()
            if len(toks) == len(pal):
                pal = [(tok, ini, fim) for tok, (_, ini, fim) in zip(toks, pal)]
            saida.append((str(clonada), duracao(clonada), pal))
        else:
            wav, dur, pal = narracao_local(i, texto)
            saida.append((str(wav), dur, pal))
    return saida


class Tempo:
    """Dá o instante em que uma palavra é falada, para sincronizar as animações à voz."""

    def __init__(self, pal, dur):
        self.pal, self.dur = pal, dur

    def __call__(self, prefixo, n=0):
        vistos = 0
        for t, s, _ in self.pal:
            if t.lower().strip(",.:?!").startswith(prefixo):
                if vistos == n:
                    return s
                vistos += 1
        raise ValueError(f"palavra não encontrada na narração: {prefixo}")


def palavras_legenda(pal):
    """A fala diz "decibéis zê", mas a legenda mostra "dBZ"; os tempos das palavras não mudam."""
    saida = []
    for p in pal:
        if saida and saida[-1][0] == "decibéis" and p[0].startswith("zê"):
            saida[-1] = ("dBZ" + p[0][2:], saida[-1][1], p[2])
        else:
            saida.append(tuple(p))
    return saida


def legenda(tela, pal, t):
    """Duas partes: faixa fixa e bloco de palavras com a palavra atual em âmbar."""
    tela.d.rectangle([0, 950 * SS, W * SS, H * SS], fill=(6, 10, 20))
    pal = palavras_legenda(pal)
    blocos, cur = [], []
    for p in pal:
        cur.append(p)
        if sum(len(q[0]) + 1 for q in cur) > 58 or p[0][-1] in ".?:":
            blocos.append(cur)
            cur = []
    if cur:
        blocos.append(cur)
    atual = next((b for b in blocos if t < b[-1][2]), blocos[-1])
    if t < atual[0][1] - .6:
        return
    f = fonte(40, True)
    larg = sum(f.getlength(p[0] + " ") for p in atual) / SS
    x = (W - larg) / 2
    for p in atual:
        tela.txt(x, 990, p[0], 40, AMBAR if p[1] <= t < p[2] else BRANCO, True, fundo=(6, 10, 20))
        x += f.getlength(p[0] + " ") / SS


# ---------------------------------------------------------------- cenas
def cena1(tl, t, b, rec, dur):
    fotos = rec["fotos"]
    t1, t2 = b("reportagens"), b("mas")
    idx = 0 if t < t1 else 1
    inicio = [0, t1][idx]
    z = 1.04 + .012 * (t - inicio)
    tl.foto(fotos[idx], (0, 0, W, 950), z, a=suave((t - inicio) / .5) if idx else 1)
    cred = "Imagens: reprodução de reportagens em vídeo"
    tl.caixa(1370, 908, 1905, 945, fill=BG, r=6)
    tl.txt(1890, 913, cred, 22, BRANCO, anc="ra")
    if t < t1:
        tl.caixa(1370, 864, 1905, 901, fill=BG, r=6)
        tl.txt(1890, 869, "Narração: voz clonada por computador", 22, BRANCO, anc="ra")
    if t < t1:
        a = suave((t - b("cento")) / .4)
        if a > 0:
            tl.caixa(70, 70, 700, 260, fill=BG)
            tl.txt(100, 80, "126 km/h", 104, AMBAR, True, a=a)
            tl.txt(102, 208, "Chapecó, 04/11/2026", 32, BRANCO, a=a)
    elif t < t2:
        heads = ["Tornado atinge Chapecó (SC) e aeroporto tem estruturas arrancadas",
                 "Tornado causa destruição em aeroporto de Chapecó",
                 "Defesa Civil de SC confirmou a ocorrência de um tornado"]
        for k, s in enumerate(heads):
            a = suave((t - t1 - k * .55) / .35)
            if a > 0:
                y = 90 + k * 130
                dx = (1 - a) * -60
                tl.caixa(70 + dx, y, 1320 + dx, y + 110, fill=(255, 255, 255), r=8)
                tl.d.rectangle([(70 + dx) * SS, y * SS, (84 + dx) * SS, (y + 110) * SS], fill=VERMELHO)
                tl.bloco(108 + dx, y + 12, s, 34, 1190, (15, 23, 42), True, fundo=(255, 255, 255), entre=1.2)
    else:
        a = suave((t - t2) / .5)
        tl.im.paste(Image.blend(tl.im, Image.new("RGB", tl.im.size, BG), .78 * a))
        tl.txt(520, 390, "TORNADO", 92, CORAL, True, "mm", a=a)
        tl.txt(960, 390, "ou", 54, BRANCO, False, "mm", a=a)
        a2 = suave((t - b("microexplosão")) / .4)
        tl.txt(1400, 390, "MICROEXPLOSÃO", 84, CIANO, True, "mm", a=a2)
        tl.txt(960, 590, "Como saber qual foi?", 66, BRANCO, True, "mm", a=suave((t - b("como")) / .3))


def _particulas(n, sem):
    r = random.Random(sem)
    return [(r.random(), r.random() * 2 * math.pi, r.uniform(.8, 1.2)) for _ in range(n)]


TOR = _particulas(90, 4)
MIC = _particulas(90, 5)


def cena2(tl, t, b, rec, dur):
    cen = {"t": (500, 450), "m": (1420, 450)}
    R = 320
    tl.linha([(960, 40), (960, 900)], LINHA, 2)
    a_t = suave((t - b("tornado")) / .4)
    a_m = suave((t - b("microexplosão")) / .4)
    t_dano = b("padrão")
    dim = 1 - .6 * suave((t - t_dano) / .6)
    tl.txt(*(500, 60), "TORNADO", 62, CORAL, True, "mm", a=max(.25, a_t))
    tl.txt(*(1420, 60), "MICROEXPLOSÃO", 62, CIANO, True, "mm", a=max(.25, a_m))
    tl.txt(500, 122, "o ar converge e gira", 34, BRANCO, False, "mm", a=a_t)
    tl.txt(1420, 122, "o ar desce e se espalha", 34, BRANCO, False, "mm", a=a_m)
    cx, cy = cen["t"]
    cy += 40
    tl.anel(cx, cy, R, mix(LINHA, .7), 2)
    for p0, a0, v in TOR:
        pts = []
        for k in range(6):
            p = (p0 + t * .16 * v - k * .012) % 1
            r = R * (1 - p) ** .8 + 12
            ang = a0 + 7.5 * p  # horário: sentido ciclônico no Hemisfério Sul
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        if abs(pts[0][0] - pts[-1][0]) < 90 and abs(pts[0][1] - pts[-1][1]) < 90:
            tl.linha(pts, mix(CORAL, a_t * dim * .95), 3.5)
    mx, my = cen["m"]
    my += 40
    tl.anel(mx, my, R, mix(LINHA, .7), 2)
    for p0, a0, v in MIC:
        p = (p0 + t * .24 * v) % 1
        r0 = R * p + 34
        if r0 > R:
            continue
        r1 = max(34, r0 - 34)
        tl.linha([(mx + r1 * math.cos(a0), my + r1 * math.sin(a0)), (mx + r0 * math.cos(a0), my + r0 * math.sin(a0))],
                 mix(CIANO, a_m * dim * .95), 3.5)
    if a_m > 0:
        tl.anel(mx, my, 28, mix(CIANO, a_m), 4)
        for s in (-1, 1):
            tl.linha([(mx - 16, my + s * 16), (mx + 16, my - s * 16)], mix(CIANO, a_m), 4)
    # árvores tombadas: a ponta indica o sentido da queda
    if t > t_dano:
        rng = random.Random(9)
        for k in range(46):
            at = suave((t - t_dano - k * .035) / .25)
            ang, r = rng.random() * 2 * math.pi, rng.uniform(.3, .95) * R
            for lado in ("t", "m"):
                ox, oy = (cx, cy) if lado == "t" else (mx, my)
                x, y = ox + r * math.cos(ang), oy + r * math.sin(ang)
                dang = ang + math.pi - .75 if lado == "t" else ang
                L = 32 * at
                if at > 0:
                    tl.seta(x, y, x + L * math.cos(dang), y + L * math.sin(dang), AMBAR, 5, 14)
    tl.txt(500, 905, "Danos convergentes", 42, AMBAR, True, "mm", a=suave((t - b("convergente")) / .3))
    tl.txt(1420, 905, "Danos divergentes", 42, AMBAR, True, "mm", a=suave((t - b("divergente")) / .3))


CHUVA = _particulas(170, 6)


def cena3(tl, t, b, rec, dur):
    cx, solo, topo = 660, 860, 280
    tl.d.rectangle([0, solo * SS, 1290 * SS, 950 * SS], fill=(44, 37, 32))
    for ex, ey, rx, ry in [(660, 170, 470, 115), (340, 210, 230, 75), (980, 215, 250, 75), (650, 245, 410, 75)]:
        tl.d.ellipse([(ex - rx) * SS, (ey - ry) * SS, (ex + rx) * SS, (ey + ry) * SS], fill=(92, 104, 125))
    # isoterma de 0 °C
    for x in range(30, 1270, 44):
        tl.linha([(x, 430), (x + 24, 430)], mix(BRANCO, .5), 2)
    tl.txt(36, 390, "0 °C", 30, CINZA)
    a_peso = suave((t - b("peso")) / .5)
    a_frio = suave((t - b("evaporação")) / .5)
    # chuva e granizo
    for p0, a0, v in CHUVA:
        p = (p0 + t * .34 * v) % 1
        y = topo + (solo - topo) * p
        x = cx + (a0 / math.pi - 1) * (130 + 50 * p)
        cor = mix(CIANO if y > 430 else BRANCO, .3 + .6 * a_peso)
        tl.linha([(x, y - 18), (x, y)], cor, 3)
        if int(a0 * 10) % 7 == 0:
            tl.disco(x, y + 3, 6, cor)
    # coluna fria
    if a_frio > 0:
        for k in range(5):
            x = cx - 120 + k * 60
            yy = 330 + ((t * 120 + k * 73) % 420)
            tl.seta(x, yy, x, yy + 90, mix((96, 165, 250), a_frio), 8, 26)
    # espalhamento e anel de vórtice
    tc = b("chegar")
    a_v = suave((t - tc) / 1.2)
    if a_v > 0:
        d = 130 + 420 * a_v
        for s in (-1, 1):
            xv = cx + s * d
            tl.seta(cx + s * 150, solo - 30, xv, solo - 30, mix(AMBAR, a_v), 10, 30)
            r = 62
            yc = solo - r - 8
            pts = []
            for k in range(26):
                ang = s * (t * 3.6) + k * .21
                pts.append((xv + s * 24 + r * math.cos(ang), yc + r * math.sin(ang)))
            tl.linha(pts, mix(CIANO, a_v), 5)
    a_r = suave((t - b("superar")) / .3)
    tl.txt(1040, 640, "> 120 km/h", 66, AMBAR, True, "mm", a=a_r)
    # cartões
    def cartao(y, h, cab, s, a, cor):
        if a <= 0:
            return
        tl.caixa(1320, y, 1880, y + h, borda=mix(cor, a, PAINEL))
        tl.txt(1350, y + 18, cab, 40, cor, True, a=a, fundo=PAINEL)
        tl.bloco(1350, y + 78, s, 32, 505, BRANCO, a=a, fundo=PAINEL)

    cartao(60, 200, "Carga", "O peso da chuva e do granizo arrasta o ar", a_peso, CIANO)
    cartao(285, 200, "Resfriamento", "Evaporação e fusão esfriam o ar", a_frio, (147, 197, 253))
    a_d = suave((t - b("denso")) / .4)
    cartao(510, 165, "Mais denso", "Ele afunda com mais força", a_d, AMBAR)
    tl.caixa(1320, 700, 1880, 915, borda=LINHA)
    tl.txt(1600, 755, "B ≈ g ( θ'/θ₀ − q_h )", 50, BRANCO, True, "mm", fundo=PAINEL)
    tl.txt(1350, 800, "B: flutuabilidade; θ': déficit térmico;", 27, CINZA, fundo=PAINEL)
    tl.txt(1350, 833, "q_h: razão de mistura de chuva e gelo", 27, CINZA, fundo=PAINEL)
    tl.txt(1350, 866, "Forma simplificada.", 27, CINZA, fundo=PAINEL)


def cena4(tl, t, b, rec, dur):
    tl.txt(60, 30, "O sistema em arco", 54, BRANCO, True)
    # animação real: echomax sobre GOES-19, 13:00 a 13:54 UTC
    qs = rec["composicao"]
    t1 = b("favorece")
    k = min(len(qs) - 1, int(clamp(t / max(t1, 1)) * len(qs)))
    tv = b("visível")
    if tv <= t < t1:
        tl.foto(rec["visivel"], (60, 110, 1240, 774), a=suave((t - tv) / .35))
        tl.txt(60, 782, "GOES-19, canal 2 (NOAA). Posição do núcleo extrapolada da trilha do radar", 26, CINZA)
        tl.caixa(1270, 110, 1860, 774, borda=CIANO)
        tl.txt(1300, 130, "Visível, 0,5 km", 38, CIANO, True, fundo=PAINEL)
        tl.txt(1300, 195, "Overshoots", 76, BRANCO, True, fundo=PAINEL)
        tl.bloco(1300, 325, "Aglomerado borbulhante a 6 km da trilha do núcleo, deslocando-se a 33 e 41 m/s; o núcleo, a 40 m/s", 36, 530, BRANCO, fundo=PAINEL)
        return
    tl.foto(qs[k], (60, 110, 879, 774))
    utc = 13 * 60 + 6 * k
    tl.txt(1860, 44, f"{utc // 60}:{utc % 60:02d} UTC ({utc // 60 - 3}:{utc % 60:02d} BRT)", 44, AMBAR, True, "ra")
    tl.txt(60, 782, "Echomax do radar de Chapecó sobre GOES-19, canal 13 (dados SDC/SC e NOAA)", 26, CINZA)
    x0, x1 = 910, 1860
    if t < t1:
        def cartao(y, cab, val, txt, a, cor):
            tl.caixa(x0, y, x1, y + 325, borda=mix(cor, max(a, .15), PAINEL))
            tl.txt(x0 + 30, y + 18, cab, 38, cor, True, a=a, fundo=PAINEL)
            tl.txt(x0 + 30, y + 72, val, 76, BRANCO, True, a=a, fundo=PAINEL)
            tl.bloco(x0 + 30, y + 190, txt, 36, 890, BRANCO, a=a, fundo=PAINEL)

        cartao(110, "Radar", "61 dBZ", "em até 5 km do aeroporto, às 10:30; a linha em arco é nítida", suave((t - b("radar")) / .4), VERMELHO)
        cartao(449, "Satélite", "−79 → −85 °C", "topo mais frio em até 40 km de Chapecó, de 10:00 a 10:20; em seguida, aquece", suave((t - b("satélite")) / .4), CIANO)
    else:
        y0, y1 = 110, 774
        tl.caixa(x0, y0, x1, y1)
        tl.txt(x0 + 30, y0 + 20, "Esquema conceitual", 30, CINZA, fundo=PAINEL)
        x0 += 180  # centraliza o desenho na caixa
        a_e = suave((t - t1) / .5)
        yc, h = (y0 + y1) / 2 + 20, 250
        pts, trasto = [], []
        for j in range(41):
            y = yc - h + 2 * h * j / 40
            x = x0 + 260 + 170 * (1 - ((y - yc) / h) ** 2)
            pts.append((x, y))
            trasto.append((x - 170, y))
        tl.d.polygon([(u * SS, v * SS) for u, v in pts + trasto[::-1]], fill=(43, 72, 92))
        tl.linha(pts, VERMELHO, 28)
        tl.linha([(u + 16, v) for u, v in pts], AMBAR, 6)
        tl.seta(x0 + 30, yc, x0 + 390, yc, mix(CIANO, a_e, PAINEL), 11, 32)
        tl.txt(x0 + 30, yc - 56, "jato traseiro", 28, CIANO, a=a_e, fundo=PAINEL)
        for dy in (-90, 0, 90):
            e = (t * 1.3 + dy) % 1
            tl.seta(x0 + 460 + 8 * e, yc + dy, x0 + 545 + 20 * e, yc + dy, mix(AMBAR, a_e, PAINEL), 8, 24)
    a_x = suave((t - b("exclui")) / .35)
    if a_x > 0:
        tl.caixa(60, 825, 1860, 935, fill=(70, 22, 22), borda=CORAL)
        tl.txt(960, 880, "Arco não descarta tornado: sistemas lineares também podem gerá-los", 44, BRANCO, True, "mm",
               a=a_x, fundo=(70, 22, 22))


PAINEIS = [
    ("chuva", "1 · Chuva intensa", "≈ 60 dBZ", "58, 59,5 e 58 dBZ na camada mais baixa às 10:24, 10:30 e 10:36, só com CC ≥ 0,90. Não há descida nítida de um máximo", VERMELHO),
    ("vento", "2 · Vento na camada baixa", "27 → 18 m/s", "Componente em direção ao radar, de 130 m a 810 m acima do radar, às 10:30. Compatível com saída de ar; é uma só varredura", CIANO),
    ("cisalhamento", "3 · Cisalhamento", "até ~0,7 km", "Em 2 km, às 10:30, o núcleo está entre os maiores da varredura até ~0,7 km acima do radar. Radar único não separa rotação de cisalhamento", AMBAR),
]
NOMES = ["Chuva por altura", "Perfil do vento", "Cisalhamento"]


def cena5(tl, t, b, rec, dur):
    atual = 0
    for k, p in enumerate(PAINEIS):
        if t >= b(p[0]):
            atual = k
    _, sig, val, txt, cor = PAINEIS[atual]
    ini = b(PAINEIS[atual][0]) if t >= b(PAINEIS[0][0]) else 0
    a = suave((t - ini) / .35) if ini else 1
    tl.foto(rec["paineis"][atual], (50, 80, 1150, 660), a=a)
    tl.txt(50, 22, "Radar de Chapecó, 04/11/2026, dados brutos", 36, BRANCO, True)
    for k in range(3):
        x = 50 + k * 372
        tl.foto(rec["paineis"][k], (x, 680, x + 356, 800))
        ativo = k == atual
        tl.d.rectangle([x * SS, 680 * SS, (x + 356) * SS, 800 * SS], outline=cor if ativo else LINHA, width=(5 if ativo else 2) * SS)
        tl.txt(x + 178, 825, NOMES[k], 26, BRANCO if ativo else CINZA, ativo, "mm")
    tl.caixa(1190, 80, 1870, 800, borda=mix(cor, a, PAINEL), w=3)
    tl.txt(1230, 110, sig, 42, cor, True, a=a, fundo=PAINEL)
    tl.txt(1230, 185, val, 72, BRANCO, True, a=a, fundo=PAINEL)
    tl.bloco(1230, 310, txt, 40, 600, BRANCO, a=a, fundo=PAINEL)
    tl.txt(1230, 735, "Aeroporto: feixe a ~100 m do radar, ~280 m do chão", 26, CINZA, fundo=PAINEL)
    a_f = suave((t - b("separa")) / .35)
    if a_f > 0:
        tl.caixa(50, 845, 1870, 935, fill=(20, 60, 74), borda=CIANO)
        tl.txt(960, 890, "Sinal localizado, mas ambíguo: esta pista fica em aberto", 48, BRANCO, True, "mm", a=a_f, fundo=(20, 60, 74))


FORMAS = _particulas(26, 7)


def cena6(tl, t, b, rec, dur):
    tl.txt(960, 62, "Isso encerra o caso? Ainda não.", 62, BRANCO, True, "mm")
    cols = [(50, "primeiro", "1 · Velocidade", "Varredura a cada 6 min e feixe mais baixo a ~280 m do chão: um vórtice curto e raso poderia escapar", CORAL),
            (660, "segundo", "2 · Polarimetria", "CC ≈ 0,7 não separa: granizo em fusão ou detritos erguidos pelo vento também a reduzem", AMBAR),
            (1270, "terceiro", "3 · Campo", "Falta o levantamento: direção de queda de árvores e estruturas. Falta também o vento medido na passagem", VERDE)]
    for x, pal, cab, txt, cor in cols:
        a = suave((t - b(pal)) / .4)
        tl.caixa(x, 125, x + 600, 900, borda=mix(cor, max(a, .15), PAINEL))
        if a <= 0:
            tl.txt(x + 300, 480, cab[0], 150, LINHA, True, "mm", fundo=PAINEL)
            continue
        tl.txt(x + 34, 150, cab, 46, cor, True, a=a, fundo=PAINEL)
        tl.bloco(x + 34, 225, txt, 36, 535, BRANCO, a=a, fundo=PAINEL)
        cx, cy = x + 300, 650
        if pal == "primeiro":
            s = 1 + .05 * math.sin(t * 3)
            tl.disco(cx - 88, cy, 84 * s, mix(VERMELHO, a, PAINEL))
            tl.disco(cx + 88, cy, 84 * s, mix(VERDE, a, PAINEL))
            tl.seta(cx - 88, cy + 42, cx - 88, cy - 45, BRANCO, 8, 26)
            tl.seta(cx + 88, cy - 42, cx + 88, cy + 45, BRANCO, 8, 26)
            tl.txt(cx - 88, cy + 145, "afasta", 30, BRANCO, False, "mm", fundo=PAINEL)
            tl.txt(cx + 88, cy + 145, "aproxima", 30, BRANCO, False, "mm", fundo=PAINEL)
        elif pal == "segundo":
            for p0, a0, v in FORMAS:
                y = 450 + ((p0 + t * .12 * v) % 1) * 400
                dx = (a0 / math.pi - 1) * 125
                if int(a0 * 10) % 2:
                    tl.disco(cx - 135 + dx, y, 16, mix(CIANO, a, PAINEL))
                else:
                    r = 26
                    ang = t * 3 * v + a0
                    q = [(cx + 135 + dx + r * math.cos(ang + j * 2.2 + (j % 2) * .5),
                          y + r * .55 * math.sin(ang + j * 2.2)) for j in range(3)]
                    tl.d.polygon([(u * SS, w * SS) for u, w in q], fill=mix(AMBAR, a, PAINEL))
            tl.txt(cx - 135, 870, "granizo", 30, CIANO, True, "mm", fundo=PAINEL)
            tl.txt(cx + 135, 870, "detritos", 30, AMBAR, True, "mm", fundo=PAINEL)
        else:
            rng = random.Random(3)
            k = .5 + .5 * math.sin((t - b(pal)) * 1.3)
            for j in range(34):
                ang, r = rng.random() * 2 * math.pi, rng.uniform(55, 205)
                gx, gy = cx + r * math.cos(ang), cy + r * math.sin(ang) * .95
                alvo = ang if k > .5 else ang + math.pi - .75
                tl.seta(gx, gy, gx + 40 * math.cos(alvo), gy + 40 * math.sin(alvo),
                        mix(CIANO if k > .5 else CORAL, a, PAINEL), 6, 16)
            tl.txt(cx, 870, "diverge" if k > .5 else "converge", 34, CIANO if k > .5 else CORAL, True, "mm", fundo=PAINEL)


def cena7(tl, t, b, rec, dur):
    tq = b("próxima") - .3
    if t < tq:
        tl.txt(960, 130, "O que os dados mostram até agora", 54, BRANCO, True, "mm", a=suave(t / .5))
        a = suave((t - b("microexplosão")) / .35)
        tl.caixa(120, 250, 930, 700, borda=mix(CIANO, max(a, .15), PAINEL))
        tl.txt(525, 330, "Microexplosão", 66, CIANO, True, "mm", a=a, fundo=PAINEL)
        tl.txt(525, 400, "dentro da linha em arco", 40, CIANO, True, "mm", a=a, fundo=PAINEL)
        tl.txt(525, 540, "a melhor hipótese,", 44, BRANCO, False, "mm", a=a, fundo=PAINEL)
        tl.txt(525, 600, "ainda não provada", 44, BRANCO, True, "mm", a=a, fundo=PAINEL)
        a = suave((t - b("tornado")) / .35)
        tl.caixa(990, 250, 1800, 700, borda=mix(CORAL, max(a, .15), PAINEL))
        tl.txt(1395, 360, "Tornado", 66, CORAL, True, "mm", a=a, fundo=PAINEL)
        tl.txt(1395, 540, "não descartado:", 44, BRANCO, False, "mm", a=a, fundo=PAINEL)
        tl.txt(1395, 600, "o descarte depende do campo", 44, BRANCO, True, "mm", a=a, fundo=PAINEL)
        tl.txt(960, 810, "Falta o levantamento de danos em campo", 46, AMBAR, True, "mm", a=a)
    elif t < b("ressalva") - .3:
        tl.txt(960, 240, "Na próxima manchete sobre um vendaval:", 46, CINZA, False, "mm", a=suave((t - tq) / .4))
        a = suave((t - b("para")) / .5)
        tl.txt(960, 400, "Para que lado caíram", 106, BRANCO, True, "mm", a=a)
        tl.txt(960, 530, "as árvores?", 106, AMBAR, True, "mm", a=a)
    else:
        tl.txt(960, 210, "Isto é ciência, não veredito", 84, BRANCO, True, "mm", a=suave((t - b("ressalva") + .3) / .4))
        a = suave((t - b("código")) / .4)
        tl.txt(960, 390, "Código e resultados abertos, para usar e refutar:", 46, CINZA, False, "mm", a=a)
        tl.txt(960, 500, "github.com/reinaldohaas/echo_em_arco", 68, AMBAR, True, "mm", a=a)
        a2 = suave((t - rec["pal"][-1][2] - .05) / .3)
        tl.txt(960, 720, "UFSC · Prof. Reinaldo Haas · Análise preliminar", 34, CINZA, False, "mm", a=a2)
        tl.txt(960, 770, "Voz clonada por programa de computador", 28, CINZA, False, "mm", a=a2)


RENDER = [cena1, cena2, cena3, cena4, cena5, cena6, cena7]


def recursos(pal):
    j = A / "jornais"
    comp = BASE / "satelite" / "figuras" / "composicao"
    r2 = A / "radar_v2"
    return {
        "pal": pal,
        "fotos": [abrir(j / "reportagem_05_siFvd4jKE3s.jpg"), abrir(j / "reportagem_03_kyrtUfC92tY.jpg")],
        # 13:00 a 13:54 UTC; recorta o título e a margem branca dos quadros de 1920x1080
        "composicao": [abrir(comp / f"c_{n:02d}.png").resize((1920, 1080)).crop((650, 34, 1920, 1080)) for n in range(10, 20)],
        "paineis": [abrir(r2 / n) for n in ("chuva.png", "vento.png", "cisalhamento.png")],
        "visivel": abrir(r2 / "visivel_1330.png"),
    }


def quadro(i, t, dur, pal, rec):
    tl = Tela()
    b = Tempo(pal, dur)
    RENDER[i](tl, t, b, rec, dur)
    legenda(tl, pal, t)
    fade = min(suave(t / .35), suave((dur - t) / .35))
    return tl.fim(fade)


def render_cena(args):
    i, wav, dur_voz, pal = args
    # a última cena segura o crédito, com o aviso de voz clonada, tempo suficiente para a leitura
    dur = dur_voz + FIM_MUDO + (3.0 if i == len(CENAS) - 1 else 0)
    saida = OUT / f"cena_{i + 1}.mp4"
    rec = recursos(pal)
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", wav, "-af", f"apad=whole_dur={dur:.3f}", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "1", str(saida)],
        stdin=subprocess.PIPE)
    for n in range(int(dur * FPS)):
        p.stdin.write(quadro(i, n / FPS, dur, pal, rec).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError(f"ffmpeg falhou na cena {i + 1}")
    print(f"cena {i + 1} pronta: {dur:.1f} s", flush=True)
    return saida


def gerar_quadros(narr):
    for i, (_, dur, pal) in enumerate(narr):
        rec = recursos(pal)
        for k, t in enumerate(dur * f for f in (.2, .55, .97)):
            quadro(i, t, dur + FIM_MUDO, pal, rec).save(OUT / f"teste_{i + 1}_{k}.png")
    print("quadros de teste em", OUT)


def gerar_video(narr):
    tarefas = [(i, wav, dur, pal) for i, (wav, dur, pal) in enumerate(narr)]
    with mp.Pool(min(7, max(2, mp.cpu_count() - 1))) as pool:
        partes = pool.map(render_cena, tarefas, 1)
    lista = OUT / "cenas.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in partes), encoding="utf-8")
    final = BASE / "video_chapeco_v2.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
    print(final, f"{duracao(final):.1f} s")


def pacote_vlab(narr):
    from pptx import Presentation
    from pptx.util import Inches
    nome = "echo_em_arco_v2"
    pasta = BASE / "video_work" / nome / "slides_img"
    pasta.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    roteiro = []
    for i, ((_, dur, pal), fala) in enumerate(zip(narr, CENAS)):
        arq = pasta / f"slide_{i + 1:03d}.png"
        quadro(i, dur * .9, dur + FIM_MUDO, pal, recursos(pal)).save(arq)
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.shapes.add_picture(str(arq), 0, 0, width=prs.slide_width, height=prs.slide_height)
        s.notes_slide.notes_text_frame.text = fala
        roteiro.append({"slide": i + 1, "imagem": arq.name, "texto_fala": fala, "texto_original": fala, "texto_exibicao": fala})
    pptx = BASE / f"{nome}.pptx"
    prs.save(pptx)
    rot = BASE / f"roteiro-{nome}.json"
    rot.write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
    leia = BASE / "LEIA-ME-vlab-v2.txt"
    leia.write_text(
        "Voz clonada, versão 2. Dentro de /home/jovyan/privado/videoaula no vlab:\n\n"
        f"  unzip -o {nome}-vlab.zip\n"
        f"  /home/jovyan/envs/voz/bin/python gerador_de_video_e_som.py {nome}.pptx --roteiro roteiro-{nome}.json -v reinaldo_haas --hf-home /tmp/hf\n"
        f"  zip -j {nome}-audios-vlab.zip video_work/{nome}/audio/slide_*.wav\n\n"
        f"Traga o zip de volta, extraia os .wav em video_work/{nome}/audio/ e rode: python gerar_video_v2.py\n",
        encoding="utf-8")
    with zipfile.ZipFile(BASE / f"{nome}-vlab.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p, dentro in [(rot, rot.name), (pptx, pptx.name), (leia, leia.name)]:
            z.write(p, dentro)
        for p in sorted(pasta.glob("slide_*.png")):
            z.write(p, f"video_work/{nome}/slides_img/{p.name}")
    print(BASE / f"{nome}-vlab.zip")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quadros", action="store_true")
    ap.add_argument("--vlab", action="store_true")
    ap.add_argument("--falas", action="store_true", help="só grava video_v2/falas.json para gerar_voz_local.py")
    a = ap.parse_args()
    if a.falas:
        OUT.mkdir(exist_ok=True)
        (OUT / "falas.json").write_text(json.dumps(CENAS, ensure_ascii=False, indent=1), encoding="utf-8")
        raise SystemExit
    n = preparar_narracao()
    print("duração da narração:", f"{sum(d for _, d, _ in n):.1f} s", flush=True)
    if a.quadros:
        gerar_quadros(n)
    elif a.vlab:
        pacote_vlab(n)
    else:
        gerar_video(n)
