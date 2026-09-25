-- Homologacao em grupo:
-- 1) ranking oficial: pontos -> estacoes realizadas -> acertos na 1a tentativa;
-- 2) durante o modo testing, cada questao recebe um codigo visual temporario Q001..Q300.
-- O codigo e derivado do UUID em ordem estavel e NAO e exposto durante o evento oficial.

create or replace function public.trilhas_individual_ranking()
returns jsonb
language sql
security definer
set search_path = public
as $$
with challenge_outcomes as (
  select
    sv.participant_id,
    sv.id as station_visit_id,
    sv.qr_point_id,
    sv.activity_date,
    coalesce(bool_or(sa.correct), false) as correct,
    min(sa.attempt_number) filter (where sa.correct) as correct_attempt,
    coalesce(sv.completed_at, sv.validated_at) as resolved_at
  from public.station_visits sv
  join public.station_attempts sa on sa.station_visit_id = sv.id
  group by
    sv.participant_id,
    sv.id,
    sv.qr_point_id,
    sv.activity_date,
    sv.completed_at,
    sv.validated_at
), ordered_outcomes as (
  select
    co.*,
    sum(case when co.correct then 0 else 1 end) over (
      partition by co.participant_id
      order by co.resolved_at, co.station_visit_id
      rows between unbounded preceding and current row
    ) as failure_group
  from challenge_outcomes co
), streaks as (
  select participant_id, failure_group, count(*)::int as streak
  from ordered_outcomes
  where correct
  group by participant_id, failure_group
), streak_stats as (
  select participant_id, max(streak)::int as best_correct_streak
  from streaks
  group by participant_id
), stats as (
  select
    p.id,
    p.nick,
    p.avatar_key,
    coalesce((
      select sum(pl.points)::int
      from public.point_ledger pl
      where pl.participant_id = p.id
        and pl.event_type in ('station_validation','challenge','manual_action','manual_reversal')
    ), 0) as points,
    coalesce((
      select count(*)::int
      from public.trail_completions tc
      where tc.participant_id = p.id
    ), 0) as trails_completed,
    coalesce((
      select count(*)::int
      from public.station_visits sv
      where sv.participant_id = p.id
    ), 0) as stations_validated,
    coalesce((
      select count(distinct sv.qr_point_id)::int
      from public.station_visits sv
      where sv.participant_id = p.id
    ), 0) as distinct_qrs,
    coalesce((
      select count(distinct sv.activity_date)::int
      from public.station_visits sv
      where sv.participant_id = p.id
    ), 0) as active_days,
    coalesce((
      select count(*)::int
      from challenge_outcomes co
      where co.participant_id = p.id and co.correct
    ), 0) as correct_answers,
    coalesce((
      select count(*)::int
      from challenge_outcomes co
      where co.participant_id = p.id and co.correct_attempt = 1
    ), 0) as first_try_correct,
    coalesce((
      select ss.best_correct_streak
      from streak_stats ss
      where ss.participant_id = p.id
    ), 0) as best_correct_streak
  from public.participants p
  where p.active = true and p.is_organizer = false
), active_stats as (
  select * from stats
  where points <> 0 or stations_validated > 0
), ranked as (
  select
    s.*,
    rank() over (
      order by
        s.points desc,
        s.stations_validated desc,
        s.first_try_correct desc
    )::int as position,
    count(*) over (
      partition by
        s.points,
        s.stations_validated,
        s.first_try_correct
    )::int as tie_count
  from active_stats s
)
select coalesce(
  jsonb_agg(
    jsonb_build_object(
      'position', position,
      'id', id,
      'nick', nick,
      'avatar_key', avatar_key,
      'points', points,
      'trails_completed', trails_completed,
      'stations_validated', stations_validated,
      'distinct_qrs', distinct_qrs,
      'active_days', active_days,
      'correct_answers', correct_answers,
      'first_try_correct', first_try_correct,
      'best_correct_streak', best_correct_streak,
      'tie_count', tie_count,
      'is_tied', tie_count > 1
    )
    order by position, lower(nick), id
  ),
  '[]'::jsonb
)
from ranked;
$$;

create or replace function public.trilhas_get_station(p_participant_id uuid, p_code text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_qr public.qr_points%rowtype;
  v_visit public.station_visits%rowtype;
  v_content public.station_contents%rowtype;
  v_question public.questions%rowtype;
  v_zone jsonb;
  v_trail jsonb;
  v_attempts jsonb := '[]'::jsonb;
  v_payload jsonb;
  v_event_state jsonb;
  v_available boolean := true;
  v_reason text;
  v_challenge_status text := 'none';
  v_has_visit boolean := false;
  v_has_content boolean := false;
  v_has_question boolean := false;
  v_review_code text;
  v_today date := (now() at time zone 'America/Cuiaba')::date;
begin
  select q.* into v_qr
  from public.qr_points q
  where lower(q.code) = lower(trim(p_code)) and q.active = true
  limit 1;

  if v_qr.id is null then
    return jsonb_build_object('ok', false, 'error', 'invalid_qr');
  end if;

  v_event_state := public.trilhas_event_state();
  if not coalesce((v_event_state->>'ok')::boolean, false) then
    return v_event_state;
  end if;

  if v_qr.active_from is not null and now() < v_qr.active_from then
    v_available := false;
    v_reason := 'not_started';
  elsif v_qr.active_until is not null and now() >= v_qr.active_until then
    v_available := false;
    v_reason := 'expired';
  end if;

  select jsonb_build_object('id', z.id, 'slug', z.slug, 'name', z.name)
  into v_zone
  from public.zones z
  where z.id = v_qr.zone_id;

  select sv.* into v_visit
  from public.station_visits sv
  where sv.participant_id = p_participant_id
    and sv.qr_point_id = v_qr.id
    and sv.activity_date = v_today
  limit 1;
  v_has_visit := v_visit.id is not null;

  if coalesce(v_qr.station_type, 'permanent') = 'sequential' then
    select jsonb_build_object(
      'id', t.id,'slug', t.slug,'name', t.name,'description', t.description,'completion_points', 0,
      'completion_title', t.completion_title,'completion_body', t.completion_body,'active', t.active,
      'step_number', ts.step_number,'step_count', (select count(*) from public.trail_steps x where x.trail_id = t.id),
      'completed', exists(select 1 from public.trail_completions tc where tc.participant_id = p_participant_id and tc.trail_id = t.id),
      'completion', (select jsonb_build_object('id', tc.id,'points_awarded', tc.points_awarded,'completed_at', tc.completed_at)
        from public.trail_completions tc where tc.participant_id = p_participant_id and tc.trail_id = t.id order by tc.completed_at desc limit 1)
    ) into v_trail
    from public.trail_steps ts
    join public.trails t on t.id = ts.trail_id
    where ts.qr_point_id = v_qr.id
    limit 1;
  end if;

  v_payload := jsonb_build_object(
    'ok', true,'mode', 'trail_station',
    'qr', jsonb_build_object(
      'id', v_qr.id,'code', v_qr.code,'name', v_qr.name,'station_type', coalesce(v_qr.station_type,'permanent'),
      'base_points', 10,'location_hint', v_qr.location_hint,'zone', v_zone,'active_from', v_qr.active_from,'active_until', v_qr.active_until
    ),
    'available', v_available,'availability_reason', v_reason,'validated', v_has_visit,
    'requires_physical_code', v_qr.validation_code_hash is not null,'trail', v_trail,
    'event_day', (v_event_state->>'day_number')::smallint,'activity_date', v_today
  );

  if not v_has_visit then
    return v_payload;
  end if;

  select sc.* into v_content
  from public.station_contents sc
  where sc.qr_point_id = v_qr.id
  limit 1;
  v_has_content := v_content.qr_point_id is not null;

  if v_visit.question_id is not null then
    select q.* into v_question
    from public.questions q
    where q.id = v_visit.question_id and q.active = true
    limit 1;
    v_has_question := v_question.id is not null;
  end if;

  if v_has_question and coalesce((v_event_state->>'is_testing')::boolean, false) then
    select 'Q' || lpad(x.rn::text, 3, '0')
    into v_review_code
    from (
      select id, row_number() over (order by id) as rn
      from public.questions
    ) x
    where x.id = v_question.id;
  end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'attempt_number',sa.attempt_number,
        'correct',sa.correct,
        'answer_value',sa.answer->>'value',
        'answered_at',sa.answered_at
      ) order by sa.attempt_number
    ),
    '[]'::jsonb
  )
  into v_attempts
  from public.station_attempts sa
  where sa.station_visit_id = v_visit.id;

  if not v_has_question then
    v_challenge_status := 'none';
  elsif v_visit.status <> 'completed' then
    v_challenge_status := 'pending';
  elsif coalesce(v_visit.challenge_points,0) > 0 then
    v_challenge_status := 'correct';
  elsif jsonb_array_length(v_attempts) > 0 then
    v_challenge_status := 'finished';
  else
    v_challenge_status := 'none';
  end if;

  return v_payload || jsonb_build_object(
    'visit', to_jsonb(v_visit),
    'content', case when v_has_content then to_jsonb(v_content) else null end,
    'question', case when v_has_question then
      jsonb_build_object(
        'id',v_question.id,
        'kind',v_question.kind,
        'prompt',v_question.prompt,
        'options',v_question.options,
        'difficulty',v_question.difficulty,
        'media_type',v_question.media_type,
        'media_url',v_question.media_url,
        'accessibility',v_question.accessibility
      ) || case
        when v_review_code is not null then jsonb_build_object('review_code', v_review_code)
        else '{}'::jsonb
      end
      else null end,
    'challenge_status', v_challenge_status,
    'attempts', v_attempts,
    'event_day', v_visit.assigned_event_day
  );
end;
$$;
