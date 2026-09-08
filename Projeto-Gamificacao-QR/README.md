# Projeto Gamificação QR — Evento IFMT

**Status:** MVP em homologação na branch `feat/gamificacao-qr-evento`; ainda não mesclado à `main`.

Aplicação web acessível para atividades e gamificação por QR Codes, com identidade visual inspirada em Inteligência Artificial e Ciência de Dados. O sistema atende público interno e externo, mantém ranking por nick e evita repetição de perguntas por participante enquanto houver conteúdo inédito.

## Stack
- Python 3.12+
- FastAPI
- Supabase / PostgreSQL
- HTML, CSS e JavaScript
- Vercel
- Pytest
- `qrcode` para geração dos QR Codes físicos

## Acesso dos participantes
- Cadastro novo: nome, nick e **PIN numérico de 4 dígitos**.
- Login normal: **nick + PIN**.
- A sessão permanece autenticada em cookie HttpOnly.
- Depois de 5 PINs incorretos, a conta fica temporariamente bloqueada por 2 minutos contra tentativas automatizadas.
- O código de recuperação é uma contingência para redefinir o PIN, não o método principal de login.
- Ao usar o código de recuperação, ele é rotacionado e um novo código é exibido.
- Participantes criados antes da regra do PIN podem defini-lo na sessão atual sem perder pontos ou histórico.
- Sair revoga a sessão no servidor e apaga o cookie local.

## Administração
- Login administrativo: **usuário + senha forte**.
- Usuário configurado por `ADMIN_USERNAME` (padrão local: `admin`).
- A senha fica apenas como hash Argon2 em `ADMIN_PASSWORD_HASH`.

## Regras principais
- QR normal: uma pontuação por pessoa/QR/dia.
- Questão não se repete para a mesma pessoa enquanto houver questão inédita.
- Verdadeiro/Falso: 1 tentativa; 10 pontos se acertar; 2 pontos por participação se errar.
- Demais questões: até 2 tentativas; 10 pontos na 1ª, 6 na 2ª; 2 pontos por participação se errar as duas.
- Pontos de participação não contam como atividade concluída para marcos de progresso.
- Verdadeiro/Falso deve ser minoria do banco para evitar vantagem pelo chute.
- Marco de 3 atividades concluídas: +5; marco de 5: +10.
- Bônus do Dia: 1/pessoa/dia, base 15.
- Bônus Dinâmico: 1/pessoa/dia, muda de hora em hora, base 20.
- Bônus oferecem alternativas equivalentes em Cantina, Térreo e 1º andar.
- Não há GPS nem mecanismo invasivo para impedir compartilhamento de QR.

## Acessibilidade e inclusão
O botão **Acessibilidade** aparece nas telas públicas e administrativas e salva preferências apenas no navegador:
- tamanho de texto de 90% a 140%;
- modo claro;
- alto contraste;
- redução de animações;
- mais espaçamento e áreas de toque;
- modo leitura.

Nas atividades, quando suportado pelo navegador, há leitura em voz alta do enunciado e alternativas. As questões podem armazenar versão em linguagem simples, descrição equivalente de imagem e transcrição de áudio/vídeo. Nenhuma atividade pode depender exclusivamente de cor, velocidade, imagem sem descrição ou áudio/vídeo sem alternativa textual.

## Banco inicial de questões
A migration `20260908_initial_accessible_question_bank.sql` adiciona **24 questões acessíveis**, distribuídas nas 12 categorias iniciais, sendo apenas 3 de Verdadeiro/Falso. Durante a homologação, essas questões são vinculadas aos QR Codes `TESTE-*`.

Categorias: Inteligência Artificial, Ciência de Dados, Lógica/Tecnologia, História de Mato Grosso, Geografia de Mato Grosso, Cultura Regional, Literatura, Poesia, Arte, Sustentabilidade, IFMT e Cidadania/Ética Digital.

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
1. Use um projeto Supabase exclusivo para a aplicação.
2. Aplique `supabase/schema.sql` e as migrations em ordem.
3. Preencha `SUPABASE_URL` e `SUPABASE_SECRET_KEY` no `.env`.
4. Execute `python scripts/seed_content.py` quando necessário para categorias e zonas.

> A secret key nunca deve aparecer no frontend ou ser commitada. PINs e senhas administrativas são armazenados apenas como hash Argon2.

## Configurar bônus de um dia
Use `docs/bonus-config.example.json` como modelo e execute:
```bash
python scripts/configure_bonus_day.py --config docs/bonus-config.example.json
```

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
A configuração usa `app.main:app` em `pyproject.toml`. Defina a raiz do projeto para `Projeto-Gamificacao-QR`, configure as variáveis de ambiente, use `APP_ENV=production` e `SESSION_COOKIE_SECURE=true`, e faça o deploy a partir do GitHub.

Homologação atual:
- projeto Vercel: `gamificacao-qr-ifmt`;
- domínio de produção: `https://gamificacao-qr-ifmt.vercel.app`;
- branch de produção temporária: `feat/gamificacao-qr-evento`;
- a `main` permanece sem merge até a homologação ser aprovada.

## Documentação adicional
- `docs/REQUISITOS.md`
- `docs/ARQUITETURA.md`
- `docs/ACESSIBILIDADE.md`
- API interativa em `/docs` quando o FastAPI estiver em execução.
