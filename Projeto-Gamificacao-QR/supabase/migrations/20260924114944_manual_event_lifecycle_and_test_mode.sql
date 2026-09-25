-- Ciclo operacional manual do evento e modo de homologacao.
-- O evento oficial pode durar de 1 a 7 dias e so comeca por comando administrativo.
-- O modo testing permite testar QRs/questoes sem comprometer o placar oficial.

create table if not exists public.event_control (
  singleton boolean primary key default true check (singleton),
  status text not null default 'draft' check (status in ('draft','testing','running','ended')),
  duration_days smallint not null default 7 check (duration_days between 1 and 7),
  test_day smallint not null default 1 check (test_day between 1 and 7),
  started_at timestamptz,
  ended_at timestamptz,
  updated_at timestamptz not null default now(),
  updated_by text,
  constraint event_control_test_day_within_duration check (test_day <= duration_days)
);

insert into public.event_control(singleton,status,duration_days,test_day)
values (true,'draft',7,1)
on conflict (singleton) do nothing;

alter table public.event_control enable row level security;
revoke all on table public.event_control from public, anon, authenticated;
grant all on table public.event_control to service_role;

create or replace function public.trilhas_event_state()
returns jsonb
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  v_control public.event_control%rowtype;
  v_today date := (now() at time zone 'America/Cuiaba')::date;
  v_start_date date;
  v_day integer;
begin
  select * into v_control from public.event_control where singleton = true;

  if v_control.singleton is null then
    return jsonb_build_object('ok',false,'error','event_not_configured','activity_date',v_today);
  end if;

  if v_control.status = 'testing' then
    return jsonb_build_object(
      'ok',true,
      'status','testing',
      'is_testing',true,
      'day_number',v_control.test_day,
      'duration_days',v_control.duration_days,
      'activity_date',v_today
    );
  end if;

  if v_control.status = 'draft' then
    return jsonb_build_object(
      'ok',false,'error','event_not_started','status','draft',
      'duration_days',v_control.duration_days,'activity_date',v_today
    );
  end if;

  if v_control.status = 'ended' then
    return jsonb_build_object(
      'ok',false,'error','event_ended','status','ended',
      'duration_days',v_control.duration_days,'activity_date',v_today,
      'started_at',v_control.started_at,'ended_at',v_control.ended_at
    );
  end if;

  if v_control.started_at is null then
    return jsonb_build_object('ok',false,'error','event_not_started','status','running','activity_date',v_today);
  end if;

  v_start_date := (v_control.started_at at time zone 'America/Cuiaba')::date;
  v_day := (v_today - v_start_date) + 1;

  if v_day < 1 then
    return jsonb_build_object('ok',false,'error','event_not_started','status','running','activity_date',v_today,'starts_on',v_start_date);
  end if;

  if v_day > v_control.duration_days then
    return jsonb_build_object(
      'ok',false,'error','event_ended','status','running',
      'activity_date',v_today,'starts_on',v_start_date,
      'duration_days',v_control.duration_days
    );
  end if;

  return jsonb_build_object(
    'ok',true,
    'status','running',
    'is_testing',false,
    'day_number',v_day,
    'duration_days',v_control.duration_days,
    'activity_date',v_today,
    'started_at',v_control.started_at,
    'starts_on',v_start_date
  );
end;
$$;

create or replace function public.trilhas_current_event_day()
returns smallint
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  v_state jsonb;
begin
  v_state := public.trilhas_event_state();
  if coalesce((v_state->>'ok')::boolean,false) then
    return (v_state->>'day_number')::smallint;
  end if;
  return null;
end;
$$;

create or replace function public.trilhas_event_readiness()
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
with target_qrs as (
  select id,code,active,validation_code_hash
  from public.qr_points
  where code ~ '^QR-(0[1-9]|1[0-5])$'
), eligible_pool as (
  select tq.id,
         count(q.id)::int as eligible_questions
  from target_qrs tq
  left join public.station_question_pool sqp
    on sqp.qr_point_id=tq.id and sqp.active=true
  left join public.questions q
    on q.id=sqp.question_id and q.active=true and q.kind='multiple_choice'
  group by tq.id
)
select jsonb_build_object(
  'qrs_total',(select count(*)::int from target_qrs),
  'qrs_active',(select count(*)::int from target_qrs where active),
  'qrs_with_physical_code',(select count(*)::int from target_qrs where validation_code_hash is not null),
  'questions_total',(select count(*)::int from public.questions where kind='multiple_choice'),
  'questions_active',(select count(*)::int from public.questions where kind='multiple_choice' and active),
  'pool_entries',(select count(*)::int from public.station_question_pool where active),
  'min_eligible_questions_per_qr',coalesce((select min(eligible_questions)::int from eligible_pool),0),
  'max_eligible_questions_per_qr',coalesce((select max(eligible_questions)::int from eligible_pool),0)
);
$$;

create or replace function public.trilhas_admin_set_test_mode(
  p_duration_days smallint,
  p_test_day smallint,
  p_actor text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_duration_days not between 1 and 7 or p_test_day not between 1 and p_duration_days then
    return jsonb_build_object('ok',false,'error','invalid_event_day');
  end if;

  update public.event_control
  set status='testing', duration_days=p_duration_days, test_day=p_test_day,
      started_at=null, ended_at=null, updated_at=now(), updated_by=p_actor
  where singleton=true;

  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,'admin','event_test_mode_set','event','singleton',jsonb_build_object('duration_days',p_duration_days,'test_day',p_test_day));

  return jsonb_build_object('ok',true,'status','testing','duration_days',p_duration_days,'test_day',p_test_day);
end;
$$;

create or replace function public.trilhas_admin_clear_test_data(p_actor text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_status text;
begin
  select status into v_status from public.event_control where singleton=true for update;
  if v_status <> 'testing' then
    return jsonb_build_object('ok',false,'error','not_in_test_mode');
  end if;

  delete from public.station_attempts;
  delete from public.station_visits;
  delete from public.trail_completions;
  delete from public.point_ledger;
  delete from public.manual_point_actions;
  delete from public.final_tiebreak_results;

  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,'admin','test_competition_data_cleared','event','singleton','{}'::jsonb);

  return jsonb_build_object('ok',true);
end;
$$;

create or replace function public.trilhas_admin_start_official_event(
  p_duration_days smallint,
  p_actor text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_ready jsonb;
  v_min_pool integer;
begin
  if p_duration_days not between 1 and 7 then
    return jsonb_build_object('ok',false,'error','invalid_event_duration');
  end if;

  perform pg_advisory_xact_lock(hashtext('trilhas-official-event-start')::bigint);
  v_ready := public.trilhas_event_readiness();
  v_min_pool := coalesce((v_ready->>'min_eligible_questions_per_qr')::int,0);

  if coalesce((v_ready->>'qrs_total')::int,0) <> 15
     or coalesce((v_ready->>'qrs_active')::int,0) <> 15
     or coalesce((v_ready->>'qrs_with_physical_code')::int,0) <> 15
     or v_min_pool < p_duration_days then
    return jsonb_build_object('ok',false,'error','event_not_ready','readiness',v_ready,'required_questions_per_qr',p_duration_days);
  end if;

  -- Zera apenas a competicao. Contas, QRs, questoes, pools e auditoria permanecem.
  delete from public.station_attempts;
  delete from public.station_visits;
  delete from public.trail_completions;
  delete from public.point_ledger;
  delete from public.manual_point_actions;
  delete from public.final_tiebreak_results;

  update public.event_control
  set status='running', duration_days=p_duration_days, test_day=1,
      started_at=now(), ended_at=null, updated_at=now(), updated_by=p_actor
  where singleton=true;

  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,'admin','official_event_started','event','singleton',jsonb_build_object('duration_days',p_duration_days,'readiness',v_ready));

  return jsonb_build_object('ok',true,'status','running','duration_days',p_duration_days,'started_at',now(),'readiness',v_ready);
end;
$$;

create or replace function public.trilhas_admin_end_event(p_actor text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.event_control
  set status='ended', ended_at=now(), updated_at=now(), updated_by=p_actor
  where singleton=true;

  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,'admin','official_event_ended','event','singleton','{}'::jsonb);

  return jsonb_build_object('ok',true,'status','ended','ended_at',now());
end;
$$;

-- Distribuicao deterministica e balanceada das 300 questoes entre os 15 QRs.
-- Cada QR recebe exatamente 20 questoes. A ordem dos estratos foi otimizada
-- para manter dificuldade e categorias o mais uniformes possivel.
create or replace function public.trilhas_admin_rebuild_balanced_question_pool(p_actor text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_questions integer;
  v_qrs integer;
begin
  select count(*)::int into v_questions from public.questions where kind='multiple_choice';
  select count(*)::int into v_qrs from public.qr_points where code ~ '^QR-(0[1-9]|1[0-5])$';

  if v_questions <> 300 or v_qrs <> 15 then
    return jsonb_build_object('ok',false,'error','unexpected_catalog_size','questions',v_questions,'qrs',v_qrs);
  end if;

  delete from public.station_question_pool;

  with ordered_questions as (
    select q.id,
      row_number() over (
        order by
          case
            when c.name='Inteligência Artificial' and q.difficulty=3 then 1
            when c.name='Lógica e Tecnologia' and q.difficulty=2 then 2
            when c.name='Cidadania e Ética Digital' and q.difficulty=2 then 3
            when c.name='Inteligência Artificial' and q.difficulty=2 then 4
            when c.name='Ciência de Dados' and q.difficulty=2 then 5
            when c.name='Ciência de Dados' and q.difficulty=1 then 6
            when c.name='Ciência de Dados' and q.difficulty=3 then 7
            when c.name='Lógica Matemática' and q.difficulty=3 then 8
            when c.name='Geografia de Mato Grosso' and q.difficulty=1 then 9
            when c.name='Lógica Computacional' and q.difficulty=2 then 10
            when c.name='Cidadania e Ética Digital' and q.difficulty=1 then 11
            when c.name='Cidadania e Ética Digital' and q.difficulty=3 then 12
            when c.name='História de Mato Grosso' and q.difficulty=1 then 13
            when c.name='Cultura Regional' and q.difficulty=1 then 14
            when c.name='Cultura Regional' and q.difficulty=2 then 15
            when c.name='Lógica Matemática' and q.difficulty=2 then 16
            when c.name='História de Mato Grosso' and q.difficulty=2 then 17
            when c.name='Geografia de Mato Grosso' and q.difficulty=2 then 18
            when c.name='Geografia de Mato Grosso' and q.difficulty=3 then 19
            when c.name='Lógica e Tecnologia' and q.difficulty=3 then 20
            when c.name='Lógica e Tecnologia' and q.difficulty=1 then 21
            when c.name='Cultura Regional' and q.difficulty=3 then 22
            when c.name='Inteligência Artificial' and q.difficulty=1 then 23
            when c.name='Lógica Computacional' and q.difficulty=3 then 24
            when c.name='História de Mato Grosso' and q.difficulty=3 then 25
            else 99
          end,
          md5(q.id::text)
      ) as rn
    from public.questions q
    join public.categories c on c.id=q.category_id
    where q.kind='multiple_choice'
  ), assigned as (
    select oq.id as question_id,
           'QR-' || lpad((((oq.rn-1) % 15)+1)::text,2,'0') as code
    from ordered_questions oq
  )
  insert into public.station_question_pool(qr_point_id,question_id,day_number,active)
  select qp.id,a.question_id,null,true
  from assigned a
  join public.qr_points qp on qp.code=a.code;

  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,'admin','question_pool_balanced','question_pool','all',jsonb_build_object('questions',300,'qrs',15,'questions_per_qr',20));

  return jsonb_build_object('ok',true,'questions',300,'qrs',15,'questions_per_qr',20);
end;
$$;

revoke execute on function public.trilhas_event_state() from public,anon,authenticated;
revoke execute on function public.trilhas_current_event_day() from public,anon,authenticated;
revoke execute on function public.trilhas_event_readiness() from public,anon,authenticated;
revoke execute on function public.trilhas_admin_set_test_mode(smallint,smallint,text) from public,anon,authenticated;
revoke execute on function public.trilhas_admin_clear_test_data(text) from public,anon,authenticated;
revoke execute on function public.trilhas_admin_start_official_event(smallint,text) from public,anon,authenticated;
revoke execute on function public.trilhas_admin_end_event(text) from public,anon,authenticated;
revoke execute on function public.trilhas_admin_rebuild_balanced_question_pool(text) from public,anon,authenticated;

grant execute on function public.trilhas_event_state() to service_role;
grant execute on function public.trilhas_current_event_day() to service_role;
grant execute on function public.trilhas_event_readiness() to service_role;
grant execute on function public.trilhas_admin_set_test_mode(smallint,smallint,text) to service_role;
grant execute on function public.trilhas_admin_clear_test_data(text) to service_role;
grant execute on function public.trilhas_admin_start_official_event(smallint,text) to service_role;
grant execute on function public.trilhas_admin_end_event(text) to service_role;
grant execute on function public.trilhas_admin_rebuild_balanced_question_pool(text) to service_role;
