# Critérios de aceitação da fusão

O conjunto completo permanece pendente. O recorte de câmera/locomoção em s00a tem evidência parcial em VERIFICATION.md; isso não aprova os requisitos amplos abaixo.

## Primeiro recorte jogável

Loading Dock (`s00a`), dentro do MGS real, não numa arena substituta:

- Entrada e saída da câmera sobre o ombro sem salto inválido de posição ou perda de controle.
- Obstrução: parede entre pivô e câmera causa recuo; mira não permite disparo atravessando a parede.
- Deitar, permanecer deitado, rastejar, entrar/sair do espaço baixo e levantar somente com espaço livre.
- Câmera respeita a postura e não exige levantar para corrigir seu enquadramento.
- Mira/tiro/recarga funcionam; munição não fica negativa; menus/cutscenes não causam tiro involuntário.
- Disparo interage com dano e alerta MGS; alvos atrás de obstáculos não são atingidos.
- Trigger de progressão e transição à próxima área continuam funcionando.
- Leon deve ter modelo e animações reconhecíveis e compatíveis, sem quebrar colisão ou o ator de missão. Um placeholder não satisfaz este item.

## Preservação de MGS

Registrar regressão por fase para campanha, stealth, detecção/alerta/evasão, radar, Codec, itens, armas especiais, encostar em paredes, escadas, dutos, portas/cartões, cutscenes, chefes, morte/retry, save/load e troca de disco. Eventos específicos devem ganhar casos conforme o caminho real do código for inspecionado.

## Combate RE4

Validar primeiro o ciclo de pistola e mira sobre o ombro. Depois especificar/reproduzir faca, reações a acerto, stagger, ações contextuais e demais armas compatíveis com os encontros MGS. A referência é o clássico; fidelidade exata e ajustes de balanceamento ainda não foram definidos.

## Evidência exigida

Para cada gate: revisão de código, comando/build, versão do jogo/emulador, passos reproduzíveis, resultado esperado versus observado e captura local quando possível. Build bem-sucedido não conta como teste de gameplay. Não declarar a campanha preservada sem playthrough e casos especiais.
