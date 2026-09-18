-- Redistribui as alternativas corretas entre as quatro posições.
-- A resposta correta continua sendo validada pelo campo value, portanto
-- esta alteração não muda a lógica de correção nem o histórico existente.

update public.questions
set options = case prompt
  when 'Qual destas opções é uma forma de expressão artística?' then '[{"label":"Senha de acesso","value":"senha"},{"label":"Pintura","value":"pintura"},{"label":"Planilha de cálculo","value":"planilha"},{"label":"Endereço de internet","value":"url"}]'::jsonb
  when 'Qual atitude ajuda a incluir mais pessoas no uso de um site?' then '[{"label":"Usar somente imagens sem descrição","value":"imagens"},{"label":"Exigir respostas muito rápidas","value":"rapidez"},{"label":"Oferecer texto claro e recursos de acessibilidade","value":"acessibilidade"},{"label":"Usar apenas cores para transmitir informações","value":"cores"}]'::jsonb
  when 'Em uma tabela, o que uma coluna normalmente representa?' then '[{"label":"Uma senha secreta","value":"senha"},{"label":"Uma música","value":"musica"},{"label":"Uma fotografia obrigatória","value":"foto"},{"label":"Uma característica dos registros","value":"caracteristica"}]'::jsonb
  when 'O que significa a sigla IFMT?' then '[{"label":"Instituto Federal de Educação, Ciência e Tecnologia de Mato Grosso","value":"ifmt"},{"label":"Instituto de Formação Musical e Teatro","value":"musica"},{"label":"Instituição Federal de Matemática e Turismo","value":"turismo"},{"label":"Instituto de Fotografia de Mato Grosso","value":"foto"}]'::jsonb
  when 'Qual manifestação cultural tradicional está associada a Mato Grosso?' then '[{"label":"Flamenco","value":"flamenco"},{"label":"Ópera italiana","value":"opera"},{"label":"Siriri","value":"siriri"},{"label":"Dança irlandesa","value":"irlandesa"}]'::jsonb
  when 'Qual destes biomas está presente em Mato Grosso?' then '[{"label":"Tundra","value":"tundra"},{"label":"Taiga","value":"taiga"},{"label":"Deserto do Saara","value":"saara"},{"label":"Pantanal","value":"pantanal"}]'::jsonb
  when 'Qual atividade teve importância na formação de Cuiabá no período colonial?' then '[{"label":"Produção de petróleo","value":"petroleo"},{"label":"Exploração de ouro","value":"ouro"},{"label":"Indústria automobilística","value":"automoveis"},{"label":"Construção naval oceânica","value":"naval"}]'::jsonb
  when 'Qual frase descreve melhor uma Inteligência Artificial?' then '[{"label":"Uma pessoa dentro do computador","value":"pessoa"},{"label":"Um tipo de cabo de internet","value":"cabo"},{"label":"Uma bateria especial","value":"bateria"},{"label":"Um sistema capaz de executar tarefas usando modelos e dados","value":"sistema"}]'::jsonb
  when 'Quem escreve uma obra literária é chamado de quê?' then '[{"label":"Autor ou autora","value":"autor"},{"label":"Leitor de código","value":"codigo"},{"label":"Navegador","value":"navegador"},{"label":"Sensor","value":"sensor"}]'::jsonb
  when 'O que é um algoritmo?' then '[{"label":"Uma cor de tela","value":"cor"},{"label":"Um tipo de cadeira","value":"cadeira"},{"label":"Uma sequência organizada de passos para realizar uma tarefa","value":"passos"},{"label":"Uma senha obrigatória","value":"senha"}]'::jsonb
  when 'Como se chama cada linha de um poema?' then '[{"label":"Verso","value":"verso"},{"label":"Capítulo","value":"capitulo"},{"label":"Tabela","value":"tabela"},{"label":"Legenda técnica","value":"legenda"}]'::jsonb
  when 'Qual atitude ajuda a reduzir a quantidade de resíduos?' then '[{"label":"Descartar objetos que ainda podem ser usados","value":"descartar"},{"label":"Reutilizar materiais quando possível","value":"reutilizar"},{"label":"Misturar todos os resíduos de propósito","value":"misturar"},{"label":"Comprar itens sem necessidade","value":"comprar"}]'::jsonb
  else options
end,
updated_at = now()
where active = true
  and kind = 'multiple_choice'
  and prompt in (
    'Qual destas opções é uma forma de expressão artística?',
    'Qual atitude ajuda a incluir mais pessoas no uso de um site?',
    'Em uma tabela, o que uma coluna normalmente representa?',
    'O que significa a sigla IFMT?',
    'Qual manifestação cultural tradicional está associada a Mato Grosso?',
    'Qual destes biomas está presente em Mato Grosso?',
    'Qual atividade teve importância na formação de Cuiabá no período colonial?',
    'Qual frase descreve melhor uma Inteligência Artificial?',
    'Quem escreve uma obra literária é chamado de quê?',
    'O que é um algoritmo?',
    'Como se chama cada linha de um poema?',
    'Qual atitude ajuda a reduzir a quantidade de resíduos?'
  );
