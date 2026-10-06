# Evidência de execução

## Baseline original: execução real (antes do protótipo)

Revisão base: `7b66372bcf156249560c90918d9472a47aabf3c5`.
SDK: `fec561c5771a981a6090c315cbe338f7967137cd`.

| Verificação | Resultado observado |
| --- | --- |
| `build.py --variant=dev_exe` | exit 0; link e conversão CPE para EXE concluídos |
| `build.py` | exit 0; verificações de hash upstream concluídas |
| Cabeçalho dos dois executáveis | `PS-X EXE` |
| SHA-256 matching versus README upstream | igualdade confirmada com assert |
| `git status --porcelain` do checkout MGS após build | vazio; fontes intactas |

Matching: `references/mgs_reversing/obj/_mgsi.exe`, 641024 bytes.
SHA-256: `4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f`.

Development: `references/mgs_reversing/obj_dev/_mgsi.exe`, 780288 bytes.
SHA-256: `8a235cd9a1289a6b3308a5b7c032f825abe262c976fecc7cf4220e6b5440e7c8`.

Os binários permanecem locais e não são publicados. Log completo do matching disponível localmente em `local/mgs-main-build.log` (ignorado pelo Git). Sucesso de build não significa ausência de warnings upstream.

## Iteração: entrada reproduzível no Loading Dock e locomoção

PCSX-Redux Windows `26704.20261005.34`, OpenBIOS incluído, disco local identificado como SLPM86247. O teste usa o build dev acima sem alterar suas fontes ou escrever na RAM do jogo.

- RED: sem o replay, o teste terminou com `SMI_STAGE_FAIL stage=title` e exit 2 no emulador.
- GREEN: `tests/run_stage_smoke.py` com `tools/enter_dock.lua` entrou em s00a, confirmou conclusão do scenario e passou as verificações de locomoção em memória real.
- Reexecução final passou com as mesmas amostras abaixo.

| Amostra | X | Z | GM_PlayerStatus (hex) |
| --- | --- | --- | --- |
| Antes de andar | -5756 | -1298 | 0 |
| Após andar | -4202 | -1296 | 10 |
| Antes de rastejar | -4202 | -1297 | 20 |
| Durante rastejo | -4851 | -1321 | 50 |
| Final do rastejo | -5233 | -1320 | 50 |
| Após levantar | -4671 | -1320 | 0 |

0x10 = MOVE; 0x20 = SQUAT; 0x40 = GROUND. O teste exige movimento entre duas amostras já no estado GROUND + MOVE, além de ausência de dano/downed/game-over nas amostras. Não considera apenas a mudança de animação uma prova de rastejo.

A tela TITLE do dev foi identificada como seletor intencional: `loader.c` remapeia `title` para `select1`, e `select.c` usa Down/Up e Circle. Não foi necessário consertar o motor ou trocar o BIOS para entrar na fase. Captura visual anterior confirmou apenas o seletor; a nova prova de locomoção é headless, por estados e coordenadas.

Comando reproduzível e limites em [TESTING.md](TESTING.md). Logs gerados permanecem em `local/smoke`, ignorados pelo Git. A implementação nova é automação/teste, não câmera ou combate.

## Iteração: câmera experimental corrigida em s00a

O recorte agora usa `src/shoulder_camera.h`, instalado por `tools/apply_camera.py` somente em DEV_EXE. O hook altera a view final, sem substituir callbacks/eventos da GM_Camera ou a máquina de estados de Snake. Permanece limitado a Loading Dock.

### Causas reproduzidas antes da correção

- **Snake fora da imagem:** `GM_PlayerPosition` acompanha `CONTROL.mov`, que já inclui `CONTROL.height` acima dos pés. O protótipo somava outra altura inteira. Na pose parada, eye/target Y=2504 contra o ponto de referência de Snake Y=1497. A captura experimental não mostrava Snake; a baseline na mesma pose mostrava. A nova asserção geométrica falhou com o ponto em Y=-177,3 relativo ao centro do viewport.
- **L3 não desligava:** `PCSX.CONSTS.PAD.BUTTON.L3` retornou `nil` na API Lua do emulador testado. O replay não enviava o clique. Usar o índice serial 1 fez off/on passar sem alterar o código C de toggle ou o tipo digital do controle. A hipótese de filtragem digital não explicou esta falha do replay.

### Correção e provas

- Pivô vertical corrigido para `GM_PlayerPosition.vy + height - control->height`. Os parâmetros 1400/850/350, distância 1600 e lateral 450 não foram ajustados para esconder a causa.
- Build DEV_EXE: compilação, link e conversão concluídos. Executável local: 780288 bytes, SHA-256 `67cf4228fd83e33810334210aecd3e6f45fe5ce8daaaedab6e788eefcc2d083e`.
- Build matching com o hook condicional instalado: exit 0, verificações upstream passaram; SHA-256 permanece `4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f`.
- Instalador aplicado duas vezes sem mudança, removido com igualdade exata a `git show HEAD:source/game/camera.c` e header gerado ausente, depois reinstalado com igualdade aos bytes anteriores.
- Smoke `--camera` final: exit 0. Andar, deitar/rastejar com deslocamento, levantar, cessão a primeira pessoa, retração por hazard e L3 off/on passaram. O teste geométrico passou para parado, rastejo e retorno experimental.

Amostras da reexecução final (coordenadas não são golden values; podem variar alguns frames):

| Amostra | X | Z | Status hex |
| --- | --- | --- | --- |
| Antes de andar | -5756 | -1298 | 0 |
| Após andar | -4202 | -1296 | 10 |
| Durante rastejo | -4826 | -1321 | 50 |
| Final do rastejo | -5179 | -1320 | 50 |
| Após levantar | -4617 | -1320 | 0 |

L3 desligado: active=0/enabled=0; religado: active=1/enabled=1. Primeira pessoa: active=0/first=1. Altura da view parada Y=1400; no rastejo Y=357. O campo `height` no log é relativo a GM_PlayerPosition, não ao chão.

### Inspeção visual real, separada do smoke

Capturas pausadas da janela PCSX-Redux confirmaram Snake visível no frame de controle 149 (parado), 205 (após andar), 320 (rastejando), 530 (câmera original após L3 e após levantar) e 550 (experimental religada). Também foi capturada a baseline original na pose 149. As imagens e diagnósticos ficam apenas em `local/smoke/visual-evidence`, não no repositório público.

Isso aprova os dois consertos no recorte exercitado, **não o design final da câmera**. No rastejo e no retorno perto da parede, a retração aproxima muito o corpo; enquadramento, oclusão e suavização ainda precisam de trabalho. O radar/créditos originais podem sobrepor o personagem. Hazard é raio simples, não volume do near-plane. Não foi provada ausência geral de clipping.

## Iteração: redução da retração excessiva junto à parede

Recorte: mesmo replay de s00a, sem escrita de RAM de gameplay, com comparação visual no controle 320 (rastejo) e inspeção do retorno experimental em 550.

- **Causa isolada:** depois do hazard, a câmera descartava 25% de toda a distância pivô–impacto. Isso adicionava uma aproximação proporcional desnecessária, além da retração fisicamente exigida pela parede. O afastamento lateral também diminui com a retração; essa característica não foi redesenhada.
- **RED real:** a nova guarda de profundidade do ponto de referência no rastejo (`>= 950`) falhou no executável anterior: `817.6 < 950`, exit 1. As demais regressões de gameplay continuaram passando.
- **Alteração mínima:** margem fixa experimental de 100 unidades ao longo do raio até o impacto, calculada com `GV_VecLen3`. Se a distância disponível não excede a margem, a câmera fica no pivô; distância zero não divide. Não força uma distância mínima através do obstáculo. Alturas, alvo, boom nominal e zoom foram preservados.
- **GREEN repetido:** build DEV_EXE e duas execuções completas do smoke passaram. No rastejo, eye passou de `(-4020,357,-1120)` para `(-3849,357,-1078)` na mesma amostra de Snake `(-4826,141,-1321)`. A profundidade do landmark passou de 817,6 para 993,0; projeção vertical de -76,6 para -63,1. Andar, deitar/rastejar com deslocamento, levantar, primeira pessoa e L3 off/on passaram.
- **Imagem renderizada:** comparação na mesma pose 320 confirmou redução do corpo em primeiro plano, sem novo obstáculo tapando Snake. Captura 550 também mostra corpo menor que a evidência anterior e Snake visível. O corpo ainda fica grande e cortado pela borda inferior; radar/créditos continuam sobrepostos. A melhoria é parcial, não aprovação do design final.

Build DEV_EXE SHA-256: `3dca5bda53b8a30206eb02a6fb26344f737f8ac806bc9a5b9a98263a06012cb4`. Build matching passou com SHA-256 original inalterado. Instalador passou aplicação dupla, remoção com igualdade exata ao original e reinstalação. Um harness local compilado com GCC executou 72 casos de aritmética axial/diagonal e limites (inclusive distância zero); usa raiz quadrada do host e não substitui a execução PS1.

Evidências locais: `local/smoke/visual-evidence/wall-before-crawl.png`, `wall-fixed-crawl.png`, `wall-fixed-restored.png` e diagnósticos correspondentes; baseline pré-alteração em `local/baseline/wall-start`. Logs de build em `local/wall-camera-build.log` e `local/wall-matching-build.log`. Nada disso é publicado.

A margem de 100 é experimental. Hazard continua sendo raio, não volume do near-plane; não foi validado um conjunto amplo de paredes, cantos, teto ou movimento contínuo da câmera. O próximo recorte deve medir enquadramento durante aproximação/afastamento e a perda do afastamento lateral, antes de outra mudança de geometria.

## Iteração: enquadramento durante mudanças de postura

O rastreamento local observou 461 Vsyncs (controle 140–600) e revelou uma falha não coberta pelas poses paradas: `PLAYER_GROUND` muda antes do término da animação. A altura nominal caía cedo ao deitar e subia cedo ao levantar. Na captura anterior em 414, Snake desaparecia abaixo da imagem.

A leitura de `GM_SnakeCamera` com desconto condicionado a `PLAYER_GROUND` também não é um landmark confiável durante toda a transição: a origem usa o stance interno da animação e pode diferir da flag. O novo teste observa diretamente a transformação mundial do bone6, com layouts do upstream fixado e validação dos ponteiros.

- **RED:** `run_stage_smoke.py --camera` passou a exigir o osso dentro do viewport em 78 amostras, a cada dois Vsyncs do controle 280 ao 434, incluindo virada, descida, rastejo, parada e subida. Falhou no build anterior em 292, projeção Y=221,5 (limite absoluto 112).
- **Hipótese rejeitada:** interpolar as alturas nominais usando `CONTROL.height` corrigiu o começo, mas falhou em 304 (Y=-114,9). O controle não segue exatamente a cabeça. Esse experimento foi removido, não publicado como solução.
- **Correção:** manter a altura nominal, mas restringir o pivô a até 250 unidades acima/abaixo do bone6 real antes de consultar hazards. As poses assentadas do recorte mantêm as alturas anteriores. O hook cede se o objeto/osso não estiver disponível. Não altera animação, flags ou locomoção.
- **GREEN:** as 78 amostras passaram; maior módulo Y observado foi 104,9 em 292. Em 414, Y=-48,3. Guarda de parede em 320 continuou com profundidade 993,0. Regressões de locomoção, primeira pessoa e L3 passaram.

- **Imagem renderizada:** capturas comparativas nos controles 294 e 414 confirmaram Snake visível. Em 414, ele reaparece onde a baseline mostrava apenas cenário; em 294, o corpo ocupa menos da imagem. Ainda há enquadramento apertado no rastejo. As capturas verificam checkpoints, não fluidez temporal de todo o replay.

Build DEV_EXE SHA-256: `21537713e0ae8698230babd3879bf8a19940e0c0c2cbac28dc0cfcca6cec9378`. Matching passou com o hash original preservado. O limite de 250 é experimental e específico do modelo de Snake neste recorte; um futuro modelo de Leon exige remapeamento explícito do osso. Não é uma prova de enquadramento universal, suavização temporal ou colisão volumétrica.

Logs locais: `local/transition-red.log`, `local/transition-green.log` (tentativa rejeitada), `local/transition-envelope-build.log`, `local/transition-envelope-smoke.log` e `local/transition-matching-build.log`. Baseline preservada em `local/baseline/transition-start`. As capturas permanecem locais, em `local/smoke/visual-evidence/transition-*.png`.

## Limitações reais

- Boot e recorte automatizado de locomoção executados; campanha completa não testada.
- RE4 não compilado. Colisão de nomes no checkout Windows registrada em BUILD.md.
- Apenas o protótipo de view final em s00a foi implementado/testado; combate RE4 não implementado.
- Nenhum asset de Leon importado.
- Inspeção visual limitada aos checkpoints acima. Nenhum playthrough completo, teste de desempenho, dutos/clearance sob teto ou save/load executado.

## Separação entre evidência e intenção

O mapa de código é inspeção estática. A arquitetura de fusão e os critérios de aceitação continuam sendo propostas. Compilação, validação binária e o teste de integração explicitado acima são evidências executadas; não comprovam requisitos ainda ausentes.
