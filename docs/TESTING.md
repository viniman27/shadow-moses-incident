# Teste local de fase e locomocao

## Requisitos

- Checkouts/build nas revisoes do manifesto; `obj_dev/_mgsi.exe` e `obj_dev/asm.map` da mesma compilacao.
- Imagem local do disco 1 MGS Integral SLPM-86247 que o usuario tenha direito de utilizar. CUE deve referenciar o BIN existente.
- PCSX-Redux com OpenBIOS ao lado do executavel; validado com pacote Windows `26704.20261005.34`.
- Python 3 (somente biblioteca padrao para o teste).
- Fechar outras instancias antes do teste. Ele cria/reutiliza memory cards EXCLUSIVOS de teste em `local/smoke`; nao usa os saves de jogo normal.
- Preparar privacidade antes de executar: o pacote Windows usa Sentry. Na instalacao local foram autorizadas e verificadas regras de bloqueio de saida para `pcsx-redux.exe`, `pcsx-redux.main` e `crashpad_handler.exe`. O script nao cria regras, nao pede elevacao e nao promete desativar telemetria. `-noupdate` so impede atualizacoes. Em outra maquina, revisar esses requisitos antes de rodar.

## Executar

Da raiz do projeto:

```text
python tests/run_stage_smoke.py --disc "CAMINHO/Disco 1.cue" --emulator "CAMINHO/pcsx-redux.exe"
```

Os argumentos sao caminhos de arquivos locais reais, nao downloads. O teste roda sem UI, desliga webserver/GDB/PCdrv, limita o tempo do subprocesso e termina o emulador ao concluir a sequencia. Logs/resultados ficam em `local/smoke`, fora do Git. Rodar uma instancia por vez; cada execucao sobrescreve os resultados anteriores desse teste.

## O que o teste prova

1. Enderecos dos observadores sao extraidos do mapa do build: `GM_CurrentStageName`, `isStageSelectionMenu`, `GM_PlayerPosition`, `GM_PlayerStatus`.
2. `tools/enter_dock.lua` aguarda o seletor de desenvolvimento e envia dois Down e Circle via API do controle emulado. Nao altera memoria nem o codigo do jogo.
3. O teste exige `s00a` e conclusao do carregamento do scenario no log, nao apenas a selecao da fase.
4. Aguarda a sequencia inicial devolver o controle antes de enviar comandos. Compara coordenadas e flags ao andar, agachar/entrar em rastejo, manter deslocamento rastejando e levantar.
5. Duas amostras durante rastejo devem conter GROUND + MOVE e posicoes diferentes. So a transicao de agachar/deitar nao satisfaz a verificacao.

A rota anda para a direita e rasteja de volta para a esquerda pelo trecho ja percorrido. Andar para cima na posicao inicial termina encostado na parede; tentar continuar para a direita deitado pode ficar sem deslocamento. A fase e as colisoes nao sao modificadas para fazer o teste passar.

## Resultado negativo observado antes da implementacao

Sem `tools/enter_dock.lua`, o teste chegou ao limite de frames permanecendo em `title`, retornando exit 2 no emulador e falha na verificacao Python. Com o replay, entrou em `s00a`. O teste mais forte de rastejo tambem rejeitou uma rota em que a flag MOVE estava ligada mas nao havia deslocamento sustentado; a rota foi corrigida sem relaxar essa assercao.

## Por que TITLE nao era um travamento

Na revisao MGS fixada, `source/game/loader.c` troca o diretorio carregado de `title` para `select1` sob DEV_EXE, enquanto o nome da fase permanece `title`. `source/game/select.c` imprime TITLE com o identificador do procedimento e confirma com PAD_CIRCLE. Esse seletor e comportamento intencional do upstream, nao um menu criado por este projeto.

## Limites

Sem `--camera`, o teste verifica a locomocao do executavel dev selecionado. Com `--camera`, verifica tambem o prototipo descrito abaixo. Nao implementa Leon ou combate RE4. Nao prova campanha completa, dutos, clearance de levantar sob teto, fidelidade visual, audio ou performance. Usa frames e uma rota especifica do spawn s00a; outro build/plataforma exige revalidacao. O smoke test nao substitui playthrough e capturas visuais.

## Camera experimental

Instale com `python tools/apply_camera.py`, recompile DEV_EXE e acrescente `--camera` ao comando de teste. Exige os simbolos do prototipo no mapa corrente. Observa ativacao, reducao de altura no rastejo, ramo de retracao por hazard, cessao a primeira pessoa (Triangle) e L3 off/on. Nao escreve RAM de gameplay.

A API Lua do Redux testado omite `PCSX.CONSTS.PAD.BUTTON.L3`. O replay usa o indice serial 1 quando a constante falta: `pad.setOverride(l3)` e `pad.clearOverride(l3)`. Esse indice NAO e a mascara MGS `PAD_L3` (0x0200). O erro anterior passava nil; trocar o tipo de controle nao era a correcao do teste. Para uso manual, configure um dispositivo Analog/DualShock e o mapeamento L3; o dispositivo digital nao mapeia o clique do analogico no teclado/controle fisico.

O teste calcula a projecao aproximada de um ponto na altura do bone6 nas poses assentadas. No rastejo desconta os 320 que MGS soma a GM_SnakeCamera. Durante a transicao, esse desconto condicionado a PLAYER_GROUND nao e confiavel: o stance interno pode divergir da flag. Por isso, as amostras MOTION observam diretamente GM_PlayerBody->objs->objs[6].world.t, usando os layouts PS1 do upstream fixado.

O replay exige camera experimental ativa e o osso dentro do viewport a cada dois Vsyncs entre os controles 280 e 434 (78 amostras, sem lacunas/duplicatas), cobrindo virada, descida, rastejo e subida. Rejeita um ponto atras da camera ou fora do viewport, mas NAO prova visibilidade do modelo, ausencia de clipping ou qualidade de enquadramento. Exige inspecao visual separada, especialmente no controle414, onde a versao anterior deixava Snake fora da imagem ao levantar.

No checkpoint de rastejo (controle 320), exige tambem profundidade do ponto de referencia >= 950 unidades. Esse limite detecta a aproximacao excessiva reproduzida no dock (817,6 antes da correcao); nao e uma distancia minima universal nem obriga a camera a atravessar paredes. Para aprovar este recorte, comparar imagens na mesma pose: corpo menor, Snake ainda visivel e nenhum novo obstaculo tapando a imagem. Conferir tambem o retorno experimental junto a parede (550). Continuam obrigatorios os asserts de locomocao, primeira pessoa e L3. Um ponto projetado dentro da tela nao aprova o design final.

Para a inspecao local, use o `stage_test.lua` recem-gerado pelo mesmo build. Crie uma copia local, acrescente `PCSX.pauseEmulator()` em um frame de controle desejado e lance o mesmo executavel com `-dofile` (nao `-lua`) e sem `-no-ui`. Nao reutilize enderecos de outro asm.map. Capture somente a janela do emulador; nao publique screenshots/assets. Frames exercitados: 149 (parado), 205 (apos andar), 320 (rastejando), 530 (original apos L3) e 550 (experimental apos segundo L3). Encerre a instancia antes do proximo teste; nao confunda encerramento manual de uma inspecao com PASS do smoke completo.

## Fluxo de entrega

A cada iteracao bem-sucedida: executar a prova relevante, revisar codigo/diff e conteudo rastreado, commitar somente arquivos originais autorizados, fazer push e comparar o SHA remoto com o local. Experimento falho nao deve ser anunciado como feature concluida. Nao publicar imagens, assets, dumps, logs pessoais ou executaveis dos jogos.
