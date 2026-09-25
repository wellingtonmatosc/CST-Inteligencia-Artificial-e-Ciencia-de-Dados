# Acessibilidade e inclusão — Trilhas Poéticas

A acessibilidade é requisito transversal da experiência, não um recurso opcional adicionado no final.

## Princípio

Nenhum participante deve perder a possibilidade de obter a pontuação máxima por uma barreira exclusivamente:

- visual;
- auditiva;
- motora;
- cognitiva/comunicacional;
- física do percurso;
- de velocidade de resposta.

## Interface

O painel **Acessibilidade** oferece:

- aumentar/diminuir o texto;
- alto contraste;
- redução de movimento;
- ouvir a tela;
- parar a síntese de voz;
- comando de voz quando suportado pelo navegador.

O painel usa o mesmo tema institucional claro nas páginas públicas e no ranking. Ao ativar **Alto contraste**, a apresentação preto/branco prevalece sobre sombras, hovers e demais elementos decorativos.

Comando de voz e síntese de voz são complementos. Nenhuma função essencial depende deles. O acesso ao painel fica integrado à navegação e não deve cobrir conteúdo ou controles no celular.

Sombras e estados de hover são apenas reforços visuais: nenhuma informação, ação ou pontuação depende de passar o mouse. Em dispositivos sem hover, todos os controles permanecem utilizáveis por toque e teclado.

## Conteúdo das estações

- texto compatível com leitor de tela;
- linguagem direta e instruções claras;
- imagem essencial deve possuir texto alternativo equivalente;
- áudio/vídeo essencial deve possuir transcrição/legenda equivalente;
- audiodescrição pode ser adicionada quando a obra/atividade exigir descrição visual mais rica;
- conteúdo não deve depender apenas de cor;
- conteúdo não deve exigir rapidez para pontuar;
- se a proposta pedir para observar algo, deve oferecer percepção equivalente por descrição, som, tato/sensação ou outro meio adequado;
- botão **Ouvir conteúdo** aparece nas estações textuais;
- desafios oferecem **Ouvir desafio**.

## Questões

A versão final utiliza somente **múltipla escolha com exatamente 4 alternativas**. Antes de ativar uma questão, o sistema verifica metadados mínimos:

- instrução clara;
- sem dependência exclusiva de cor;
- sem exigência de rapidez;
- texto alternativo quando há imagem;
- transcrição/legenda quando há áudio/vídeo;
- quatro alternativas textuais distintas;
- resposta correta pertencente ao conjunto de alternativas.

A ordem das alternativas é embaralhada de forma estável por participante + questão, sem modificar o conteúdo ou exigir rapidez.

## Navegação

- link “Pular para o conteúdo”;
- navegação por teclado;
- foco visível;
- controles grandes em celular;
- mensagens de erro/sucesso com texto e `aria-live`;
- nenhum estado importante é comunicado somente por cor;
- `prefers-reduced-motion` e opção manual de redução de movimento são respeitados;
- ranking evita animações contínuas e efeitos visuais pesados;
- hovers decorativos são desativáveis por redução de movimento e não substituem foco de teclado.

## Espaço físico

A aplicação registra zona/referência, mas a instalação cabe à frente de espaços. Os 15 QRs devem permanecer inativos enquanto a localização física não estiver definida e homologada.

Na homologação física devem ser conferidos:

- rota sem barreira para atividades necessárias à pontuação máxima;
- altura e posição alcançáveis do QR e do código local;
- segurança de circulação;
- iluminação e contraste do material impresso;
- leitura do QR por diferentes celulares;
- alternativa equivalente se uma estação física ficar temporariamente inacessível.

## Testes obrigatórios

Antes do evento testar:

- Android e iPhone;
- zoom do navegador e texto ampliado;
- teclado;
- TalkBack e/ou leitor de tela Android;
- VoiceOver no iPhone quando disponível;
- alto contraste;
- redução de movimento;
- áudio desativado;
- atividade sem visão da imagem;
- atividade sem uso de comando de voz;
- rota física acessível;
- painel de acessibilidade na home, ranking e fluxo de estação.

A homologação não deve considerar acessibilidade concluída apenas porque o botão de acessibilidade existe.
