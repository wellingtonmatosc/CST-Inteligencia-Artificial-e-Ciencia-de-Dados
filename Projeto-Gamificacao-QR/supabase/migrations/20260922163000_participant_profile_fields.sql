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
      'active',v_p.active,
      'team_id',v_p.team_id,
      'team_revealed_at',v_p.team_revealed_at,
      'is_organizer',v_p.is_organizer,
      'has_password',true
    )
  );
end;
$$;
