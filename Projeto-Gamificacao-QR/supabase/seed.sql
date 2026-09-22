-- Seed mínimo da versão final.
-- Não inclui participantes, QRs, questões ou dados de homologação.

insert into public.categories(slug,name) values
('arte','Arte'),
('cidadania-etica-digital','Cidadania e Ética Digital'),
('ciencia-de-dados','Ciência de Dados'),
('ifmt','Conhecimentos sobre o IFMT'),
('cultura-regional','Cultura Regional'),
('geografia-mt','Geografia de Mato Grosso'),
('historia-mt','História de Mato Grosso'),
('inteligencia-artificial','Inteligência Artificial'),
('literatura','Literatura'),
('logica-tecnologia','Lógica e Tecnologia'),
('poesia','Poesia'),
('sustentabilidade','Sustentabilidade e Meio Ambiente')
on conflict(slug) do update set name=excluded.name,active=true;

insert into public.zones(slug,name) values
('cantina','Cantina'),
('terreo','Térreo'),
('primeiro-andar','1º andar'),
('externo-opcional','Área externa opcional')
on conflict(slug) do update set name=excluded.name,active=true;
