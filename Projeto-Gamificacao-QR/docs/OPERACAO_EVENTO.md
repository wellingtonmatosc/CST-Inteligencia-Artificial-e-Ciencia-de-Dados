# Operação do evento — Trilhas Poéticas

## 1. Preparação de participantes

1. revisar as regras de cadastro do evento;
2. confirmar que alunos informam matrícula e curso/turma;
3. confirmar que servidores e público externo usam o tipo correto de participante;
4. marcar organizadores no painel para mantê-los fora da competição;
5. conferir a distribuição das cinco equipes durante a homologação.

O sistema usa um único fluxo de cadastro. Não existe ativação institucional separada.

## 2. Curadoria e estações

No painel administrativo:

1. cadastrar/revisar desafios;
2. criar estação como permanente, sequencial, temporária ou especial;
3. configurar pontos-base;
4. definir código físico local;
5. configurar janela de horário quando necessário;
6. inserir conteúdo cultural e recursos equivalentes de acessibilidade;
7. vincular desafio opcional;
8. montar e ordenar trilhas sequenciais.

A tecnologia não define o local físico exato. A frente de espaços informa os pontos finais depois de testar circulação, segurança e acessibilidade.

## 3. Material físico

Criar `qrs.csv` a partir de `docs/qrs.example.csv` e executar:

```bash
python scripts/generate_qr_codes.py --input qrs.csv --base-url https://gamificacao-qr-ifmt.vercel.app
```

Imprimir a `folha_impressao.html` ou adaptar os PNGs ao material visual oficial. O código físico deve ficar disponível somente na estação correspondente e legível/acessível.

## 4. Antes de abrir ao público

- confirmar Vercel saudável;
- confirmar Supabase saudável;
- confirmar 5 equipes ativas;
- confirmar 12+ desafios ativos e acessíveis;
- conferir todas as estações ativas;
- testar cada QR físico no local real;
- testar código correto/incorreto;
- testar sequência fora de ordem;
- testar temporário antes/durante/depois da janela;
- testar ranking zerado sem posição falsa;
- conferir contas dos organizadores fora da competição;
- testar Android/iPhone e acessibilidade;
- manter uma cópia local do manifesto dos QRs.

## 5. Durante o evento

### Participante

1. encontra o QR;
2. abre pelo celular;
3. entra ou cria a conta se necessário;
4. volta automaticamente à estação;
5. informa o código físico;
6. recebe os pontos-base uma única vez;
7. acessa conteúdo cultural;
8. responde ao desafio, se houver;
9. acompanha equipe, progresso e ranking.

### Organização

Usuários administrativos operam conforme papel:

- administrador: configura tudo;
- operador: estações, conteúdo, trilhas e extras;
- validador: pontos extras/estornos;
- consulta: monitoramento sem alterar dados.

## 6. Pontos extras

Ao validar uma ação extra:

1. selecionar participante;
2. escolher o tipo da ação;
3. registrar descrição;
4. registrar evidência/referência quando houver;
5. informar pontos;
6. conceder.

Se houver erro, usar **Estornar** e informar justificativa. Não apagar o lançamento original.

## 7. Ocorrências

- QR danificado: desativar a estação e substituir o material físico;
- código físico exposto indevidamente: editar a estação e gerar novo código físico/material;
- participante em equipe incorreta por cadastro: não alterar pontuação manualmente sem registrar o motivo; tratar administrativamente;
- conteúdo inacessível: desativar a estação até oferecer alternativa equivalente;
- temporário com horário errado: corrigir janela antes de reabrir;
- instabilidade: não duplicar pontos manualmente sem verificar o ledger/visitas.

## 8. Encerramento

- desativar temporários/especiais;
- registrar últimos pontos extras;
- conferir estornos;
- exportar/registrar indicadores necessários ao relatório institucional;
- preservar auditoria;
- não apagar histórico oficial do evento;
- somente limpar dados de homologação antes do evento real, nunca depois da execução oficial sem autorização.
