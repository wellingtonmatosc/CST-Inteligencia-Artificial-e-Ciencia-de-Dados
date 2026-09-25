-- Trilhas Poéticas — competição individual
-- Mantém estruturas e snapshots históricos de equipe, mas todo novo jogo competitivo passa a ser individual.

update public.teams
set active = false
where active = true;

update public.participants
set team_id = null,
    team_revealed_at = null,
    updated_at = now()
where team_id is not null
   or team_revealed_at is not null;

create or replace function public.trilhas_assign_team(p_participant_id uuid)
returns uuid
language sql
security definer
set search_path = public
as $$
  select null::uuid;
$$;

create or replace function public.trilhas_individual_ranking()
returns jsonb
language sql
security definer
set search_path = public
as $$
with stats as (
  select
    p.id,
    p.nick,
    coalesce((
      select sum(pl.points)::int
      from public.point_ledger pl
      where pl.participant_id = p.id
        and pl.event_type in ('station_validation','challenge','trail_completion','manual_action','manual_reversal')
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
    ), 0) as stations_validated
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
      order by s.points desc, s.trails_completed desc, s.stations_validated desc
    )::int as position
  from active_stats s
)
select coalesce(
  jsonb_agg(
    jsonb_build_object(
      'position', position,
      'id', id,
      'nick', nick,
      'points', points,
      'trails_completed', trails_completed,
      'stations_validated', stations_validated
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
  v_pos int;
begin
  select * into v_p
  from public.participants
  where id = p_participant_id;

  if v_p.id is null then
    return jsonb_build_object('ok', false, 'error', 'participant_not_found');
  end if;

  select coalesce(sum(points), 0)::int into v_points
  from public.point_ledger
  where participant_id = p_participant_id
    and event_type in ('station_validation','challenge','trail_completion','manual_action','manual_reversal');

  select count(*)::int into v_stations
  from public.station_visits
  where participant_id = p_participant_id;

  select count(*)::int into v_trails
  from public.trail_completions
  where participant_id = p_participant_id;

  select count(*)::int into v_pending
  from public.station_visits
  where participant_id = p_participant_id
    and status = 'validated';

  select count(*)::int into v_active
  from public.qr_points q
  where q.active
    and q.station_type in ('temporary','special')
    and (q.active_from is null or now() >= q.active_from)
    and (q.active_until is null or now() < q.active_until);

  if not v_p.is_organizer then
    v_rank := public.trilhas_individual_ranking();
    select nullif(item->>'position', '')::int into v_pos
    from jsonb_array_elements(v_rank) as e(item)
    where item->>'id' = v_p.id::text
    limit 1;
  end if;

  return jsonb_build_object(
    'ok', true,
    'points', v_points,
    'stations_validated', v_stations,
    'trails_completed', v_trails,
    'pending_challenges', v_pending,
    'active_specials', v_active,
    'competitive', not v_p.is_organizer,
    'individual_position', v_pos
  );
end;
$$;

create or replace function public.trilhas_validate_station(
  p_participant_id uuid,
  p_code text,
  p_physical_code text
)
returns jsonb
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_p public.participants%rowtype;
  v_q public.qr_points%rowtype;
  v_c public.station_contents%rowtype;
  v_v public.station_visits%rowtype;
  v_s public.trail_steps%rowtype;
  v_team_id uuid;
  v_points integer := 0;
  v_bonus integer := 0;
  v_missing boolean;
  v_status text;
begin
  select * into v_p
  from public.participants
  where id = p_participant_id and active = true
  for update;

  if v_p.id is null then
    return jsonb_build_object('ok', false, 'error', 'participant_not_found');
  end if;

  select * into v_q
  from public.qr_points
  where upper(code) = upper(trim(p_code)) and active = true
  limit 1;

  if v_q.id is null then return jsonb_build_object('ok', false, 'error', 'invalid_qr'); end if;
  if v_q.active_from is not null and now() < v_q.active_from then return jsonb_build_object('ok', false, 'error', 'not_started', 'starts_at', v_q.active_from); end if;
  if v_q.active_until is not null and now() >= v_q.active_until then return jsonb_build_object('ok', false, 'error', 'expired', 'ends_at', v_q.active_until); end if;

  if v_q.validation_code_hash is not null
     and (
       p_physical_code is null
       or v_q.validation_code_hash <> encode(extensions.digest(upper(trim(p_physical_code)), 'sha256'), 'hex')
     ) then
    return jsonb_build_object('ok', false, 'error', 'invalid_physical_code');
  end if;

  select * into v_v
  from public.station_visits
  where participant_id = p_participant_id
    and qr_point_id = v_q.id
  limit 1;

  if v_v.id is not null then
    return jsonb_build_object(
      'ok', true,
      'already_validated', true,
      'visit_id', v_v.id,
      'station_points', v_v.station_points,
      'challenge_points', v_v.challenge_points,
      'total_points', v_v.total_points,
      'status', v_v.status
    );
  end if;

  if v_q.station_type = 'sequential' then
    select * into v_s
    from public.trail_steps
    where qr_point_id = v_q.id;

    if v_s.trail_id is null then
      return jsonb_build_object('ok', false, 'error', 'sequence_not_configured');
    end if;

    select exists(
      select 1
      from public.trail_steps prev
      where prev.trail_id = v_s.trail_id
        and prev.step_number < v_s.step_number
        and not exists(
          select 1
          from public.station_visits sv
          where sv.participant_id = p_participant_id
            and sv.qr_point_id = prev.qr_point_id
            and sv.status = 'completed'
        )
    ) into v_missing;

    if v_missing then
      return jsonb_build_object('ok', false, 'error', 'sequence_locked', 'step', v_s.step_number);
    end if;
  end if;

  if not v_p.is_organizer then
    v_points := v_q.base_points;
  end if;

  select * into v_c
  from public.station_contents
  where qr_point_id = v_q.id;

  v_status := case when v_c.challenge_question_id is null then 'completed' else 'validated' end;

  insert into public.station_visits(
    participant_id, team_id, qr_point_id, question_id, status,
    station_points, challenge_points, total_points, completed_at
  )
  values(
    p_participant_id, v_team_id, v_q.id, v_c.challenge_question_id, v_status,
    v_points, 0, v_points, case when v_status = 'completed' then now() else null end
  )
  returning * into v_v;

  if v_points > 0 then
    insert into public.point_ledger(
      participant_id, team_id, event_type, source_id, points, activity_date, dedupe_key, metadata
    )
    values(
      p_participant_id, v_team_id, 'station_validation', v_v.id, v_points,
      (now() at time zone 'America/Cuiaba')::date,
      'station:' || p_participant_id::text || ':' || v_q.id::text,
      jsonb_build_object('qr_code', v_q.code, 'station_type', v_q.station_type)
    )
    on conflict(dedupe_key) do nothing;
  end if;

  if v_q.station_type = 'sequential' and v_status = 'completed' then
    v_bonus := public.trilhas_complete_trail_if_ready(
      p_participant_id, v_q.id, v_team_id, v_p.is_organizer
    );
  end if;

  return jsonb_build_object(
    'ok', true,
    'already_validated', false,
    'visit_id', v_v.id,
    'station_points', v_points,
    'trail_bonus', v_bonus,
    'status', v_v.status,
    'competitive', not v_p.is_organizer
  );
end;
$$;

create or replace function public.trilhas_admin_grant_manual_points(
  p_participant_id uuid,
  p_action_type text,
  p_description text,
  p_evidence text,
  p_points integer,
  p_actor text,
  p_actor_role text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id uuid;
  v_date date;
  v_p public.participants%rowtype;
begin
  select * into v_p
  from public.participants
  where id = p_participant_id and active = true;

  if v_p.id is null then return jsonb_build_object('ok', false, 'error', 'participant_not_found'); end if;
  if p_points < 0 or p_points > 200 then return jsonb_build_object('ok', false, 'error', 'invalid_points'); end if;

  insert into public.manual_point_actions(
    participant_id, team_id, action_type, description, evidence, points, approved_by
  )
  values(
    p_participant_id, null, p_action_type, trim(p_description),
    nullif(trim(coalesce(p_evidence, '')), ''), p_points, p_actor
  )
  returning id into v_id;

  v_date := (now() at time zone 'America/Cuiaba')::date;

  if p_points > 0 and not v_p.is_organizer then
    insert into public.point_ledger(
      participant_id, team_id, event_type, source_id, points, activity_date, dedupe_key, metadata
    )
    values(
      p_participant_id, null, 'manual_action', v_id, p_points, v_date,
      'manual:' || v_id::text,
      jsonb_build_object('action_type', p_action_type, 'approved_by', p_actor)
    );
  end if;

  insert into public.audit_log(
    actor_username, actor_role, action, entity_type, entity_id, metadata
  )
  values(
    p_actor, p_actor_role, 'manual_points_granted', 'manual_point_action', v_id::text,
    jsonb_build_object('participant_id', p_participant_id, 'points', p_points, 'action_type', p_action_type)
  );

  return jsonb_build_object(
    'ok', true,
    'id', v_id,
    'points', case when v_p.is_organizer then 0 else p_points end
  );
end;
$$;

create or replace function public.trilhas_admin_reverse_manual_points(
  p_action_id uuid,
  p_reason text,
  p_actor text,
  p_actor_role text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_a public.manual_point_actions%rowtype;
  v_date date;
  v_had_ledger boolean := false;
  v_team_id uuid;
begin
  select * into v_a
  from public.manual_point_actions
  where id = p_action_id
  for update;

  if v_a.id is null then return jsonb_build_object('ok', false, 'error', 'action_not_found'); end if;
  if v_a.status = 'reversed' then return jsonb_build_object('ok', true, 'already_reversed', true, 'id', v_a.id); end if;

  update public.manual_point_actions
  set status = 'reversed',
      reversed_by = p_actor,
      reversed_at = now(),
      reversal_reason = trim(p_reason)
  where id = v_a.id;

  select exists(
    select 1
    from public.point_ledger pl
    where pl.event_type = 'manual_action'
      and pl.source_id = v_a.id
  ) into v_had_ledger;

  if v_had_ledger then
    select pl.team_id into v_team_id
    from public.point_ledger pl
    where pl.event_type = 'manual_action'
      and pl.source_id = v_a.id
    order by pl.created_at
    limit 1;
  end if;

  v_date := (now() at time zone 'America/Cuiaba')::date;

  if v_a.points <> 0 and v_had_ledger then
    insert into public.point_ledger(
      participant_id, team_id, event_type, source_id, points, activity_date, dedupe_key, metadata
    )
    values(
      v_a.participant_id, v_team_id, 'manual_reversal', v_a.id, -v_a.points, v_date,
      'manual-reversal:' || v_a.id::text,
      jsonb_build_object('reason', p_reason, 'reversed_by', p_actor)
    );
  end if;

  insert into public.audit_log(
    actor_username, actor_role, action, entity_type, entity_id, metadata
  )
  values(
    p_actor, p_actor_role, 'manual_points_reversed', 'manual_point_action', v_a.id::text,
    jsonb_build_object('participant_id', v_a.participant_id, 'points', v_a.points, 'reason', p_reason)
  );

  return jsonb_build_object('ok', true, 'id', v_a.id, 'reversed_points', v_a.points);
end;
$$;

revoke all on function public.trilhas_assign_team(uuid) from public, anon, authenticated;
revoke all on function public.trilhas_individual_ranking() from public, anon, authenticated;
revoke all on function public.trilhas_participant_summary(uuid) from public, anon, authenticated;
revoke all on function public.trilhas_validate_station(uuid,text,text) from public, anon, authenticated;
revoke all on function public.trilhas_admin_grant_manual_points(uuid,text,text,text,integer,text,text) from public, anon, authenticated;
revoke all on function public.trilhas_admin_reverse_manual_points(uuid,text,text,text) from public, anon, authenticated;

grant execute on function public.trilhas_assign_team(uuid) to service_role;
grant execute on function public.trilhas_individual_ranking() to service_role;
grant execute on function public.trilhas_participant_summary(uuid) to service_role;
grant execute on function public.trilhas_validate_station(uuid,text,text) to service_role;
grant execute on function public.trilhas_admin_grant_manual_points(uuid,text,text,text,integer,text,text) to service_role;
grant execute on function public.trilhas_admin_reverse_manual_points(uuid,text,text,text) to service_role;
