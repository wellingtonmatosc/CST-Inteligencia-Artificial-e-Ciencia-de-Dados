-- Regras consolidadas do evento de 7 dias.
-- Mantem historico existente e passa a controlar uso por participante + QR + data local.

alter table public.participants
  drop constraint if exists participants_check;

alter table public.participants
  add column if not exists campus text,
  add column if not exists course_name text;

alter table public.station_visits
  add column if not exists activity_date date;

update public.station_visits
set activity_date = (validated_at at time zone 'America/Cuiaba')::date
where activity_date is null;

alter table public.station_visits
  alter column activity_date set default ((now() at time zone 'America/Cuiaba')::date),
  alter column activity_date set not null;

alter table public.station_visits
  drop constraint if exists station_visits_participant_id_qr_point_id_key;

drop index if exists public.station_visits_participant_id_qr_point_id_key;

create unique index if not exists uq_station_visits_participant_qr_day
  on public.station_visits(participant_id, qr_point_id, activity_date);

create index if not exists idx_station_visits_qr_day_question
  on public.station_visits(qr_point_id, activity_date, question_id);

-- A pontuacao-base oficial passa a ser 10 para as estacoes ativas.
update public.qr_points
set base_points = 10
where active = true and base_points is distinct from 10;

create or replace function public.trilhas_select_station_question(
  p_participant_id uuid,
  p_qr_point_id uuid
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_day smallint;
  v_today date := (now() at time zone 'America/Cuiaba')::date;
  v_question_id uuid;
  v_has_pool boolean := false;
begin
  v_day := public.trilhas_current_event_day();

  select exists(
    select 1
    from public.station_question_pool sqp
    join public.questions q on q.id = sqp.question_id and q.active = true
    where sqp.qr_point_id = p_qr_point_id
      and sqp.active = true
      and (sqp.day_number is null or (v_day is not null and sqp.day_number = v_day))
  ) into v_has_pool;

  if v_has_pool then
    select sqp.question_id
      into v_question_id
    from public.station_question_pool sqp
    join public.questions q on q.id = sqp.question_id and q.active = true
    where sqp.qr_point_id = p_qr_point_id
      and sqp.active = true
      and (sqp.day_number is null or (v_day is not null and sqp.day_number = v_day))
      and not exists (
        select 1
        from public.station_visits previous_visit
        where previous_visit.participant_id = p_participant_id
          and previous_visit.question_id = sqp.question_id
      )
    order by
      case when v_day is not null and sqp.day_number = v_day then 0 else 1 end,
      (
        select count(*)
        from public.station_visits participant_visit
        join public.questions participant_question on participant_question.id = participant_visit.question_id
        where participant_visit.participant_id = p_participant_id
          and participant_question.difficulty = q.difficulty
      ) asc,
      (
        select count(*)
        from public.station_visits daily_visit
        where daily_visit.qr_point_id = p_qr_point_id
          and daily_visit.activity_date = v_today
          and daily_visit.question_id = sqp.question_id
      ) asc,
      md5(
        p_participant_id::text || ':' || p_qr_point_id::text || ':' ||
        sqp.question_id::text || ':' || v_today::text
      )
    limit 1;

    -- Pool configurado e esgotado para este participante: nao repetir questao.
    return v_question_id;
  end if;

  -- Compatibilidade temporaria com estacoes legadas ainda sem pool.
  select sc.challenge_question_id
    into v_question_id
  from public.station_contents sc
  join public.questions q on q.id = sc.challenge_question_id and q.active = true
  where sc.qr_point_id = p_qr_point_id
    and not exists (
      select 1
      from public.station_visits previous_visit
      where previous_visit.participant_id = p_participant_id
        and previous_visit.question_id = sc.challenge_question_id
    )
  limit 1;

  return v_question_id;
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
  v_v public.station_visits%rowtype;
  v_s public.trail_steps%rowtype;
  v_team_id uuid;
  v_points integer := 0;
  v_bonus integer := 0;
  v_missing boolean;
  v_status text;
  v_question_id uuid;
  v_event_day smallint;
  v_today date := (now() at time zone 'America/Cuiaba')::date;
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

  if v_q.id is null then
    return jsonb_build_object('ok', false, 'error', 'invalid_qr');
  end if;
  if v_q.active_from is not null and now() < v_q.active_from then
    return jsonb_build_object('ok', false, 'error', 'not_started', 'starts_at', v_q.active_from);
  end if;
  if v_q.active_until is not null and now() >= v_q.active_until then
    return jsonb_build_object('ok', false, 'error', 'expired', 'ends_at', v_q.active_until);
  end if;
  if v_q.validation_code_hash is not null and (
    p_physical_code is null or
    v_q.validation_code_hash <> encode(extensions.digest(upper(trim(p_physical_code)), 'sha256'), 'hex')
  ) then
    return jsonb_build_object('ok', false, 'error', 'invalid_physical_code');
  end if;

  select * into v_v
  from public.station_visits
  where participant_id = p_participant_id
    and qr_point_id = v_q.id
    and activity_date = v_today
  limit 1;

  if v_v.id is not null then
    return jsonb_build_object(
      'ok', true,
      'already_validated', true,
      'visit_id', v_v.id,
      'station_points', v_v.station_points,
      'challenge_points', v_v.challenge_points,
      'total_points', v_v.total_points,
      'status', v_v.status,
      'question_id', v_v.question_id,
      'event_day', v_v.assigned_event_day,
      'activity_date', v_v.activity_date
    );
  end if;

  if v_q.station_type = 'sequential' then
    select * into v_s from public.trail_steps where qr_point_id = v_q.id;
    if v_s.trail_id is null then
      return jsonb_build_object('ok', false, 'error', 'sequence_not_configured');
    end if;

    select exists(
      select 1
      from public.trail_steps prev
      where prev.trail_id = v_s.trail_id
        and prev.step_number < v_s.step_number
        and not exists (
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
    v_points := 10;
  end if;

  v_event_day := public.trilhas_current_event_day();
  v_question_id := public.trilhas_select_station_question(p_participant_id, v_q.id);
  v_status := case when v_question_id is null then 'completed' else 'validated' end;

  insert into public.station_visits(
    participant_id, team_id, qr_point_id, question_id, assigned_event_day,
    activity_date, status, station_points, challenge_points, total_points, completed_at
  ) values (
    p_participant_id, v_team_id, v_q.id, v_question_id, v_event_day,
    v_today, v_status, v_points, 0, v_points,
    case when v_status = 'completed' then now() else null end
  ) returning * into v_v;

  if v_points > 0 then
    insert into public.point_ledger(
      participant_id, team_id, event_type, source_id, points,
      activity_date, dedupe_key, metadata
    ) values (
      p_participant_id, v_team_id, 'station_validation', v_v.id, v_points,
      v_today, 'station:' || v_v.id::text,
      jsonb_build_object(
        'qr_code', v_q.code,
        'station_type', v_q.station_type,
        'question_id', v_question_id,
        'event_day', v_event_day,
        'activity_date', v_today
      )
    ) on conflict(dedupe_key) do nothing;
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
    'competitive', not v_p.is_organizer,
    'question_id', v_question_id,
    'event_day', v_event_day,
    'activity_date', v_today
  );
end;
$$;

create or replace function public.trilhas_get_station(
  p_participant_id uuid,
  p_code text
)
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
  v_available boolean := true;
  v_reason text;
  v_challenge_status text := 'none';
  v_has_visit boolean := false;
  v_has_content boolean := false;
  v_has_question boolean := false;
  v_today date := (now() at time zone 'America/Cuiaba')::date;
begin
  select q.* into v_qr
  from public.qr_points q
  where lower(q.code) = lower(trim(p_code)) and q.active = true
  limit 1;

  if v_qr.id is null then
    return jsonb_build_object('ok', false, 'error', 'invalid_qr');
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
      'id', t.id,
      'slug', t.slug,
      'name', t.name,
      'description', t.description,
      'completion_points', t.completion_points,
      'completion_title', t.completion_title,
      'completion_body', t.completion_body,
      'active', t.active,
      'step_number', ts.step_number,
      'step_count', (select count(*) from public.trail_steps x where x.trail_id = t.id),
      'completed', exists(
        select 1 from public.trail_completions tc
        where tc.participant_id = p_participant_id and tc.trail_id = t.id
      ),
      'completion', (
        select jsonb_build_object(
          'id', tc.id,
          'points_awarded', tc.points_awarded,
          'completed_at', tc.completed_at
        )
        from public.trail_completions tc
        where tc.participant_id = p_participant_id and tc.trail_id = t.id
        order by tc.completed_at desc
        limit 1
      )
    ) into v_trail
    from public.trail_steps ts
    join public.trails t on t.id = ts.trail_id
    where ts.qr_point_id = v_qr.id
    limit 1;
  end if;

  v_payload := jsonb_build_object(
    'ok', true,
    'mode', 'trail_station',
    'qr', jsonb_build_object(
      'id', v_qr.id,
      'code', v_qr.code,
      'name', v_qr.name,
      'station_type', coalesce(v_qr.station_type, 'permanent'),
      'base_points', 10,
      'location_hint', v_qr.location_hint,
      'zone', v_zone,
      'active_from', v_qr.active_from,
      'active_until', v_qr.active_until
    ),
    'available', v_available,
    'availability_reason', v_reason,
    'validated', v_has_visit,
    'requires_physical_code', v_qr.validation_code_hash is not null,
    'trail', v_trail,
    'activity_date', v_today
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

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'attempt_number', sa.attempt_number,
        'correct', sa.correct,
        'answer_value', sa.answer->>'value',
        'answered_at', sa.answered_at
      ) order by sa.attempt_number
    ),
    '[]'::jsonb
  ) into v_attempts
  from public.station_attempts sa
  where sa.station_visit_id = v_visit.id;

  if not v_has_question then
    v_challenge_status := 'none';
  elsif v_visit.status <> 'completed' then
    v_challenge_status := 'pending';
  elsif coalesce(v_visit.challenge_points, 0) > 0 then
    v_challenge_status := 'correct';
  elsif jsonb_array_length(v_attempts) > 0 then
    v_challenge_status := 'finished';
  else
    v_challenge_status := 'none';
  end if;

  return v_payload || jsonb_build_object(
    'visit', to_jsonb(v_visit),
    'content', case when v_has_content then to_jsonb(v_content) else null end,
    'question', case when v_has_question then jsonb_build_object(
      'id', v_question.id,
      'kind', v_question.kind,
      'prompt', v_question.prompt,
      'options', v_question.options,
      'difficulty', v_question.difficulty,
      'media_type', v_question.media_type,
      'media_url', v_question.media_url,
      'accessibility', v_question.accessibility
    ) else null end,
    'challenge_status', v_challenge_status,
    'attempts', v_attempts,
    'event_day', v_visit.assigned_event_day
  );
end;
$$;

create or replace function public.trilhas_answer_challenge(
  p_participant_id uuid,
  p_code text,
  p_answer text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_v public.station_visits%rowtype;
  v_q public.qr_points%rowtype;
  v_c public.station_contents%rowtype;
  v_quest public.questions%rowtype;
  v_p public.participants%rowtype;
  v_attempt smallint;
  v_max smallint := 2;
  v_correct boolean := false;
  v_points integer := 0;
  v_bonus integer := 0;
  v_text text;
  v_finished boolean := false;
  v_today date := (now() at time zone 'America/Cuiaba')::date;
begin
  select * into v_q
  from public.qr_points
  where upper(code) = upper(trim(p_code)) and active = true
  limit 1;

  if v_q.id is null then return jsonb_build_object('ok', false, 'error', 'invalid_qr'); end if;
  if v_q.active_from is not null and now() < v_q.active_from then return jsonb_build_object('ok', false, 'error', 'not_started', 'starts_at', v_q.active_from); end if;
  if v_q.active_until is not null and now() >= v_q.active_until then return jsonb_build_object('ok', false, 'error', 'expired', 'ends_at', v_q.active_until); end if;

  select * into v_p
  from public.participants
  where id = p_participant_id and active = true;
  if v_p.id is null then return jsonb_build_object('ok', false, 'error', 'participant_not_found'); end if;

  select * into v_v
  from public.station_visits
  where participant_id = p_participant_id
    and qr_point_id = v_q.id
    and activity_date = v_today
  for update;

  if v_v.id is null then return jsonb_build_object('ok', false, 'error', 'station_not_validated'); end if;
  if v_v.question_id is null then return jsonb_build_object('ok', false, 'error', 'no_challenge'); end if;
  if v_v.status = 'completed' then return jsonb_build_object('ok', false, 'error', 'already_completed', 'points', v_v.challenge_points); end if;

  select * into v_c from public.station_contents where qr_point_id = v_q.id;
  select * into v_quest from public.questions where id = v_v.question_id and active = true;
  if v_quest.id is null then return jsonb_build_object('ok', false, 'error', 'challenge_unavailable'); end if;

  v_attempt := v_v.attempts_count + 1;
  if v_attempt > v_max then return jsonb_build_object('ok', false, 'error', 'already_completed'); end if;

  if v_quest.kind in ('multiple_choice', 'true_false') then
    v_correct := coalesce(p_answer, '') = coalesce(v_quest.correct_answer->>'value', '');
  elsif v_quest.kind = 'short_text' then
    v_text := public.trilhas_normalize_text(coalesce(p_answer, ''));
    if jsonb_typeof(v_quest.correct_answer->'accepted') = 'array' then
      select exists(
        select 1
        from jsonb_array_elements_text(v_quest.correct_answer->'accepted') a(value)
        where public.trilhas_normalize_text(a.value) = v_text
      ) into v_correct;
    else
      v_correct := public.trilhas_normalize_text(v_quest.correct_answer->>'value') = v_text;
    end if;
  end if;

  insert into public.station_attempts(
    station_visit_id, participant_id, question_id, attempt_number, answer, correct
  ) values (
    v_v.id, p_participant_id, v_quest.id, v_attempt,
    jsonb_build_object('value', p_answer), v_correct
  );

  if v_correct then
    v_points := case
      when v_p.is_organizer then 0
      when v_attempt = 1 then 10
      else 6
    end;
    v_finished := true;

    update public.station_visits
    set status = 'completed',
        attempts_count = v_attempt,
        challenge_points = v_points,
        total_points = station_points + v_points,
        completed_at = now()
    where id = v_v.id;

    if v_points > 0 then
      insert into public.point_ledger(
        participant_id, team_id, event_type, source_id, points,
        activity_date, dedupe_key, metadata
      ) values (
        p_participant_id, v_v.team_id, 'challenge', v_v.id, v_points,
        v_v.activity_date, 'challenge:' || v_v.id::text,
        jsonb_build_object(
          'qr_code', v_q.code,
          'question_id', v_quest.id,
          'event_day', v_v.assigned_event_day,
          'attempt', v_attempt
        )
      ) on conflict(dedupe_key) do nothing;
    end if;
  else
    v_finished := v_attempt >= v_max;
    update public.station_visits
    set attempts_count = v_attempt,
        status = case when v_finished then 'completed' else status end,
        completed_at = case when v_finished then now() else completed_at end
    where id = v_v.id;
  end if;

  if v_finished and v_q.station_type = 'sequential' then
    v_bonus := public.trilhas_complete_trail_if_ready(
      p_participant_id, v_q.id, v_v.team_id, v_p.is_organizer
    );
  end if;

  if v_correct then
    return jsonb_build_object(
      'ok', true,
      'correct', true,
      'completed', true,
      'points', v_points,
      'trail_bonus', v_bonus,
      'attempts', v_attempt,
      'remaining', 0,
      'max_attempts', v_max,
      'explanation', v_quest.explanation
    );
  end if;

  return jsonb_build_object(
    'ok', true,
    'correct', false,
    'completed', v_finished,
    'points', 0,
    'trail_bonus', v_bonus,
    'attempts', v_attempt,
    'remaining', greatest(0, v_max - v_attempt),
    'max_attempts', v_max,
    'explanation', case when v_finished then v_quest.explanation else null end
  );
end;
$$;
