# Arquitetura — Trilhas Poéticas

## Fluxo

```text
Celular / navegador
        │ HTTPS
        ▼
Vercel + FastAPI
        │ service role somente no servidor
        ▼
Supabase / PostgreSQL
```

O browser nunca acessa o banco privilegiado diretamente.

## Frontend

HTML/CSS/JavaScript simples, mobile-first e sem framework pesado:

- `index.html` + `index.js`: login, cadastro, perfil, avatar e leitor de QR;
- `scan.html` + `scan.js`: estação, conteúdo e desafio;
- `ranking.html` + `ranking.js`: ranking individual;
- `admin.html` + `admin.js`: painel administrativo;
- `common.js`: API helper e acessibilidade;
- `avatars.js`: catálogo vetorial local de avatares.

Tema final: institucional claro nas telas gerais e ranking escuro, sem verde. Efeitos contínuos pesados foram removidos.

## Backend

FastAPI concentra autenticação, validação e acesso ao Supabase. Operações críticas de pontuação ficam em RPCs PostgreSQL atômicas.

Principais RPCs:

- `trilhas_participant_from_session`;
- `trilhas_home_state_from_session`;
- `trilhas_get_station`;
- `trilhas_validate_station`;
- `trilhas_select_station_question`;
- `trilhas_answer_challenge`;
- `trilhas_complete_trail_if_ready`;
- `trilhas_participant_summary`;
- `trilhas_individual_ranking`;
- RPCs administrativas de pontos manuais.

Não existem mais funções de equipes.

## Banco final

Entidades principais:

```text
participants ──< participant_sessions
      │
      ├──< station_visits ──< station_attempts
      ├──< trail_completions
      ├──< point_ledger
      └──< manual_point_actions

categories ──< questions
zones ──< qr_points ──1 station_contents
                   ├──< station_question_pool >── questions
                   └──< trail_steps >── trails

event_days
final_tiebreak_results
admin_users
audit_log
blocked_terms
```

A estrutura antiga de equipes e os campos antigos de matrícula/turma/instituição foram removidos. `station_contents` contém conteúdo cultural; questões são atribuídas pelo `station_question_pool`.

## Concorrência e idempotência

- índice único impede duas validações do mesmo participante + QR + data;
- ledger usa chaves únicas de deduplicação;
- seleção de questão é serializada por QR/dia com advisory lock para reduzir colisões simultâneas;
- questões previamente atribuídas ao participante são excluídas da seleção;
- tentativas e pontuação são calculadas no PostgreSQL.

## Segurança

- RLS nas tabelas expostas pela Data API;
- `anon`/`authenticated` sem acesso direto às tabelas do jogo;
- RPCs críticas executáveis pelo backend com `service_role`;
- PIN e senha administrativa não são persistidos em texto puro;
- código físico e código de recuperação são armazenados como hash;
- sessão participante por token aleatório armazenado como hash;
- sessão administrativa assinada e expira;
- headers de frame, MIME sniffing, referrer e Permissions-Policy ativos.

## Produção

Domínio: `https://gamificacao-qr-ifmt.vercel.app`

A branch de desenvolvimento/homologação permanece `feat/gamificacao-qr-evento` até autorização explícita para merge em `main`.
