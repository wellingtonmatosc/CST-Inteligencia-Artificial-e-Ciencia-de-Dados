# Acessibilidade e inclusão

A regra central é: **nenhuma característica física, sensorial ou necessidade de acessibilidade pode reduzir a pontuação máxima que uma pessoa consegue alcançar**.

## Espaço físico
- Nenhuma pontuação necessária pode exigir uso de escadas.
- Bônus oferecem opções equivalentes simultâneas em Cantina, Térreo e 1º andar.
- Se um QR acessível for removido/danificado, deve existir substituição equivalente na mesma zona.
- Pontos externos distantes são opcionais.
- A equipe de espaços deve validar presencialmente rampas, circulação, portas e obstáculos; o sistema não presume que uma rota é acessível apenas por existir uma rampa.

## Painel de acessibilidade da interface
O botão **Acessibilidade** fica disponível nas telas do sistema e armazena preferências apenas no navegador do participante.

Recursos implementados:
- tamanho de texto ajustável de 90% a 140%;
- modo claro;
- alto contraste;
- redução de animações;
- maior espaçamento entre controles e áreas de toque;
- modo leitura, que reduz elementos decorativos e prioriza conteúdo.

## Interface
- HTML semântico e navegação por teclado.
- Foco visível e alvos de interação grandes.
- Contraste adequado e suporte à ampliação de texto.
- Informação não depende somente de cor.
- Verde não é utilizado como cor principal nem como indicador de estado.
- A paleta usa azul, roxo, âmbar/laranja e vermelho, sempre acompanhados de texto explícito.
- Respeito a `prefers-reduced-motion` e também a uma preferência manual de redução de animações.
- Mensagens de erro/sucesso são anunciadas por regiões `aria-live`.
- Ranking público exibe nick, não dados pessoais.

## Apoio de leitura nas questões
- Quando o navegador oferece Web Speech API, o participante pode ouvir apenas o enunciado ou o enunciado com as alternativas.
- O participante pode interromper a leitura em voz alta a qualquer momento.
- Questões podem ter `simplified_prompt`, uma versão de linguagem mais direta que preserva o mesmo conteúdo e não oferece pista da resposta.
- O nível de leitura pode ser registrado nos metadados da questão.
- Imagem essencial exige `alt_text` equivalente.
- Áudio/vídeo essencial exige `transcript` ou legenda equivalente.

## Regras do conteúdo
- Linguagem objetiva e instruções relíveis.
- Sem cronômetro como critério de pontuação.
- Não criar questão cuja resposta dependa somente de cor.
- Não exigir precisão motora ou rapidez para receber pontuação máxima.
- Quando um formato não puder ser adaptado com equivalência, oferecer atividade alternativa com a mesma pontuação.
- Questão ativa deve passar pela validação de metadados de acessibilidade.
- Verdadeiro/Falso deve representar uma parcela menor do banco para evitar vantagem estatística pelo chute.

## Banco inicial
A versão de homologação inclui 24 questões acessíveis distribuídas nas 12 categorias, com apenas 3 questões de Verdadeiro/Falso. Todas recebem os metadados `instructions_clear=true`, `depends_on_color_only=false` e `requires_speed=false`, além de nível de leitura e versão simples quando cadastradas pelo seed inicial.

## Dados, autenticação e respeito
- Nick passa por moderação configurável; conteúdo agressivo, discriminatório ou impróprio pode ser bloqueado/desativado.
- Termos de moderação são configuráveis, evitando uma lista cultural rígida no código.
- Dados pessoais ficam fora do ranking e do frontend público.
- Participante entra por nick + PIN de 4 dígitos; PIN é armazenado apenas como hash Argon2.
- Cinco tentativas incorretas de PIN provocam bloqueio temporário de 2 minutos, reduzindo risco de força bruta sem criar grande atrito no evento.
