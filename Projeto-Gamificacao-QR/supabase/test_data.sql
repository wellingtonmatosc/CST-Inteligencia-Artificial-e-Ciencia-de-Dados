-- Dados mínimos para teste ponta a ponta do MVP.
-- Idempotente: pode ser executado novamente sem duplicar QR, perguntas ou vínculos.

with zone_ids as (
  select slug, id from public.zones where slug in ('cantina','terreo','primeiro-andar')
)
insert into public.qr_points (code, name, zone_id, kind, active)
select v.code, v.name, z.id, 'normal', true
from (values
  ('TESTE-CAN-01','QR Teste — Cantina','cantina'),
  ('TESTE-TER-01','QR Teste — Térreo','terreo'),
  ('TESTE-1A-01','QR Teste — 1º andar','primeiro-andar')
) as v(code,name,zone_slug)
join zone_ids z on z.slug = v.zone_slug
on conflict (code) do update set
  name = excluded.name,
  zone_id = excluded.zone_id,
  kind = excluded.kind,
  active = true;

with cats as (
  select slug, id from public.categories where slug in (
    'inteligencia-artificial','ciencia-de-dados','logica-tecnologia','cultura-regional','cidadania-etica-digital'
  )
), payload as (
  select * from (values
    ('inteligencia-artificial','multiple_choice','Qual alternativa descreve melhor o aprendizado de máquina?',
      '[{"value":"Modelos aprendem padrões a partir de dados","label":"Modelos aprendem padrões a partir de dados"},{"value":"Todo programa usa robôs físicos","label":"Todo programa usa robôs físicos"},{"value":"É apenas armazenamento de arquivos","label":"É apenas armazenamento de arquivos"},{"value":"É sinônimo de internet","label":"É sinônimo de internet"}]'::jsonb,
      '{"value":"Modelos aprendem padrões a partir de dados"}'::jsonb),
    ('ciencia-de-dados','multiple_choice','Antes de interpretar os resultados de uma análise de dados, qual ação é recomendada?',
      '[{"value":"Verificar e preparar os dados","label":"Verificar e preparar os dados"},{"value":"Apagar os dados originais","label":"Apagar os dados originais"},{"value":"Escolher o resultado desejado","label":"Escolher o resultado desejado"},{"value":"Publicar sem conferir","label":"Publicar sem conferir"}]'::jsonb,
      '{"value":"Verificar e preparar os dados"}'::jsonb),
    ('logica-tecnologia','true_false','Um algoritmo pode ser entendido como uma sequência organizada de passos para resolver um problema.',
      '[{"value":"Verdadeiro","label":"Verdadeiro"},{"value":"Falso","label":"Falso"}]'::jsonb,
      '{"value":"Verdadeiro"}'::jsonb),
    ('cultura-regional','true_false','Siriri e cururu fazem parte de manifestações culturais tradicionais de Mato Grosso.',
      '[{"value":"Verdadeiro","label":"Verdadeiro"},{"value":"Falso","label":"Falso"}]'::jsonb,
      '{"value":"Verdadeiro"}'::jsonb),
    ('cidadania-etica-digital','multiple_choice','Qual prática aumenta a segurança de uma conta digital?',
      '[{"value":"Usar senha exclusiva e autenticação em dois fatores","label":"Usar senha exclusiva e autenticação em dois fatores"},{"value":"Compartilhar a senha com colegas","label":"Compartilhar a senha com colegas"},{"value":"Repetir a mesma senha em todos os serviços","label":"Repetir a mesma senha em todos os serviços"},{"value":"Desativar atualizações de segurança","label":"Desativar atualizações de segurança"}]'::jsonb,
      '{"value":"Usar senha exclusiva e autenticação em dois fatores"}'::jsonb)
  ) as q(category_slug,kind,prompt,options,correct_answer)
)
insert into public.questions (category_id, kind, prompt, options, correct_answer, difficulty, accessibility, active)
select c.id, p.kind, p.prompt, p.options, p.correct_answer, 1,
  '{"instructions_clear":true,"depends_on_color_only":false,"requires_speed":false}'::jsonb,
  true
from payload p
join cats c on c.slug = p.category_slug
where not exists (select 1 from public.questions q where q.prompt = p.prompt);

insert into public.qr_question_pool (qr_point_id, question_id)
select qr.id, q.id
from public.qr_points qr
cross join public.questions q
where qr.code in ('TESTE-CAN-01','TESTE-TER-01','TESTE-1A-01')
  and q.prompt in (
    'Qual alternativa descreve melhor o aprendizado de máquina?',
    'Antes de interpretar os resultados de uma análise de dados, qual ação é recomendada?',
    'Um algoritmo pode ser entendido como uma sequência organizada de passos para resolver um problema.',
    'Siriri e cururu fazem parte de manifestações culturais tradicionais de Mato Grosso.',
    'Qual prática aumenta a segurança de uma conta digital?'
  )
on conflict do nothing;
