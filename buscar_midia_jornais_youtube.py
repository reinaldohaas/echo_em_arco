# -*- coding: utf-8 -*-
r"""
buscar_midia_jornais_youtube.py
Busca fotos reais de jornais sobre os estragos em Chapecó (Aeroporto Serafim Enoss Bertaso,
galpões, árvores em linha reta) e vídeos do YouTube do evento de 04/11/2026 e de microexplosões.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from PIL import Image
import io

BASE_DIR = r"C:\Users\haas\github\echo_em_arco"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
JORNAIS_DIR = os.path.join(ASSETS_DIR, "jornais")
os.makedirs(JORNAIS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def fetch_url(url, timeout=12):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search_bing_images(query, max_results=6):
    q = urllib.parse.quote(query)
    url = f"https://www.bing.com/images/search?q={q}&form=HDRSC2&first=1"
    html = fetch_url(url).decode("utf-8", errors="ignore")
    # Extract murl (media URL) and turl (thumbnail URL) and title
    murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?)&quot;', html)
    turls = re.findall(r'turl&quot;:&quot;(https?://[^&]+?)&quot;', html)
    titles = re.findall(r't&quot;:&quot;([^&]+?)&quot;', html)
    results = []
    for i in range(min(max_results, len(turls))):
        results.append({
            "murl": murls[i] if i < len(murls) else turls[i],
            "turl": turls[i],
            "title": titles[i] if i < len(titles) else query
        })
    return results


def search_youtube_videos(query, max_results=5):
    q = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={q}"
    html = fetch_url(url).decode("utf-8", errors="ignore")
    vids = []
    seen = set()
    for m in re.finditer(r'"videoId":"([A-Za-z0-9_-]{11})".*?"title":\{"runs":\[\{"text":"([^"]+)"\}', html):
        vid, title = m.group(1), m.group(2)
        if vid not in seen:
            seen.add(vid)
            vids.append({"videoId": vid, "title": title, "url": f"https://www.youtube.com/watch?v={vid}"})
            if len(vids) >= max_results:
                break
    return vids


def main():
    queries_img = [
        ("aeroporto_chapeco", "Aeroporto Chapecó estragos temporal vento 126 km/h"),
        ("destruicao_chapeco", "Chapecó temporal estragos árvores telhados Defesa Civil"),
        ("microburst_dano", "wet microburst straight line wind damage trees"),
    ]
    saved_images = []
    for prefix, q in queries_img:
        print(f"Buscando imagens: {q}")
        items = search_bing_images(q, max_results=6)
        count = 0
        for idx, it in enumerate(items):
            for candidate_url in [it["murl"], it["turl"]]:
                try:
                    raw = fetch_url(candidate_url, timeout=8)
                    im = Image.open(io.BytesIO(raw)).convert("RGB")
                    if im.width >= 300 and im.height >= 200:
                        out_name = f"{prefix}_{count+1:02d}.jpg"
                        out_path = os.path.join(JORNAIS_DIR, out_name)
                        im.save(out_path, quality=92)
                        saved_images.append({"file": out_name, "title": it["title"], "query": q, "size": f"{im.width}x{im.height}"})
                        print(f"  Salvo: {out_name} ({im.width}x{im.height}) - {it['title'][:60]}")
                        count += 1
                        break
                except Exception:
                    pass
            if count >= 2:
                break

    yt_queries = [
        "Chapecó temporal aeroporto vento 126 km/h",
        "Chapecó tornado microexplosão Defesa Civil",
        "wet microburst animation downburst",
    ]
    yt_results = []
    for yq in yt_queries:
        print(f"Buscando YouTube: {yq}")
        vids = search_youtube_videos(yq, max_results=4)
        for v in vids:
            print(f"  YouTube: {v['videoId']} | {v['title']}")
            yt_results.append(v)

    meta_path = os.path.join(ASSETS_DIR, "midia_externa.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"images": saved_images, "youtube": yt_results}, f, ensure_ascii=False, indent=2)
    print("Metadados salvos em:", meta_path)


if __name__ == "__main__":
    main()
