# Trilhas Poéticas — IFMT

Sistema web mobile-first para a experiência gamificada **Trilhas Poéticas: Arte, Tecnologia, Gamificação e Inclusão**.

**Status:** versão final em homologação na branch `feat/gamificacao-qr-evento`. A `main` permanece sem merge até autorização explícita.

## Regras principais

- competição individual durante 7 dias;
- fuso `America/Cuiaba`, com virada diária às 00:00;
- 15 QR Codes no evento;
- cada participante pode validar o mesmo QR uma vez por dia e novamente no dia seguinte;
- cada validação válida vale **+10 pontos**;
- banco final previsto de 300 questões, todas de múltipla escolha com 4 alternativas;
- questão nunca se repete para a mesma pessoa;
- alternativas são embaralhadas de forma estável por participante + questão;
- acerto na 1ª tentativa: **+10**;
- acerto na 2ª tentativa: **+6**;
- duas respostas erradas: **+0** no desafio;
- máximo de 2 tentativas, persistidas no servidor;
- organizadores não pontuam;
- velocidade/tempo não geram pontos nem servem como desempate;
- sem GPS.

## Ranking

Ordem de classificação:

1. pontos;
2. total de acertos;
3. acertos na 1ª tentativa;
4. QRs distintos;
5. dias ativos;
6. resultado supervisionado do Dia 7, apenas se o empate permanecer.

Ouro, prata e bronze são destaques visuais para os três primeiros e não alteram a pontuação.

## Cadastro

O fluxo público usa:

- nome completo;
- nick;
- PIN de 4 dígitos;
- tipo de participante;
- campus;
- curso;
- avatar vetorial local.

Não há e-mail, matrícula, turma ou semestre. Campus e curso permitem opção personalizada.

## Stack

- Python 3.12
- FastAPI
- Supabase / PostgreSQL
- HTML, CSS e JavaScript sem framework pesado
- Vercel
- Pytest
- `qrcode`

## Arquitetura

```text
Celular / navegador
        │ HTTPS
        ▼
Vercel + FastAPI
        │ service_role somente no servidor
        ▼
Supabase / PostgreSQL
```

O navegador não acessa o banco privilegiado diretamente. Pontuação, tentativas, atribuição de questões, idempotência diária e ranking são protegidos no backend/RPCs PostgreSQL.

## Questões e QRs

A estação só pode ser validada quando possui pool de questões configurado. A seleção:

- exclui qualquer questão já atribuída ao participante;
- prioriza questões menos usadas naquele QR/dia;
- equilibra dificuldade quando possível;
- usa desempate pseudoaleatório determinístico;
- não recorre silenciosamente a pergunta repetida quando o pool se esgota.

O gerador de QR físico usa `docs/qrs.example.csv`:

```bash
python scripts/generate_qr_codes.py \
  --input qrs.csv \
  --base-url https://gamificacao-qr-ifmt.vercel.app
```

## Administração

`/admin` concentra:

- visão geral e alertas;
- participantes e organizadores;
- estações/QRs e conteúdo cultural;
- banco e distribuição de questões por QR/dia;
- calendário de 7 dias;
- trilhas sequenciais;
- pontos extras e estornos auditáveis;
- ranking e desempate final;
- monitoramento de acessos;
- auditoria e moderação de nick.

Acessos em horários incomuns são sinalizados para conferência; não há bloqueio ou retirada automática de pontos.

## Banco de dados

A fonte de verdade estrutural é `supabase/migrations/`. O antigo `schema.sql` foi removido para evitar manter uma cópia desatualizada da estrutura.

`supabase/seed.sql` contém somente catálogo base (categorias e zonas). Ele não cria participantes, QRs, questões ou dados de homologação.

Os dados de teste/homologação das versões anteriores foram removidos antes da preparação desta versão final.

## Identidade visual e acessibilidade

A interface usa tema institucional claro nas telas gerais e ranking escuro. A paleta trabalha com azul/ink, roxo/plum, Embers/laranja, branco e neutros. **Verde não faz parte da identidade visual.**

Recursos preservados:

- ajuste de tamanho do texto;
- alto contraste;
- redução de movimento;
- síntese de voz;
- comandos de voz quando suportados;
- navegação por teclado;
- alternativas textuais para mídia essencial.

## Desenvolvimento local

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Testes:

```bash
pytest
```

O CI também compila Python, valida JavaScript e verifica que módulos do motor legado não retornem.

## Produção

- público: `https://gamificacao-qr-ifmt.vercel.app`
- administração: `https://gamificacao-qr-ifmt.vercel.app/admin`
- branch atual: `feat/gamificacao-qr-evento`

Antes do evento real ainda devem ser carregados os dados oficiais: datas dos 7 dias, 15 QRs/localizações, 300 questões aprovadas, distribuição por QR/dia e conteúdo/trilhas definitivos.

## Documentação

- `docs/REQUISITOS.md`
- `docs/ARQUITETURA.md`
- `docs/ACESSIBILIDADE.md`
- `docs/OPERACAO_EVENTO.md`
- `docs/HOMOLOGACAO_FINAL.md`
