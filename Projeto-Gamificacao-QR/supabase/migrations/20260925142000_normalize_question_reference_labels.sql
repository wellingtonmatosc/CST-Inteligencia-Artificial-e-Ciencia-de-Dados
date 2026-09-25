-- Homologação real: padroniza referências de alternativas por letras.
-- Questões que já usam algarismos romanos (I, II, III...) não são alteradas.
-- O valor interno das alternativas (A/B/C/D) e a resposta correta permanecem intactos.

update public.questions
set prompt = replace(
               replace(
                 replace(
                   replace(prompt,
                     chr(10) || 'a)', chr(10) || 'A)'),
                   chr(10) || 'b)', chr(10) || 'B)'),
                 chr(10) || 'c)', chr(10) || 'C)'),
               chr(10) || 'd)', chr(10) || 'D)'),
    updated_at = now()
where prompt like '%' || chr(10) || 'a)%'
   or prompt like '%' || chr(10) || 'b)%'
   or prompt like '%' || chr(10) || 'c)%'
   or prompt like '%' || chr(10) || 'd)%';

with normalized_options as (
  select
    q.id,
    jsonb_agg(
      case
        when jsonb_typeof(item.option_value) = 'object'
         and item.option_value ? 'label'
         and trim(item.option_value->>'label') ~ '^[a-d]([[:space:]]*(,|e)[[:space:]]*[a-d])*$'
        then jsonb_set(
          item.option_value,
          '{label}',
          to_jsonb(
            regexp_replace(
              regexp_replace(
                regexp_replace(
                  regexp_replace(item.option_value->>'label', '\ma\M', 'A', 'g'),
                  '\mb\M', 'B', 'g'),
                '\mc\M', 'C', 'g'),
              '\md\M', 'D', 'g')
          ),
          false
        )
        else item.option_value
      end
      order by item.ordinality
    ) as options
  from public.questions q
  cross join lateral jsonb_array_elements(q.options) with ordinality as item(option_value, ordinality)
  where exists (
    select 1
    from jsonb_array_elements(q.options) as candidate(option_value)
    where jsonb_typeof(candidate.option_value) = 'object'
      and candidate.option_value ? 'label'
      and trim(candidate.option_value->>'label') ~ '^[a-d]([[:space:]]*(,|e)[[:space:]]*[a-d])*$'
  )
  group by q.id
)
update public.questions q
set options = n.options,
    updated_at = now()
from normalized_options n
where n.id = q.id;
