# Arquitetura — Trilhas Poéticas

## Visão geral

```text
Celular / navegador
        │ HTTPS
        ▼
Vercel + FastAPI
        │ secret key somente no servidor
        ▼
Supabase / PostgreSQL
```

O navegador nunca acessa o Supabase diretamente.

## Camadas

### Frontend

HTML/CSS/JavaScript simples, responsivo e acessível:

- `index.html` / `index.js`: login, cadastro, recuperação, perfil e leitor de QR;
- `scan.html` / `scan.js`: validação física, conteúdo cultural e desafio;
- `ranking.html` / `ranking.js`: ranking coletivo;
- `admin.html` / `admin.js`: operação administrativa;
- `common.js`: API helper e recursos de acessibilidade.

### API FastAPI

- `api/participants.py`: cadastro, login, recuperação, sessão e logout;
- `api/game.py`: estação, validação, resposta, resumo e ranking;
- `api/admin.py`: administração, RBAC, pontos extras e auditoria;
- `api/deps.py`: injeção de dependências e autorização.

### Serviços

- `services/participants.py`: regras de conta, PIN, recuperação e sessão;
- `services/trilhas.py`: fachada das regras de gamificação;
- `services/questions.py`: avaliação/validação acessível dos desafios;
- `services/moderation.py`: moderação de nick.

O motor antigo de gamificação, bônus diário/dinâmico, scoring 10/6/2 e ativação institucional foram removidos.

## Banco

Tabelas centrais:

```text
teams ──< participants ──< participant_sessions
                    │
                    ├──< station_visits ──< station_attempts
                    ├──< trail_completions
                    ├──< point_ledger
                    └──< manual_point_actions

categories ──< questions
zones ──< qr_points ──1 station_contents
                   └──< trail_steps >── trails

admin_users
audit_log
blocked_terms
```

`supabase/schema.sql` é a definição canônica para recriar um banco novo. `supabase/seed.sql` cria apenas dados-base não sensíveis.

## RPCs atômicas

- `trilhas_assign_team`
- `trilhas_participant_from_session`
- `trilhas_home_state_from_session`
- `trilhas_get_station`
- `trilhas_validate_station`
- `trilhas_answer_challenge`
- `trilhas_participant_summary`
- `trilhas_team_ranking`
- `trilhas_admin_grant_manual_points`
- `trilhas_admin_reverse_manual_points`

Validação/pontuação ocorre dentro do PostgreSQL para reduzir condições de corrida e duplicidade.

## Segurança

- tabelas com RLS;
- sem acesso de `anon`/`authenticated` às tabelas do jogo;
- RPCs críticas executáveis somente pelo `service_role`;
- browser não recebe chave de banco;
- PIN e senha administrativa com Argon2;
- código físico e código de recuperação persistidos somente como SHA-256;
- sessão participante por token aleatório armazenado no banco apenas como hash;
- sessão admin assinada com expiração;
- CSP não foi implantada de forma rígida porque ainda há JavaScript inline na página inicial; cabeçalho de frame, MIME sniffing, referrer e Permissions-Policy estão habilitados.

## Desempenho

- cliente HTTPX é reaproveitado enquanto a função Vercel permanece quente;
- a abertura da estação usa uma RPC consolidada;
- a home autenticada usa uma RPC consolidada;
- arquivos estáticos recebem cache na CDN;
- páginas autenticáveis recebem `no-store`;
- o leitor interno do QR verifica a câmera em intervalos, não a cada frame;
- tema animado pesado antigo foi removido.

## Produção

O projeto continua no mesmo domínio Vercel para não invalidar QR Codes já gerados:

`https://gamificacao-qr-ifmt.vercel.app`

A branch de homologação permanece `feat/gamificacao-qr-evento` até a aprovação final.
