-- Trilhas Poéticas — schema canônico
-- PostgreSQL / Supabase. Este arquivo representa SOMENTE o sistema novo.

create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.categories (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.zones (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.blocked_terms (
  id uuid primary key default gen_random_uuid(),
  term text not null unique,
  reason text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.teams (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  reference_name text not null,
  description text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.participants (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  nick text not null,
  participant_type text not null check (participant_type in ('student','staff','external')),
  registration text,
  course_class text,
  institution text,
  access_code_hash char(64) not null unique,
  password_hash text,
  pin_failed_attempts smallint not null default 0 check (pin_failed_attempts between 0 and 20),
  pin_locked_until timestamptz,
  team_id uuid references public.teams(id),
  team_revealed_at timestamptz,
  is_organizer boolean not null default false,
  activated_at timestamptz,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (participant_type <> 'student' or (registration is not null and course_class is not null))
);
create unique index if not exists participants_nick_lower_uq on public.participants(lower(nick));
create unique index if not exists participants_registration_uq on public.participants(registration) where registration is not null;
create index if not exists participants_team_idx on public.participants(team_id, active, is_organizer);

create table if not exists public.participant_sessions (
  id uuid primary key default gen_random_uuid(),
  participant_id uuid not null references public.participants(id) on delete cascade,
  token_hash char(64) not null unique,
  expires_at timestamptz not null,
  last_seen_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists participant_sessions_participant_idx on public.participant_sessions(participant_id);
create index if not exists participant_sessions_expires_idx on public.participant_sessions(expires_at);

create table if not exists public.questions (
  id uuid primary key default gen_random_uuid(),
  category_id uuid not null references public.categories(id),
  kind text not null check (kind in ('multiple_choice','true_false','short_text')),
  prompt text not null,
  options jsonb not null default '[]'::jsonb,
  correct_answer jsonb not null,
  explanation text,
  difficulty smallint not null default 1 check (difficulty between 1 and 5),
  media_type text check (media_type is null or media_type in ('image','audio','video')),
  media_url text,
  accessibility jsonb not null default '{}'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists questions_category_active_idx on public.questions(category_id,active);

create table if not exists public.qr_points (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  zone_id uuid not null references public.zones(id),
  station_type text not null default 'permanent' check (station_type in ('permanent','sequential','temporary','special')),
  base_points integer not null default 10 check (base_points between 0 and 1000),
  validation_code_hash char(64),
  active_from timestamptz,
  active_until timestamptz,
  location_hint text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (active_until is null or active_from is null or active_until > active_from)
);
create index if not exists qr_points_type_active_idx on public.qr_points(station_type,active);
create index if not exists qr_points_zone_active_idx on public.qr_points(zone_id,active);

create table if not exists public.trails (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text,
  completion_points integer not null default 30 check (completion_points between 0 and 500),
  completion_title text,
  completion_body text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.trail_steps (
  trail_id uuid not null references public.trails(id) on delete cascade,
  qr_point_id uuid not null references public.qr_points(id) on delete cascade,
  step_number integer not null check (step_number > 0),
  created_at timestamptz not null default now(),
  primary key (trail_id,qr_point_id),
  unique (trail_id,step_number),
  unique (qr_point_id)
);

create table if not exists public.station_contents (
  qr_point_id uuid primary key references public.qr_points(id) on delete cascade,
  content_kind text not null default 'mixed' check (content_kind in ('poetry','literature','art','culture','regional','mixed')),
  title text not null,
  body text,
  author_name text,
  media_type text check (media_type is null or media_type in ('image','audio','video')),
  media_url text,
  accessibility jsonb not null default '{}'::jsonb,
  challenge_question_id uuid references public.questions(id) on delete set null,
  challenge_points integer not null default 10 check (challenge_points between 0 and 20),
  completion_body text,
  updated_at timestamptz not null default now()
);

create table if not exists public.station_visits (
  id uuid primary key default gen_random_uuid(),
  participant_id uuid not null references public.participants(id) on delete cascade,
  qr_point_id uuid not null references public.qr_points(id) on delete cascade,
  question_id uuid references public.questions(id) on delete set null,
  status text not null default 'validated' check (status in ('validated','completed')),
  attempts_count smallint not null default 0 check (attempts_count between 0 and 3),
  station_points integer not null default 0 check (station_points >= 0),
  challenge_points integer not null default 0 check (challenge_points >= 0),
  total_points integer not null default 0 check (total_points >= 0),
  validated_at timestamptz not null default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (participant_id,qr_point_id)
);
create index if not exists station_visits_participant_idx on public.station_visits(participant_id,validated_at);
create index if not exists station_visits_qr_idx on public.station_visits(qr_point_id,validated_at);

create table if not exists public.station_attempts (
  id uuid primary key default gen_random_uuid(),
  station_visit_id uuid not null references public.station_visits(id) on delete cascade,
  participant_id uuid not null references public.participants(id) on delete cascade,
  question_id uuid not null references public.questions(id),
  attempt_number smallint not null check (attempt_number between 1 and 3),
  answer jsonb not null,
  correct boolean not null,
  answered_at timestamptz not null default now(),
  unique (station_visit_id,attempt_number)
);
create index if not exists station_attempts_participant_idx on public.station_attempts(participant_id,answered_at);

create table if not exists public.trail_completions (
  id uuid primary key default gen_random_uuid(),
  participant_id uuid not null references public.participants(id) on delete cascade,
  trail_id uuid not null references public.trails(id) on delete cascade,
  points_awarded integer not null default 0 check (points_awarded >= 0),
  completed_at timestamptz not null default now(),
  unique (participant_id,trail_id)
);

create table if not exists public.point_ledger (
  id uuid primary key default gen_random_uuid(),
  participant_id uuid not null references public.participants(id) on delete cascade,
  event_type text not null check (event_type in ('station_validation','challenge','trail_completion','manual_action','manual_reversal')),
  source_id uuid,
  points integer not null,
  activity_date date not null,
  dedupe_key text not null unique,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists point_ledger_participant_idx on public.point_ledger(participant_id,activity_date);

create table if not exists public.admin_users (
  id uuid primary key default gen_random_uuid(),
  username text not null,
  password_hash text not null,
  role text not null check (role in ('admin','operator','validator','viewer')),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists admin_users_username_lower_uq on public.admin_users(lower(username));

create table if not exists public.manual_point_actions (
  id uuid primary key default gen_random_uuid(),
  participant_id uuid not null references public.participants(id) on delete cascade,
  action_type text not null check (action_type in ('recitation','original_work','poem_suggestion','selected_suggestion','artistic_production','social_post','event_participation','other')),
  description text not null,
  evidence text,
  points integer not null check (points between 0 and 200),
  status text not null default 'approved' check (status in ('approved','reversed')),
  approved_by text not null,
  approved_at timestamptz not null default now(),
  reversed_by text,
  reversed_at timestamptz,
  reversal_reason text
);
create index if not exists manual_point_actions_participant_idx on public.manual_point_actions(participant_id,approved_at desc);

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  actor_username text not null,
  actor_role text not null,
  action text not null,
  entity_type text not null,
  entity_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists audit_log_created_idx on public.audit_log(created_at desc);
create index if not exists audit_log_entity_idx on public.audit_log(entity_type,entity_id);

create or replace function public.trilhas_normalize_text(p_value text)
returns text language sql immutable as $$
  select trim(regexp_replace(lower(translate(coalesce(p_value,''),
    'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
    'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC')), '\s+', ' ', 'g'));
$$;

create or replace function public.trilhas_assign_team(p_participant_id uuid)
returns uuid language plpgsql security definer set search_path to 'public' as $$
declare v_p public.participants%rowtype; v_team uuid;
begin
  select * into v_p from public.participants where id=p_participant_id for update;
  if v_p.id is null or v_p.is_organizer then return null; end if;
  if v_p.team_id is not null then return v_p.team_id; end if;
  select t.id into v_team from public.teams t where t.active=true
  order by
    (select count(*) from public.participants p2 where p2.team_id=t.id and p2.active and not p2.is_organizer and p2.participant_type=v_p.participant_type and coalesce(p2.course_class,'')=coalesce(v_p.course_class,'')),
    (select count(*) from public.participants p2 where p2.team_id=t.id and p2.active and not p2.is_organizer and p2.participant_type=v_p.participant_type),
    (select count(*) from public.participants p2 where p2.team_id=t.id and p2.active and not p2.is_organizer),
    t.slug
  limit 1;
  update public.participants set team_id=v_team,updated_at=now() where id=p_participant_id;
  return v_team;
end $$;

create or replace function public.trilhas_team_ranking()
returns jsonb language sql security definer set search_path to 'public' as $$
with members as(
  select team_id,count(*)::int members from public.participants where active and not is_organizer and team_id is not null group by team_id
), activated as(
  select p.team_id,count(distinct sv.participant_id)::int activated,count(distinct sv.id)::int stations_validated
  from public.participants p join public.station_visits sv on sv.participant_id=p.id
  where p.active and not p.is_organizer and p.team_id is not null group by p.team_id
), points as(
  select p.team_id,coalesce(sum(pl.points),0)::int points from public.participants p join public.point_ledger pl on pl.participant_id=p.id
  where p.active and not p.is_organizer and p.team_id is not null and pl.event_type in('station_validation','challenge','trail_completion','manual_action','manual_reversal') group by p.team_id
), trails as(
  select p.team_id,count(tc.id)::int trails_completed from public.participants p join public.trail_completions tc on tc.participant_id=p.id
  where p.active and not p.is_organizer and p.team_id is not null group by p.team_id
), stats as(
  select t.id,t.slug,t.name,t.reference_name,t.description,coalesce(m.members,0) members,coalesce(a.activated,0) activated,
         coalesce(p.points,0) points,coalesce(tr.trails_completed,0) trails_completed,coalesce(a.stations_validated,0) stations_validated
  from public.teams t left join members m on m.team_id=t.id left join activated a on a.team_id=t.id left join points p on p.team_id=t.id left join trails tr on tr.team_id=t.id where t.active
), norm as(
  select *,case when members>0 then round(activated::numeric/members*100,1) else 0 end activation_rate,
           case when activated>0 then round(points::numeric/activated,1) else 0 end avg_points_active from stats
), flag as(
  select exists(select 1 from norm where points<>0 or activated>0 or trails_completed>0) started
), ranked as(
  select n.*,case when f.started then row_number() over(order by points desc,activation_rate desc,avg_points_active desc,trails_completed desc,name) end position
  from norm n cross join flag f
)
select coalesce(jsonb_agg(jsonb_build_object('position',position,'id',id,'slug',slug,'name',name,'reference_name',reference_name,'description',description,
'points',points,'members',members,'activated',activated,'activation_rate',activation_rate,'avg_points_active',avg_points_active,'trails_completed',trails_completed,'stations_validated',stations_validated)
order by case when position is null then 999999 else position end,name),'[]'::jsonb) from ranked;
$$;

create or replace function public.trilhas_participant_summary(p_participant_id uuid)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_p public.participants%rowtype; v_team public.teams%rowtype; v_points int:=0; v_stations int:=0; v_trails int:=0; v_pending int:=0; v_active int:=0; v_rank jsonb; v_pos int;
begin
  select * into v_p from public.participants where id=p_participant_id;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select coalesce(sum(points),0)::int into v_points from public.point_ledger where participant_id=p_participant_id and event_type in('station_validation','challenge','trail_completion','manual_action','manual_reversal');
  select count(*)::int into v_stations from public.station_visits where participant_id=p_participant_id;
  select count(*)::int into v_trails from public.trail_completions where participant_id=p_participant_id;
  select count(*)::int into v_pending from public.station_visits where participant_id=p_participant_id and status='validated';
  select count(*)::int into v_active from public.qr_points q where q.active and q.station_type in('temporary','special') and (q.active_from is null or now()>=q.active_from) and (q.active_until is null or now()<q.active_until);
  if v_p.team_revealed_at is not null and v_p.team_id is not null then
    select * into v_team from public.teams where id=v_p.team_id; v_rank:=public.trilhas_team_ranking();
    select nullif(item->>'position','')::int into v_pos from jsonb_array_elements(v_rank) as e(item) where item->>'id'=v_team.id::text limit 1;
  end if;
  return jsonb_build_object('ok',true,'points',v_points,'stations_validated',v_stations,'trails_completed',v_trails,'pending_challenges',v_pending,'active_specials',v_active,
    'competitive',not v_p.is_organizer,'team_revealed',v_p.team_revealed_at is not null,'team_position',v_pos,
    'team',case when v_team.id is null then null else jsonb_build_object('id',v_team.id,'slug',v_team.slug,'name',v_team.name,'reference_name',v_team.reference_name,'description',v_team.description) end);
end $$;

create or replace function public.trilhas_participant_from_session(p_token_hash text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_p public.participants%rowtype;
begin
  select p.* into v_p from public.participant_sessions s join public.participants p on p.id=s.participant_id
  where s.token_hash=p_token_hash and s.revoked_at is null and s.expires_at>now() and p.active=true limit 1;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','invalid_session'); end if;
  update public.participant_sessions set last_seen_at=now() where token_hash=p_token_hash and revoked_at is null and expires_at>now() and (last_seen_at is null or last_seen_at<now()-interval '5 minutes');
  return jsonb_build_object('ok',true,'participant',jsonb_build_object('id',v_p.id,'full_name',v_p.full_name,'nick',v_p.nick,'participant_type',v_p.participant_type,
    'registration',v_p.registration,'course_class',v_p.course_class,'institution',v_p.institution,'active',v_p.active,'team_id',v_p.team_id,
    'team_revealed_at',v_p.team_revealed_at,'is_organizer',v_p.is_organizer,'activated_at',v_p.activated_at,'has_password',v_p.password_hash is not null));
end $$;

create or replace function public.trilhas_home_state_from_session(p_token_hash text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_session jsonb; v_participant jsonb; v_summary jsonb;
begin
  v_session:=public.trilhas_participant_from_session(p_token_hash);
  if not coalesce((v_session->>'ok')::boolean,false) then return v_session; end if;
  v_participant:=v_session->'participant'; v_summary:=public.trilhas_participant_summary((v_participant->>'id')::uuid);
  if not coalesce((v_summary->>'ok')::boolean,false) then return jsonb_build_object('ok',false,'error','summary_unavailable'); end if;
  return jsonb_build_object('ok',true,'participant',v_participant,'summary',v_summary-'ok');
end $$;

create or replace function public.trilhas_get_station(p_participant_id uuid,p_code text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_qr public.qr_points%rowtype; v_visit public.station_visits%rowtype; v_content public.station_contents%rowtype; v_question public.questions%rowtype;
  v_zone jsonb; v_trail jsonb; v_attempts jsonb:='[]'::jsonb; v_payload jsonb; v_available boolean:=true; v_reason text; v_challenge_status text:='none';
begin
  select * into v_qr from public.qr_points where lower(code)=lower(trim(p_code)) and active=true limit 1;
  if v_qr.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  if v_qr.active_from is not null and now()<v_qr.active_from then v_available:=false; v_reason:='not_started';
  elsif v_qr.active_until is not null and now()>=v_qr.active_until then v_available:=false; v_reason:='expired'; end if;
  select jsonb_build_object('id',z.id,'slug',z.slug,'name',z.name) into v_zone from public.zones z where z.id=v_qr.zone_id;
  select * into v_visit from public.station_visits where participant_id=p_participant_id and qr_point_id=v_qr.id limit 1;
  if v_qr.station_type='sequential' then
    select jsonb_build_object('id',t.id,'slug',t.slug,'name',t.name,'description',t.description,'completion_points',t.completion_points,
      'completion_title',t.completion_title,'completion_body',t.completion_body,'active',t.active,'step_number',ts.step_number,
      'step_count',(select count(*) from public.trail_steps x where x.trail_id=t.id),
      'completed',exists(select 1 from public.trail_completions tc where tc.participant_id=p_participant_id and tc.trail_id=t.id),
      'completion',(select jsonb_build_object('id',tc.id,'points_awarded',tc.points_awarded,'completed_at',tc.completed_at) from public.trail_completions tc where tc.participant_id=p_participant_id and tc.trail_id=t.id order by tc.completed_at desc limit 1))
    into v_trail from public.trail_steps ts join public.trails t on t.id=ts.trail_id where ts.qr_point_id=v_qr.id limit 1;
  end if;
  v_payload:=jsonb_build_object('ok',true,'mode','trail_station','qr',jsonb_build_object('id',v_qr.id,'code',v_qr.code,'name',v_qr.name,
    'station_type',v_qr.station_type,'base_points',v_qr.base_points,'location_hint',v_qr.location_hint,'zone',v_zone,'active_from',v_qr.active_from,'active_until',v_qr.active_until),
    'available',v_available,'availability_reason',v_reason,'validated',v_visit.id is not null,'requires_physical_code',v_qr.validation_code_hash is not null,'trail',v_trail);
  if v_visit.id is null then return v_payload; end if;
  select * into v_content from public.station_contents where qr_point_id=v_qr.id limit 1;
  if v_content.qr_point_id is not null and v_content.challenge_question_id is not null then select * into v_question from public.questions where id=v_content.challenge_question_id and active=true limit 1; end if;
  select coalesce(jsonb_agg(jsonb_build_object('attempt_number',sa.attempt_number,'correct',sa.correct,'answered_at',sa.answered_at) order by sa.attempt_number),'[]'::jsonb)
  into v_attempts from public.station_attempts sa where sa.station_visit_id=v_visit.id;
  if v_question.id is null then v_challenge_status:='none'; elsif v_visit.status<>'completed' then v_challenge_status:='pending'; elsif coalesce(v_visit.challenge_points,0)>0 then v_challenge_status:='correct'; elsif jsonb_array_length(v_attempts)>0 then v_challenge_status:='finished'; end if;
  return v_payload||jsonb_build_object('visit',to_jsonb(v_visit),'content',case when v_content.qr_point_id is not null then to_jsonb(v_content) else null end,
    'question',case when v_question.id is not null then jsonb_build_object('id',v_question.id,'kind',v_question.kind,'prompt',v_question.prompt,'options',v_question.options,
      'difficulty',v_question.difficulty,'media_type',v_question.media_type,'media_url',v_question.media_url,'accessibility',v_question.accessibility) else null end,
    'challenge_status',v_challenge_status,'attempts',v_attempts);
end $$;

create or replace function public.trilhas_validate_station(p_participant_id uuid,p_code text,p_physical_code text)
returns jsonb language plpgsql security definer set search_path to 'public','extensions' as $$
declare v_p public.participants%rowtype; v_q public.qr_points%rowtype; v_c public.station_contents%rowtype; v_v public.station_visits%rowtype;
  v_s public.trail_steps%rowtype; v_t public.trails%rowtype; v_team public.teams%rowtype; v_team_id uuid; v_points integer:=0; v_bonus integer:=0; v_completion uuid; v_missing boolean; v_status text;
begin
  select * into v_p from public.participants where id=p_participant_id and active=true for update;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select * into v_q from public.qr_points where upper(code)=upper(trim(p_code)) and active=true limit 1;
  if v_q.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  if v_q.active_from is not null and now()<v_q.active_from then return jsonb_build_object('ok',false,'error','not_started','starts_at',v_q.active_from); end if;
  if v_q.active_until is not null and now()>=v_q.active_until then return jsonb_build_object('ok',false,'error','expired','ends_at',v_q.active_until); end if;
  if v_q.validation_code_hash is not null and (p_physical_code is null or v_q.validation_code_hash<>encode(extensions.digest(upper(trim(p_physical_code)),'sha256'),'hex')) then return jsonb_build_object('ok',false,'error','invalid_physical_code'); end if;
  select * into v_v from public.station_visits where participant_id=p_participant_id and qr_point_id=v_q.id limit 1;
  if v_v.id is not null then return jsonb_build_object('ok',true,'already_validated',true,'visit_id',v_v.id,'station_points',v_v.station_points,'challenge_points',v_v.challenge_points,'total_points',v_v.total_points,'status',v_v.status); end if;
  if v_q.station_type='sequential' then
    select * into v_s from public.trail_steps where qr_point_id=v_q.id;
    if v_s.trail_id is null then return jsonb_build_object('ok',false,'error','sequence_not_configured'); end if;
    select exists(select 1 from public.trail_steps prev where prev.trail_id=v_s.trail_id and prev.step_number<v_s.step_number and not exists(select 1 from public.station_visits sv where sv.participant_id=p_participant_id and sv.qr_point_id=prev.qr_point_id)) into v_missing;
    if v_missing then return jsonb_build_object('ok',false,'error','sequence_locked','step',v_s.step_number); end if;
  end if;
  if not v_p.is_organizer then v_team_id:=coalesce(v_p.team_id,public.trilhas_assign_team(p_participant_id)); v_points:=v_q.base_points; end if;
  select * into v_c from public.station_contents where qr_point_id=v_q.id;
  v_status:=case when v_c.challenge_question_id is null then 'completed' else 'validated' end;
  insert into public.station_visits(participant_id,qr_point_id,question_id,status,station_points,challenge_points,total_points,completed_at)
  values(p_participant_id,v_q.id,v_c.challenge_question_id,v_status,v_points,0,v_points,case when v_status='completed' then now() else null end) returning * into v_v;
  if v_points>0 then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,'station_validation',v_v.id,v_points,(now() at time zone 'America/Cuiaba')::date,'station:'||p_participant_id::text||':'||v_q.id::text,jsonb_build_object('qr_code',v_q.code,'station_type',v_q.station_type)) on conflict(dedupe_key) do nothing; end if;
  if not v_p.is_organizer and v_p.team_revealed_at is null then update public.participants set team_revealed_at=now(),activated_at=coalesce(activated_at,now()),updated_at=now() where id=p_participant_id; end if;
  if v_q.station_type='sequential' and v_s.trail_id is not null then
    select * into v_t from public.trails where id=v_s.trail_id and active=true;
    select exists(select 1 from public.trail_steps ts where ts.trail_id=v_s.trail_id and not exists(select 1 from public.station_visits sv where sv.participant_id=p_participant_id and sv.qr_point_id=ts.qr_point_id)) into v_missing;
    if not v_missing then
      insert into public.trail_completions(participant_id,trail_id,points_awarded) values(p_participant_id,v_s.trail_id,case when v_p.is_organizer then 0 else v_t.completion_points end)
      on conflict(participant_id,trail_id) do nothing returning id into v_completion;
      if v_completion is not null and not v_p.is_organizer then v_bonus:=v_t.completion_points;
        insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
        values(p_participant_id,'trail_completion',v_completion,v_bonus,(now() at time zone 'America/Cuiaba')::date,'trail:'||p_participant_id::text||':'||v_s.trail_id::text,jsonb_build_object('trail_id',v_s.trail_id,'trail_name',v_t.name)) on conflict(dedupe_key) do nothing;
      end if;
    end if;
  end if;
  if v_team_id is not null then select * into v_team from public.teams where id=v_team_id; end if;
  return jsonb_build_object('ok',true,'already_validated',false,'visit_id',v_v.id,'station_points',v_points,'trail_bonus',v_bonus,'status',v_v.status,
    'team',case when v_team.id is null then null else jsonb_build_object('id',v_team.id,'name',v_team.name,'reference_name',v_team.reference_name) end,'competitive',not v_p.is_organizer);
end $$;

create or replace function public.trilhas_answer_challenge(p_participant_id uuid,p_code text,p_answer text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_v public.station_visits%rowtype; v_q public.qr_points%rowtype; v_c public.station_contents%rowtype; v_quest public.questions%rowtype; v_p public.participants%rowtype;
  v_attempt smallint; v_max smallint; v_correct boolean:=false; v_points integer:=0; v_text text;
begin
  select * into v_q from public.qr_points where upper(code)=upper(trim(p_code)) and active=true limit 1;
  if v_q.id is null then return jsonb_build_object('ok',false,'error','invalid_qr'); end if;
  select * into v_v from public.station_visits where participant_id=p_participant_id and qr_point_id=v_q.id for update;
  if v_v.id is null then return jsonb_build_object('ok',false,'error','station_not_validated'); end if;
  select * into v_c from public.station_contents where qr_point_id=v_q.id;
  if v_c.challenge_question_id is null then return jsonb_build_object('ok',false,'error','no_challenge'); end if;
  if v_v.status='completed' then return jsonb_build_object('ok',false,'error','already_completed','points',v_v.challenge_points); end if;
  select * into v_quest from public.questions where id=v_c.challenge_question_id and active=true;
  if v_quest.id is null then return jsonb_build_object('ok',false,'error','challenge_unavailable'); end if;
  select * into v_p from public.participants where id=p_participant_id;
  v_max:=case when v_quest.kind='true_false' then 1 else 2 end; v_attempt:=v_v.attempts_count+1;
  if v_attempt>v_max then return jsonb_build_object('ok',false,'error','already_completed'); end if;
  if v_quest.kind in ('multiple_choice','true_false') then v_correct:=coalesce(p_answer,'')=coalesce(v_quest.correct_answer->>'value','');
  elsif v_quest.kind='short_text' then v_text:=public.trilhas_normalize_text(coalesce(p_answer,''));
    if jsonb_typeof(v_quest.correct_answer->'accepted')='array' then select exists(select 1 from jsonb_array_elements_text(v_quest.correct_answer->'accepted') a(value) where public.trilhas_normalize_text(a.value)=v_text) into v_correct;
    else v_correct:=public.trilhas_normalize_text(v_quest.correct_answer->>'value')=v_text; end if;
  end if;
  insert into public.station_attempts(station_visit_id,participant_id,question_id,attempt_number,answer,correct) values(v_v.id,p_participant_id,v_quest.id,v_attempt,jsonb_build_object('value',p_answer),v_correct);
  if v_correct then v_points:=case when v_p.is_organizer then 0 else v_c.challenge_points end;
    update public.station_visits set status='completed',attempts_count=v_attempt,challenge_points=v_points,total_points=station_points+v_points,completed_at=now() where id=v_v.id;
    if v_points>0 then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
      values(p_participant_id,'challenge',v_v.id,v_points,(now() at time zone 'America/Cuiaba')::date,'challenge:'||v_v.id::text,jsonb_build_object('qr_code',v_q.code,'question_id',v_quest.id)) on conflict(dedupe_key) do nothing; end if;
    return jsonb_build_object('ok',true,'correct',true,'completed',true,'points',v_points,'attempts',v_attempt,'remaining',0,'max_attempts',v_max,'explanation',v_quest.explanation);
  end if;
  update public.station_visits set attempts_count=v_attempt,status=case when v_attempt>=v_max then 'completed' else status end,completed_at=case when v_attempt>=v_max then now() else completed_at end where id=v_v.id;
  return jsonb_build_object('ok',true,'correct',false,'completed',v_attempt>=v_max,'points',0,'attempts',v_attempt,'remaining',greatest(0,v_max-v_attempt),'max_attempts',v_max,'explanation',case when v_attempt>=v_max then v_quest.explanation else null end);
end $$;

create or replace function public.trilhas_admin_grant_manual_points(p_participant_id uuid,p_action_type text,p_description text,p_evidence text,p_points integer,p_actor text,p_actor_role text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_id uuid; v_date date;
begin
  if not exists(select 1 from public.participants where id=p_participant_id and active=true) then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  if p_points<0 or p_points>200 then return jsonb_build_object('ok',false,'error','invalid_points'); end if;
  insert into public.manual_point_actions(participant_id,action_type,description,evidence,points,approved_by)
  values(p_participant_id,p_action_type,trim(p_description),nullif(trim(coalesce(p_evidence,'')),''),p_points,p_actor) returning id into v_id;
  v_date:=(now() at time zone 'America/Cuiaba')::date;
  if p_points>0 then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(p_participant_id,'manual_action',v_id,p_points,v_date,'manual:'||v_id::text,jsonb_build_object('action_type',p_action_type,'approved_by',p_actor)); end if;
  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,p_actor_role,'manual_points_granted','manual_point_action',v_id::text,jsonb_build_object('participant_id',p_participant_id,'points',p_points,'action_type',p_action_type));
  return jsonb_build_object('ok',true,'id',v_id,'points',p_points);
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
  if v_a.points<>0 then insert into public.point_ledger(participant_id,event_type,source_id,points,activity_date,dedupe_key,metadata)
    values(v_a.participant_id,'manual_reversal',v_a.id,-v_a.points,v_date,'manual-reversal:'||v_a.id::text,jsonb_build_object('reason',p_reason,'reversed_by',p_actor)); end if;
  insert into public.audit_log(actor_username,actor_role,action,entity_type,entity_id,metadata)
  values(p_actor,p_actor_role,'manual_points_reversed','manual_point_action',v_a.id::text,jsonb_build_object('participant_id',v_a.participant_id,'points',v_a.points,'reason',p_reason));
  return jsonb_build_object('ok',true,'id',v_a.id,'reversed_points',v_a.points);
end $$;

-- Cinco equipes previstas no projeto.
insert into public.teams(slug,name,reference_name,description) values
('tarsila','Equipe Tarsila','Tarsila do Amaral','Identidade brasileira, experimentação e Modernismo.'),
('anita','Equipe Anita','Anita Malfatti','Ruptura, vanguarda e transformação artística.'),
('mario','Equipe Mário','Mário de Andrade','Literatura, pesquisa cultural e diversidade brasileira.'),
('oswald','Equipe Oswald','Oswald de Andrade','Antropofagia cultural, inovação e irreverência.'),
('pagu','Equipe Pagu','Patrícia Galvão','Expressão cultural, participação e contestação.')
on conflict(slug) do update set name=excluded.name,reference_name=excluded.reference_name,description=excluded.description,active=true;

-- RLS: somente o backend com service_role acessa o Data API.
do $$ declare r record; begin
  for r in select tablename from pg_tables where schemaname='public' and tablename in (
    'categories','zones','blocked_terms','teams','participants','participant_sessions','questions','qr_points','trails','trail_steps','station_contents','station_visits','station_attempts','trail_completions','point_ledger','admin_users','manual_point_actions','audit_log'
  ) loop execute format('alter table public.%I enable row level security',r.tablename); end loop;
end $$;

revoke all on public.categories,public.zones,public.blocked_terms,public.teams,public.participants,public.participant_sessions,public.questions,public.qr_points,
 public.trails,public.trail_steps,public.station_contents,public.station_visits,public.station_attempts,public.trail_completions,public.point_ledger,
 public.admin_users,public.manual_point_actions,public.audit_log from anon,authenticated;

grant usage on schema public to service_role;
grant all privileges on public.categories,public.zones,public.blocked_terms,public.teams,public.participants,public.participant_sessions,public.questions,public.qr_points,
 public.trails,public.trail_steps,public.station_contents,public.station_visits,public.station_attempts,public.trail_completions,public.point_ledger,
 public.admin_users,public.manual_point_actions,public.audit_log to service_role;

revoke execute on function public.trilhas_assign_team(uuid),public.trilhas_team_ranking(),public.trilhas_participant_summary(uuid),public.trilhas_participant_from_session(text),
 public.trilhas_home_state_from_session(text),public.trilhas_get_station(uuid,text),public.trilhas_validate_station(uuid,text,text),public.trilhas_answer_challenge(uuid,text,text),
 public.trilhas_admin_grant_manual_points(uuid,text,text,text,integer,text,text),public.trilhas_admin_reverse_manual_points(uuid,text,text,text),public.trilhas_normalize_text(text)
from public,anon,authenticated;

grant execute on function public.trilhas_assign_team(uuid),public.trilhas_team_ranking(),public.trilhas_participant_summary(uuid),public.trilhas_participant_from_session(text),
 public.trilhas_home_state_from_session(text),public.trilhas_get_station(uuid,text),public.trilhas_validate_station(uuid,text,text),public.trilhas_answer_challenge(uuid,text,text),
 public.trilhas_admin_grant_manual_points(uuid,text,text,text,integer,text,text),public.trilhas_admin_reverse_manual_points(uuid,text,text,text),public.trilhas_normalize_text(text)
to service_role;

alter default privileges in schema public revoke all on tables from anon,authenticated;
alter default privileges in schema public grant all on tables to service_role;
