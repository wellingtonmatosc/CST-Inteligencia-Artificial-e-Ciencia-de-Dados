-- Regras de pontuação das atividades normais.
-- Verdadeiro/Falso: 1 tentativa; 10 pontos se acertar, 2 pontos por participação se errar.
-- Demais tipos: até 2 tentativas; 10 pontos na 1ª, 6 na 2ª; 2 pontos por participação se errar as duas.
-- Pontuação por participação não conta como atividade concluída para marcos de progresso.

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
    v_max_attempts smallint;
    v_correct boolean := false;
    v_points integer := 0;
    v_status text;
    v_completed integer := 0;
    v_milestones jsonb := '[]'::jsonb;
    v_rows integer;
    v_answer_text text;
    v_participation boolean := false;
begin
    select * into v_run
    from public.activity_runs
    where id = p_run_id
      and participant_id = p_participant_id
    for update;

    if v_run.id is null then
        return jsonb_build_object('ok', false, 'error', 'activity_not_found');
    end if;

    if v_run.status <> 'in_progress' then
        return jsonb_build_object(
            'ok', false,
            'error', 'already_finalized',
            'status', v_run.status,
            'points', v_run.points_awarded
        );
    end if;

    select * into v_question
    from public.questions
    where id = v_run.question_id;

    v_max_attempts := case when v_question.kind = 'true_false' then 1 else 2 end;
    v_attempt := v_run.attempts_count + 1;

    if v_attempt > v_max_attempts then
        return jsonb_build_object(
            'ok', false,
            'error', 'already_finalized',
            'status', v_run.status,
            'points', v_run.points_awarded
        );
    end if;

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
        participant_id,
        activity_run_id,
        question_id,
        attempt_number,
        answer,
        correct
    ) values (
        p_participant_id,
        p_run_id,
        v_question.id,
        v_attempt,
        jsonb_build_object('value', p_answer),
        v_correct
    );

    if v_correct then
        v_points := case v_attempt when 1 then 10 when 2 then 6 else 0 end;

        update public.activity_runs
        set status = 'completed',
            attempts_count = v_attempt,
            points_awarded = v_points,
            completed_at = now()
        where id = p_run_id;

        insert into public.point_ledger (
            participant_id,
            event_type,
            source_id,
            points,
            activity_date,
            dedupe_key,
            metadata
        ) values (
            p_participant_id,
            'normal_activity',
            p_run_id,
            v_points,
            p_activity_date,
            'activity:' || p_run_id::text,
            jsonb_build_object('participation_only', false)
        ) on conflict (dedupe_key) do nothing;

        select count(*) into v_completed
        from public.activity_runs
        where participant_id = p_participant_id
          and activity_date = p_activity_date
          and status = 'completed';

        if v_completed >= 3 then
            insert into public.point_ledger (
                participant_id,
                event_type,
                source_id,
                points,
                activity_date,
                dedupe_key,
                metadata
            ) values (
                p_participant_id,
                'milestone',
                null,
                5,
                p_activity_date,
                'milestone:' || p_participant_id::text || ':' || p_activity_date::text || ':3',
                jsonb_build_object('threshold', 3)
            ) on conflict (dedupe_key) do nothing;

            get diagnostics v_rows = row_count;
            if v_rows > 0 then
                v_milestones := v_milestones || jsonb_build_array(
                    jsonb_build_object('threshold', 3, 'points', 5)
                );
            end if;
        end if;

        if v_completed >= 5 then
            insert into public.point_ledger (
                participant_id,
                event_type,
                source_id,
                points,
                activity_date,
                dedupe_key,
                metadata
            ) values (
                p_participant_id,
                'milestone',
                null,
                10,
                p_activity_date,
                'milestone:' || p_participant_id::text || ':' || p_activity_date::text || ':5',
                jsonb_build_object('threshold', 5)
            ) on conflict (dedupe_key) do nothing;

            get diagnostics v_rows = row_count;
            if v_rows > 0 then
                v_milestones := v_milestones || jsonb_build_array(
                    jsonb_build_object('threshold', 5, 'points', 10)
                );
            end if;
        end if;

        return jsonb_build_object(
            'ok', true,
            'correct', true,
            'completed', true,
            'points', v_points,
            'attempts', v_attempt,
            'remaining', 0,
            'max_attempts', v_max_attempts,
            'participation', false,
            'milestones', v_milestones
        );
    end if;

    if v_attempt >= v_max_attempts then
        v_status := 'failed';
        v_points := 2;
        v_participation := true;

        update public.activity_runs
        set status = v_status,
            attempts_count = v_attempt,
            points_awarded = v_points,
            completed_at = now()
        where id = p_run_id;

        insert into public.point_ledger (
            participant_id,
            event_type,
            source_id,
            points,
            activity_date,
            dedupe_key,
            metadata
        ) values (
            p_participant_id,
            'normal_activity',
            p_run_id,
            v_points,
            p_activity_date,
            'activity:' || p_run_id::text,
            jsonb_build_object('participation_only', true)
        ) on conflict (dedupe_key) do nothing;
    else
        v_status := 'in_progress';

        update public.activity_runs
        set status = v_status,
            attempts_count = v_attempt
        where id = p_run_id;
    end if;

    return jsonb_build_object(
        'ok', true,
        'correct', false,
        'completed', v_status = 'failed',
        'attempts', v_attempt,
        'remaining', greatest(0, v_max_attempts - v_attempt),
        'max_attempts', v_max_attempts,
        'points', v_points,
        'participation', v_participation
    );
end;
$$;
