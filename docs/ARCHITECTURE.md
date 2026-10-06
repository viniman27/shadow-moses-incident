# Arquitetura: MGS permanece a autoridade

## Decisão inicial e seu limite

Investigar um mod da base MGS Integral, começando pela variante upstream `dev_exe`. Não transplantar o loop principal de RE4 e não substituir os sistemas de missão de MGS. Isso é uma direção técnica provisória, não viabilidade comprovada.

As bases têm plataformas, ABI, renderização, formatos de assets e toolchains diferentes: MIPS/PS1 versus PowerPC/GameCube. Colar arquivos C/C++ de uma na outra não produz uma fusão funcional. RE4 será referência de comportamento; eventual código original de adaptação precisa respeitar os sistemas e orçamento de MGS.

## Mapa extraído do código

Os caminhos abaixo são relativos ao respectivo upstream fixado no manifesto. Sem índice de grafo disponível, o levantamento foi feito nos arquivos.

### MGS: câmera

`source/game/camera.h` declara `GM_CameraSystemWork`, `GM_SnakeCameraWork` e `GM_SetCameraCallbackFunc`.

`source/game/camera.c:280-352` mostra caminhos condicionais para callbacks: índice 0 sob flag 0x200, índice 1 sob flag 2, com prioridade de outros modos. São candidatos de integração, NÃO um hook universal livre de efeitos colaterais. É necessário verificar quem já ocupa os callbacks e quem restaura os flags em cada fase antes de usar.

`GM_CameraEventReset` e `GM_CheckBehindCamera` também fazem parte da superfície de investigação. A câmera nova deve ceder aos eventos, cutscenes, dutos e modos especiais; nunca sobrescrever o resultado final incondicionalmente a cada frame.

### MGS: deitar e rastejar

`source/chara/snake/sna_init.c`:

- `sna_prone_check_standup_80050398` (linha 1226): combina o comando de levantar com uma verificação espacial antes de iniciar a transição.
- `sna_anim_prone_idle_800528BC` (2737).
- `sna_anim_prone_move_800529C0` (2771).
- `sna_anim_prone_begin_80053BE8` (3433).
- `sna_anim_prone_standup_80053D74` (3483).

Preservar os estados de gameplay do ator MGS; a representação de Leon precisará acompanhá-los. Não substituir esse controlador pelo de RE4. Animações de rastejar compatíveis com Leon ainda precisam ser produzidas/retargeteadas; não foi provado que o pacote de RE4 forneça tudo que MGS exige.

### RE4: referência de câmera e combate

- `src/game/cam_qfps.cpp`: `CameraQuasiFPS`, offsets por contexto, mistura de estados e `hitCheck` (linha 705). Sua colisão depende de sistemas do próprio RE4; não portar sem adaptador de colisão MGS.
- `src/wep/pl_handgun.cpp`: candidato de leitura para a sequência de uso de pistola.
- `docs/overview.md:97-105`: guia upstream descreve ready/fire/reload, `cPlayer` e `cPlWep`.

A leitura atual localizou os pontos; não reconstruiu ainda o grafo completo de dano, projéteis, inimigos ou animações. Valores e timing finais devem ser validados por gameplay, não inventados como se fossem os originais.

## Contrato proposto

1. Mundo, colisão, missões e flags persistentes pertencem a MGS.
2. Câmera sobre o ombro recebe pose e postura MGS; testa obstrução na geometria MGS e recua antes da parede. Retorna controle integralmente aos modos especiais.
3. Mira, tiro e recarga devem acionar dano/ruído/alerta nos sistemas MGS. Não adicionar um sistema paralelo de vida que os chefes e scripts desconheçam.
4. Leon é a representação do protagonista, sem quebrar identidade de ator, triggers, inventário ou scripts. Troca de modelo não resolve rig, animações, colisores e interações por si só.
5. Referência inicial é RE4 clássico (o repositório indicado), não o remake. Movimento durante mira, faca, stagger, golpe contextual e balanceamento precisam de especificação/validação incremental.

## Riscos ainda abertos

- Geometria criada para câmera alta pode expor faces ausentes e problemas de visibilidade/culling com câmera baixa.
- Memória, precisão de coordenadas, clipping e desempenho PS1 limitam câmera/modelo/combate; emular mais rápido não remove essas limitações automaticamente.
- O upstream MGS ainda tem overlays incompletos. Executável principal totalmente reconstruído não comprova toda a campanha modificável.
- A variante dev embute overlays e pode ter comportamento diferente do matching; é ambiente de trabalho, não promessa de distribuição final.
- Hitboxes, reações por região e melee exigem alterações nos inimigos e regressão de chefes; não são só alterações na arma.
- Save/load, troca de disco, cutscenes e modos especiais precisam de testes de ponta a ponta.

## Ordem de gates

A. Build original e dev: executados. Boot baseline: pendente de arquivos do jogo e emulador configurado.
B. Spike de câmera no Loading Dock (`s00a`), com alternância para câmera original e rastejo preservado.
C. Pistola: mira, colisão do disparo, recarga e alertas, sem comprometer stealth.
D. Leon: pipeline local de modelo/rig/animações, incluindo deitar/rastejar/levantar.
E. Expandir combate e campanha por áreas; testar todos os critérios de aceitação.

Se B mostrar que o renderizador impede o objetivo, apresentar evidências e pedir decisão antes de mudar para um port nativo ou outro motor. Não substituir silenciosamente o pedido por um demonstrador genérico.
