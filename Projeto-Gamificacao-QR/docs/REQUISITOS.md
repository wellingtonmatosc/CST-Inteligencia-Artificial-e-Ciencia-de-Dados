# Requisitos funcionais — Trilhas Poéticas

Este documento registra apenas o sistema atual, alinhado ao projeto-base Trilhas Poéticas.

## Participantes

- Público interno e externo.
- A base institucional pode ser pré-importada com minimização de dados.
- Participante pré-importado ativa a conta com código de ativação, escolhe nick e define PIN de 4 dígitos.
- Quem não estiver na base pode usar cadastro público quando essa opção for mantida pela organização.
- Aluno em cadastro público informa matrícula e curso/turma.
- Login normal: nick + PIN.
- Recuperação por código rotativo.
- PIN armazenado somente como Argon2.
- Após 5 PINs incorretos, bloqueio temporário por 2 minutos.
- Sessão em cookie HttpOnly; logout revoga a sessão no servidor.
- Organizadores ficam fora da competição e não pontuam.

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
- QR inativo, não iniciado ou expirado não pontua;
- estação danificada pode ser desativada pelo painel.

## Trilhas sequenciais

- Uma trilha possui etapas ordenadas.
- Etapa posterior fica bloqueada enquanto faltar etapa anterior.
- Ao validar todas as etapas, o participante recebe o bônus configurado uma única vez.
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
- Indicadores: pontos, participantes ativos, percentual de ativação, média por ativo, estações e trilhas concluídas.
- Desempate: pontos, ativação, média por participante ativo, trilhas concluídas.
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

Cada lançamento registra participante, descrição, evidência/referência, pontos, aprovador e data. O estorno gera lançamento negativo e mantém o histórico original.

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
