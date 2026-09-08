# Acessibilidade e inclusão

Regra central: **nenhuma necessidade de acessibilidade pode reduzir a pontuação máxima que a pessoa consegue alcançar**.

## Espaço físico
- Nenhuma pontuação necessária pode exigir escadas.
- Bônus devem ter opções equivalentes nas zonas acessíveis definidas para o evento.
- QR danificado deve ter substituição equivalente.
- A equipe de espaços valida presencialmente circulação, rampas, portas e obstáculos.

## Interface
O botão **Acessibilidade** fica disponível em todas as telas.

Recursos atuais:
- aumentar ou diminuir o texto;
- alto contraste;
- reduzir animações;
- **Ouvir tela**;
- **Parar áudio**;
- **Comando de voz**, quando o navegador oferece reconhecimento de fala.

O comando de voz é complementar. Nenhuma função essencial depende dele: tudo continua disponível por toque, teclado ou leitor de tela.

Comandos reconhecidos incluem ações como criar conta, recuperar acesso, abrir ranking, ler QR, aumentar texto, ativar contraste, ouvir pergunta, ouvir alternativas, selecionar alternativa e responder.

## Questões
- Leitura em voz alta do enunciado.
- Leitura do enunciado com alternativas.
- Interrupção da leitura a qualquer momento.
- Imagem essencial exige descrição equivalente.
- Áudio ou vídeo essencial exige transcrição/legenda equivalente.
- Sem pontuação baseada em velocidade.
- Informação não depende apenas de cor.

## Movimento e tema visual
O sistema usa animações decorativas relacionadas a IA e Ciência de Dados, como nós, fluxo de dados, brilho e movimento de interface. Elas são desligadas quando:
- o usuário ativa **Reduzir animações**; ou
- o dispositivo informa `prefers-reduced-motion`.

As animações nunca carregam informação necessária para jogar.

## Privacidade e autenticação
- Ranking público mostra somente nick.
- Participante entra com nick + PIN de 4 dígitos.
- PIN é armazenado como hash Argon2.
- Cinco PINs incorretos provocam bloqueio temporário de 2 minutos.
- Dados pessoais não aparecem no ranking público.
