# Homologação final

Objetivo: testar o sistema com pessoas reais antes do evento sem explicar previamente como usar.

## Amostra mínima
- 5 participantes.
- Pelo menos 2 modelos de celular diferentes.
- Preferencialmente Android e iPhone.
- Pelo menos uma pessoa usando recurso de acessibilidade ou áudio.

## Fluxo a testar
1. Abrir a página inicial.
2. Criar conta sem ajuda.
3. Sair e entrar novamente com nick + PIN.
4. Abrir um QR físico pela câmera do celular.
5. Testar também o leitor interno após login.
6. Responder uma questão V/F e uma questão com 2 tentativas.
7. Confirmar pontuação e ranking.
8. Testar Ouvir tela, Ouvir pergunta e Ouvir tudo.
9. Testar comando de voz quando o navegador oferecer suporte.
10. Testar aumentar texto, alto contraste e reduzir animações.
11. Recuperar acesso usando um participante de teste.

## Critérios de aprovação
- Nenhuma tela exige explicação verbal da equipe para ser entendida.
- Nenhum botão ou campo fica cortado no celular.
- V/F aplica 10 pontos se correta e 2 por participação se errada.
- Demais questões aplicam 10 na primeira, 6 na segunda e 2 por participação após erro final.
- Pontos de participação não contam para marcos de 3 e 5 atividades corretas.
- QR já contabilizado no dia não gera nova pontuação.
- Áudio pode ser interrompido.
- Falha ou ausência de comando de voz não impede nenhuma ação essencial.
- Redução de animações remove movimentos decorativos.
- Ranking não expõe nome completo, matrícula ou instituição.

## Registro do teste
Para cada problema, registrar:
- aparelho/navegador;
- tela;
- ação executada;
- resultado esperado;
- resultado encontrado;
- print quando útil;
- prioridade: bloqueante, importante ou visual.

## Regra de fechamento
Só mesclar a branch de homologação na `main` depois de corrigir todos os problemas bloqueantes e repetir o fluxo principal do início ao fim.
