# Requisitos funcionais — Trilhas Poéticas

Este documento registra apenas o sistema atual, alinhado ao projeto-base Trilhas Poéticas.

## Participantes

- Público interno e externo.
- Existe um único fluxo de cadastro.
- Aluno informa matrícula e curso/turma.
- Servidor informa o tipo de participante.
- Público externo pode informar instituição/empresa.
- O participante escolhe nick e define PIN de 4 dígitos no próprio cadastro.
- Login normal: nick + PIN.
- Recuperação por código rotativo.
- PIN armazenado somente como Argon2.
- Após 5 PINs incorretos, bloqueio temporário por 2 minutos.
- Sessão em cookie HttpOnly; logout revoga a sessão no servidor.
- Organizadores ficam fora da competição e não pontuam.
- Não existe etapa separada de ativação institucional.
- Desativar um participante impede novas ações, mas não apaga os pontos que ele já conquistou para sua equipe.
- Se um participante for transferido de equipe, somente as novas ações passam a pontuar para a nova equipe; o histórico permanece com a equipe do momento da conquista.

## Equipes

- Cinco equipes secretas: Tarsila, Anita, Mário, Oswald e Pagu.
- O participante não escolhe a equipe.
- A distribuição busca equilíbrio por tipo de participante, curso/turma e tamanho da equipe.
- A equipe fica oculta até a primeira estação validada.

## Estações QR

Tipos suportados:

- `permanent` — referência 10 pontos;
- `sequential` — referência 15 pontos;
- `temporary` — referência 30 pontos;
- `special` — referência 40 pontos.

Regras:

- uma pessoa + um QR = uma única pontuação válida;
- várias pessoas podem usar a mesma estação simultaneamente;
- o link do QR sozinho não concede pontos quando a estação possui código físico;
- código/palavra-chave local é comparado por hash;
- não é usado GPS;
- temporários/especiais podem ter janela de início/fim;
- a janela temporal é validada tanto ao abrir/validar a estação quanto ao enviar a resposta do desafio;
- QR inativo, não iniciado ou expirado não pontua;
- estação danificada pode ser desativada pelo painel.

## Trilhas sequenciais

- Uma trilha possui etapas ordenadas.
- Etapa posterior fica bloqueada enquanto faltar uma etapa anterior finalizada.
- Se a estação anterior possuir desafio, a etapa só é considerada finalizada depois de o participante acertar ou esgotar as tentativas permitidas.
- Errar o desafio não bloqueia definitivamente a trilha: ao esgotar as tentativas, a etapa é finalizada sem os pontos extras do desafio.
- Ao finalizar todas as etapas, o participante recebe o bônus configurado uma única vez.
- Referência inicial de bônus: +30 pontos.

## Conteúdo cultural

Uma estação pode conter:

- poesia;
- literatura;
- arte;
- cultura brasileira/regional;
- texto contextual;
- imagem com descrição equivalente;
- áudio/vídeo com transcrição ou legenda equivalente;
- desafio opcional.

Nem toda estação precisa usar todas essas mídias. A curadoria cultural é cadastrada após aprovação da frente responsável.

## Desafios

Tipos habilitados atualmente:

- múltipla escolha;
- verdadeiro/falso;
- resposta curta.

Associação e ordenação não fazem parte da versão atual porque exigiriam interface própria para garantir boa usabilidade e acessibilidade.

- desafio pode conceder de 0 a 20 pontos;
- verdadeiro/falso: 1 tentativa;
- demais tipos: até 2 tentativas;
- erro não retira os pontos-base já obtidos na validação da estação;
- não existe cronômetro de resposta nem bônus por velocidade.

## Ranking

- Ranking público principal é por equipe, sem exposição de nome completo/matrícula.
- Cada lançamento de pontuação, visita, conclusão de trilha e ação manual registra também a equipe do momento da conquista.
- Pontos históricos não desaparecem quando o participante é desativado e não migram quando ele muda de equipe.
- A classificação principal prioriza a média de pontos por participante que efetivamente contribuiu para a equipe.
- Pontos totais, trilhas concluídas, estações validadas e nome da equipe são usados como critérios sucessivos de desempate.
- Número atual de integrantes e percentual de ativação continuam visíveis como indicadores, mas não alteram a posição por si só; assim, uma entrada tardia sem atividade não derruba a equipe no ranking.
- Enquanto ninguém iniciou a experiência, nenhuma equipe recebe posição artificial.

## Área do participante

Exibe:

- nick;
- pontos individuais;
- equipe após revelação;
- posição da equipe quando houver classificação iniciada;
- estações validadas;
- trilhas concluídas;
- desafios pendentes;
- temporários/especiais ativos;
- acesso ao leitor de QR e ranking.

## Pontos extras

Ações extras são concedidas somente por usuário autorizado. Tipos previstos pelo sistema:

- declamação;
- obra autoral;
- sugestão de poema;
- sugestão selecionada;
- produção artística;
- postagem válida;
- participação em atividade;
- outra ação aprovada.

Cada lançamento registra participante, equipe do momento, descrição, evidência/referência, pontos, aprovador e data. O estorno gera lançamento negativo na mesma equipe histórica e mantém o lançamento original.

## Administração e papéis

- `admin`: tudo, inclusive usuários administrativos e status de organizador;
- `operator`: desafios, estações, conteúdo, trilhas, moderação e pontos extras;
- `validator`: consulta e validação/estorno de pontos extras;
- `viewer`: somente consulta.

Toda alteração relevante produz registro de auditoria.

## Segurança

- Browser → FastAPI → Supabase.
- Secret key somente no backend.
- RLS habilitado nas tabelas expostas pela Data API.
- `anon` e `authenticated` sem acesso direto às tabelas do jogo.
- RPCs críticas `SECURITY DEFINER` executáveis somente por `service_role`.
- Sessões administrativas assinadas e com expiração.
- Senhas administrativas e PINs nunca persistidos em texto puro.

## Acessibilidade

- nenhuma atividade pode depender exclusivamente de visão, audição, cor, rapidez ou precisão motora;
- texto ajustável;
- alto contraste;
- redução de movimento;
- leitura de tela/conteúdo/desafio quando o navegador oferece síntese de voz;
- comando de voz opcional, nunca obrigatório;
- navegação por teclado e foco visível;
- mensagens com texto e `aria-live`;
- imagem essencial exige descrição equivalente;
- áudio/vídeo essencial exige transcrição/legenda;
- conteúdo que mencione percepção do ambiente deve permitir formas sensoriais equivalentes.

## Responsabilidade física

A tecnologia suporta zona, referência e regras de acessibilidade. A definição do ponto físico exato, percurso e instalação dos QR Codes pertence à frente de espaços/logística.
