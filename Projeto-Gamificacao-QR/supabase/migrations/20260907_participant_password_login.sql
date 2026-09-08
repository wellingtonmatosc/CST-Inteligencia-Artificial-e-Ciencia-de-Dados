-- Login de participantes por nick + senha.
-- O código de recuperação continua existindo apenas como contingência.

alter table public.participants
    add column if not exists password_hash text;

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
            'active', v_participant.active,
            'has_password', v_participant.password_hash is not null
        )
    );
end;
$$;
