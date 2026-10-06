# Build local da base

Estes comandos recompõem o upstream MGS SEM a fusão. Executados no Windows com Python 3.14.7 e ambiente virtual dedicado. Os caminhos abaixo usam `D:/ShadowMosesIncident` como raiz.

## Referências e ambiente

```text
git clone https://github.com/FoxdieTeam/mgs_reversing D:/ShadowMosesIncident/references/mgs_reversing
git clone https://github.com/FoxdieTeam/psyq_sdk D:/ShadowMosesIncident/references/psyq_sdk
git -C D:/ShadowMosesIncident/references/mgs_reversing checkout 7b66372bcf156249560c90918d9472a47aabf3c5
git -C D:/ShadowMosesIncident/references/psyq_sdk checkout fec561c5771a981a6090c315cbe338f7967137cd
python -m venv D:/ShadowMosesIncident/.venv
D:/ShadowMosesIncident/.venv/Scripts/python.exe -m pip install -r D:/ShadowMosesIncident/references/mgs_reversing/build/requirements.txt
```

Não rodar clone por cima dos checkouts existentes. Não distribuir o SDK com o projeto.

Dependências instaladas nesta verificação: ninja 1.13.2, colorama 0.4.6, termcolor 3.3.0, capstone 5.0.9, iterfzf 1.9.0.67.0, pyperclip 1.11.0, Jinja2 3.1.6, levenshtein 0.27.5, MarkupSafe 3.0.4 e rapidfuzz 3.14.6. O requirements upstream não fixa versões; a lista registra o ambiente testado.

## Compilar

No diretório `D:/ShadowMosesIncident/references/mgs_reversing/build`:

```text
D:/ShadowMosesIncident/.venv/Scripts/python.exe build.py --variant=dev_exe
D:/ShadowMosesIncident/.venv/Scripts/python.exe build.py
```

Saídas relativas ao checkout MGS:

- `obj_dev/_mgsi.exe`: build de desenvolvimento.
- `obj/_mgsi.exe`: build matching; SHA-256 esperado `4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f`.

O build dev NÃO precisa manter o hash original. Os dois arquivos são executáveis PS1, não programas Windows; não abrir como aplicações de PC.

## Rodar pelo helper upstream — alternativa não utilizada

O upstream documenta, a partir de `build/`:

```text
python run.py --iso <imagem-local-compativel> --pcsx-redux <diretorio-pcsx-redux>
```

Usar o Python do ambiente virtual no lugar de `python`. O alvo documentado é o disco 1 MGS Integral `SLPM-86247`, não qualquer edição americana/europeia. Verificar a versão e configurar emulador/BIOS conforme necessário, usando arquivos que o usuário tenha direito de utilizar. Nenhuma imagem ou BIOS foi fornecida, procurada indiscriminadamente nos discos ou baixada nesta etapa.

## Instalar/remover a câmera experimental

Na raiz do projeto, `python tools/apply_camera.py` instala o header original e um hook sob `#ifdef DEV_EXE` no checkout MGS fixado. Depois execute o build dev acima e o teste com `--camera` descrito em TESTING.md. O instalador recusa uma revisão diferente e edições não reconhecidas em camera.c.

`python tools/apply_camera.py --remove` restaura camera.c e remove o header gerado. É obrigatório recompilar DEV_EXE para restaurar também o executável. Instalação repetida, remoção exata e reinstalação foram exercitadas. O build matching continua igual ao hash upstream com o hook instalado, pois ele só participa de DEV_EXE.

## RE4

Não é necessário compilar RE4 para o primeiro spike de câmera MGS. O upstream RE4 exige Linux, toolchains próprias e os dois discos debug G4BE08 de novembro de 2004 para reconstrução; uma cópia comercial comum não substitui esses insumos.

O checkout RE4 no Windows apresentou colisões entre `src/Tools` e `src/tools` em `t_prim.cpp`, `t_util.cpp`, `tools.cpp`. Ele serve apenas para a inspeção dos arquivos não afetados. Para build confiável, obter um checkout em filesystem Linux case-sensitive (por exemplo, ext4 no WSL), não apenas usar `/mnt/d` sobre um diretório Windows insensível a caixa. Não tratar os arquivos colididos como alterações intencionais.
