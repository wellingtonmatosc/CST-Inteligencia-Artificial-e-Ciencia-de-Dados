# Operação do evento — Trilhas Poéticas

## Preparação

1. definir as 7 datas no calendário administrativo;
2. revisar os 15 QRs já provisionados (`QR-01` a `QR-15`), atribuir zona/localização definitiva e ativar somente após homologação;
3. cadastrar/importar as 300 questões finais, todas com 4 alternativas;
4. distribuir questões entre os QRs e, se necessário, por dia;
5. configurar conteúdo cultural e trilhas;
6. testar cada QR em celular real antes da abertura.

O cadastro público usa nome, nick, PIN, tipo, campus, curso e um dos 20 avatares WebP locais. Organizadores devem ser marcados para permanecerem fora da pontuação.

## Estado inicial dos 15 QRs

Os registros `QR-01` a `QR-15` já existem no banco com:

- nome `Estação 01` a `Estação 15`;
- tipo inicial `permanent`;
- 10 pontos por validação;
- estado **inativo**;
- zona provisória **Local a definir**;
- sem código físico configurado;
- sem conteúdo e sem pool de questões.

Antes de ativar cada estação, substituir a zona provisória, revisar o tipo, definir a referência física e configurar conteúdo/pool. Nenhum QR deve ser ativado apenas por existir no banco.

## Material físico

O manifesto-base está em `docs/qrs.example.csv` e já contém os 15 códigos. Executar:

```bash
python scripts/generate_qr_codes.py --input docs/qrs.example.csv --base-url https://gamificacao-qr-ifmt.vercel.app
```

O script gera PNGs, `manifest.csv` e `folha_impressao.html`. Cada QR válido concede 10 pontos por participante/dia. O gerador não recebe pontuação variável.

Se a organização optar por código físico adicional, ele deve ser definido somente na preparação final; o banco armazena apenas o hash.

## Checklist antes do público

- Vercel e `/health` respondendo;
- Supabase acessível pelo backend;
- 7 dias configurados no fuso `America/Cuiaba`;
- 15 QRs com zona e localização definitivas;
- 15 QRs ativos e testados somente após configuração completa;
- pool de questões configurado para cada QR;
- questões com exatamente 4 alternativas;
- cadastro/login/recuperação testados;
- 1ª tentativa correta = +10;
- 2ª tentativa correta = +6;
- duas erradas = +0 no desafio;
- mesmo QR no mesmo dia não pontua novamente;
- mesmo QR no dia seguinte volta a ser elegível;
- questão nunca se repete para a mesma pessoa;
- organizador permanece com zero;
- ranking e desempates conferidos;
- painel de acessibilidade conferido na home e no ranking;
- Android/iPhone e recursos de acessibilidade conferidos.

## Durante o evento

Participante: entra/cria conta → encontra QR → valida → recebe +10 → responde à questão → acompanha perfil/ranking.

A organização acompanha participantes, estações, acessos, questões, ranking e auditoria. Atividade em horário incomum é sinalizada para revisão, sem bloqueio ou punição automática.

## Ocorrências

- QR danificado: desativar/substituir material;
- código físico exposto: trocar código físico da estação;
- pool esgotado: ampliar/revisar o pool; o sistema não repete questão silenciosamente;
- conteúdo inacessível: corrigir ou desativar a estação até haver alternativa equivalente;
- pontuação manual incorreta: usar estorno com justificativa, nunca apagar silenciosamente o lançamento.

## Encerramento

Preservar os dados oficiais, ranking, ledger e auditoria do evento. A limpeza destrutiva é apropriada apenas para dados de teste/homologação ou quando houver autorização explícita.
