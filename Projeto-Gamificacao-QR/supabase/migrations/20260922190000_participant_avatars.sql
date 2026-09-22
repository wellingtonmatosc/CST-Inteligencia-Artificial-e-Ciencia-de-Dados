-- Avatares internos: somente uma chave pequena e validada é persistida.
-- Compatível com participantes existentes e sem alterar qualquer regra de gamificação.

alter table public.participants
  add column if not exists avatar_key text not null default 'avatar-01';

update public.participants
set avatar_key = 'avatar-01'
where avatar_key is null
   or avatar_key !~ '^avatar-(0[1-9]|1[0-2])$';

alter table public.participants
  drop constraint if exists participants_avatar_key_check;

alter table public.participants
  add constraint participants_avatar_key_check
  check (avatar_key ~ '^avatar-(0[1-9]|1[0-2])$');

create or replace function public.trilhas_participant_from_session(p_token_hash text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare v_p public.participants%rowtype;
begin
  select p.* into v_p
  from public.participant_sessions s
  join public.participants p on p.id=s.participant_id
  where s.token_hash=p_token_hash
    and s.revoked_at is null
    and s.expires_at>now()
    and p.active=true
  limit 1;

  if v_p.id is null then
    return jsonb_build_object('ok',false,'error','invalid_session');
  end if;

  update public.participant_sessions
  set last_seen_at=now()
  where token_hash=p_token_hash
    and revoked_at is null
    and expires_at>now()
    and (last_seen_at is null or last_seen_at<now()-interval '5 minutes');

  return jsonb_build_object(
    'ok',true,
    'participant',jsonb_build_object(
      'id',v_p.id,
      'full_name',v_p.full_name,
      'nick',v_p.nick,
      'participant_type',v_p.participant_type,
      'campus',v_p.campus,
      'course_name',v_p.course_name,
      'avatar_key',v_p.avatar_key,
      'active',v_p.active,
      'team_id',v_p.team_id,
      'team_revealed_at',v_p.team_revealed_at,
      'is_organizer',v_p.is_organizer,
      'has_password',true
    )
  );
end;
$$;

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
  group by sv.participant_id, sv.id, sv.qr_point_id, sv.activity_date, sv.completed_at, sv.validated_at
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
    coalesce((select sum(pl.points)::int from public.point_ledger pl where pl.participant_id = p.id and pl.event_type in ('station_validation','challenge','trail_completion','manual_action','manual_reversal')), 0) as points,
    coalesce((select count(*)::int from public.trail_completions tc where tc.participant_id = p.id), 0) as trails_completed,
    coalesce((select count(*)::int from public.station_visits sv where sv.participant_id = p.id), 0) as stations_validated,
    coalesce((select count(distinct sv.qr_point_id)::int from public.station_visits sv where sv.participant_id = p.id), 0) as distinct_qrs,
    coalesce((select count(distinct sv.activity_date)::int from public.station_visits sv where sv.participant_id = p.id), 0) as active_days,
    coalesce((select count(*)::int from challenge_outcomes co where co.participant_id = p.id and co.correct), 0) as correct_answers,
    coalesce((select count(*)::int from challenge_outcomes co where co.participant_id = p.id and co.correct_attempt = 1), 0) as first_try_correct,
    coalesce((select ss.best_correct_streak from streak_stats ss where ss.participant_id = p.id), 0) as best_correct_streak,
    coalesce((select ftr.score from public.final_tiebreak_results ftr where ftr.participant_id = p.id), 0) as final_tiebreak_score,
    exists(select 1 from public.final_tiebreak_results ftr where ftr.participant_id = p.id) as final_tiebreak_recorded
  from public.participants p
  where p.active = true and p.is_organizer = false
), active_stats as (
  select * from stats
  where points <> 0 or trails_completed > 0 or stations_validated > 0 or final_tiebreak_recorded
), pre_ties as (
  select
    s.*,
    count(*) over (
      partition by s.points, s.correct_answers, s.first_try_correct, s.distinct_qrs, s.active_days
    )::int as pre_final_tie_count,
    count(*) filter (where s.final_tiebreak_recorded) over (
      partition by s.points, s.correct_answers, s.first_try_correct, s.distinct_qrs, s.active_days
    )::int as final_scores_recorded_count
  from active_stats s
), prepared as (
  select
    p.*,
    case
      when p.pre_final_tie_count > 1
       and p.final_scores_recorded_count = p.pre_final_tie_count
      then p.final_tiebreak_score
      else 0
    end as effective_final_tiebreak_score
  from pre_ties p
), ranked as (
  select
    p.*,
    rank() over (
      order by
        p.points desc,
        p.correct_answers desc,
        p.first_try_correct desc,
        p.distinct_qrs desc,
        p.active_days desc,
        p.effective_final_tiebreak_score desc
    )::int as position,
    count(*) over (
      partition by
        p.points,
        p.correct_answers,
        p.first_try_correct,
        p.distinct_qrs,
        p.active_days,
        p.effective_final_tiebreak_score
    )::int as final_tie_count
  from prepared p
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
      'final_tiebreak_score', final_tiebreak_score,
      'final_tiebreak_recorded', final_tiebreak_recorded,
      'effective_final_tiebreak_score', effective_final_tiebreak_score,
      'pre_final_tie_count', pre_final_tie_count,
      'final_scores_recorded_count', final_scores_recorded_count,
      'tie_count', final_tie_count,
      'needs_final_tiebreak', pre_final_tie_count > 1,
      'final_tiebreak_resolved', pre_final_tie_count > 1 and final_scores_recorded_count = pre_final_tie_count and final_tie_count = 1,
      'unresolved_tie', pre_final_tie_count > 1 and (final_scores_recorded_count < pre_final_tie_count or final_tie_count > 1)
    )
    order by position, lower(nick), id
  ),
  '[]'::jsonb
)
from ranked;
$$;
