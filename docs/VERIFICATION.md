# Evidência de execução

## MGS: execução real

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

## Limitações reais

- Boot e recorte automatizado de locomoção executados; campanha completa não testada.
- RE4 não compilado. Colisão de nomes no checkout Windows registrada em BUILD.md.
- Nenhuma modificação de gameplay implementada ou testada.
- Nenhum asset de Leon importado.
- Nenhum playthrough completo, validação visual do recorte jogável, teste de desempenho ou de save/load executado.

## Separação entre evidência e intenção

O mapa de código é inspeção estática. A arquitetura de fusão e os critérios de aceitação continuam sendo propostas. Compilação, validação binária e o teste de integração explicitado acima são evidências executadas; não comprovam requisitos ainda ausentes.
