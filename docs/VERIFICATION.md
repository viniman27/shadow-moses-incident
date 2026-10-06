# Evidência inicial

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

## Bloqueios/limitações reais

- Boot/gameplay não executados: usuário ainda não indicou imagem compatível nem emulador configurado.
- RE4 não compilado. Colisão de nomes no checkout Windows registrada em BUILD.md.
- Nenhuma modificação de gameplay implementada ou testada.
- Nenhum asset de Leon importado.
- Nenhum playthrough, teste visual, de desempenho ou de save/load executado.

## Separação entre evidência e intenção

O mapa de código é inspeção estática. A arquitetura e os critérios de aceitação são propostas de implementação. Somente os resultados de compilação e validação binária acima constituem evidência executada nesta etapa.
