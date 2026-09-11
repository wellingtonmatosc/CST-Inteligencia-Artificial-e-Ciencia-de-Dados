# Trilhas Poéticas — IFMT

Sistema web acessível para a experiência gamificada **Trilhas Poéticas: Arte, Tecnologia, Gamificação e Inclusão**.

**Status:** homologação na branch `feat/gamificacao-qr-evento`. A `main` permanece sem merge até a homologação final.

## O que o sistema faz

- cadastro, login por nick + PIN e recuperação de acesso;
- cinco equipes secretas: Tarsila, Anita, Mário, Oswald e Pagu;
- distribuição equilibrada por tipo de participante, curso/turma e tamanho da equipe;
- organizadores fora da competição;
- estações QR `permanent`, `sequential`, `temporary` e `special`;
- código físico local como validação antifraude, sem GPS;
- uma única pontuação válida por participante + QR;
- trilhas sequenciais com bloqueio de etapas e bônus de conclusão;
- conteúdo cultural em texto, imagem, áudio ou vídeo, com equivalentes acessíveis;
- desafios de múltipla escolha, verdadeiro/falso ou resposta curta;
- ranking coletivo por equipes;
- pontos extras validados, estorno e auditoria;
- painel administrativo com papéis `admin`, `operator`, `validator` e `viewer`;
- geração de PNGs, manifesto e folha de impressão dos QRs;
- acessibilidade: texto ajustável, alto contraste, redução de movimento, leitura da tela/conteúdo/desafio e comando de voz opcional.

## Stack

- Python 3.12
- FastAPI
- Supabase / PostgreSQL
- HTML, CSS e JavaScript sem framework
- Vercel
- Pytest
- `qrcode`

## Fluxo principal

```text
cadastro do participante
        ↓
equipe secreta
        ↓
QR físico
        ↓
login, se necessário
        ↓
código físico
        ↓
duplicidade + sequência + horário
        ↓
conteúdo cultural acessível
        ↓
desafio opcional
        ↓
pontuação individual → equipe → ranking
```

## Pontuação-base adotada

| Tipo | Pontos |
|---|---:|
| Permanente | 10 |
| Sequencial | 15 |
| Temporário | 30 |
| Especial | 40 |
| Conclusão da trilha | +30 por padrão |
| Desafio | 0–20 configurável |

A velocidade de resposta/deslocamento não gera vantagem.

## Banco

`supabase/schema.sql` é o **schema canônico do sistema atual**.

Para um banco novo:

1. execute `supabase/schema.sql`;
2. execute `supabase/seed.sql` para categorias, zonas e os 12 desafios iniciais acessíveis;
3. configure as variáveis do `.env`.

O Data API não fica disponível para `anon` ou `authenticated`. O navegador fala apenas com o FastAPI; as RPCs críticas são executáveis somente pelo backend com `service_role`.

## Cadastro de participantes

O sistema usa um único fluxo de cadastro. O participante informa os dados necessários, escolhe nick e PIN e recebe um código de recuperação.

- aluno IFMT: matrícula e curso/turma;
- servidor IFMT: identificação como servidor;
- público externo: instituição/empresa opcional.

Não existe etapa separada de **ativação de cadastro IFMT**.

## Administração

O primeiro acesso pode usar o administrador bootstrap configurado em variáveis de ambiente. Depois, usuários administrativos podem ser criados no painel ou localmente:

```bash
python scripts/create_admin_user.py usuario --role admin
```

Papéis:

- `admin`: acesso total e gestão de usuários/organizadores;
- `operator`: estações, conteúdo, trilhas, desafios e pontos extras;
- `validator`: valida/estorna pontos extras e consulta dados;
- `viewer`: somente consulta.

Senhas ficam somente como hash Argon2.

## QR Codes físicos

Use `docs/qrs.example.csv` como modelo:

```bash
python scripts/generate_qr_codes.py \
  --input qrs.csv \
  --base-url https://gamificacao-qr-ifmt.vercel.app
```

Saída em `qr_output/`:

- um PNG por estação;
- `manifest.csv`;
- `folha_impressao.html` com QR, código físico, tipo, pontos e referência de local.

A escolha do **ponto físico exato** pertence à frente responsável pelos espaços.

## Desenvolvimento local

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`.

## Testes

```bash
pytest
```

O CI também compila Python, valida os arquivos JavaScript e impede o retorno dos módulos/regras do motor antigo.

## Produção / homologação

- domínio: `https://gamificacao-qr-ifmt.vercel.app`;
- Vercel continua usando o mesmo projeto e domínio já adotados;
- a branch de homologação é `feat/gamificacao-qr-evento`;
- a `main` só deve receber merge depois da homologação em celular, acessibilidade e fluxo físico.

## Documentação

- `docs/REQUISITOS.md`
- `docs/ARQUITETURA.md`
- `docs/ACESSIBILIDADE.md`
- `docs/OPERACAO_EVENTO.md`
- `docs/HOMOLOGACAO_FINAL.md`
