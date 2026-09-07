-- Otimizações de latência para o fluxo principal da gamificação.
-- Concentra validação de sessão, carregamento de QR normal, resposta e ranking
-- em funções PostgreSQL para reduzir viagens entre FastAPI e Supabase.

create or replace function public.game_normalize_text(p_value text)
returns text
language sql
immutable
set search_path = public
as $$
    select regexp_replace(
        translate(
            lower(trim(coalesce(p_value, ''))),
            'áàâãäéèêëíìîïóòôõöúùûüç',
            'aaaaaeeeeiiiiooooouuuuc'
        ),
        '\s+', ' ', 'g'
    );
$$;

create or replace function public.game_participant_from_session(p_token_hash text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_participant public.participants%rowtype;
begin
    select p.* into v_participant
    from public.participant_sessions s
    join public.participants p on p.id = s.participant_id
    where s.token_hash = p_token_hash
      and s.revoked_at is null
      and s.expires_at > now()
      and p.active = true
    limit 1;

    if v_participant.id is null then
        return jsonb_build_object('ok', false, 'error', 'invalid_session');
    end if;

    update public.participant_sessions
    set last_seen_at = now()
    where token_hash = p_token_hash
      and revoked_at is null
      and expires_at > now()
      and (last_seen_at is null or last_seen_at < now() - interval '5 minutes');

    return jsonb_build_object(
        'ok', true,
        'participant', jsonb_build_object(
            'id', v_participant.id,
            'full_name', v_participant.full_name,
            'nick', v_participant.nick,
            'participant_type', v_participant.participant_type,
            'registration', v_participant.registration,
            'course_class', v_participant.course_class,
            'institution', v_participant.institution,
            'active', v_participant.active
        )
    );
end;
$$;

create or replace function public.game_get_normal_activity(
    p_participant_id uuid,
    p_code text,
    p_activity_date date
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_qr public.qr_points%rowtype;
    v_run public.activity_runs%rowtype;
    v_question public.questions%rowtype;
begin
    select * into v_qr
    from public.qr_points
    where code = p_code and active = true
    limit 1;

    if v_qr.id is null then
        return jsonb_build_object('ok', false, 'error', 'invalid_qr');
    end if;

    if v_qr.kind <> 'normal' then
        return jsonb_build_object('ok', true, 'fallback', true, 'kind', v_qr.kind);
    end if;

    perform 1 from public.participants where id = p_participant_id and active = true for update;
    if not found then
        return jsonb_build_object('ok', false, 'error', 'participant_not_found');
    end if;

    select * into v_run
    from public.activity_runs
    where participant_id = p_participant_id
      and qr_point_id = v_qr.id
      and activity_date = p_activity_date
    limit 1;

    if v_run.id is not null then
        if v_run.question_id is not null then
            select * into v_question from public.questions where id = v_run.question_id;
        end if;

        return jsonb_build_object(
            'ok', true,
            'mode', 'normal',
            'qr', jsonb_build_object('code', v_qr.code, 'name', v_qr.name),
            'run_id', v_run.id,
            'status', v_run.status,
            'attempts', v_run.attempts_count,
            'points_awarded', v_run.points_awarded,
            'question', case when v_run.status = 'in_progress' then jsonb_build_object(
                'id', v_question.id,
                'kind', v_question.kind,
                'prompt', v_question.prompt,
                'options', v_question.options,
                'media_url', v_question.media_url,
                'media_type', v_question.media_type,
                'accessibility', v_question.accessibility,
                'difficulty', v_question.difficulty
            ) else null end
        );
    end if;

    select q.* into v_question
    from public.qr_question_pool qp
    join public.questions q on q.id = qp.question_id and q.active = true
    left join public.participant_question_history h
      on h.participant_id = p_participant_id and h.question_id = q.id
    where qp.qr_point_id = v_qr.id
      and h.id is null
    order by random()
    limit 1;

    if v_question.id is null then
        return jsonb_build_object('ok', false, 'error', 'no_unseen_question');
    end if;

    insert into public.participant_question_history (
        participant_id, question_id, source_qr_point_id
    ) values (
        p_participant_id, v_question.id, v_qr.id
    );

    insert into public.activity_runs (
        participant_id, qr_point_id, question_id, activity_date, status
    ) values (
        p_participant_id, v_qr.id, v_question.id, p_activity_date, 'in_progress'
    )
    returning * into v_run;

    return jsonb_build_object(
        'ok', true,
        'mode', 'normal',
        'qr', jsonb_build_object('code', v_qr.code, 'name', v_qr.name),
        'run_id', v_run.id,
        'status', v_run.status,
        'attempts', v_run.attempts_count,
        'points_awarded', v_run.points_awarded,
        'question', jsonb_build_object(
            'id', v_question.id,
            'kind', v_question.kind,
            'prompt', v_question.prompt,
            'options', v_question.options,
            'media_url', v_question.media_url,
            'media_type', v_question.media_type,
            'accessibility', v_question.accessibility,
            'difficulty', v_question.difficulty
        )
    );
end;
$$;

create or replace function public.game_answer_normal(
    p_participant_id uuid,
    p_run_id uuid,
    p_answer jsonb,
    p_activity_date date
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_run public.activity_runs%rowtype;
    v_question public.questions%rowtype;
    v_attempt smallint;
    v_correct boolean := false;
    v_points integer := 0;
    v_status text;
    v_completed integer := 0;
    v_milestones jsonb := '[]'::jsonb;
    v_rows integer;
    v_answer_text text;
begin
    select * into v_run
    from public.activity_runs
    where id = p_run_id and participant_id = p_participant_id
    for update;

    if v_run.id is null then
        return jsonb_build_object('ok', false, 'error', 'activity_not_found');
    end if;

    if v_run.status <> 'in_progress' then
        return jsonb_build_object('ok', false, 'error', 'already_finalized', 'status', v_run.status, 'points', v_run.points_awarded);
    end if;

    select * into v_question from public.questions where id = v_run.question_id;
    v_attempt := v_run.attempts_count + 1;

    if v_question.kind in ('multiple_choice', 'true_false', 'association', 'ordering') then
        v_correct := p_answer = (v_question.correct_answer -> 'value');
    elsif v_question.kind = 'short_text' then
        v_answer_text := public.game_normalize_text(p_answer #>> '{}');
        if jsonb_typeof(v_question.correct_answer -> 'accepted') = 'array' then
            select exists(
                select 1
                from jsonb_array_elements_text(v_question.correct_answer -> 'accepted') a(value)
                where public.game_normalize_text(a.value) = v_answer_text
            ) into v_correct;
        else
            v_correct := public.game_normalize_text(v_question.correct_answer ->> 'value') = v_answer_text;
        end if;
    end if;

    insert into public.attempts (
        participant_id, activity_run_id, question_id, attempt_number, answer, correct
    ) values (
        p_participant_id, p_run_id, v_question.id, v_attempt,
        jsonb_build_object('value', p_answer), v_correct
    );

    if v_correct then
        v_points := case v_attempt when 1 then 10 when 2 then 7 when 3 then 5 else 0 end;

        update public.activity_runs
        set status = 'completed', attempts_count = v_attempt,
            points_awarded = v_points, completed_at = now()
        where id = p_run_id;

        insert into public.point_ledger (
            participant_id, event_type, source_id, points, activity_date, dedupe_key, metadata
        ) values (
            p_participant_id, 'normal_activity', p_run_id, v_points,
            p_activity_date, 'activity:' || p_run_id::text, '{}'::jsonb
        ) on conflict (dedupe_key) do nothing;

        select count(*) into v_completed
        from public.activity_runs
        where participant_id = p_participant_id
          and activity_date = p_activity_date
          and status = 'completed';

        if v_completed >= 3 then
            insert into public.point_ledger (
                participant_id, event_type, source_id, points, activity_date, dedupe_key, metadata
            ) values (
                p_participant_id, 'milestone', null, 5, p_activity_date,
                'milestone:' || p_participant_id::text || ':' || p_activity_date::text || ':3',
                jsonb_build_object('threshold', 3)
            ) on conflict (dedupe_key) do nothing;
            get diagnostics v_rows = row_count;
            if v_rows > 0 then
                v_milestones := v_milestones || jsonb_build_array(jsonb_build_object('threshold', 3, 'points', 5));
            end if;
        end if;

        if v_completed >= 5 then
            insert into public.point_ledger (
                participant_id, event_type, source_id, points, activity_date, dedupe_key, metadata
            ) values (
                p_participant_id, 'milestone', null, 10, p_activity_date,
                'milestone:' || p_participant_id::text || ':' || p_activity_date::text || ':5',
                jsonb_build_object('threshold', 5)
            ) on conflict (dedupe_key) do nothing;
            get diagnostics v_rows = row_count;
            if v_rows > 0 then
                v_milestones := v_milestones || jsonb_build_array(jsonb_build_object('threshold', 5, 'points', 10));
            end if;
        end if;

        return jsonb_build_object('ok', true, 'correct', true, 'completed', true, 'points', v_points, 'milestones', v_milestones);
    end if;

    v_status := case when v_attempt >= 3 then 'failed' else 'in_progress' end;
    update public.activity_runs
    set status = v_status, attempts_count = v_attempt
    where id = p_run_id;

    return jsonb_build_object(
        'ok', true, 'correct', false, 'completed', v_status = 'failed',
        'attempts', v_attempt, 'remaining', greatest(0, 3 - v_attempt), 'points', 0
    );
end;
$$;

create or replace function public.game_ranking(p_limit integer default 100)
returns jsonb
language sql
security definer
set search_path = public
as $$
with totals as (
    select participant_id, sum(points)::integer as points
    from public.point_ledger group by participant_id
), normal_completed as (
    select participant_id, count(*)::integer as normal_completed
    from public.activity_runs where status = 'completed' group by participant_id
), category_events as (
    select ar.participant_id, q.category_id
    from public.activity_runs ar join public.questions q on q.id = ar.question_id
    where ar.status = 'completed'
    union all
    select br.participant_id, q.category_id
    from public.bonus_runs br join public.questions q on q.id = br.question_id
    where br.status = 'completed'
), category_diversity as (
    select participant_id, count(distinct category_id)::integer as category_diversity
    from category_events group by participant_id
), first_try as (
    select participant_id, count(*)::integer as first_try_correct
    from public.attempts where correct = true and attempt_number = 1 group by participant_id
), base as (
    select p.id, p.nick,
           coalesce(t.points, 0) as points,
           coalesce(n.normal_completed, 0) as normal_completed,
           coalesce(c.category_diversity, 0) as category_diversity,
           coalesce(f.first_try_correct, 0) as first_try_correct
    from public.participants p
    left join totals t on t.participant_id = p.id
    left join normal_completed n on n.participant_id = p.id
    left join category_diversity c on c.participant_id = p.id
    left join first_try f on f.participant_id = p.id
    where p.active = true and coalesce(t.points, 0) > 0
), ranked as (
    select rank() over (
        order by points desc, normal_completed desc,
                 category_diversity desc, first_try_correct desc
    )::integer as position,
    nick, points, normal_completed, category_diversity, first_try_correct
    from base
), limited as (
    select * from ranked
    order by position, lower(nick)
    limit greatest(1, least(coalesce(p_limit, 100), 500))
)
select coalesce(
    jsonb_agg(jsonb_build_object(
        'position', position,
        'nick', nick,
        'points', points,
        'normal_completed', normal_completed,
        'category_diversity', category_diversity,
        'first_try_correct', first_try_correct
    ) order by position, lower(nick)),
    '[]'::jsonb
)
from limited;
$$;

revoke all on function public.game_normalize_text(text) from public, anon, authenticated;
revoke all on function public.game_participant_from_session(text) from public, anon, authenticated;
revoke all on function public.game_get_normal_activity(uuid, text, date) from public, anon, authenticated;
revoke all on function public.game_answer_normal(uuid, uuid, jsonb, date) from public, anon, authenticated;
revoke all on function public.game_ranking(integer) from public, anon, authenticated;

grant execute on function public.game_normalize_text(text) to service_role;
grant execute on function public.game_participant_from_session(text) to service_role;
grant execute on function public.game_get_normal_activity(uuid, text, date) to service_role;
grant execute on function public.game_answer_normal(uuid, uuid, jsonb, date) to service_role;
grant execute on function public.game_ranking(integer) to service_role;
