# Shadow Moses Incident

Projeto experimental: Metal Gear Solid 1 como base, Leon como protagonista e câmera/combate inspirados em Resident Evil 4 clássico (2005).

**Estado: fundação técnica; a fusão ainda NÃO está implementada nem jogável.**

MGS Integral foi reconstruído (build original com SHA-256 idêntico ao esperado) e executado em PCSX-Redux/OpenBIOS. Um teste local automatizado entra em Loading Dock pelo seletor de fases e verifica andar, rastejar com deslocamento sustentado e levantar pela memória do jogo. Isso valida a base original, não a fusão: ainda não há câmera nova, combate novo ou modelo de Leon integrado.

## Objetivo

Preservar a campanha, mapas, scripts, stealth, alertas, Codec, itens, chefes e progressão de MGS1. Adicionar câmera sobre o ombro, mira e combate inspirados em RE4, controlando Leon. Deitar, rastejar, atravessar dutos e levantar com verificação de espaço são requisitos obrigatórios, não funcionalidades descartáveis.

O alvo inicial de investigação é MGS Integral PS1 executado em emulador no PC. Não é um port nativo para Windows nem uma promessa de compatibilidade com hardware PS1. A viabilidade do conjunto completo permanece aberta.

## Referências

- https://github.com/FoxdieTeam/mgs_reversing
- https://github.com/adonis-singh/re4
- https://github.com/FoxdieTeam/psyq_sdk (toolchain do build MGS)

Revisões fixadas em `upstreams.lock.json`. Os repositórios externos são checkouts locais separados, não conteúdo redistribuído aqui.

## Documentação

- [Arquitetura e riscos](docs/ARCHITECTURE.md)
- [Critérios de aceitação](docs/ACCEPTANCE.md)
- [Build reproduzível](docs/BUILD.md)
- [Resultados efetivamente verificados](docs/VERIFICATION.md)
- [Teste local de fase e locomoção](docs/TESTING.md)

## Limites de distribuição

Este repositório publica documentação, automação de controle e testes originais de integração neste estágio. Não contém imagens de discos, BIOS, executáveis reconstruídos, SDKs, modelos, texturas, áudio ou código descompilado dos jogos. O futuro formato de entrega deverá permitir alterações locais sobre arquivos que o usuário tenha direito de utilizar.

Disponibilidade pública de uma descompilação não equivale a uma licença irrestrita de reutilização. A licença de RE4 exclui expressamente o código reconstruído do jogo/SDK/middleware de seu CC0. Não foi encontrado LICENSE/COPYING na raiz de MGS. Não se presume autorização para redistribuição nem se promete imunidade a reclamações de titulares.

Projeto de fã não afiliado a Konami, Capcom, Sony ou Nintendo. Nenhuma licença sobre propriedade de terceiros é concedida por este repositório.
