-- O desempate do Dia 7 só passa a ordenar o ranking quando todos os membros
-- do mesmo empate técnico tiverem resultado registrado.

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

create or replace function public.trilhas_participant_summary(p_participant_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_p public.participants%rowtype;
  v_points int := 0;
  v_stations int := 0;
  v_trails int := 0;
  v_pending int := 0;
  v_active int := 0;
  v_rank jsonb;
  v_row jsonb;
  v_pos int;
begin
  select * into v_p from public.participants where id = p_participant_id;
  if v_p.id is null then return jsonb_build_object('ok', false, 'error', 'participant_not_found'); end if;

  select coalesce(sum(points), 0)::int into v_points from public.point_ledger where participant_id = p_participant_id and event_type in ('station_validation','challenge','trail_completion','manual_action','manual_reversal');
  select count(*)::int into v_stations from public.station_visits where participant_id = p_participant_id;
  select count(*)::int into v_trails from public.trail_completions where participant_id = p_participant_id;
  select count(*)::int into v_pending from public.station_visits where participant_id = p_participant_id and status = 'validated';
  select count(*)::int into v_active from public.qr_points q where q.active and q.station_type in ('temporary','special') and (q.active_from is null or now() >= q.active_from) and (q.active_until is null or now() < q.active_until);

  if not v_p.is_organizer then
    v_rank := public.trilhas_individual_ranking();
    select item into v_row from jsonb_array_elements(v_rank) as e(item) where item->>'id' = v_p.id::text limit 1;
    v_pos := nullif(v_row->>'position', '')::int;
  end if;

  return jsonb_build_object(
    'ok', true,
    'points', v_points,
    'stations_validated', v_stations,
    'trails_completed', v_trails,
    'pending_challenges', v_pending,
    'active_specials', v_active,
    'competitive', not v_p.is_organizer,
    'individual_position', v_pos,
    'distinct_qrs', coalesce((v_row->>'distinct_qrs')::int, 0),
    'active_days', coalesce((v_row->>'active_days')::int, 0),
    'correct_answers', coalesce((v_row->>'correct_answers')::int, 0),
    'first_try_correct', coalesce((v_row->>'first_try_correct')::int, 0),
    'best_correct_streak', coalesce((v_row->>'best_correct_streak')::int, 0),
    'final_tiebreak_score', coalesce((v_row->>'final_tiebreak_score')::int, 0),
    'final_tiebreak_recorded', coalesce((v_row->>'final_tiebreak_recorded')::boolean, false),
    'ranking_tie_count', coalesce((v_row->>'tie_count')::int, 1),
    'needs_final_tiebreak', coalesce((v_row->>'needs_final_tiebreak')::boolean, false),
    'final_tiebreak_resolved', coalesce((v_row->>'final_tiebreak_resolved')::boolean, false),
    'unresolved_tie', coalesce((v_row->>'unresolved_tie')::boolean, false)
  );
end;
$$;
