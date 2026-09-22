# Homologação final — Trilhas Poéticas

Este documento substitui homologações das versões antigas.

## Estado da base

A base de teste anterior foi apagada de forma destrutiva com autorização explícita. Participantes, questões, QRs, visitas, tentativas, ledger, trilhas e auditoria de homologação foram reiniciados. As datas do evento permanecem em branco até definição oficial.

## Regras a validar

- competição individual por 7 dias;
- 15 QRs;
- +10 por validação diária de QR;
- +10 por acerto na 1ª tentativa;
- +6 por acerto na 2ª tentativa;
- +0 no desafio após duas respostas erradas;
- máximo de duas tentativas;
- somente múltipla escolha com 4 alternativas;
- nenhuma repetição de questão para a mesma pessoa;
- distribuição balanceada entre participantes quando houver alternativas disponíveis;
- organizadores com zero pontos;
- sem velocidade como critério;
- ranking por pontos, acertos, primeira tentativa, QRs distintos, dias ativos e desempate supervisionado do Dia 7.

## Teste de integração do banco

Foi executado um cenário transacional com rollback validando:

- primeira validação = 10 pontos;
- repetição no mesmo QR/dia é idempotente;
- participantes diferentes recebem questão diferente quando o pool permite;
- primeiro erro mantém a questão aberta e não revela explicação;
- acerto na segunda tentativa = 6 pontos;
- organizador = 0 pontos;
- ledger = 20 para QR + acerto de primeira e 16 para QR + acerto de segunda.

O teste foi revertido ao final, portanto não deixou registros de homologação na base.

## Pendências de conteúdo, não de motor

Antes do evento real ainda precisam ser fornecidos/configurados:

1. datas oficiais dos 7 dias;
2. 15 pontos/QRs finais e seus locais/códigos físicos;
3. banco final de 300 questões aprovado;
4. distribuição das questões por QR/dia;
5. conteúdo cultural e trilhas que serão efetivamente usados.

Esses itens são dados do evento. O motor deve ser homologado novamente depois de sua carga definitiva.
