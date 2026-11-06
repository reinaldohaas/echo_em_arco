# Checklist de hipóteses: Chapecó, 04/11/2026

## Introdução

Argumentos baseados na literatura são válidos; opiniões, não. A ciência é feita de dados, assim como uma casa é feita de tijolos. Mas um monte de dados não é ciência, assim como um monte de tijolos não é uma casa. A imagem é de Henri Poincaré, em *A ciência e a hipótese*.

Por isso, este checklist conta observações e as interpreta pelo que elas podem separar entre as hipóteses, segundo a literatura citada. Afirmações sem dado publicado ou referência ficam fora da contagem, venham de quem vierem.

## Pré-avaliação

Pré-avaliação com radar, satélite, vídeos e fotos publicados. Vídeo e foto não substituem o levantamento de campo.

**Resultado:** contando só dados observados, 8 itens favorecem vento linear e nenhum favorece tornado; o CC anômalo e o cisalhamento são neutros. Nenhum item é decisivo, e vários não são independentes. A contagem não é uma probabilidade e não descarta tornado.

**Esses itens não distinguem microexplosão de outros mecanismos de vento linear.** A literatura documenta vento linear severo em linha em arco ligado ao jato traseiro e a mesovórtices, sem exigir microexplosão (Atkins et al. 2005; Wakimoto et al. 2006b). O que apontaria diretamente para a descida, o item 9, é fraco.

## Hipóteses

- **L. Vento linear:** downburst ou microexplosão, ou jato traseiro com mesovórtice.
- **T. Tornado:** vórtice na superfície causando os danos principais.

Uma combinação das duas fica fora da contagem porque nenhum dado aqui mostra um vórtice na superfície. Ela não é impossível: Atkins et al. (2005) documentam, na mesma linha em arco, uma faixa de vento linear de ~8 km por 50 km e cinco tornados F0–F1.

O termo "microexplosão" exige saída de ar com menos de 4 km; acima disso, é "macroexplosão" (Fujita e Wakimoto, conforme [NWS](https://www.weather.gov/ohx/downbursts)). Os bairros mais atingidos chegam a ~5 km do aeroporto, e a tempestade se desloca a 40 m/s. Sem mapa de danos, "downburst" é o termo mais seguro.

## Checklist

Peso: **M** = médio, **f** = fraco. Nenhum item recebeu peso forte. "—" = não ajuda a separar.

| # | Evidência | Fonte | L | T | Literatura e ressalva |
|---|---|---|---|---|---|
| 1 | Nenhum funil visível nas câmeras do aeroporto até 10:29:39, quando a chuva encobre a vista | Vídeo | a favor f | contra f | Sem referência específica; a chuva pode esconder um funil |
| 2 | Cortina larga de chuva chega ao solo às 10:29:27–33 | Vídeo | — | — | Só mostra a chuva. Perdeu o peso que tinha, por falta de critério na literatura |
| 3 | Vento severo por pelo menos ~1 min: destroços às 10:30:31, palmeiras dobradas às 10:31:29 | Vídeo | a favor M | contra M | Vento danoso de macroexplosão dura 2–5 min (NWS). A 40 m/s, 1 min equivale a ~2,4 km. A câmera não mede vento |
| 4 | Palmeiras dobradas para o mesmo lado de 10:31:14 a 10:31:29 | Vídeo | a favor f | contra f | Só ~15 s, numa câmera. A direção do vento segue a dos danos só de forma indireta |
| 5 | Dano espalhado em volta do aeroporto; carros ainda em fileiras e muitas árvores de pé | Drone | a favor M | contra f | Compatível com faixa larga de vento linear (Atkins et al. 2005). Imagens oblíquas e amostradas |
| 6 | Centros dos bairros citados distam ~1,5 km na direção norte-sul | Mapa | a favor f | — | Centro de bairro não é largura da faixa de danos |
| 7 | Bairros citados ficam a leste do aeroporto, alinhados com o núcleo do radar | Mapa e radar | — | — | Confirma a trilha, não o mecanismo |
| 8 | Coluna de ZDR às 10:12–10:18 e topos mais frios até 10:20 | Radar e satélite | — | — | Indica corrente ascendente forte (Kumjian e Ryzhkov 2008, citação indireta). Overshoots se associam tanto a vento danoso quanto a tornados (Bedka et al. 2010). Antes era a favor de L; agora é neutro |
| 9 | Z perto do solo: 58, 59,5 e 58 dBZ com CC ≥ 0,90 | Radar | a favor f | — | Microexplosão úmida tem refletividade alta (Atkins e Wakimoto 1991), mas não há descida nítida de um máximo |
| 10 | Vento atrás da linha maior embaixo às 10:30 | Radar | a favor M | — | Compatível com saída de ar ou jato traseiro (Wakimoto et al. 2006a). Uma varredura, só a componente radial |
| 11 | Às 10:30, em 2 km e sem gates dobrados, o cisalhamento junto ao aeroporto está entre os maiores da varredura até ~0,7 km acima do radar; não se mantém às 10:24 nem às 10:36 | Radar (`radar/teste_reconciliacao.py`) | — | — | Vórtices tornádicos são mais fortes em 0–3 km e se intensificam antes do tornado (Atkins et al. 2005), mas mesovórtices também acompanham vento linear (Wakimoto et al. 2006b). Radar único não separa rotação de cisalhamento. Antes era a favor de L; o teste com controle único tirou esse peso |
| 12 | Forma de linha em arco | Radar | a favor f | — | 18% dos tornados dos EUA vieram de sistemas lineares, com mais F1 e menos F2–F3 que os de células (Trapp et al. 2005) |
| 13 | CC anômalo (≈ 0,74, ZDR ≈ 0, KDP baixo), só neste núcleo | Radar | — | — | Neutro por decisão do autor da análise: os destroços ocorreriam nas duas hipóteses. Fica dentro dos limiares de detritos a 0,5° (Z > 45, CC < 0,8, ZDR < 0,5), mas o critério também exige vórtice, aqui não demonstrado (Ryzhkov et al. 2005, citação indireta). Assinaturas ocorrem mais perto do radar e sobre área urbana (Van Den Broeke e Jauernic 2014). Em granizo, CC cai a ~0,8 (Balakrishnan e Zrnić 1990, citação indireta). Não encontrei estudo que documente assinatura assim sem tornado |
| 14 | Telhas e chapas "enroladas e retorcidas" | Defesa Civil de Chapecó | fora | fora | Não encontrei critério na literatura que ligue isso à rotação |
| 15 | Rotação e assinatura de mesovórtice relatadas pela Defesa Civil | Imprensa | fora | fora | Produtos não publicados. Mesovórtice também ocorre com vento linear (Wakimoto et al. 2006b) |
| 16 | Confirmação oficial de tornado | Defesa Civil de SC | fora | fora | Sem dados publicados; o relatório ressalva que nem todos os bairros foram atingidos diretamente |
| 17 | Outro tornado relatado em Xanxerê às 10:48 | Defesa Civil de SC | fora | fora | Sem dados publicados; não diz respeito a este caso |
| 18 | Rajadas de 93 km/h (estação da Defesa Civil) e 126 km/h (equipamento do Inmet, que as reportagens situam em outro ponto da cidade) | Imprensa | — | — | É rajada, não vento sustentado, e não há medida confirmada no aeroporto |
| 19 | Danos vistos: coberturas e estruturas leves de aço; nada varrido até a base | Vídeo e fotos | — | — | Painéis arrancados de edifício metálico: 155 km/h, faixa de 125–195 ([guia EF do Canadá](https://www.canada.ca/en/environment-climate-change/services/seasonal-weather-hazards/publications/enhanced-fujita-scale-damage-indicators/chapter-21.html)). A escala não separa os mecanismos. Não vi apoio para F2–F3 |
| 20 | **Direção de queda de árvores e estruturas** | Falta | ? | ? | **É o teste mais direto:** queda convergente indica tornado, divergente indica downburst (NWS 2007). Pode ser ambíguo (Rodríguez et al.), e dano de tornado pode estar dentro do de downburst (NWS 2007) |
| 21 | **Vento no aeroporto durante a passagem** | Falta | ? | ? | O último METAR é de 10:00 local (item 22). Queda brusca de pressão junto ao pico de vento indica tornado (Karstens et al. 2010, citação indireta) |
| 22 | METAR de 10:00 local: 16 kt de 360°, rajada de 36 kt (30 e 67 km/h), 25/24 °C | METAR | — | — | É 30 min antes da passagem. Umidade baixa em altura e úmida embaixo é típica de microexplosão úmida (Atkins e Wakimoto 1991); base baixa favorece tornado significativo em supercélulas (Rasmussen e Blanchard 1998, citação indireta) |
| 23 | **Perfil de θe em sondagem ou reanálise** | Falta | ? | ? | Diferença acima de 20 K entre a superfície e o mínimo em altura marcou dias de microexplosão úmida; abaixo de 13 K, dias sem elas (Atkins e Wakimoto 1991). Região e época diferentes |

| Contagem (só dados: itens 1–13) | A favor | Contra |
|---|---|---|
| **L** | 8 (3 M, 5 f) | 0 |
| **T** | 0 | 4 (1 M, 3 f) |

Os itens 14 a 17 ficam fora da contagem porque são relatos ou avaliações sem dados publicados. Os itens 1 a 6 são observações visuais, sem medida de vento. Os pesos são julgamento meu, aplicado à literatura citada.

## O que foi visto em cada vídeo

Vi ~40 quadros, sem áudio, e não cada segundo. Os horários são os do relógio gravado na imagem.

**[Portal Chapecó, câmeras do aeroporto](https://www.youtube.com/watch?v=cgaVfPKLRAg):**

| Hora | Posição no vídeo | O que aparece |
|---|---|---|
| 10:28:31 | 4:00 | Base escura se aproximando; ainda sem chuva na pista |
| 10:29:05–10:29:33 | 4:34–5:02 | Cortina larga e escura até o solo; nenhum funil definido |
| 10:30:01 | 5:30 | Chuva na lente; visibilidade caindo |
| 10:30:31 | 6:00 | Objetos pequenos voando no quadro |
| 10:30:46 | 6:15 | Vegetação quase apagada pela chuva e por borrifos |
| 10:31:14–10:31:29 | 6:43–7:00 | Palmeiras muito dobradas para o mesmo lado |
| ~10:31:40 | ~7:10 | Câmeras desconectam |

**[UOL](https://www.youtube.com/watch?v=atSH8aWnl8I):** apresenta uma câmera de rua como "início do tornado", mas os quadros que vi mostram a rua normal (0:25) e depois o ar branco com destroços (0:34), sem funil. As imagens de drone (1:30) mostram o dano em torno do aeroporto.

**[Terra, imagens aéreas](https://www.youtube.com/watch?v=gcCoru4QoiE) e [Terra, reportagem](https://www.youtube.com/watch?v=c2NQdpkxo1Q):** coberturas destruídas, estrutura metálica leve sobre um telhado e chapas dobradas.

**Miniaturas em `assets/jornais/`:** aeronave tombada dentro de um hangar sem cobertura (CBN) e estrutura leve arrancada diante do terminal (Metrópoles). Não indicam direção de vento por si só.

Não assisti a todos os vídeos publicados. Algum outro pode mostrar um funil.

## O que resolveria

1. **Direção de queda** de árvores, postes e estruturas, georreferenciada ao longo da trilha.
2. **Imagens de drone da Defesa Civil**, ainda não publicadas: mostram a largura da faixa e possíveis marcas curvas no solo.
3. **Série de vento e pressão do aeroporto e das estações**, de preferência de 1 minuto. Nos boletins públicos consultados, não há METAR nem SPECI de SBCH entre 13:00 UTC de 04/11 e 12:00 UTC de 05/11; depois, o vento e a temperatura vêm como `/////`. Não consegui acessar o Inmet nesta verificação.
4. **Perfil de θe** do dia, para aplicar o teste de Atkins e Wakimoto (1991).
5. **Produtos de radar da Defesa Civil** que sustentam a rotação relatada.
6. **Outras câmeras com relógio**: a direção dos objetos voando em várias delas permitiria medir o giro do vento.

## Literatura

**Lidos no texto ou no documento:**

- Bedka, K., et al., 2010: Objective satellite-based detection of overshooting tops using infrared window channel brightness temperature gradients. *J. Appl. Meteor. Climatol.* [PDF](https://www.ssec.wisc.edu/~jasono/papers/bedka_jamc_feb2010.pdf). Critério conferido: ≥ 6,5 K abaixo da bigorna e ≤ 215 K (−58 °C).
- Wakimoto, R. M., H. V. Murphey, C. A. Davis e N. T. Atkins, 2006b: High winds generated by bow echoes. Part II. *Mon. Wea. Rev.* [PDF](https://training.weather.gov/wdtd/courses/rac/severe/multicell-severity/story_content/external_files/Wakimoto2_2006.pdf).
- NWS Grand Rapids, 2007: [Storm Damage Survey Training](https://www.weather.gov/media/grr/brochures/INVEST2007.pdf). Material de treinamento, não artigo.
- Meio Ambiente Canadá: [guia de indicadores da escala EF, edifícios metálicos](https://www.canada.ca/en/environment-climate-change/services/seasonal-weather-hazards/publications/enhanced-fujita-scale-damage-indicators/chapter-21.html).
- Rodríguez, O., et al.: [resposta aos revisores](https://nhess.copernicus.org/preprints/nhess-2019-294/nhess-2019-294-AR1.pdf) do manuscrito sobre levantamento de danos de vento (*NHESS*). Documento de revisão; resume Bech et al. (2009).

**Lidos só no resumo:**

- Atkins, N. T., et al., 2005: Damaging surface wind mechanisms within the 10 June 2003 Saint Louis bow echo during BAMEX. *Mon. Wea. Rev.* [doi:10.1175/mwr2973.1](https://doi.org/10.1175/mwr2973.1)
- Atkins, N. T., e R. M. Wakimoto, 1991: Wet microburst activity over the southeastern United States. *Wea. Forecasting*, 6, 470–482. [doi](https://doi.org/10.1175/1520-0434(1991)006<0470:wmaots>2.0.co;2)
- Trapp, R. J., et al., 2005: Tornadoes from squall lines and bow echoes. Part I. *Wea. Forecasting*. [doi:10.1175/waf-835.1](https://doi.org/10.1175/waf-835.1)
- Van Den Broeke, M. S., e S. T. Jauernic, 2014: Spatial and temporal characteristics of polarimetric tornadic debris signatures. *J. Appl. Meteor. Climatol.* [doi:10.1175/jamc-d-14-0094.1](https://doi.org/10.1175/jamc-d-14-0094.1)
- Wakimoto, R. M., et al., 2006a: High winds generated by bow echoes. Part I. *Mon. Wea. Rev.* [doi:10.1175/mwr3215.1](https://doi.org/10.1175/mwr3215.1)

**Citação indireta (original não lido; conferir antes de publicar):**

- Balakrishnan e Zrnić (1990), CC em núcleos de granizo: [revisão que cita o trabalho](https://caps.ou.edu/reu/reu04/finalpapers/Rowe-finalpaper.pdf).
- Fujita (1985), Fujita e Wakimoto (1981) e Wakimoto (1985), definições: [NWS](https://www.weather.gov/ohx/downbursts).
- Karstens et al. (2010), *Mon. Wea. Rev.*, medidas perto do solo em tornados: [registro bibliográfico](https://works.bepress.com/william_gallus/39/); a coincidência entre queda de pressão e pico de vento vem de [pôster do mesmo grupo](https://meteor.geol.iastate.edu/~ckarsten/portfolio/projects/Twistex_Poster.pdf).
- Kumjian e Ryzhkov (2008), assinaturas polarimétricas: [registro](https://pure.psu.edu/en/publications/polarimetric-signatures-in-supercell-thunderstorms).
- Rasmussen e Blanchard (1998), altura de base: [artigo que cita o trabalho](https://origin-east-www-spc.woc.noaa.gov/publications/craven/baseclim.pdf).
- Ryzhkov et al. (2005), *J. Appl. Meteor.*, 44, limiares de detritos: [pôster que cita o trabalho](https://ams.confex.com/ams/94Annual/webprogram/Handout/Paper234221/AMS_Poster_2014_DebrisSignatures.pdf).

## Fontes dos dados e reportagens

- [ND+: tornado atinge Chapecó](https://ndmais.com.br/tempo/tornado-atinge-chapeco-provoca-destruicao-e-suspende-operacoes-no-aeroporto/)
- [ND+: novas imagens](https://ndmais.com.br/tempo/novas-imagens-mostram-cenario-devastador-apos-tornado-atingir-chapeco/)
- [ND+: decreto e 126,4 km/h](https://ndmais.com.br/tempo/tornado-com-ventos-de-1264-km-h-deixa-mais-de-2-mil-registros-de-destruicao-e-provoca-situacao-de-emergencia-em-chapeco/)
- [ClicRDC: Defesa Civil confirma tornado](https://clicrdc.com.br/tempo/defesa-civil-confirma-tornado-em-chapeco-e-identifica-segundo-fenomeno-em-xanxere/)
- [Folha Desbravador: Relatório Técnico 1008/2026](https://folhadesbravador.com.br/clima/chapeco-registra-rajadas-de-126-km-h-e-danos-compativeis-com-tornado-defesa-civil-contabiliza-24-mil-ocorrencias)
- [CenárioMT: Chapecó e Xanxerê](https://cenariomt.com.br/clima/tornados-atingem-chapeco-e-xanxere-em-18-minutos/)
- [CREA-SC: estimativa F2–F3](https://portal.crea-sc.org.br/tornados-em-santa-catarina-alertam-para-seguranca-estrutural/)
- [CNN Brasil: imagens](https://www.cnnbrasil.com.br/nacional/sul/sc/imagens-mostram-tornado-se-formando-e-atravessando-chapeco/)
- METAR de SBCH: [NOAA Aviation Weather](https://aviationweather.gov/api/data/metar?ids=SBCH&format=raw&hours=72), conferido com [IEM](https://mesonet.agron.iastate.edu/request/download.phtml) e [Ogimet](https://www.ogimet.com/metars.phtml)
- Imagem dos tijolos: [Henri Poincaré, citações na Britannica](https://www.britannica.com/quotes/Henri-Poincare)
- Coordenadas dos bairros: [Nominatim/OpenStreetMap](https://nominatim.openstreetmap.org/)
