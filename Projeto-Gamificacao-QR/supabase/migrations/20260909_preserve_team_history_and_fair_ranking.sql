-- Recomendações incorporadas após simulação com equipes de tamanhos e participação variáveis.
-- 1. Pontos/visitas/trilhas ficam vinculados à equipe do momento da conquista.
-- 2. Desativar ou transferir participante não move nem apaga pontuação histórica.
-- 3. Ranking prioriza média por participante que contribuiu; tamanho/ativação atual é informativo.
-- 4. Temporários/especiais recusam respostas fora da janela também no backend.
-- 5. Em trilhas, a etapa só é concluída após finalizar o desafio (acertando ou esgotando tentativas).

alter table public.station_visits add column if not exists team_id uuid references public.teams(id);
alter table public.trail_completions add column if not exists team_id uuid references public.teams(id);
alter table public.point_ledger add column if not exists team_id uuid references public.teams(id);
alter table public.manual_point_actions add column if not exists team_id uuid references public.teams(id);

create index if not exists station_visits_team_idx on public.station_visits(team_id,validated_at);
create index if not exists trail_completions_team_idx on public.trail_completions(team_id,completed_at);
create index if not exists point_ledger_team_idx on public.point_ledger(team_id,activity_date);
create index if not exists manual_point_actions_team_idx on public.manual_point_actions(team_id,approved_at desc);

update public.station_visits sv set team_id=p.team_id
from public.participants p
where sv.participant_id=p.id and sv.team_id is null and not p.is_organizer;

update public.trail_completions tc set team_id=p.team_id
from public.participants p
where tc.participant_id=p.id and tc.team_id is null and not p.is_organizer;

update public.point_ledger pl set team_id=p.team_id
from public.participants p
where pl.participant_id=p.id and pl.team_id is null and not p.is_organizer;

update public.manual_point_actions ma set team_id=p.team_id
from public.participants p
where ma.participant_id=p.id and ma.team_id is null and not p.is_organizer;

create or replace function public.trilhas_complete_trail_if_ready(
  p_participant_id uuid,
  p_qr_point_id uuid,
  p_team_id uuid,
  p_is_organizer boolean
)
returns integer
language plpgsql
security definer
set search_path to 'public'
as $$
declare
  v_s public.trail_steps%rowtype;
  v_t public.trails%rowtype;
  v_missing boolean;
  v_completion uuid;
  v_bonus integer:=0;
begin
  select * into v_s from public.trail_steps where qr_point_id=p_qr_point_id limit 1;
  if v_s.trail_id is null then return 0; end if;
  select * into v_t from public.trails where id=v_s.trail_id and active=true;
  if v_t.id is null then return 0; end if;

  select exists(
    select 1 from public.trail_steps ts
    where ts.trail_id=v_s.trail_id
      and not exists(
        select 1 from public.station_visits sv
        where sv.participant_id=p_participant_id
          and sv.qr_point_id=ts.qr_point_id
          and sv.status='completed'
      )
  ) into v_missing;
  if v_missing then return 0; end if;

  insert into public.trail_completions(participant_id,trail_id,team_id,points_awarded)
  values(p_participant_id,v_s.trail_id,p_team_id,case when p_is_organizer then 0 else v_t.completion_points end)
  on conflict(participant_id,trail_id) do nothing returning id into v_completion;

  if v_completion is not null and not p_is_organizer then
    v_bonus:=v_t.completion_points;
    insert into public.point_ledger(participant_id,team_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,p_team_id,'trail_completion',v_completion,v_bonus,
      (now() at time zone 'America/Cuiaba')::date,
      'trail:'||p_participant_id::text||':'||v_s.trail_id::text,
      jsonb_build_object('trail_id',v_s.trail_id,'trail_name',v_t.name))
    on conflict(dedupe_key) do nothing;
  end if;
  return v_bonus;
end $$;

create or replace function public.trilhas_team_ranking()
returns jsonb language sql security definer set search_path to 'public' as $$
with members as(
  select team_id,count(*)::int members
  from public.participants
  where active and not is_organizer and team_id is not null
  group by team_id
), current_activated as(
  select p.team_id,count(distinct p.id)::int activated
  from public.participants p
  where p.active and not p.is_organizer and p.team_id is not null
    and exists(select 1 from public.station_visits sv where sv.participant_id=p.id and sv.team_id=p.team_id)
  group by p.team_id
), contributors as(
  select team_id,count(distinct participant_id)::int contributors
  from public.point_ledger
  where team_id is not null and event_type in('station_validation','challenge','trail_completion','manual_action','manual_reversal')
  group by team_id
), points as(
  select team_id,coalesce(sum(points),0)::int points
  from public.point_ledger
  where team_id is not null and event_type in('station_validation','challenge','trail_completion','manual_action','manual_reversal')
  group by team_id
), trails as(
  select team_id,count(*)::int trails_completed from public.trail_completions where team_id is not null group by team_id
), stations as(
  select team_id,count(*)::int stations_validated from public.station_visits where team_id is not null group by team_id
), stats as(
  select t.id,t.slug,t.name,t.reference_name,t.description,
    coalesce(m.members,0) members,coalesce(a.activated,0) activated,coalesce(c.contributors,0) contributors,
    coalesce(p.points,0) points,coalesce(tr.trails_completed,0) trails_completed,coalesce(s.stations_validated,0) stations_validated
  from public.teams t
  left join members m on m.team_id=t.id
  left join current_activated a on a.team_id=t.id
  left join contributors c on c.team_id=t.id
  left join points p on p.team_id=t.id
  left join trails tr on tr.team_id=t.id
  left join stations s on s.team_id=t.id
  where t.active
), norm as(
  select *,
    case when members>0 then round(activated::numeric/members*100,1) else 0 end activation_rate,
    case when contributors>0 then round(points::numeric/contributors,1) else 0 end avg_points_active
  from stats
), flag as(
  select exists(select 1 from norm where points<>0 or contributors>0 or stations_validated>0 or trails_completed>0) started
), ranked as(
  select n.*,case when f.started then row_number() over(
    order by avg_points_active desc,points desc,trails_completed desc,stations_validated desc,name
  ) end position
  from norm n cross join flag f
)
select coalesce(jsonb_agg(jsonb_build_object(
  'position',position,'id',id,'slug',slug,'name',name,'reference_name',reference_name,'description',description,
  'points',points,'members',members,'activated',activated,'contributors',contributors,'activation_rate',activation_rate,
  'avg_points_active',avg_points_active,'trails_completed',trails_completed,'stations_validated',stations_validated
) order by case when position is null then 999999 else position end,name),'[]'::jsonb)
from ranked;
$$;

create or replace function public.trilhas_validate_station(p_participant_id uuid,p_code text,p_physical_code text)
returns jsonb language plpgsql security definer set search_path to 'public','extensions' as $$
declare
  v_p public.participants%rowtype; v_q public.qr_points%rowtype; v_c public.station_contents%rowtype;
  v_v public.station_visits%rowtype; v_s public.trail_steps%rowtype; v_team public.teams%rowtype;
  v_team_id uuid; v_points integer:=0; v_bonus integer:=0; v_missing boolean; v_status text;
begin
  select * into v_p from public.participants where id=p_participant_id and active=true for update;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select * into v_q from public.qr_points where upper(code)=upper(trim(p_code)) and active=true limit 1;
  if v_q.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  if v_q.active_from is not null and now()<v_q.active_from then return jsonb_build_object('ok',false,'error','not_started','starts_at',v_q.active_from); end if;
  if v_q.active_until is not null and now()>=v_q.active_until then return jsonb_build_object('ok',false,'error','expired','ends_at',v_q.active_until); end if;
  if v_q.validation_code_hash is not null and (p_physical_code is null or v_q.validation_code_hash<>encode(extensions.digest(upper(trim(p_physical_code)),'sha256'),'hex')) then
    return jsonb_build_object('ok',false,'error','invalid_physical_code');
  end if;

  select * into v_v from public.station_visits where participant_id=p_participant_id and qr_point_id=v_q.id limit 1;
  if v_v.id is not null then return jsonb_build_object('ok',true,'already_validated',true,'visit_id',v_v.id,'station_points',v_v.station_points,'challenge_points',v_v.challenge_points,'total_points',v_v.total_points,'status',v_v.status); end if;

  if v_q.station_type='sequential' then
    select * into v_s from public.trail_steps where qr_point_id=v_q.id;
    if v_s.trail_id is null then return jsonb_build_object('ok',false,'error','sequence_not_configured'); end if;
    select exists(
      select 1 from public.trail_steps prev
      where prev.trail_id=v_s.trail_id and prev.step_number<v_s.step_number
        and not exists(select 1 from public.station_visits sv where sv.participant_id=p_participant_id and sv.qr_point_id=prev.qr_point_id and sv.status='completed')
    ) into v_missing;
    if v_missing then return jsonb_build_object('ok',false,'error','sequence_locked','step',v_s.step_number); end if;
  end if;

  if not v_p.is_organizer then
    v_team_id:=coalesce(v_p.team_id,public.trilhas_assign_team(p_participant_id));
    v_points:=v_q.base_points;
  end if;
  select * into v_c from public.station_contents where qr_point_id=v_q.id;
  v_status:=case when v_c.challenge_question_id is null then 'completed' else 'validated' end;

  insert into public.station_visits(participant_id,team_id,qr_point_id,question_id,status,station_points,challenge_points,total_points,completed_at)
  values(p_participant_id,v_team_id,v_q.id,v_c.challenge_question_id,v_status,v_points,0,v_points,case when v_status='completed' then now() else null end)
  returning * into v_v;

  if v_points>0 then
    insert into public.point_ledger(participant_id,team_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,v_team_id,'station_validation',v_v.id,v_points,(now() at time zone 'America/Cuiaba')::date,
      'station:'||p_participant_id::text||':'||v_q.id::text,jsonb_build_object('qr_code',v_q.code,'station_type',v_q.station_type))
    on conflict(dedupe_key) do nothing;
  end if;

  if not v_p.is_organizer and v_p.team_revealed_at is null then
    update public.participants set team_revealed_at=now(),updated_at=now() where id=p_participant_id;
  end if;

  if v_q.station_type='sequential' and v_status='completed' then
    v_bonus:=public.trilhas_complete_trail_if_ready(p_participant_id,v_q.id,v_team_id,v_p.is_organizer);
  end if;

  if v_team_id is not null then select * into v_team from public.teams where id=v_team_id; end if;
  return jsonb_build_object('ok',true,'already_validated',false,'visit_id',v_v.id,'station_points',v_points,'trail_bonus',v_bonus,'status',v_v.status,
    'team',case when v_team.id is null then null else jsonb_build_object('id',v_team.id,'name',v_team.name,'reference_name',v_team.reference_name) end,
    'competitive',not v_p.is_organizer);
end $$;

create or replace function public.trilhas_answer_challenge(p_participant_id uuid,p_code text,p_answer text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare
  v_v public.station_visits%rowtype; v_q public.qr_points%rowtype; v_c public.station_contents%rowtype;
  v_quest public.questions%rowtype; v_p public.participants%rowtype;
  v_attempt smallint; v_max smallint; v_correct boolean:=false; v_points integer:=0; v_bonus integer:=0; v_text text; v_finished boolean:=false;
begin
  select * into v_q from public.qr_points where upper(code)=upper(trim(p_code)) and active=true limit 1;
  if v_q.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  if v_q.active_from is not null and now()<v_q.active_from then return jsonb_build_object('ok',false,'error','not_started','starts_at',v_q.active_from); end if;
  if v_q.active_until is not null and now()>=v_q.active_until then return jsonb_build_object('ok',false,'error','expired','ends_at',v_q.active_until); end if;

  select * into v_p from public.participants where id=p_participant_id and active=true;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select * into v_v from public.station_visits where participant_id=p_participant_id and qr_point_id=v_q.id for update;
  if v_v.id is null then return jsonb_build_object('ok',false,'error','station_not_validated'); end if;
  select * into v_c from public.station_contents where qr_point_id=v_q.id;
  if v_c.challenge_question_id is null then return jsonb_build_object('ok',false,'error','no_challenge'); end if;
  if v_v.status='completed' then return jsonb_build_object('ok',false,'error','already_completed','points',v_v.challenge_points); end if;
  select * into v_quest from public.questions where id=v_c.challenge_question_id and active=true;
  if v_quest.id is null then return jsonb_build_object('ok',false,'error','challenge_unavailable'); end if;

  v_max:=case when v_quest.kind='true_false' then 1 else 2 end;
  v_attempt:=v_v.attempts_count+1;
  if v_attempt>v_max then return jsonb_build_object('ok',false,'error','already_completed'); end if;

  if v_quest.kind in ('multiple_choice','true_false') then
    v_correct:=coalesce(p_answer,'')=coalesce(v_quest.correct_answer->>'value','');
  elsif v_quest.kind='short_text' then
    v_text:=public.trilhas_normalize_text(coalesce(p_answer,''));
    if jsonb_typeof(v_quest.correct_answer->'accepted')='array' then
      select exists(select 1 from jsonb_array_elements_text(v_quest.correct_answer->'accepted') a(value) where public.trilhas_normalize_text(a.value)=v_text) into v_correct;
    else
      v_correct:=public.trilhas_normalize_text(v_quest.correct_answer->>'value')=v_text;
    end if;
  end if;

  insert into public.station_attempts(station_visit_id,participant_id,question_id,attempt_number,answer,correct)
  values(v_v.id,p_participant_id,v_quest.id,v_attempt,jsonb_build_object('value',p_answer),v_correct);

  if v_correct then
    v_points:=case when v_p.is_organizer then 0 else v_c.challenge_points end;
    v_finished:=true;
    update public.station_visits set status='completed',attempts_count=v_attempt,challenge_points=v_points,total_points=station_points+v_points,completed_at=now() where id=v_v.id;
    if v_points>0 then
      insert into public.point_ledger(participant_id,team_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
      values(p_participant_id,v_v.team_id,'challenge',v_v.id,v_points,(now() at time zone 'America/Cuiaba')::date,
        'challenge:'||v_v.id::text,jsonb_build_object('qr_code',v_q.code,'question_id',v_quest.id))
      on conflict(dedupe_key) do nothing;
    end if;
  else
    v_finished:=v_attempt>=v_max;
    update public.station_visits set attempts_count=v_attempt,status=case when v_finished then 'completed' else status end,
      completed_at=case when v_finished then now() else completed_at end where id=v_v.id;
  end if;

  if v_finished and v_q.station_type='sequential' then
    v_bonus:=public.trilhas_complete_trail_if_ready(p_participant_id,v_q.id,v_v.team_id,v_p.is_organizer);
  end if;

  if v_correct then
    return jsonb_build_object('ok',true,'correct',true,'completed',true,'points',v_points,'trail_bonus',v_bonus,'attempts',v_attempt,'remaining',0,'max_attempts',v_max,'explanation',v_quest.explanation);
  end if;
  return jsonb_build_object('ok',true,'correct',false,'completed',v_finished,'points',0,'trail_bonus',v_bonus,'attempts',v_attempt,
    'remaining',greatest(0,v_max-v_attempt),'max_attempts',v_max,'explanation',case when v_finished then v_quest.explanation else null end);
end $$;

create or replace function public.trilhas_admin_grant_manual_points(p_participant_id uuid,p_action_type text,p_description text,p_evidence text,p_points integer,p_actor text,p_actor_role text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_id uuid; v_date date; v_p public.participants%rowtype; v_team_id uuid;
begin
  select * into v_p from public.participants where id=p_participant_id and active=true;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  if p_points<0 or p_points>200 then return jsonb_build_object('ok',false,'error','invalid_points'); end if;
  if not v_p.is_organizer then v_team_id:=coalesce(v_p.team_id,public.trilhas_assign_team(p_participant_id)); end if;

  insert into public.manual_point_actions(participant_id,team_id,action_type,description,evidence,points,approved_by)
  values(p_participant_id,v_team_id,p_action_type,trim(p_description),nullif(trim(coalesce(p_evidence,'')),''),p_points,p_actor)
  returning id into v_id;
  v_date:=(now() at time zone 'America/Cuiaba')::date;
  if p_points>0 and not v_p.is_organizer then
    insert into public.point_ledger(participant_id,team_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,v_team_id,'manual_action',v_id,p_points,v_date,'manual:'||v_id::text,jsonb_build_object('action_type',p_action_type,'approved_by',p_actor));
  end if;
  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,p_actor_role,'manual_points_granted','manual_point_action',v_id::text,jsonb_build_object('participant_id',p_participant_id,'team_id',v_team_id,'points',p_points,'action_type',p_action_type));
  return jsonb_build_object('ok',true,'id',v_id,'points',case when v_p.is_organizer then 0 else p_points end);
end $$;

create or replace function public.trilhas_admin_reverse_manual_points(p_action_id uuid,p_reason text,p_actor text,p_actor_role text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_a public.manual_point_actions%rowtype; v_date date;
begin
  select * into v_a from public.manual_point_actions where id=p_action_id for update;
  if v_a.id is null then return jsonb_build_object('ok',false,'error','action_not_found'); end if;
  if v_a.status='reversed' then return jsonb_build_object('ok',true,'already_reversed',true,'id',v_a.id); end if;
  update public.manual_point_actions set status='reversed',reversed_by=p_actor,reversed_at=now(),reversal_reason=trim(p_reason) where id=v_a.id;
  v_date:=(now() at time zone 'America/Cuiaba')::date;
  if v_a.points<>0 and v_a.team_id is not null then
    insert into public.point_ledger(participant_id,team_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(v_a.participant_id,v_a.team_id,'manual_reversal',v_a.id,-v_a.points,v_date,'manual-reversal:'||v_a.id::text,jsonb_build_object('reason',p_reason,'reversed_by',p_actor));
  end if;
  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,p_actor_role,'manual_points_reversed','manual_point_action',v_a.id::text,jsonb_build_object('participant_id',v_a.participant_id,'team_id',v_a.team_id,'points',v_a.points,'reason',p_reason));
  return jsonb_build_object('ok',true,'id',v_a.id,'reversed_points',v_a.points);
end $$;

revoke execute on function public.trilhas_complete_trail_if_ready(uuid,uuid,uuid,boolean) from public,anon,authenticated;
grant execute on function public.trilhas_complete_trail_if_ready(uuid,uuid,uuid,boolean) to service_role;
