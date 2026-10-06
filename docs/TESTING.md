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

Este e um teste de integracao da BASE ORIGINAL, nao uma implementacao de Leon/camera/combate RE4. Nao prova campanha completa, dutos, clearance de levantar sob teto, fidelidade visual, audio ou performance. Usa frames e uma rota especifica do spawn s00a; outro build/plataforma exige revalidacao. O smoke test nao substitui playthrough e capturas visuais.

## Fluxo de entrega

A cada iteracao bem-sucedida: executar a prova relevante, revisar codigo/diff e conteudo rastreado, commitar somente arquivos originais autorizados, fazer push e comparar o SHA remoto com o local. Experimento falho nao deve ser anunciado como feature concluida. Nao publicar imagens, assets, dumps, logs pessoais ou executaveis dos jogos.
