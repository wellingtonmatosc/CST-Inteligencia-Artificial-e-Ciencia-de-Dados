# Projeto Gamificação QR — Evento IFMT

**Status:** MVP 0.1 em branch de desenvolvimento; ainda não mesclado à `main`.

MVP web acessível para atividades e gamificação por QR Codes. O projeto foi desenhado para público interno e externo, três zonas físicas (Cantina, Térreo e 1º andar), ranking por nick, questões sem repetição por participante e dois tipos de bônus diários.

## Stack
- Python 3.12+
- FastAPI
- Supabase / PostgreSQL
- HTML, CSS e JavaScript
- Vercel
- Pytest
- `qrcode` para geração dos QR Codes físicos

## Acesso dos participantes
- Cadastro novo: nome, nick e senha.
- Login normal: nick + senha.
- A sessão permanece autenticada em cookie HttpOnly.
- O código de recuperação é uma contingência para redefinir a senha, não o método principal de login.
- Ao usar o código de recuperação, ele é rotacionado e um novo código é exibido.
- Participantes criados antes desta regra podem definir uma senha sem perder pontos ou histórico.
- Sair revoga a sessão no servidor e apaga o cookie local.

## Regras principais
- QR normal: uma pontuação por pessoa/QR/dia.
- Questão não se repete para a mesma pessoa enquanto houver questão inédita.
- Verdadeiro/Falso: 1 tentativa; 10 pontos se acertar; 2 pontos por participação se errar.
- Demais questões: até 2 tentativas; 10 pontos na 1ª, 6 na 2ª; 2 pontos por participação se errar as duas.
- A pontuação de participação não conta como atividade concluída para os marcos de progresso.
- Questões de verdadeiro/falso devem ser minoria e distribuídas de forma equilibrada.
- Marco de 3 atividades concluídas: +5; marco de 5: +10.
- Bônus do Dia: 1/pessoa/dia, base 15.
- Bônus Dinâmico: 1/pessoa/dia, muda de hora em hora, base 20.
- Bônus sempre com alternativas equivalentes na Cantina, Térreo e 1º andar.
- Sem GPS ou mecanismo invasivo para impedir compartilhamento de QR.
- A interface não usa verde como cor principal/estado e nunca depende apenas de cor para comunicar informação.

## Desenvolvimento local
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
python scripts/hash_admin_password.py
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`.

## Banco Supabase
1. Crie um projeto Supabase exclusivo para este sistema.
2. Execute `supabase/schema.sql` no SQL Editor.
3. Preencha `SUPABASE_URL` e `SUPABASE_SECRET_KEY` no `.env`.
4. Execute `python scripts/seed_content.py`.
5. Para testes, opcionalmente execute `python scripts/seed_sample_questions.py` (conteúdo demonstrativo, deve ser revisado antes do evento).

> A secret key nunca deve aparecer no frontend ou ser commitada. Senhas de participantes e de administração são armazenadas apenas como hash Argon2.

## Configurar bônus de um dia
Use `docs/bonus-config.example.json` como modelo e execute:
```bash
python scripts/configure_bonus_day.py --config docs/bonus-config.example.json
```
O script cria janelas de 1 em 1 hora e falha se faltar Cantina, Térreo ou 1º andar.

## Gerar QR Codes
Prepare um CSV:
```csv
code,name
BIB-01,Biblioteca
CAN-01,Cantina
```
Execute:
```bash
python scripts/generate_qr_codes.py --input qrs.csv --base-url https://seu-app.vercel.app
```

## Testes
```bash
pytest
```

## Vercel
A configuração usa `app.main:app` em `pyproject.toml`. No painel da Vercel, defina a raiz do projeto para esta pasta caso ela esteja dentro de um monorepo/repositório maior, configure as variáveis de ambiente e faça o deploy a partir do GitHub.

## Documentação adicional
- `docs/REQUISITOS.md`
- `docs/ARQUITETURA.md`
- `docs/ACESSIBILIDADE.md`
- API interativa em `/docs` quando o FastAPI estiver em execução.
