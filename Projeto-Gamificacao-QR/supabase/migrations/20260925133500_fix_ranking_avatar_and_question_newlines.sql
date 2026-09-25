-- Corrige regressões identificadas na homologação real:
-- 1) ranking passa a usar sempre o avatar atual do participante;
-- 2) sequências literais "\\n" nos enunciados viram quebras de linha reais.

update public.questions
set prompt = replace(prompt, chr(92) || 'n', chr(10)),
    updated_at = now()
where position(chr(92) || 'n' in prompt) > 0;

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
  select
    participant_id,
    failure_group,
    count(*)::int as streak
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
        and pl.event_type in (
          'station_validation',
          'challenge',
          'manual_action',
          'manual_reversal'
        )
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
      where co.participant_id = p.id
        and co.correct
    ), 0) as correct_answers,
    coalesce((
      select count(*)::int
      from challenge_outcomes co
      where co.participant_id = p.id
        and co.correct_attempt = 1
    ), 0) as first_try_correct,
    coalesce((
      select ss.best_correct_streak
      from streak_stats ss
      where ss.participant_id = p.id
    ), 0) as best_correct_streak
  from public.participants p
  where p.active = true
    and p.is_organizer = false
), active_stats as (
  select *
  from stats
  where points <> 0
     or trails_completed > 0
     or stations_validated > 0
), ranked as (
  select
    s.*,
    rank() over (
      order by
        s.points desc,
        s.trails_completed desc,
        s.stations_validated desc
    )::int as position,
    count(*) over (
      partition by
        s.points,
        s.trails_completed,
        s.stations_validated
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
