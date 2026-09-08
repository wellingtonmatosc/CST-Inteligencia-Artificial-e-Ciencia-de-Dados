# Requisitos funcionais — Gamificação QR

## Participantes
- Público interno e externo.
- Cadastro: nome completo, nick público, senha e tipo de participante.
- Login normal: nick + senha.
- Senhas são armazenadas somente como hash Argon2; senha em texto puro não é persistida.
- Aluno: matrícula e curso/turma obrigatórios.
- Público externo: instituição/empresa opcional.
- Nome completo e matrícula não aparecem no ranking público.
- O sistema fornece um código de recuperação como contingência para redefinir a senha.
- Ao usar o código de recuperação, o código antigo deixa de valer e um novo é gerado.
- A sessão é mantida em cookie HttpOnly e pode ser encerrada pelo botão Sair; o logout também revoga a sessão no servidor.
- Participantes criados antes da implantação de senha podem definir uma senha a partir de uma sessão válida, sem perder pontos ou histórico.

## QR e atividades normais
- Várias pessoas podem ler o mesmo QR simultaneamente.
- Cada participante pontua em cada QR normal no máximo uma vez por dia.
- No dia seguinte o mesmo QR pode ser usado novamente.
- A pergunta sorteada nunca se repete para a mesma pessoa enquanto houver perguntas inéditas.
- Questões de verdadeiro/falso: **1 tentativa**. Acerto = **10 pontos**; erro = **2 pontos por participação**.
- Demais tipos: **até 2 tentativas**. Acerto na 1ª = **10 pontos**; acerto na 2ª = **6 pontos**; se errar as duas = **2 pontos por participação**.
- A pontuação por participação não transforma uma resposta errada em atividade concluída para fins dos marcos de 3 e 5 atividades.
- Questões de verdadeiro/falso devem representar uma parcela menor do banco e ser distribuídas de maneira equilibrada, pois possuem 50% de chance de acerto ao acaso.
- Não há cronômetro de resposta nem perda de pontos por demora.
- Compartilhamento de QR não será combatido com GPS/códigos invasivos; a proposta confia nos participantes e registra as regras no servidor.
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
- Pontuação inicial sugerida: 15.

### Bônus Dinâmico
- 1 por pessoa por dia.
- Local ativo muda de 1 em 1 hora.
- A cada hora deve existir alternativa simultânea em Cantina, Térreo e 1º andar.
- Ao encontrar, o participante escolhe 1 de 3 categorias/desafios disponíveis.
- Pontuação inicial sugerida: 20.

## Categorias iniciais
IA, Ciência de Dados, Lógica/Tecnologia, História de Mato Grosso, Geografia de Mato Grosso, Cultura Regional, Literatura, Poesia, Arte, Sustentabilidade, IFMT e Cidadania/Ética Digital.

## Ranking
Ordem: maior pontuação; mais atividades normais concluídas; maior diversidade de categorias; mais acertos na primeira tentativa. Se todos esses critérios forem iguais, permanece empate. Velocidade/deslocamento não é critério.

## Interface, inclusão e acessibilidade visual
- Não utilizar verde como cor principal ou de estado do sistema.
- A interface pode usar azul, roxo, âmbar/laranja e vermelho, desde que mantenha contraste suficiente.
- Cor nunca pode ser o único meio de transmitir informação: estados devem incluir texto e, quando útil, ícone/símbolo.
- Acerto/conclusão: destaque azul acompanhado de texto explícito, como “Resposta correta” ou “Atividade concluída”.
- Bônus: roxo, sempre acompanhado do rótulo “Bônus”.
- Avisos: âmbar/laranja, acompanhados de texto explicativo.
- Erros/respostas incorretas: vermelho, acompanhados de mensagem textual.
- Foco por teclado deve permanecer claramente visível e independente da cor do componente.
- Nenhuma atividade pode depender apenas de cor, imagem ou áudio para ser compreendida ou respondida.

## Zonas
A equipe de tecnologia sugere as zonas; a escolha do ponto físico exato pertence à frente responsável pelos espaços.
- Cantina.
- Térreo: biblioteca, auditório, secretaria, salão de entrada e corredores.
- 1º andar: salas/corredores e áreas públicas próximas.
- Estacionamento/ponto de ônibus: opcionais; não podem ser necessários para alcançar a pontuação máxima.

## Administração
Cadastrar/ativar/desativar questões e QR Codes, vincular questão a QR, moderar nicks, acompanhar bônus, ranking, tentativas e estatísticas. A configuração horária dos bônus é feita em lote para preservar a regra das três zonas.
