# Microexplosão ou tornado em Chapecó? (04/11/2026)

Análise preliminar do evento de 4 de novembro de 2026, com volumes brutos do radar banda S de Chapecó (SDC/SC) e imagens do GOES-19. Horários locais (UTC−3).

**Isto é ciência, não veredito.** Use o código e os resultados, e tente refutá-los. Críticas com dados ou literatura são bem-vindas nas [issues](https://github.com/reinaldohaas/echo_em_arco/issues).

## Diagnóstico

**Hipótese principal: microexplosão dentro de uma linha em arco. O caso não está fechado.** A Defesa Civil confirmou tornado. Estes dados pesam contra tornado supercelular, sobretudo pela ausência de BWER, mas não permitem descartar tornado de sistema linear. O teste que falta é o levantamento da direção de queda em campo.

Vídeos e fotos publicados, com a contagem a favor e contra cada hipótese, estão em [`CHECKLIST_HIPOTESES.md`](CHECKLIST_HIPOTESES.md). Contando só dados observados e aplicando a literatura citada, 12 itens favorecem vento linear e nenhum favorece tornado supercelular, com o CC anômalo e o cisalhamento neutros. Nenhum é decisivo, e esses itens não distinguem microexplosão de outros mecanismos de vento linear. Ainda faltam a direção de queda e a série de vento durante a passagem.

| Contagem | A favor | Contra |
|---|---|---|
| Vento linear | 12 (3 médios, 9 fracos) | 0 |
| Tornado supercelular | 0 | 8 (1 forte, 1 médio, 6 fracos) |

Os pesos são julgamento e vários itens não são independentes. Tornado de sistema linear fica fora da contagem. Como taxa de base, Ashley et al. (2019) atribuem a sistemas lineares nos EUA ~15 relatos de vento severo por relato de tornado, mas ~2 por 1 em vento significativo; isso não é observação deste caso nem contagem de microexplosões.

| Evidência | Observado | Leitura |
|---|---|---|
| Forma no radar | Linha em arco, sem supercélula isolada | Favorece vento em linha reta; não exclui tornado |
| Corrente ascendente | ZDR de ~2 dB até 4,6–5,3 km às 10:12–10:18; topos esfriam de −79 °C para −85 °C até as 10:20 e depois aquecem | Compatível com microexplosão logo depois |
| Chuva perto do solo | Com CC ≥ 0,90, a camada mais baixa fica em 58, 59,5 e 58 dBZ (10:24, 10:30, 10:36); em 2–3 km, Z cai de 63,5 para 57 dBZ | Apoio fraco; não há descida nítida de um máximo |
| Vento atrás da linha, 10:30 | Componente radial de 27 m/s a 130 m e 18 m/s a 810 m | Compatível com saída de ar; só uma varredura |
| Cisalhamento | Às 10:30, em 2 km e sem *gates* dobrados, fica entre os maiores da varredura até ~0,7 km acima do radar; não se mantém às 10:24 nem às 10:36 | Sinal localizado, mas ambíguo: radar único não separa rotação de cisalhamento |
| *Overshoot* | Topos borbulhantes no visível, 212 km² a ~6 km do núcleo às 10:30; canal 13 no limiar (contraste de 6,6 K para um limiar de 6,5 K) | Apoio moderado; há outros aglomerados no recorte |
| CC anômalo | CC ≈ 0,74, ZDR ≈ 0 e KDP ≈ 1,1 °/km nos *gates* mais fortes | **Principal pendência:** granizo em fusão ou detritos. Detritos não são argumento contra microexplosão, pois vento linear forte também pode erguê-los. |

## Corte vertical e hidrometeoros

Figura: [`assets/radar_v2/corte_vertical.png`](assets/radar_v2/corte_vertical.png). Números: [`radar/figuras/corte_vertical_saida.txt`](radar/figuras/corte_vertical_saida.txt) e [`radar/figuras/corte_vertical_complemento.txt`](radar/figuras/corte_vertical_complemento.txt).

- **A coluna é de chuva intensa.** De 10:12 a 10:24, os *gates* mais fortes têm CC de 0,98 a 0,99 e KDP de 2 a 3 °/km. O ZDR de 1,3 a 2,6 dB indica gotas grandes, sem assinatura de granizo grande seco.
- **O pico de Z está dentro do sinal anômalo.** Os 65,5 dBZ de 10:30 têm CC baixo. Excluindo CC < 0,90, o máximo é 59,5 dBZ.
- **O sinal anômalo não é chuva.** Ele aparece entre 10:24 e 10:30, fica a 3–4 km do centro da chuva intensa e, às 10:42, só resta na camada mais baixa, a ~9 km atrás do núcleo.
- **Ele enfraquece com a altura.** A fração de CC < 0,85 em Z ≥ 45 dBZ, às 10:30, é de 35–46% até 0,7 km, 25% a 0,9 km, 12% a 2,0 km e 1% a 3,2 km.
- **Os hidrometeoros sozinhos não decidem.** Esse perfil combina com granizo em fusão e com detritos. Vento forte sem rotação também pode erguer destroços, então detritos não provariam tornado.

## Limitações

- **Alturas:** são acima do radar (822 m de altitude). Sobre o aeroporto, o feixe de 0,5° passa ~100 m acima do radar, a cerca de 280 m do chão.
- **Nível de fusão:** ~3,0–3,3 km acima do radar, estimado depois da passagem (14:30–15:00 UTC), em chuva estratiforme. A figura antiga usava 3,8 km e está errada nesse ponto.
- **Posição do núcleo:** vem do ajuste de 10:30 (40 m/s para leste). Longe desse horário é extrapolação, e a análise supõe o mesmo movimento em todas as alturas.
- **Radar único:** com a fronteira quase radial, rotação e cisalhamento linear dão o mesmo sinal.
- **ZDR:** vale 0,4–0,7 dB em chuva fraca, o que sugere um pequeno viés positivo. Não foi corrigido.
- **Classes de hidrometeoros:** são limiares simples, escolhidos para leitura, não um classificador validado.
- **CC em granizo:** os valores de referência vêm de fontes secundárias, citadas em [`radar/RELATORIO_ROTACAO.md`](radar/RELATORIO_ROTACAO.md). A seção "Reconciliação" desse relatório traz o teste com controle único, que substitui as comparações anteriores.

## Vídeo

[`video_chapeco_v2.mp4`](video_chapeco_v2.mp4) resume esta análise, com voz clonada por computador.

## Reproduzir

- **Radar:** os volumes da SDC/SC não estão neste repositório. Os scripts esperam os arquivos em `radar/dados_chp_vol/`; as saídas numéricas estão em `radar/figuras/`.
- **Satélite:** o GOES-19 é público. `satelite/baixar_goes19.py` baixa os dados.
- **Caminhos:** alguns scripts têm caminhos desta máquina e precisam de ajuste.
- **Voz:** a amostra de voz não está no repositório, e a síntese precisa de uma amostra própria.

## Arquivos

| Arquivo | Descrição |
|---|---|
| [`index.html`](index.html) | Página com o vídeo, as evidências e os esquemas ilustrativos |
| [`gerar_video_v2.py`](gerar_video_v2.py) | Gerador do vídeo atual |
| [`gerar_voz_local.py`](gerar_voz_local.py), [`conferir_voz.py`](conferir_voz.py) | Síntese local da voz clonada e checagem por transcrição |
| [`radar/corte_vertical_hidrometeoros.py`](radar/corte_vertical_hidrometeoros.py), [`radar/corte_vertical_complemento.py`](radar/corte_vertical_complemento.py) | Corte vertical, nível de fusão e separação entre chuva e CC anômalo |
| [`radar/teste_microexplosao.py`](radar/teste_microexplosao.py), [`radar/teste_microexplosao_2.py`](radar/teste_microexplosao_2.py), [`radar/figuras_video_microexplosao.py`](radar/figuras_video_microexplosao.py) | Testes de escala e vento, e painéis do vídeo |
| [`satelite/teste_overshoot.py`](satelite/teste_overshoot.py), [`satelite/visivel_recorte_remoto.py`](satelite/visivel_recorte_remoto.py), [`satelite/visivel_textura.py`](satelite/visivel_textura.py), [`satelite/animar_overshoot.py`](satelite/animar_overshoot.py) | *Overshoot* nos canais 13 e 2 do GOES-19 e animação sincronizada ([`assets/radar_v2/overshoot_animacao.mp4`](assets/radar_v2/overshoot_animacao.mp4)) |
| [`radar/teste_reconciliacao.py`](radar/teste_reconciliacao.py), [`radar/mapa_danos_trilha.py`](radar/mapa_danos_trilha.py) | Controle único do cisalhamento e mapa da trilha |
| [`buscar_midia_jornais_youtube.py`](buscar_midia_jornais_youtube.py) | Catálogo de reportagens em [`assets/midia_externa.json`](assets/midia_externa.json); as imagens não estão no repositório |

## Licença

Código sob MIT e textos, figuras e vídeo sob CC BY 4.0, com as exceções em [`LICENSE`](LICENSE).
