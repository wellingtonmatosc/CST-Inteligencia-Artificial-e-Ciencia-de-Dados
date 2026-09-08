# Homologação final — Trilhas Poéticas

A homologação só termina quando o fluxo tecnológico e o percurso físico forem testados como participante real.

## Critério de aprovação

Não pode existir bloqueador de:

- segurança;
- pontuação duplicada/incorreta;
- sequência;
- autenticação/ativação;
- acessibilidade;
- uso em celular;
- operação administrativa.

## 1. CI e banco

- [ ] Python compila.
- [ ] JavaScript passa em `node --check`.
- [ ] Pytest 100% aprovado.
- [ ] Não existem módulos `gamification.py`, `gamification_optimized.py`, `scoring.py` ou `bonus_schedule.py`.
- [ ] Não existem tabelas antigas de activity/bonus/question pool.
- [ ] Não existem funções `game_*` do protótipo.
- [ ] `anon`/`authenticated` não executam RPCs críticas.
- [ ] RLS habilitado.
- [ ] `service_role` é o único caminho de escrita/leitura do jogo pela Data API.

## 2. Acesso

Testar pelo menos:

- [ ] cadastro externo;
- [ ] cadastro público de aluno não pré-carregado;
- [ ] matrícula já pré-carregada direciona para ativação;
- [ ] ativação institucional por código;
- [ ] nick bloqueado;
- [ ] nick duplicado;
- [ ] login por nick + PIN;
- [ ] 5 PINs errados → bloqueio temporário;
- [ ] recuperação rotaciona o código;
- [ ] logout revoga a sessão;
- [ ] QR aberto antes do login retorna automaticamente à mesma estação após autenticação.

## 3. Equipes

- [ ] cinco equipes ativas;
- [ ] distribuição equilibrada em amostra com diferentes turmas/tipos;
- [ ] participante não escolhe equipe;
- [ ] equipe fica secreta antes da primeira validação;
- [ ] equipe é revelada depois da primeira validação;
- [ ] organizador fica sem equipe competitiva e sem pontos.

## 4. Estações

Para cada tipo:

- [ ] permanente concede pontos uma única vez;
- [ ] sequencial bloqueia etapa fora de ordem;
- [ ] sequência completa gera bônus uma única vez;
- [ ] temporário respeita início e fim;
- [ ] especial funciona com pontuação configurada;
- [ ] código físico errado é recusado;
- [ ] repetição do mesmo QR não duplica pontos;
- [ ] link compartilhado sem código físico não concede pontos;
- [ ] QR inativo retorna indisponível.

## 5. Desafios

- [ ] múltipla escolha;
- [ ] verdadeiro/falso com 1 tentativa;
- [ ] resposta curta normalizada;
- [ ] resposta incorreta mostra tentativa restante junto ao formulário;
- [ ] desafio correto adiciona os pontos configurados;
- [ ] erro no desafio não remove pontos-base;
- [ ] desafio concluído não pode ser pontuado novamente.

## 6. Ranking

- [ ] zerado → nenhuma posição fictícia;
- [ ] após pontuação → equipes ordenadas;
- [ ] total de pontos confere com `point_ledger`;
- [ ] organizadores não influenciam ranking;
- [ ] estorno reduz ranking corretamente;
- [ ] nenhum nome completo/matrícula aparece publicamente.

## 7. Administração

Testar papéis:

- [ ] `admin` — total;
- [ ] `operator` — operação sem gestão de admins/organizadores;
- [ ] `validator` — consulta + pontos extras/estornos;
- [ ] `viewer` — somente leitura.

Testar:

- [ ] criar/editar/desativar estação;
- [ ] salvar código físico;
- [ ] salvar janela temporária;
- [ ] cadastrar conteúdo com imagem acessível;
- [ ] rejeitar imagem sem alt text;
- [ ] rejeitar áudio/vídeo sem transcrição;
- [ ] criar trilha e sequência;
- [ ] cadastrar desafio;
- [ ] conceder ponto extra;
- [ ] estornar com justificativa;
- [ ] auditoria registra mudanças.

## 8. Acessibilidade

- [ ] teclado completo;
- [ ] foco visível;
- [ ] zoom/texto ampliado;
- [ ] alto contraste;
- [ ] redução de movimento;
- [ ] ouvir tela;
- [ ] ouvir conteúdo;
- [ ] ouvir desafio;
- [ ] uso normal com comando de voz indisponível;
- [ ] TalkBack ou equivalente Android;
- [ ] VoiceOver ou equivalente iOS;
- [ ] conteúdo visual com alternativa textual;
- [ ] conteúdo sonoro com transcrição;
- [ ] percurso físico equivalente/acessível.

## 9. Dispositivos e carga

Mínimo recomendado para homologação:

- 2 modelos Android;
- 1 iPhone;
- câmera nativa + leitor interno quando suportado;
- Wi-Fi e rede móvel;
- múltiplos participantes validando a mesma estação simultaneamente;
- repetição rápida da mesma requisição para confirmar idempotência.

## 10. Fechamento

Somente depois de todos os bloqueadores resolvidos:

1. remover usuários/dados temporários de homologação;
2. zerar pontuação para início oficial;
3. carregar base oficial;
4. cadastrar conteúdo/estações definitivos;
5. gerar e imprimir QRs finais;
6. testar fisicamente;
7. validar Vercel e Supabase;
8. aprovar merge na `main`.
