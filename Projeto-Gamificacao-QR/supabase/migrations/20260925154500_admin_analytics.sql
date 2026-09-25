-- Analytics administrativos do evento.
-- Mantém a leitura agregada no banco para evitar transferir milhares de visitas ao navegador.

create or replace function public.trilhas_admin_analytics()
returns jsonb
language sql
security definer
set search_path = public
as $$
with question_codes as (
  select q.id, q.prompt, 'Q' || lpad(row_number() over (order by q.id)::text, 3, '0') as review_code
  from public.questions q
),
challenge_outcomes as (
  select
    sv.id as visit_id,
    sv.participant_id,
    sv.qr_point_id,
    sv.question_id,
    sv.activity_date,
    min(sa.attempt_number) filter (where sa.correct) as correct_attempt,
    count(sa.id)::int as attempts
  from public.station_visits sv
  left join public.station_attempts sa on sa.station_visit_id = sv.id
  group by sv.id, sv.participant_id, sv.qr_point_id, sv.question_id, sv.activity_date
),
daily_usage_rows as (
  select
    sv.activity_date,
    max(sv.assigned_event_day)::int as event_day,
    count(*)::int as validations,
    count(distinct sv.qr_point_id)::int as distinct_qrs,
    count(distinct sv.participant_id)::int as participants,
    coalesce(sum(sv.total_points),0)::int as points
  from public.station_visits sv
  group by sv.activity_date
),
qr_usage_rows as (
  select
    q.code,
    q.name,
    count(sv.id)::int as validations,
    count(distinct sv.participant_id)::int as participants,
    coalesce(sum(sv.total_points),0)::int as points,
    count(*) filter (where co.correct_attempt = 1)::int as first_try,
    count(*) filter (where co.correct_attempt = 2)::int as second_try,
    count(*) filter (where co.attempts > 0 and co.correct_attempt is null)::int as failed
  from public.qr_points q
  left join public.station_visits sv on sv.qr_point_id = q.id
  left join challenge_outcomes co on co.visit_id = sv.id
  group by q.id, q.code, q.name
),
daily_visit_stats as (
  select
    sv.activity_date,
    sv.participant_id,
    count(*)::int as stations,
    count(*) filter (where co.correct_attempt = 1)::int as first_try_correct
  from public.station_visits sv
  left join challenge_outcomes co on co.visit_id = sv.id
  group by sv.activity_date, sv.participant_id
),
daily_points as (
  select
    pl.activity_date,
    p.id as participant_id,
    p.nick,
    sum(pl.points)::int as points
  from public.point_ledger pl
  join public.participants p on p.id = pl.participant_id
  where p.active = true
    and p.is_organizer = false
    and pl.event_type in ('station_validation','challenge','manual_action','manual_reversal')
  group by pl.activity_date, p.id, p.nick
),
daily_combined as (
  select
    dp.activity_date,
    dp.participant_id,
    dp.nick,
    dp.points,
    coalesce(dvs.stations,0)::int as stations,
    coalesce(dvs.first_try_correct,0)::int as first_try_correct
  from daily_points dp
  left join daily_visit_stats dvs on dvs.activity_date = dp.activity_date and dvs.participant_id = dp.participant_id
),
daily_ranked as (
  select d.*, rank() over (partition by d.activity_date order by d.points desc, d.stations desc, d.first_try_correct desc)::int as position
  from daily_combined d
),
question_player_rows as (
  select
    p.id,
    p.nick,
    coalesce(sum(sv.challenge_points),0)::int as challenge_points,
    count(*) filter (where co.correct_attempt is not null)::int as correct_answers,
    count(*) filter (where co.correct_attempt = 1)::int as first_try_correct,
    count(*) filter (where co.correct_attempt = 2)::int as second_try_correct,
    count(*) filter (where co.attempts > 0 and co.correct_attempt is null)::int as failed
  from public.participants p
  join public.station_visits sv on sv.participant_id = p.id
  left join challenge_outcomes co on co.visit_id = sv.id
  where p.active = true and p.is_organizer = false
  group by p.id, p.nick
),
question_player_ranked as (
  select q.*, rank() over (order by q.challenge_points desc, q.correct_answers desc, q.first_try_correct desc)::int as position
  from question_player_rows q
),
qr_player_rows as (
  select
    p.id,
    p.nick,
    count(sv.id)::int as stations_validated,
    count(distinct sv.qr_point_id)::int as distinct_qrs,
    coalesce(sum(sv.station_points),0)::int as station_points
  from public.participants p
  join public.station_visits sv on sv.participant_id = p.id
  where p.active = true and p.is_organizer = false
  group by p.id, p.nick
),
qr_player_ranked as (
  select q.*, rank() over (order by q.distinct_qrs desc, q.stations_validated desc, q.station_points desc)::int as position
  from qr_player_rows q
),
question_performance_rows as (
  select
    qc.review_code,
    qc.prompt,
    count(sv.id)::int as assigned,
    count(*) filter (where co.attempts > 0)::int as attempted,
    count(*) filter (where co.correct_attempt = 1)::int as first_try,
    count(*) filter (where co.correct_attempt = 2)::int as second_try,
    count(*) filter (where co.attempts > 0 and co.correct_attempt is null)::int as failed,
    coalesce(round(100.0 * count(*) filter (where co.correct_attempt is not null) / nullif(count(*) filter (where co.attempts > 0),0),1),0) as success_rate
  from question_codes qc
  left join public.station_visits sv on sv.question_id = qc.id
  left join challenge_outcomes co on co.visit_id = sv.id
  group by qc.id, qc.review_code, qc.prompt
  having count(sv.id) > 0
)
select jsonb_build_object(
  'summary', jsonb_build_object(
    'participants_with_activity', (select count(distinct participant_id)::int from public.station_visits),
    'qrs_with_activity', (select count(distinct qr_point_id)::int from public.station_visits),
    'qrs_with_physical_code', (select count(*)::int from public.qr_points where validation_code_hash is not null),
    'questions_with_activity', (select count(distinct question_id)::int from public.station_visits where question_id is not null)
  ),
  'daily_usage', coalesce((select jsonb_agg(to_jsonb(x) order by x.activity_date) from daily_usage_rows x), '[]'::jsonb),
  'qr_usage', coalesce((select jsonb_agg(to_jsonb(x) order by x.code) from qr_usage_rows x), '[]'::jsonb),
  'general_ranking', public.trilhas_individual_ranking(),
  'daily_ranking', coalesce((select jsonb_agg(to_jsonb(x) order by x.activity_date, x.position, lower(x.nick)) from daily_ranked x), '[]'::jsonb),
  'question_ranking', coalesce((select jsonb_agg(to_jsonb(x) order by x.position, lower(x.nick)) from question_player_ranked x), '[]'::jsonb),
  'qr_ranking', coalesce((select jsonb_agg(to_jsonb(x) order by x.position, lower(x.nick)) from qr_player_ranked x), '[]'::jsonb),
  'attempt_ranking', coalesce((select jsonb_agg(jsonb_build_object('nick',x.nick,'first_try_correct',x.first_try_correct,'second_try_correct',x.second_try_correct,'failed',x.failed) order by x.first_try_correct desc, x.second_try_correct desc, lower(x.nick)) from question_player_rows x), '[]'::jsonb),
  'question_performance', coalesce((select jsonb_agg(to_jsonb(x) order by x.review_code) from question_performance_rows x), '[]'::jsonb)
);
$$;

revoke all on function public.trilhas_admin_analytics() from public, anon, authenticated;
grant execute on function public.trilhas_admin_analytics() to postgres, service_role;
