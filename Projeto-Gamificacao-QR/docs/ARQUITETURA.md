# Arquitetura

```text
Celular / navegador
      |
      v
HTML + CSS + JavaScript
      |
      v
FastAPI / Python (Vercel)
      |
      v
Supabase Data API
      |
      v
PostgreSQL
```

## Decisões
- O navegador não recebe a secret key do Supabase e não consulta tabelas diretamente.
- FastAPI aplica cadastro, sessão, moderação, sorteio sem repetição, tentativas, pontuação, bônus e ranking.
- Supabase fornece PostgreSQL gerenciado; todas as tabelas têm RLS habilitado e permissões diretas de `anon`/`authenticated` revogadas.
- O backend usa `SUPABASE_SECRET_KEY` somente em ambiente controlado.
- Sessão do participante usa token aleatório; apenas SHA-256 do token é persistido.
- Recuperação usa código aleatório; apenas o hash é persistido.
- Senha administrativa é armazenada como hash Argon2 em variável de ambiente.
- `point_ledger.dedupe_key` evita pontuação duplicada.
- `participant_question_history` garante pergunta inédita por participante.

## Deploy
A Vercel reconhece FastAPI e o projeto usa `[tool.vercel] entrypoint = "app.main:app"`. Configure a raiz do projeto Vercel como `Projeto-Gamificacao-QR` dentro deste repositório.

Variáveis de produção:
- `APP_ENV=production`
- `APP_BASE_URL`
- `EVENT_TIMEZONE=America/Cuiaba`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_SESSION_SECRET`
- `SESSION_COOKIE_SECURE=true`

## Dados principais
`participants`, `participant_sessions`, `categories`, `questions`, `qr_points`, `qr_question_pool`, `participant_question_history`, `activity_runs`, `attempts`, `bonus_campaigns`, `bonus_locations`, `bonus_runs`, `point_ledger`, `blocked_terms` e `zones`.
