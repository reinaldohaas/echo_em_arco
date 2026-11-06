# Há rotação colocalizada com o núcleo de CC baixo? Chapecó, 04/11/2026

> **Correção de 06/11/2026:** o teste com controle único (seção "Reconciliação") confirma o cisalhamento às 13:30 UTC, mas enfraquece duas afirmações abaixo: o sinal de 13:24 UTC depende inteiramente de *gates* corrigidos do *aliasing*, e a continuação às 13:36 UTC não é consistente.

**Resposta:** sim, há cisalhamento azimutal ciclônico concentrado e colocalizado com o núcleo. A confiança é **moderada a alta** nesse cisalhamento e **média** em uma circulação fechada, porque o centro não tem $V_r$. Os dados não confirmam tornado, mas a assinatura é compatível com detritos em um mesovórtice de sistema linear. Eles deixam de sustentar "granizo em fusão, sem rotação" como diagnóstico fechado. Microexplosão não fica refutada, mas não explica sozinha o conjunto das observações.

Dados: volumes Rainbow5 do radar banda S de Chapecó (`dados_chp_vol`). Convenção: $V_r$ < 0 aproxima-se do radar.

## O que foi medido

| Item | Resultado |
|---|---|
| Passagem | A 0,5°, o raio do aeroporto foi amostrado perto de 13:30:06 UTC, com centroide do núcleo a cerca de 0,1 km do aeroporto (10,5 km do radar) |
| Núcleo a 0,5° | Z máx. 65,5 dBZ; dentro do núcleo, CC mediano 0,68 e $Z_{DR}$ mediano 0,35 dB |
| Movimento | 40,4 m/s, quase para leste, ajustado em 8 elevações com resíduo de 0,29 km |
| Teste independente | O ajuste de 13:30 UTC previu 13:36 UTC em (9,6; −9,9) km; observado (8,7; −10,2) km, erro de cerca de 1 km |
| Duração | Ausente até 13:24 UTC, presente em 13:30 UTC e 13:36 UTC, não confirmado em 13:42 UTC |
| Profundidade | Único objeto de CC baixo em mais de 2 elevações, de 13:00 UTC a 14:00 UTC: 8 elevações, até cerca de 0,9 km acima do radar |
| Coluna acima do núcleo | Z cai de 65,5 para 53 dBZ a 0,9 km e fica entre 53 e 54 dBZ até 4 km; CC sobe de 0,86 para 0,97 (disco de 1,5 km) |
| Comparação | Dos 45 núcleos Z ≥ 55 dBZ até 60 km, só este tem CC baixo: 0,73 contra 0,97–0,99 nos demais. Dos 22 núcleos Z ≥ 60 dBZ entre 20 e 120 km, 21 têm CC mediano acima de 0,85 |
| Vento | $V_r$ até −44,8 m/s (mediana 3x3) perto do núcleo, com feixe a cerca de 0,28 km do solo. É um valor mínimo do vento total |
| Largura espectral | 2,3 m/s no núcleo (P90 3,6; máx. 5,5) contra 1,5 no anel: aumento moderado |

### Cisalhamento em arco de 2 km, às 13:30 UTC (sentido horário em todas até 4,0°)

| Elevação | $\Delta V$ no núcleo (m/s) | Máximo em outros alcances da fronteira (m/s) | $V_r$ relativa ao núcleo (m/s) | $V_{\text{rot}}$ (m/s) |
|---|---|---|---|---|
| 0,5° | 48,7 | 31,2 | −27,6 / +22,8 | 25,2 |
| 0,9° | 38,4 | 30,1 | −17,9 / +22,5 | 20,2 |
| 1,3° | 40,9 | 35,6 | −18,3 / +17,6 | 17,9 |
| 1,8° | 35,5 | 33,3 | −17,8 / +18,5 | 18,2 |
| 2,4° | 35,0 | 35,1 | −17,4 / +16,3 | 16,8 |
| 3,1° | 39,7 | 34,6 | −18,7 / +15,7 | 17,2 |
| 4,0° | 33,3 | 32,3 | −15,6 / +19,0 | 17,3 |

No mesmo alcance, a 0,5° e 2 km: 5,5 m/s às 13:24 UTC e 9,1 m/s às 13:36 UTC (o núcleo já tinha saído dali). Seguindo o núcleo às 13:36 UTC, o $\Delta V$ caiu para 18–26 m/s a 0,5°, 0,9°, 1,3° e 2,4°, com controle P90 de 15–19 m/s. A 1,8° o controle está contaminado.

## Testes de robustez
- **_Aliasing_:** a mancha vermelha ao lado do aeroporto é *aliasing* (salto na fronteira de 58,7 para 3,8 m/s, 154 *gates*). Não é um dipolo.
- **_Dealiasing_ (desdobramento de velocidade) e filtro:** com limiar de 6 a 14 m/s e mediana de 1, 3 ou 5, $\Delta V$ a 0,5° ficou em 53–63 m/s, sempre em sentido horário. O número é a amplitude em disco de 2,5 km, por isso difere da tabela.
- **Dual-PRF:** menos de 1% dos *gates* têm saltos em 20,8 ou 31,25 m/s.
- **_Clutter_:** o objeto muda de lugar entre elevações e volumes, e o local volta a CC acima de 0,9 às 13:36 UTC. Mas 8% do disco do aeroporto foi marcado como *clutter* recorrente.
- **Escala:** o resultado em arco de 1 km é instável (5,8 a 39,5 m/s a 0,5°, conforme o alcance), porque o centro não tem $V_r$.

## Comparação das hipóteses

| Evidência | Detritos / vórtice | Granizo em fusão | Microexplosão sem rotação |
|---|---|---|---|
| Z > 45 dBZ, CC < 0,8, $Z_{DR}$ < 0,5 dB no núcleo | A favor | Parcial: CC baixo demais para o típico | Neutra |
| Cisalhamento ciclônico localizado | A favor | Neutra | Contra, se for circulação |
| Excesso de Z e CC baixo só no primeiro km | A favor (inferência) | Contra: falta núcleo forte em altura | Neutra |
| Objeto compacto a 40 m/s, 6–12 min | A favor | Pouco esperado | Pouco esperado |
| W só moderadamente elevado | Contra um tornado forte e resolvido | Neutra | Neutra |
| Z 58–60 dBZ em 1–4 km antes da passagem | Neutra | A favor, fraco | A favor, fraco |

- **Critério de TDS:** Ryzhkov et al. (2005) aparecem citados com Z > 45 dBZ, $\rho_{hv}$ < 0,8 e $Z_{DR}$ < 0,5 dB, junto a gancho e vórtice. Só consultei fontes secundárias; confira no artigo. Não há gancho clássico aqui, o que era esperado em sistema linear.
- **Granizo em banda S:** um resumo em slides (ESSL 2011) dá $\rho_{hv}$ mediano de 0,94 para granizo grande e 0,92 (±0,06) para gigante. O núcleo tem cerca de 0,7. Não é trabalho revisado, e isso não exclui granizo em mistura com chuva.

## Limitações
1. **Geometria:** a fronteira é quase radial. O radar vê a componente ao longo dela, então rotação e cisalhamento linear dão sinal igual, e a convergência não é observável. A simetria relativa ao núcleo também ocorreria em uma linha de cisalhamento. A distinção depende da localização, medida pelo controle.
2. **Centro sem $V_r$:** 11–19% dos *gates* do núcleo não têm $V_r$ até 1,8°, justamente onde um vórtice estreito apareceria.
3. **Radar único:** sem vetor de vento, sem dados de vento em superfície e sem levantamento de danos.
4. **Decodificação:** o leitor pode ter erro de cerca de 0,5 dBZ. O ponto mais próximo do print dá 62,0 dBZ e CC 0,76, contra 63 dBZ e 0,70 no print.
5. **Hipótese de movimento:** o perfil vertical supõe o mesmo movimento em todas as alturas.
6. **Inferências, não medidas:** "detritos", "vórtice" e "sem granizo em altura".

## O que resolveria
Levantamento de danos ao longo da trilha, com direção de queda:
- 13:30 UTC: −27,135; −52,649 (observado).
- 13:36 UTC: −27,140; −52,516 (observado).
- 13:42 UTC: −27,144; −52,360 (só previsão, não confirmada).

Uma faixa estreita e contínua com padrão convergente favoreceria tornado. Danos largos, divergentes e sem faixa favoreceriam vento linear. Ajudariam também a série de 1 minuto da estação de superfície, a sondagem e um segundo radar, se houver.

## Extensão, retilinearidade e hipótese da tromba (06/11/2026)

**Extensão:** cerca de 16 km aparece atribuído à Defesa Civil só em um texto do PSTU. A largura não foi publicada. Os polígonos de 4 bairros citados formam um envelope de 4,1 x 2,8 km, e de Palmital dos Fundos à borda leste de Seminário são cerca de 6,9 km. Bairro é área administrativa, não faixa de dano, e as fotos disponíveis não têm posição conhecida.

**Linha reta:**
- Radar (medido): 13:24 UTC a 13:36 UTC, 24,2 km, rumo 90°, desvio máximo de 0,40 km, com só 3 posições. Às 13:24 UTC, o que se mede é um máximo de cisalhamento, não o núcleo de CC baixo. Dentro de 13:30 UTC, o núcleo cobre cerca de 8 km com resíduo de 0,29 km.
- Danos: eixo dos 5 centroides com rumo 86°, rms de 0,57 km. Os centroides ficam 0,6–2,0 km ao norte da trilha. Teste fraco.
- Uma trilha reta não distingue tornado de vento linear: descreve o deslocamento, não o padrão do vento.
- Conflito: a ClicRDC, citando o mapeamento da Defesa Civil, descreve toque no nordeste do município, sentido nordeste-sudoeste, cruzamento da BR-480 e dissipação no sudoeste rural. O radar mede o núcleo avançando para leste. Pode ser erro de sentido, outra feição ou falha da minha associação. Falta o mapa original.

**Riacho como origem:** não sustentado. O cisalhamento já estava em cerca de (−27,140; −52,760) às 13:24:20 UTC, antes dos 5 cruzamentos da trilha com cursos d'água (o primeiro em −52,723). O Lajeado Ferreira passa a 0,9 km ao sul do aeroporto e não cruza a reta. O rio Uruguai fica a mais de 10 km ao sul, e a trilha vem de oeste. A amostragem de 6 min não permite ver se houve intensificação sobre um curso d'água, e o feixe mais baixo está a 0,28 km do solo, portanto o radar não vê um funil junto à superfície.

**Rotação em queda:** parcialmente compatível, confiança baixa a média.
- 13:18 UTC: sem sinal localizado consistente; um único valor acima do P90, a 4,4 km.
- 13:24 UTC: $\Delta V$ de 38–50 m/s até 2,2 km (P90 fora da trilha: 24–30) e 34–37 m/s até 3,8 km.
- 13:30 UTC: forte só até 0,7 km (36–49 m/s); 25–28 m/s acima de 1,5 km, próximo ao P90.
- O CC baixo só aparece às 13:30 UTC.
- Às 13:24 UTC, os níveis baixos foram amostrados primeiro, então a ordem no tempo não prova descida. Há valores excluídos por suspeita de *aliasing* residual (a ≈ +26, b ≈ −25). O alcance muda de 13–18 para 9–10 km entre os volumes.
- O termo mesociclone exige cautela: a feição durou cerca de 12 min, em sistema linear; mesovórtice descreve melhor.

Mapa: `figuras/mapa_danos_trilha.png`. Hidrografia e bairros: © colaboradores do OpenStreetMap.

## Reconciliação com `teste_microexplosao.py` (06/11/2026)

As duas análises discordavam porque usavam controles diferentes. Este relatório comparava arcos só na fronteira. O teste de microexplosão compara pares de *gates*, sem suavizar, com o máximo do resto da varredura, que inclui saltos de cerca de 60 m/s típicos de *aliasing* não resolvido.

`teste_reconciliacao.py` aplica o mesmo estimador ao núcleo e a 110–165 discos independentes de 3 km de raio: maior $\Delta V$ ciclônico em 2 km, após mediana 3x3, só nos *gates* sem dobra. Assim, não depende do *dealiasing* (desdobramento de velocidade).

| 13:30 UTC, sem dobra | 0,5° | 0,9° | 1,3° | 1,8° | 2,4° | 3,1° | 4,0° |
|---|---|---|---|---|---|---|---|
| $\Delta V$ no núcleo (m/s) | 38,9 | 39,3 | 43,4 | 43,1 | 41,7 | 42,6 | 36,0 |
| Máximo dos outros discos (m/s) | 31,8 | 35,0 | 37,0 | 47,1 | 59,0 | 47,6 | 44,6 |
| Discos iguais ou acima do núcleo | 0 | 0 | 0 | 1 | 2 | 1 | 1 |

Conclusões:
- **13:30 UTC, 2 km:** o núcleo está entre os mais altos da varredura até cerca de 0,7 km acima do radar. A frase "acima de ~200 m não supera o resto da linha" não se sustenta nessa escala.
- **13:30 UTC, 1 km:** o núcleo lidera só até 1,3° (nenhum disco acima a 0,5° e 1,3°; empate com 1 disco a 0,9°). Acima disso, de 1 a 5 discos o igualam ou superam.
- **Margem:** é modesta acima de 0,5°, e as elevações não são independentes entre si.
- **13:24 UTC:** sem *gates* dobrados, o sinal some (10,8 e 13,1 m/s em 1 km a 2,4° e 3,1°; sem dados suficientes a 0,5° e 0,9°). A precedência sobre os cursos d'água e a sequência "desce entre 13:24 UTC e 13:30 UTC" passam a confiança baixa.
- **13:36 UTC:** de 1 a 7 discos superam o núcleo a 0,5° e 0,9°; não é sinal consistente.
- **_Inbound_ extremo:** os −45 m/s dependem de dobra (por exemplo, bruto +15,3 para −47,2). O valor sem dobra é −29,6 m/s; a correção de cerca de −34 m/s na região é plausível, e os −45 m/s são incertos.
- **Mantido:** o cisalhamento localizado não prova vórtice, porque radar único não separa rotação de cisalhamento nesta geometria.

Saída: `figuras/teste_reconciliacao_saida.txt`.

## Arquivos
Scripts: `teste_reconciliacao.py`, `mapa_danos_trilha.py`, `analise_descida.py`, `analise_velocidade.py`, `analise_nucleo.py`, `analise_rotacao.py`, `analise_rotacao_checagens.py`, `analise_rotacao_final.py`.
Em `figuras/`: `rotacao_resumo.png`, `rotacao_evolucao.png`, `rotacao_perfil_vertical.png`, `aeroporto_1330_elevacoes.png`, `rotacao_seguindo_nucleo.csv`, `rotacao_resumo.csv`, `rotacao_trilha.csv`, `rotacao_nucleos_z55.csv`, `rotacao_controle_z60.csv`, `rotacao_perfil_fronteira.csv`.
