# Shadow Moses Incident

Projeto experimental: Metal Gear Solid 1 como base, Leon como protagonista e câmera/combate inspirados em Resident Evil 4 clássico (2005).

**Estado: protótipo de câmera limitado ao Loading Dock; a fusão completa ainda NÃO está implementada.**

MGS Integral foi reconstruído (build original com SHA-256 idêntico ao esperado) e executado em PCSX-Redux/OpenBIOS. Um teste local automatizado entra em Loading Dock pelo seletor de fases e verifica andar, rastejar com deslocamento sustentado e levantar pela memória do jogo. Há agora uma câmera experimental DEV_EXE em s00a, com Snake visível nas capturas locais, altura por postura e toggle L3. A margem de retração junto à parede foi reduzida de proporcional para fixa, com melhora parcial confirmada no replay e nas imagens de rastejo/retorno; o corpo ainda ocupa muito espaço perto de obstáculos. A altura também acompanha um limite relativo à cabeça durante mudanças de postura, corrigindo o desaparecimento visual ao levantar no replay testado. Uma compensação limitada de zoom agora reduz a ampliação do corpo quando a parede não permite mais recuo, sem mover o olho através dela; a nova rota de ida/aproximação de costas/afastamento verifica a projeção e foi comparada visualmente. A perda do afastamento lateral e a colisão volumétrica ainda não foram redesenhadas. Isso não aprova a câmera para a campanha: combate RE4 e Leon ainda não foram implementados. Consulte os limites e evidências em VERIFICATION.md.

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

Este repositório publica documentação, automação de controle, código original do protótipo de câmera e testes de integração neste estágio. Não contém imagens de discos, BIOS, executáveis reconstruídos, SDKs, modelos, texturas, áudio ou código descompilado dos jogos. O futuro formato de entrega deverá permitir alterações locais sobre arquivos que o usuário tenha direito de utilizar.

Disponibilidade pública de uma descompilação não equivale a uma licença irrestrita de reutilização. A licença de RE4 exclui expressamente o código reconstruído do jogo/SDK/middleware de seu CC0. Não foi encontrado LICENSE/COPYING na raiz de MGS. Não se presume autorização para redistribuição nem se promete imunidade a reclamações de titulares.

Projeto de fã não afiliado a Konami, Capcom, Sony ou Nintendo. Nenhuma licença sobre propriedade de terceiros é concedida por este repositório.
