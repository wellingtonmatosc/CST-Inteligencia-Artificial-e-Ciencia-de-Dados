# Requisitos funcionais — Gamificação QR

## Participantes
- Público interno e externo.
- Cadastro: nome completo, nick público, **PIN numérico de 4 dígitos** e tipo de participante.
- Login normal: **nick + PIN**.
- PIN é armazenado somente como hash Argon2; o valor em texto puro não é persistido.
- Após 5 PINs incorretos, o login daquele participante fica bloqueado por 2 minutos para reduzir tentativas automatizadas.
- Aluno: matrícula e curso/turma obrigatórios.
- Público externo: instituição/empresa opcional.
- Nome completo e matrícula não aparecem no ranking público.
- O sistema fornece um código de recuperação como contingência para redefinir o PIN.
- Ao usar o código de recuperação, o código antigo deixa de valer e um novo é gerado.
- A sessão é mantida em cookie HttpOnly e pode ser encerrada pelo botão Sair; o logout também revoga a sessão no servidor.
- Participantes criados antes do PIN podem defini-lo a partir de uma sessão válida, sem perder pontos ou histórico.

## Administração
- Login administrativo exige usuário + senha forte.
- Usuário é configurável por `ADMIN_USERNAME`; localmente o padrão é `admin`.
- Senha administrativa é armazenada apenas como hash Argon2.

## QR e atividades normais
- Várias pessoas podem ler o mesmo QR simultaneamente.
- Cada participante pontua em cada QR normal no máximo uma vez por dia.
- No dia seguinte o mesmo QR pode ser usado novamente.
- A pergunta sorteada nunca se repete para a mesma pessoa enquanto houver perguntas inéditas.
- Questões de verdadeiro/falso: **1 tentativa**. Acerto = **10 pontos**; erro = **2 pontos por participação**.
- Demais tipos: **até 2 tentativas**. Acerto na 1ª = **10 pontos**; acerto na 2ª = **6 pontos**; se errar as duas = **2 pontos por participação**.
- A pontuação por participação não transforma uma resposta errada em atividade concluída para fins dos marcos de 3 e 5 atividades.
- Questões de verdadeiro/falso devem representar uma parcela menor do banco, pois possuem 50% de chance de acerto ao acaso.
- Não há cronômetro de resposta nem perda de pontos por demora.
- Compartilhamento de QR não será combatido com GPS/códigos invasivos.
- QR danificado pode ser desativado e substituído pelo administrador.

## Progressão diária
- 3 atividades normais concluídas corretamente: +5 pontos.
- 5 atividades normais concluídas corretamente: +10 pontos adicionais.
- O ledger impede concessão duplicada do mesmo marco.

## Bônus
### Bônus do Dia
- 1 por pessoa por dia.
- Disponível durante todo o período configurado do evento.
- Mesmo bônus simultaneamente em Cantina, Térreo e 1º andar.
- Pontuação-base atual do MVP: 15.

### Bônus Dinâmico
- 1 por pessoa por dia.
- Local ativo muda de 1 em 1 hora.
- A cada hora deve existir alternativa simultânea em Cantina, Térreo e 1º andar.
- Ao encontrar, o participante escolhe 1 de 3 categorias/desafios disponíveis.
- Pontuação-base atual do MVP: 20.

## Categorias iniciais
IA, Ciência de Dados, Lógica/Tecnologia, História de Mato Grosso, Geografia de Mato Grosso, Cultura Regional, Literatura, Poesia, Arte, Sustentabilidade, IFMT e Cidadania/Ética Digital.

## Banco inicial de conteúdo
- 24 questões iniciais acessíveis, 2 por categoria.
- Apenas 3 das 24 são Verdadeiro/Falso.
- Cada questão inclui metadados mínimos de acessibilidade.
- Na homologação, o banco inicial é vinculado aos QR Codes `TESTE-*`.

## Ranking
Ordem: maior pontuação; mais atividades normais concluídas; maior diversidade de categorias; mais acertos na primeira tentativa. Se todos esses critérios forem iguais, permanece empate. Velocidade/deslocamento não é critério.

## Interface e identidade visual
- Identidade inspirada em Inteligência Artificial e Ciência de Dados: redes, nós, dados, painéis e geometria digital de forma sutil.
- Não utilizar verde como cor principal ou de estado do sistema.
- Paleta principal: azul e roxo; âmbar/laranja para avisos; vermelho para erros; cinzas para base.
- Cor nunca pode ser o único meio de transmitir informação.
- Design responsivo, com controles grandes e legíveis em celular.

## Acessibilidade e inclusão na interface
O botão **Acessibilidade** deve estar disponível nas páginas principais com preferências persistidas apenas no navegador:
- aumentar/diminuir texto entre 90% e 140%;
- modo claro;
- alto contraste;
- redução de animações;
- maior espaçamento e áreas de toque;
- modo leitura.

Nas questões:
- opção de ouvir o enunciado;
- opção de ouvir enunciado + alternativas quando o navegador oferecer síntese de voz;
- versão opcional em linguagem simples sem alterar a resposta correta;
- imagem essencial exige descrição textual equivalente;
- áudio/vídeo essencial exige transcrição ou legenda equivalente;
- nenhuma questão pode depender apenas de cor ou rapidez;
- foco por teclado deve ser claramente visível;
- mensagens importantes usam texto e regiões `aria-live`.

## Zonas
A equipe de tecnologia sugere as zonas; a escolha do ponto físico exato pertence à frente responsável pelos espaços.
- Cantina.
- Térreo: biblioteca, auditório, secretaria, salão de entrada e corredores.
- 1º andar: salas/corredores e áreas públicas próximas.
- Estacionamento/ponto de ônibus: opcionais; não podem ser necessários para alcançar a pontuação máxima.

## Administração
O painel permite cadastrar/ativar/desativar questões e QR Codes, vincular questão a QR, moderar nicks, acompanhar bônus, ranking, tentativas e estatísticas. Ao cadastrar questão, o painel também registra nível de leitura, versão simples e alternativas equivalentes de mídia. A configuração horária dos bônus é feita em lote para preservar a regra das três zonas.
