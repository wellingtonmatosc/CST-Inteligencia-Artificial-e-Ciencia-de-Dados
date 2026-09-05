# Requisitos funcionais — Gamificação QR

## Participantes
- Público interno e externo.
- Cadastro: nome completo, nick público e tipo de participante.
- Aluno: matrícula e curso/turma obrigatórios.
- Público externo: instituição/empresa opcional.
- Nome completo e matrícula não aparecem no ranking público.
- O sistema fornece um código de recuperação e mantém sessão em cookie HttpOnly.

## QR e atividades normais
- Várias pessoas podem ler o mesmo QR simultaneamente.
- Cada participante pontua em cada QR normal no máximo uma vez por dia.
- No dia seguinte o mesmo QR pode ser usado novamente.
- A pergunta sorteada nunca se repete para a mesma pessoa enquanto houver perguntas inéditas.
- Até 3 tentativas: 10 pontos na 1ª, 7 na 2ª e 5 na 3ª; depois, 0.
- Não há cronômetro de resposta.
- Compartilhamento de QR não será combatido com GPS/códigos invasivos; a proposta confia nos participantes e registra as regras no servidor.
- QR danificado pode ser desativado e substituído pelo administrador.

## Progressão diária
- 3 atividades normais concluídas: +5 pontos.
- 5 atividades normais concluídas: +10 pontos adicionais.
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

## Zonas
A equipe de tecnologia sugere as zonas; a escolha do ponto físico exato pertence à frente responsável pelos espaços.
- Cantina.
- Térreo: biblioteca, auditório, secretaria, salão de entrada e corredores.
- 1º andar: salas/corredores e áreas públicas próximas.
- Estacionamento/ponto de ônibus: opcionais; não podem ser necessários para alcançar a pontuação máxima.

## Administração
Cadastrar/ativar/desativar questões e QR Codes, vincular questão a QR, moderar nicks, acompanhar bônus, ranking, tentativas e estatísticas. A configuração horária dos bônus é feita em lote para preservar a regra das três zonas.
