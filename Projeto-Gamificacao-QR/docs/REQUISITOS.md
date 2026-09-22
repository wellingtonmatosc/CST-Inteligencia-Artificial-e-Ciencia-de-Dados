# Requisitos — Trilhas Poéticas

Documento da versão final. Regras antigas de equipes, matrícula/turma, pontuação por tipo de estação e desafios V/F/resposta curta não fazem parte deste sistema.

## Evento e participantes

- competição individual por 7 dias;
- fuso oficial `America/Cuiaba`, com virada diária às 00:00;
- cadastro: nome, nick, PIN, tipo de participante, campus, curso e avatar;
- sem e-mail, matrícula, turma ou semestre;
- campus/curso permitem opção predefinida e preenchimento de outro valor;
- login por nick + PIN de 4 dígitos;
- recuperação por código rotativo;
- organizadores não pontuam.

## QRs

- 15 QR Codes no evento;
- cada participante valida o mesmo QR no máximo uma vez por dia;
- o mesmo QR pode ser validado novamente no dia seguinte;
- diferentes participantes usam o mesmo QR independentemente;
- GPS não é usado;
- código físico opcional pode proteger uma estação;
- cada validação válida concede **10 pontos**.

## Questões

- banco final previsto: 300 questões;
- somente múltipla escolha;
- exatamente 4 alternativas diferentes;
- alternativas embaralhadas de forma pseudoaleatória e estável por participante + questão;
- uma pessoa nunca recebe novamente uma questão já atribuída a ela no evento;
- no mesmo QR/dia, o sistema prioriza questões menos usadas e equilibra dificuldade quando possível;
- sem questão inédita disponível, a validação não substitui silenciosamente por questão repetida.

## Tentativas e pontos

- acerto na 1ª tentativa: **+10**;
- acerto na 2ª tentativa: **+6**;
- erro nas duas: **+0** no desafio;
- após o 1º erro, a resposta correta não é revelada;
- no máximo 2 tentativas;
- tentativas ficam registradas no servidor e não reiniciam ao recarregar a página;
- tempo/velocidade não alteram pontuação.

## Trilhas

- estações podem formar sequências ordenadas;
- etapa posterior fica bloqueada enquanto faltar etapa anterior concluída;
- uma etapa é concluída quando o desafio termina, com acerto ou após as duas tentativas;
- bônus configurado da trilha é concedido uma única vez por participante.

## Ranking

Classificação individual por:

1. pontos;
2. total de acertos;
3. acertos na 1ª tentativa;
4. QRs distintos;
5. dias ativos;
6. resultado supervisionado do Dia 7, somente quando necessário.

Tempo e velocidade não são critérios. 1º, 2º e 3º recebem apenas destaque visual ouro/prata/bronze; isso não altera pontos.

## Administração

O painel permite operar participantes, estações, banco de questões, distribuição por QR/dia, calendário de 7 dias, trilhas, ranking, pontos extras, auditoria e monitoramento de acessos. Acessos em horários incomuns são apenas sinalizados para análise; o sistema não bloqueia nem retira pontos automaticamente.

## Segurança e acessibilidade

- Browser → FastAPI → Supabase/PostgreSQL;
- chave privilegiada somente no backend;
- RLS e RPCs críticas restritas ao `service_role`;
- PIN e senha administrativa com hash;
- cookies de sessão HttpOnly;
- sem dependência exclusiva de cor, imagem, áudio, rapidez ou precisão motora;
- texto ajustável, alto contraste, redução de movimento, síntese de voz e navegação por teclado;
- imagens essenciais exigem descrição; áudio/vídeo essencial exige transcrição/legenda;
- identidade visual sem qualquer tom de verde.
