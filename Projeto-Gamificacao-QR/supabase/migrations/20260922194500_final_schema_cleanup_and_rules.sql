-- Versao final: remove legado de equipes/cadastro antigo e endurece as regras da gamificacao.

create or replace function public.trilhas_complete_trail_if_ready(p_participant_id uuid,p_qr_point_id uuid,p_is_organizer boolean)
returns integer language plpgsql security definer set search_path to 'public' as $$
declare v_s public.trail_steps%rowtype; v_t public.trails%rowtype; v_missing boolean; v_completion uuid; v_bonus integer:=0;
begin
  select * into v_s from public.trail_steps where qr_point_id=p_qr_point_id limit 1;
  if v_s.trail_id is null then return 0; end if;
  select * into v_t from public.trails where id=v_s.trail_id and active=true;
  if v_t.id is null then return 0; end if;
  select exists(select 1 from public.trail_steps ts where ts.trail_id=v_s.trail_id and not exists(select 1 from public.station_visits sv where sv.participant_id=p_participant_id and sv.qr_point_id=ts.qr_point_id and sv.status='completed')) into v_missing;
  if v_missing then return 0; end if;
  insert into public.trail_completions(participant_id,trail_id,points_awarded)
  values(p_participant_id,v_s.trail_id,case when p_is_organizer then 0 else v_t.completion_points end)
  on conflict(participant_id,trail_id) do nothing returning id into v_completion;
  if v_completion is not null and not p_is_organizer then
    v_bonus:=v_t.completion_points;
    insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,'trail_completion',v_completion,v_bonus,(now() at time zone 'America/Cuiaba')::date,'trail:'||p_participant_id::text||':'||v_s.trail_id::text,jsonb_build_object('trail_id',v_s.trail_id,'trail_name',v_t.name))
    on conflict(dedupe_key) do nothing;
  end if;
  return v_bonus;
end $$;

create or replace function public.trilhas_select_station_question(p_participant_id uuid,p_qr_point_id uuid)
returns uuid language plpgsql security definer set search_path to 'public' as $$
declare v_day smallint; v_today date:=(now() at time zone 'America/Cuiaba')::date; v_question_id uuid;
begin
  v_day:=public.trilhas_current_event_day();
  select sqp.question_id into v_question_id
  from public.station_question_pool sqp join public.questions q on q.id=sqp.question_id and q.active=true
  where sqp.qr_point_id=p_qr_point_id and sqp.active=true
    and (sqp.day_number is null or (v_day is not null and sqp.day_number=v_day))
    and not exists(select 1 from public.station_visits pv where pv.participant_id=p_participant_id and pv.question_id=sqp.question_id)
  order by case when v_day is not null and sqp.day_number=v_day then 0 else 1 end,
    (select count(*) from public.station_visits pv join public.questions pq on pq.id=pv.question_id where pv.participant_id=p_participant_id and pq.difficulty=q.difficulty) asc,
    (select count(*) from public.station_visits dv where dv.qr_point_id=p_qr_point_id and dv.activity_date=v_today and dv.question_id=sqp.question_id) asc,
    md5(p_participant_id::text||':'||p_qr_point_id::text||':'||sqp.question_id::text||':'||v_today::text)
  limit 1;
  return v_question_id;
end $$;

create or replace function public.trilhas_validate_station(p_participant_id uuid,p_code text,p_physical_code text)
returns jsonb language plpgsql security definer set search_path to 'public','extensions' as $$
declare v_p public.participants%rowtype; v_q public.qr_points%rowtype; v_v public.station_visits%rowtype; v_s public.trail_steps%rowtype; v_points integer:=0; v_missing boolean; v_question_id uuid; v_event_day smallint; v_today date:=(now() at time zone 'America/Cuiaba')::date; v_has_pool boolean:=false;
begin
  select * into v_p from public.participants where id=p_participant_id and active=true for update;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select * into v_q from public.qr_points where upper(code)=upper(trim(p_code)) and active=true limit 1;
  if v_q.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  if v_q.active_from is not null and now()<v_q.active_from then return jsonb_build_object('ok',false,'error','not_started','starts_at',v_q.active_from); end if;
  if v_q.active_until is not null and now()>=v_q.active_until then return jsonb_build_object('ok',false,'error','expired','ends_at',v_q.active_until); end if;
  if v_q.validation_code_hash is not null and (p_physical_code is null or v_q.validation_code_hash<>encode(extensions.digest(upper(trim(p_physical_code)),'sha256'),'hex')) then return jsonb_build_object('ok',false,'error','invalid_physical_code'); end if;
  select * into v_v from public.station_visits where participant_id=p_participant_id and qr_point_id=v_q.id and activity_date=v_today limit 1;
  if v_v.id is not null then return jsonb_build_object('ok',true,'already_validated',true,'visit_id',v_v.id,'station_points',v_v.station_points,'challenge_points',v_v.challenge_points,'total_points',v_v.total_points,'status',v_v.status,'question_id',v_v.question_id,'event_day',v_v.assigned_event_day,'activity_date',v_v.activity_date); end if;
  if v_q.station_type='sequential' then
    select * into v_s from public.trail_steps where qr_point_id=v_q.id;
    if v_s.trail_id is null then return jsonb_build_object('ok',false,'error','sequence_not_configured'); end if;
    select exists(select 1 from public.trail_steps prev where prev.trail_id=v_s.trail_id and prev.step_number<v_s.step_number and not exists(select 1 from public.station_visits sv where sv.participant_id=p_participant_id and sv.qr_point_id=prev.qr_point_id and sv.status='completed')) into v_missing;
    if v_missing then return jsonb_build_object('ok',false,'error','sequence_locked','step',v_s.step_number); end if;
  end if;
  v_event_day:=public.trilhas_current_event_day();
  select exists(select 1 from public.station_question_pool sqp join public.questions q on q.id=sqp.question_id and q.active=true where sqp.qr_point_id=v_q.id and sqp.active=true and (sqp.day_number is null or (v_event_day is not null and sqp.day_number=v_event_day))) into v_has_pool;
  if not v_has_pool then return jsonb_build_object('ok',false,'error','question_pool_not_configured'); end if;
  perform pg_advisory_xact_lock(hashtext(v_q.id::text||':'||v_today::text)::bigint);
  v_question_id:=public.trilhas_select_station_question(p_participant_id,v_q.id);
  if v_question_id is null then return jsonb_build_object('ok',false,'error','question_pool_exhausted'); end if;
  if not v_p.is_organizer then v_points:=10; end if;
  insert into public.station_visits(participant_id,qr_point_id,question_id,assigned_event_day,activity_date,status,station_points,challenge_points,total_points)
  values(p_participant_id,v_q.id,v_question_id,v_event_day,v_today,'validated',v_points,0,v_points) returning * into v_v;
  if v_points>0 then
    insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,'station_validation',v_v.id,v_points,v_today,'station:'||v_v.id::text,jsonb_build_object('qr_code',v_q.code,'station_type',v_q.station_type,'question_id',v_question_id,'event_day',v_event_day,'activity_date',v_today)) on conflict(dedupe_key) do nothing;
  end if;
  return jsonb_build_object('ok',true,'already_validated',false,'visit_id',v_v.id,'station_points',v_points,'trail_bonus',0,'status',v_v.status,'competitive',not v_p.is_organizer,'question_id',v_question_id,'event_day',v_event_day,'activity_date',v_today);
end $$;

create or replace function public.trilhas_answer_challenge(p_participant_id uuid,p_code text,p_answer text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_v public.station_visits%rowtype; v_q public.qr_points%rowtype; v_quest public.questions%rowtype; v_p public.participants%rowtype; v_attempt smallint; v_correct boolean:=false; v_points integer:=0; v_bonus integer:=0; v_finished boolean:=false; v_today date:=(now() at time zone 'America/Cuiaba')::date;
begin
  select * into v_q from public.qr_points where upper(code)=upper(trim(p_code)) and active=true limit 1;
  if v_q.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  if v_q.active_from is not null and now()<v_q.active_from then return jsonb_build_object('ok',false,'error','not_started','starts_at',v_q.active_from); end if;
  if v_q.active_until is not null and now()>=v_q.active_until then return jsonb_build_object('ok',false,'error','expired','ends_at',v_q.active_until); end if;
  select * into v_p from public.participants where id=p_participant_id and active=true;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select * into v_v from public.station_visits where participant_id=p_participant_id and qr_point_id=v_q.id and status='validated' order by case when activity_date=v_today then 0 else 1 end,validated_at desc limit 1 for update;
  if v_v.id is null then return jsonb_build_object('ok',false,'error','station_not_validated'); end if;
  if v_v.question_id is null then return jsonb_build_object('ok',false,'error','no_challenge'); end if;
  select * into v_quest from public.questions where id=v_v.question_id and active=true;
  if v_quest.id is null or v_quest.kind<>'multiple_choice' then return jsonb_build_object('ok',false,'error','challenge_unavailable'); end if;
  v_attempt:=v_v.attempts_count+1;
  if v_attempt>2 then return jsonb_build_object('ok',false,'error','already_completed'); end if;
  v_correct:=coalesce(p_answer,'')=coalesce(v_quest.correct_answer->>'value','');
  insert into public.station_attempts(station_visit_id,participant_id,question_id,attempt_number,answer,correct) values(v_v.id,p_participant_id,v_quest.id,v_attempt,jsonb_build_object('value',p_answer),v_correct);
  if v_correct then
    v_points:=case when v_p.is_organizer then 0 when v_attempt=1 then 10 else 6 end; v_finished:=true;
    update public.station_visits set status='completed',attempts_count=v_attempt,challenge_points=v_points,total_points=station_points+v_points,completed_at=now() where id=v_v.id;
    if v_points>0 then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata) values(p_participant_id,'challenge',v_v.id,v_points,v_v.activity_date,'challenge:'||v_v.id::text,jsonb_build_object('qr_code',v_q.code,'question_id',v_quest.id,'event_day',v_v.assigned_event_day,'attempt',v_attempt)) on conflict(dedupe_key) do nothing; end if;
  else
    v_finished:=v_attempt>=2;
    update public.station_visits set attempts_count=v_attempt,status=case when v_finished then 'completed' else status end,completed_at=case when v_finished then now() else completed_at end where id=v_v.id;
  end if;
  if v_finished and v_q.station_type='sequential' then v_bonus:=public.trilhas_complete_trail_if_ready(p_participant_id,v_q.id,v_p.is_organizer); end if;
  if v_correct then return jsonb_build_object('ok',true,'correct',true,'completed',true,'points',v_points,'trail_bonus',v_bonus,'attempts',v_attempt,'remaining',0,'max_attempts',2,'explanation',v_quest.explanation); end if;
  return jsonb_build_object('ok',true,'correct',false,'completed',v_finished,'points',0,'trail_bonus',v_bonus,'attempts',v_attempt,'remaining',greatest(0,2-v_attempt),'max_attempts',2,'explanation',case when v_finished then v_quest.explanation else null end);
end $$;

create or replace function public.trilhas_admin_grant_manual_points(p_participant_id uuid,p_action_type text,p_description text,p_evidence text,p_points integer,p_actor text,p_actor_role text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_id uuid; v_date date; v_p public.participants%rowtype;
begin
  select * into v_p from public.participants where id=p_participant_id and active=true;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  if p_points<0 or p_points>200 then return jsonb_build_object('ok',false,'error','invalid_points'); end if;
  insert into public.manual_point_actions(participant_id,action_type,description,evidence,points,approved_by) values(p_participant_id,p_action_type,trim(p_description),nullif(trim(coalesce(p_evidence,'')),''),p_points,p_actor) returning id into v_id;
  v_date:=(now() at time zone 'America/Cuiaba')::date;
  if p_points>0 and not v_p.is_organizer then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata) values(p_participant_id,'manual_action',v_id,p_points,v_date,'manual:'||v_id::text,jsonb_build_object('action_type',p_action_type,'approved_by',p_actor)); end if;
  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata) values(p_actor,p_actor_role,'manual_points_granted','manual_point_action',v_id::text,jsonb_build_object('participant_id',p_participant_id,'points',p_points,'action_type',p_action_type));
  return jsonb_build_object('ok',true,'id',v_id,'points',case when v_p.is_organizer then 0 else p_points end);
end $$;

create or replace function public.trilhas_admin_reverse_manual_points(p_action_id uuid,p_reason text,p_actor text,p_actor_role text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_a public.manual_point_actions%rowtype; v_date date; v_had_ledger boolean:=false;
begin
  select * into v_a from public.manual_point_actions where id=p_action_id for update;
  if v_a.id is null then return jsonb_build_object('ok',false,'error','action_not_found'); end if;
  if v_a.status='reversed' then return jsonb_build_object('ok',true,'already_reversed',true,'id',v_a.id); end if;
  update public.manual_point_actions set status='reversed',reversed_by=p_actor,reversed_at=now(),reversal_reason=trim(p_reason) where id=v_a.id;
  select exists(select 1 from public.point_ledger pl where pl.event_type='manual_action' and pl.source_id=v_a.id) into v_had_ledger;
  v_date:=(now() at time zone 'America/Cuiaba')::date;
  if v_a.points<>0 and v_had_ledger then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata) values(v_a.participant_id,'manual_reversal',v_a.id,-v_a.points,v_date,'manual-reversal:'||v_a.id::text,jsonb_build_object('reason',p_reason,'reversed_by',p_actor)); end if;
  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata) values(p_actor,p_actor_role,'manual_points_reversed','manual_point_action',v_a.id::text,jsonb_build_object('participant_id',v_a.participant_id,'points',v_a.points,'reason',p_reason));
  return jsonb_build_object('ok',true,'id',v_a.id,'reversed_points',v_a.points);
end $$;

create or replace function public.trilhas_participant_from_session(p_token_hash text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_p public.participants%rowtype;
begin
  select p.* into v_p from public.participant_sessions s join public.participants p on p.id=s.participant_id where s.token_hash=p_token_hash and s.revoked_at is null and s.expires_at>now() and p.active=true limit 1;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','invalid_session'); end if;
  update public.participant_sessions set last_seen_at=now() where token_hash=p_token_hash and revoked_at is null and expires_at>now() and (last_seen_at is null or last_seen_at<now()-interval '5 minutes');
  return jsonb_build_object('ok',true,'participant',jsonb_build_object('id',v_p.id,'full_name',v_p.full_name,'nick',v_p.nick,'participant_type',v_p.participant_type,'campus',v_p.campus,'course_name',v_p.course_name,'avatar_key',v_p.avatar_key,'active',v_p.active,'is_organizer',v_p.is_organizer,'has_password',true));
end $$;

drop function if exists public.trilhas_assign_team(uuid);
drop function if exists public.trilhas_team_ranking();
drop function if exists public.trilhas_complete_trail_if_ready(uuid,uuid,uuid,boolean);

alter table public.manual_point_actions drop column if exists team_id;
alter table public.point_ledger drop column if exists team_id;
alter table public.station_visits drop column if exists team_id;
alter table public.trail_completions drop column if exists team_id;
alter table public.participants drop column if exists team_id;
alter table public.participants drop column if exists team_revealed_at;
drop table if exists public.teams;

alter table public.participants drop column if exists registration;
alter table public.participants drop column if exists course_class;
alter table public.participants drop column if exists institution;
alter table public.station_contents drop column if exists challenge_question_id;
alter table public.station_contents drop column if exists challenge_points;

alter table public.questions drop constraint if exists questions_kind_check;
alter table public.questions add constraint questions_kind_check check (kind='multiple_choice');
alter table public.questions add constraint questions_four_options_check check (jsonb_typeof(options)='array' and jsonb_array_length(options)=4);
alter table public.questions add constraint questions_correct_value_check check (jsonb_typeof(correct_answer)='object' and nullif(trim(correct_answer->>'value'),'') is not null);
alter table public.station_attempts drop constraint if exists station_attempts_attempt_number_check;
alter table public.station_attempts add constraint station_attempts_attempt_number_check check (attempt_number between 1 and 2);
alter table public.station_visits drop constraint if exists station_visits_attempts_count_check;
alter table public.station_visits add constraint station_visits_attempts_count_check check (attempts_count between 0 and 2);
alter table public.qr_points drop constraint if exists qr_points_base_points_check;
alter table public.qr_points alter column base_points set default 10;
alter table public.qr_points add constraint qr_points_base_points_check check (base_points=10);

revoke execute on function public.trilhas_complete_trail_if_ready(uuid,uuid,boolean) from public,anon,authenticated;
grant execute on function public.trilhas_complete_trail_if_ready(uuid,uuid,boolean) to service_role;
