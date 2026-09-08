-- Banco inicial de questões acessíveis para homologação e evento.
-- 24 questões: 2 por categoria. Verdadeiro/Falso permanece minoria.

with seed(slug, kind, prompt, options, correct_answer, explanation, difficulty, accessibility) as (
values
('inteligencia-artificial','multiple_choice','Em aprendizado supervisionado, o que normalmente acompanha os exemplos usados no treinamento?',
 '[{"value":"Rótulos ou respostas esperadas","label":"Rótulos ou respostas esperadas"},{"value":"Somente arquivos compactados","label":"Somente arquivos compactados"},{"value":"Apenas coordenadas de GPS","label":"Apenas coordenadas de GPS"},{"value":"Somente cores aleatórias","label":"Somente cores aleatórias"}]'::jsonb,
 '{"value":"Rótulos ou respostas esperadas"}'::jsonb,'No aprendizado supervisionado, os exemplos possuem uma resposta-alvo conhecida que orienta o treinamento.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"No aprendizado supervisionado, qual informação ajuda o modelo a saber qual resposta deveria aprender?","seed_group":"initial-accessible-v1"}'::jsonb),
('inteligencia-artificial','true_false','Um modelo de Inteligência Artificial pode reproduzir erros ou vieses presentes nos dados usados em seu treinamento.',
 '[{"value":"Verdadeiro","label":"Verdadeiro"},{"value":"Falso","label":"Falso"}]'::jsonb,
 '{"value":"Verdadeiro"}'::jsonb,'Modelos aprendem padrões dos dados e podem reproduzir limitações presentes nesses dados.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Se os dados de treino tiverem vieses, a IA também pode apresentar esses vieses.","seed_group":"initial-accessible-v1"}'::jsonb),

('ciencia-de-dados','multiple_choice','Qual medida de tendência central costuma ser menos afetada por valores muito extremos?',
 '[{"value":"Mediana","label":"Mediana"},{"value":"Média aritmética","label":"Média aritmética"},{"value":"Amplitude","label":"Amplitude"},{"value":"Soma total","label":"Soma total"}]'::jsonb,
 '{"value":"Mediana"}'::jsonb,'A mediana depende da posição dos valores ordenados e tende a ser mais resistente a valores extremos.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"intermediária","simplified_prompt":"Qual medida central muda menos quando aparece um valor muito alto ou muito baixo?","seed_group":"initial-accessible-v1"}'::jsonb),
('ciencia-de-dados','multiple_choice','Em uma tabela de dados, uma linha normalmente representa o quê?',
 '[{"value":"Um registro ou observação","label":"Um registro ou observação"},{"value":"Todas as fórmulas do banco","label":"Todas as fórmulas do banco"},{"value":"A senha do sistema","label":"A senha do sistema"},{"value":"Somente o nome das colunas","label":"Somente o nome das colunas"}]'::jsonb,
 '{"value":"Um registro ou observação"}'::jsonb,'Em dados tabulares, cada linha costuma representar uma observação e as colunas representam atributos dessa observação.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Numa planilha, o que uma linha geralmente representa?","seed_group":"initial-accessible-v1"}'::jsonb),

('logica-tecnologia','multiple_choice','Na lógica booleana, quando a operação E (AND) resulta em verdadeiro?',
 '[{"value":"Quando as duas condições são verdadeiras","label":"Quando as duas condições são verdadeiras"},{"value":"Quando pelo menos uma condição é falsa","label":"Quando pelo menos uma condição é falsa"},{"value":"Sempre","label":"Sempre"},{"value":"Nunca","label":"Nunca"}]'::jsonb,
 '{"value":"Quando as duas condições são verdadeiras"}'::jsonb,'A operação AND exige que todas as condições avaliadas sejam verdadeiras.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"No operador E, o resultado só é verdadeiro em qual situação?","seed_group":"initial-accessible-v1"}'::jsonb),
('logica-tecnologia','multiple_choice','Qual é o próximo número da sequência 2, 4, 8, 16?',
 '[{"value":"32","label":"32"},{"value":"18","label":"18"},{"value":"20","label":"20"},{"value":"24","label":"24"}]'::jsonb,
 '{"value":"32"}'::jsonb,'Cada número é o dobro do anterior.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"A sequência dobra a cada passo: 2, 4, 8, 16. Qual vem depois?","seed_group":"initial-accessible-v1"}'::jsonb),

('historia-mt','multiple_choice','Qual atividade econômica teve papel importante na formação inicial de Cuiabá durante o período colonial?',
 '[{"value":"Mineração de ouro","label":"Mineração de ouro"},{"value":"Produção de petróleo","label":"Produção de petróleo"},{"value":"Indústria automobilística","label":"Indústria automobilística"},{"value":"Extração de carvão mineral","label":"Extração de carvão mineral"}]'::jsonb,
 '{"value":"Mineração de ouro"}'::jsonb,'A descoberta e exploração de ouro foi um fator central na ocupação colonial da região de Cuiabá.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"intermediária","simplified_prompt":"Qual atividade ligada ao ouro ajudou no início da formação de Cuiabá?","seed_group":"initial-accessible-v1"}'::jsonb),
('historia-mt','true_false','A criação de Mato Grosso do Sul ocorreu a partir do desmembramento de parte do território de Mato Grosso.',
 '[{"value":"Verdadeiro","label":"Verdadeiro"},{"value":"Falso","label":"Falso"}]'::jsonb,
 '{"value":"Verdadeiro"}'::jsonb,'Mato Grosso do Sul foi criado a partir da divisão territorial de Mato Grosso.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Mato Grosso do Sul surgiu da divisão do território de Mato Grosso.","seed_group":"initial-accessible-v1"}'::jsonb),

('geografia-mt','multiple_choice','Qual bioma ocupa grande área de Mato Grosso e apresenta vegetação típica de savana tropical?',
 '[{"value":"Cerrado","label":"Cerrado"},{"value":"Pampa","label":"Pampa"},{"value":"Caatinga","label":"Caatinga"},{"value":"Tundra","label":"Tundra"}]'::jsonb,
 '{"value":"Cerrado"}'::jsonb,'O Cerrado está presente em grande parte do território mato-grossense.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Qual bioma de savana tropical aparece em grande parte de Mato Grosso?","seed_group":"initial-accessible-v1"}'::jsonb),
('geografia-mt','multiple_choice','O Pantanal brasileiro está presente principalmente em quais dois estados?',
 '[{"value":"Mato Grosso e Mato Grosso do Sul","label":"Mato Grosso e Mato Grosso do Sul"},{"value":"Paraná e Santa Catarina","label":"Paraná e Santa Catarina"},{"value":"Bahia e Sergipe","label":"Bahia e Sergipe"},{"value":"Acre e Amapá","label":"Acre e Amapá"}]'::jsonb,
 '{"value":"Mato Grosso e Mato Grosso do Sul"}'::jsonb,'No Brasil, o Pantanal se estende principalmente pelos estados de Mato Grosso e Mato Grosso do Sul.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Em quais dois estados brasileiros fica a maior parte do Pantanal?","seed_group":"initial-accessible-v1"}'::jsonb),

('cultura-regional','multiple_choice','A viola de cocho está tradicionalmente associada a quais manifestações culturais de Mato Grosso?',
 '[{"value":"Cururu e siriri","label":"Cururu e siriri"},{"value":"Frevo e maracatu","label":"Frevo e maracatu"},{"value":"Fandango gaúcho e vanerão","label":"Fandango gaúcho e vanerão"},{"value":"Bumba meu boi e carimbó","label":"Bumba meu boi e carimbó"}]'::jsonb,
 '{"value":"Cururu e siriri"}'::jsonb,'A viola de cocho é um instrumento fortemente ligado ao cururu e ao siriri na cultura regional.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"intermediária","simplified_prompt":"Em Mato Grosso, a viola de cocho aparece muito em quais danças e tradições?","seed_group":"initial-accessible-v1"}'::jsonb),
('cultura-regional','multiple_choice','O rasqueado cuiabano é principalmente uma expressão de qual área cultural?',
 '[{"value":"Música","label":"Música"},{"value":"Arquitetura","label":"Arquitetura"},{"value":"Escultura em mármore","label":"Escultura em mármore"},{"value":"Cinema mudo","label":"Cinema mudo"}]'::jsonb,
 '{"value":"Música"}'::jsonb,'O rasqueado cuiabano é uma expressão musical característica da cultura regional.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"O rasqueado cuiabano é um estilo ligado à música, dança, pintura ou arquitetura?","seed_group":"initial-accessible-v1"}'::jsonb),

('literatura','multiple_choice','Em uma narrativa em primeira pessoa, qual pronome costuma aparecer quando o narrador fala de si?',
 '[{"value":"Eu","label":"Eu"},{"value":"Ele","label":"Ele"},{"value":"Eles","label":"Eles"},{"value":"Vós","label":"Vós"}]'::jsonb,
 '{"value":"Eu"}'::jsonb,'Na primeira pessoa, o narrador participa da perspectiva apresentada e costuma empregar pronomes como eu e nós.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Qual pronome indica que o narrador conta a história falando de si mesmo?","seed_group":"initial-accessible-v1"}'::jsonb),
('literatura','multiple_choice','Qual figura de linguagem faz uma comparação implícita, sem usar necessariamente palavras como “como”?',
 '[{"value":"Metáfora","label":"Metáfora"},{"value":"Onomatopeia","label":"Onomatopeia"},{"value":"Enumeração","label":"Enumeração"},{"value":"Pontuação","label":"Pontuação"}]'::jsonb,
 '{"value":"Metáfora"}'::jsonb,'A metáfora aproxima ideias por semelhança de forma implícita.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"intermediária","simplified_prompt":"Qual figura compara duas ideias de modo implícito?","seed_group":"initial-accessible-v1"}'::jsonb),

('poesia','multiple_choice','Como se chama um conjunto de versos organizado dentro de um poema?',
 '[{"value":"Estrofe","label":"Estrofe"},{"value":"Capítulo","label":"Capítulo"},{"value":"Parágrafo técnico","label":"Parágrafo técnico"},{"value":"Índice","label":"Índice"}]'::jsonb,
 '{"value":"Estrofe"}'::jsonb,'Uma estrofe é um agrupamento de versos em um poema.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Qual é o nome do grupo de versos de um poema?","seed_group":"initial-accessible-v1"}'::jsonb),
('poesia','true_false','Um poema pode existir sem apresentar rimas no final dos versos.',
 '[{"value":"Verdadeiro","label":"Verdadeiro"},{"value":"Falso","label":"Falso"}]'::jsonb,
 '{"value":"Verdadeiro"}'::jsonb,'Rima é um recurso possível, mas não obrigatório para que um texto seja poético.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Todo poema precisa ter rima? Não. Então a afirmação de que pode existir poema sem rima é verdadeira ou falsa?","seed_group":"initial-accessible-v1"}'::jsonb),

('arte','multiple_choice','Qual técnica artística cria uma composição reunindo e colando diferentes materiais sobre uma superfície?',
 '[{"value":"Colagem","label":"Colagem"},{"value":"Perspectiva linear","label":"Perspectiva linear"},{"value":"Gravação de áudio","label":"Gravação de áudio"},{"value":"Programação de banco de dados","label":"Programação de banco de dados"}]'::jsonb,
 '{"value":"Colagem"}'::jsonb,'A colagem combina materiais e imagens diferentes em uma nova composição visual.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Qual técnica de arte usa pedaços de materiais colados para formar uma obra?","seed_group":"initial-accessible-v1"}'::jsonb),
('arte','multiple_choice','Em desenho e pintura, a perspectiva pode ser usada principalmente para criar qual sensação?',
 '[{"value":"Profundidade e distância","label":"Profundidade e distância"},{"value":"Som mais alto","label":"Som mais alto"},{"value":"Cheiro mais forte","label":"Cheiro mais forte"},{"value":"Temperatura menor","label":"Temperatura menor"}]'::jsonb,
 '{"value":"Profundidade e distância"}'::jsonb,'Recursos de perspectiva ajudam a representar profundidade e relações espaciais em uma superfície plana.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"A perspectiva ajuda um desenho plano a parecer ter profundidade ou som?","seed_group":"initial-accessible-v1"}'::jsonb),

('sustentabilidade','multiple_choice','Qual destas é uma fonte de energia renovável?',
 '[{"value":"Solar","label":"Solar"},{"value":"Carvão mineral","label":"Carvão mineral"},{"value":"Petróleo","label":"Petróleo"},{"value":"Gás natural fóssil","label":"Gás natural fóssil"}]'::jsonb,
 '{"value":"Solar"}'::jsonb,'A energia solar utiliza uma fonte naturalmente renovada: a radiação do Sol.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Qual opção usa uma fonte que se renova naturalmente: Sol, carvão, petróleo ou gás fóssil?","seed_group":"initial-accessible-v1"}'::jsonb),
('sustentabilidade','multiple_choice','Qual é um objetivo importante da coleta seletiva de resíduos?',
 '[{"value":"Separar materiais para facilitar reaproveitamento e reciclagem","label":"Separar materiais para facilitar reaproveitamento e reciclagem"},{"value":"Misturar todos os resíduos","label":"Misturar todos os resíduos"},{"value":"Aumentar o desperdício","label":"Aumentar o desperdício"},{"value":"Impedir qualquer reutilização","label":"Impedir qualquer reutilização"}]'::jsonb,
 '{"value":"Separar materiais para facilitar reaproveitamento e reciclagem"}'::jsonb,'A separação adequada facilita a destinação, o reaproveitamento e a reciclagem de materiais.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Para que serve separar corretamente os resíduos na coleta seletiva?","seed_group":"initial-accessible-v1"}'::jsonb),

('ifmt','multiple_choice','O que significa a sigla IFMT?',
 '[{"value":"Instituto Federal de Educação, Ciência e Tecnologia de Mato Grosso","label":"Instituto Federal de Educação, Ciência e Tecnologia de Mato Grosso"},{"value":"Instituto Financeiro Municipal de Tecnologia","label":"Instituto Financeiro Municipal de Tecnologia"},{"value":"Índice Federal de Matemática e Turismo","label":"Índice Federal de Matemática e Turismo"},{"value":"Instituto de Física Médica Tropical","label":"Instituto de Física Médica Tropical"}]'::jsonb,
 '{"value":"Instituto Federal de Educação, Ciência e Tecnologia de Mato Grosso"}'::jsonb,'IFMT é a sigla do Instituto Federal de Educação, Ciência e Tecnologia de Mato Grosso.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Qual é o nome completo representado pela sigla IFMT?","seed_group":"initial-accessible-v1"}'::jsonb),
('ifmt','multiple_choice','Além do ensino, quais atividades fazem parte da atuação acadêmica dos Institutos Federais?',
 '[{"value":"Pesquisa e extensão","label":"Pesquisa e extensão"},{"value":"Somente venda de produtos","label":"Somente venda de produtos"},{"value":"Apenas entretenimento","label":"Apenas entretenimento"},{"value":"Exclusivamente transporte","label":"Exclusivamente transporte"}]'::jsonb,
 '{"value":"Pesquisa e extensão"}'::jsonb,'Ensino, pesquisa e extensão são dimensões importantes da atuação das instituições federais de educação.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"intermediária","simplified_prompt":"Além de ensinar, os Institutos Federais também desenvolvem pesquisa e qual outra atividade ligada à comunidade?","seed_group":"initial-accessible-v1"}'::jsonb),

('cidadania-etica-digital','multiple_choice','O que é phishing?',
 '[{"value":"Tentativa de enganar alguém para obter dados ou credenciais","label":"Tentativa de enganar alguém para obter dados ou credenciais"},{"value":"Método de compactação de imagens","label":"Método de compactação de imagens"},{"value":"Tipo de cabo de rede","label":"Tipo de cabo de rede"},{"value":"Sistema de impressão 3D","label":"Sistema de impressão 3D"}]'::jsonb,
 '{"value":"Tentativa de enganar alguém para obter dados ou credenciais"}'::jsonb,'Phishing usa mensagens, páginas ou contatos falsos para induzir a vítima a fornecer informações ou executar ações inseguras.',2,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"intermediária","simplified_prompt":"Como se chama o golpe que tenta enganar a pessoa para roubar senha ou outros dados?","seed_group":"initial-accessible-v1"}'::jsonb),
('cidadania-etica-digital','multiple_choice','Antes de compartilhar um dado pessoal em um formulário ou site, qual atitude é mais adequada?',
 '[{"value":"Verificar quem solicita, por que o dado é necessário e se o canal é confiável","label":"Verificar quem solicita, por que o dado é necessário e se o canal é confiável"},{"value":"Enviar qualquer dado imediatamente","label":"Enviar qualquer dado imediatamente"},{"value":"Publicar a senha junto com o dado","label":"Publicar a senha junto com o dado"},{"value":"Ignorar qualquer aviso de segurança","label":"Ignorar qualquer aviso de segurança"}]'::jsonb,
 '{"value":"Verificar quem solicita, por que o dado é necessário e se o canal é confiável"}'::jsonb,'Cidadania digital inclui avaliar necessidade, finalidade e confiabilidade antes de compartilhar informações pessoais.',1,
 '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false,"reading_level":"básica","simplified_prompt":"Antes de informar um dado pessoal, o que você deve conferir?","seed_group":"initial-accessible-v1"}'::jsonb)
)
insert into public.questions(category_id,kind,prompt,options,correct_answer,explanation,difficulty,media_type,media_url,accessibility,active)
select c.id,s.kind,s.prompt,s.options,s.correct_answer,s.explanation,s.difficulty,null,null,s.accessibility,true
from seed s
join public.categories c on c.slug=s.slug
where not exists (select 1 from public.questions q where q.prompt=s.prompt);

-- Durante a homologação, disponibiliza o banco inicial em todos os QR normais de teste.
insert into public.qr_question_pool(qr_point_id,question_id)
select qr.id,q.id
from public.qr_points qr
cross join public.questions q
where qr.kind='normal'
  and qr.code like 'TESTE-%'
  and q.accessibility->>'seed_group'='initial-accessible-v1'
on conflict do nothing;
