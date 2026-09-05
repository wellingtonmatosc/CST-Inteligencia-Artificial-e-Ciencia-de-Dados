-- Projeto Gamificação QR — schema inicial
-- PostgreSQL / Supabase. Execute em um projeto dedicado.

create extension if not exists pgcrypto;

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

create table if not exists public.participants (
    id uuid primary key default gen_random_uuid(),
    full_name text not null,
    nick text not null,
    participant_type text not null check (participant_type in ('student','staff','external')),
    registration text,
    course_class text,
    institution text,
    access_code_hash char(64) not null unique,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (participant_type <> 'student' or (registration is not null and course_class is not null))
);

create unique index if not exists participants_nick_lower_uq on public.participants (lower(nick));
create unique index if not exists participants_registration_uq on public.participants (registration) where registration is not null;

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
    kind text not null check (kind in ('multiple_choice','true_false','short_text','association','ordering')),
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
create index if not exists questions_category_active_idx on public.questions(category_id, active);

create table if not exists public.qr_points (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    zone_id uuid not null references public.zones(id),
    kind text not null check (kind in ('normal','daily_bonus','dynamic_bonus')),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists qr_points_zone_kind_idx on public.qr_points(zone_id, kind, active);

create table if not exists public.qr_question_pool (
    qr_point_id uuid not null references public.qr_points(id) on delete cascade,
    question_id uuid not null references public.questions(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (qr_point_id, question_id)
);

create table if not exists public.bonus_campaigns (
    id uuid primary key default gen_random_uuid(),
    event_date date not null,
    bonus_type text not null check (bonus_type in ('daily_bonus','dynamic_bonus')),
    name text not null,
    points integer not null check (points >= 0),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (event_date, bonus_type)
);

create table if not exists public.bonus_locations (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid not null references public.bonus_campaigns(id) on delete cascade,
    qr_point_id uuid not null references public.qr_points(id),
    zone_id uuid not null references public.zones(id),
    starts_at timestamptz not null,
    ends_at timestamptz not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    check (ends_at > starts_at),
    unique (campaign_id, starts_at, zone_id)
);
create index if not exists bonus_locations_active_window_idx on public.bonus_locations(qr_point_id, starts_at, ends_at, active);

create table if not exists public.bonus_runs (
    id uuid primary key default gen_random_uuid(),
    participant_id uuid not null references public.participants(id) on delete cascade,
    campaign_id uuid not null references public.bonus_campaigns(id) on delete cascade,
    bonus_location_id uuid not null references public.bonus_locations(id),
    choice_category_ids jsonb not null default '[]'::jsonb,
    category_id uuid references public.categories(id),
    question_id uuid references public.questions(id),
    status text not null default 'choosing' check (status in ('choosing','in_progress','completed','failed','cancelled')),
    attempts_count smallint not null default 0 check (attempts_count between 0 and 3),
    points_awarded integer not null default 0 check (points_awarded >= 0),
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    unique (participant_id, campaign_id)
);
create index if not exists bonus_runs_participant_idx on public.bonus_runs(participant_id, status);

create table if not exists public.activity_runs (
    id uuid primary key default gen_random_uuid(),
    participant_id uuid not null references public.participants(id) on delete cascade,
    qr_point_id uuid not null references public.qr_points(id),
    question_id uuid not null references public.questions(id),
    activity_date date not null,
    status text not null default 'in_progress' check (status in ('in_progress','completed','failed','cancelled')),
    attempts_count smallint not null default 0 check (attempts_count between 0 and 3),
    points_awarded integer not null default 0 check (points_awarded >= 0),
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    unique (participant_id, qr_point_id, activity_date)
);
create index if not exists activity_runs_participant_date_idx on public.activity_runs(participant_id, activity_date, status);

create table if not exists public.attempts (
    id uuid primary key default gen_random_uuid(),
    participant_id uuid not null references public.participants(id) on delete cascade,
    activity_run_id uuid references public.activity_runs(id) on delete cascade,
    bonus_run_id uuid references public.bonus_runs(id) on delete cascade,
    question_id uuid not null references public.questions(id),
    attempt_number smallint not null check (attempt_number between 1 and 3),
    answer jsonb not null,
    correct boolean not null,
    answered_at timestamptz not null default now(),
    check ((activity_run_id is not null)::int + (bonus_run_id is not null)::int = 1)
);
create index if not exists attempts_participant_idx on public.attempts(participant_id, answered_at);
create index if not exists attempts_question_idx on public.attempts(question_id, correct);

create table if not exists public.participant_question_history (
    id uuid primary key default gen_random_uuid(),
    participant_id uuid not null references public.participants(id) on delete cascade,
    question_id uuid not null references public.questions(id) on delete cascade,
    source_qr_point_id uuid references public.qr_points(id),
    source_bonus_run_id uuid references public.bonus_runs(id) on delete cascade,
    first_seen_at timestamptz not null default now(),
    unique (participant_id, question_id)
);
create index if not exists participant_question_history_participant_idx on public.participant_question_history(participant_id);

create table if not exists public.point_ledger (
    id uuid primary key default gen_random_uuid(),
    participant_id uuid not null references public.participants(id) on delete cascade,
    event_type text not null check (event_type in ('normal_activity','milestone','daily_bonus','dynamic_bonus','admin_adjustment')),
    source_id uuid,
    points integer not null,
    activity_date date not null,
    dedupe_key text not null unique,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);
create index if not exists point_ledger_participant_idx on public.point_ledger(participant_id, activity_date);

-- Todas as tabelas do Data API ficam com RLS ativo. O navegador não acessa o Supabase diretamente.
alter table public.categories enable row level security;
alter table public.zones enable row level security;
alter table public.blocked_terms enable row level security;
alter table public.participants enable row level security;
alter table public.participant_sessions enable row level security;
alter table public.questions enable row level security;
alter table public.qr_points enable row level security;
alter table public.qr_question_pool enable row level security;
alter table public.bonus_campaigns enable row level security;
alter table public.bonus_locations enable row level security;
alter table public.bonus_runs enable row level security;
alter table public.activity_runs enable row level security;
alter table public.attempts enable row level security;
alter table public.participant_question_history enable row level security;
alter table public.point_ledger enable row level security;

-- Defesa em profundidade: sem acesso direto de anon/authenticated.
revoke all on public.categories, public.zones, public.blocked_terms, public.participants,
    public.participant_sessions, public.questions, public.qr_points, public.qr_question_pool,
    public.bonus_campaigns, public.bonus_locations, public.bonus_runs, public.activity_runs,
    public.attempts, public.participant_question_history, public.point_ledger
from anon, authenticated;

grant usage on schema public to service_role;
grant all privileges on public.categories, public.zones, public.blocked_terms, public.participants,
    public.participant_sessions, public.questions, public.qr_points, public.qr_question_pool,
    public.bonus_campaigns, public.bonus_locations, public.bonus_runs, public.activity_runs,
    public.attempts, public.participant_question_history, public.point_ledger
to service_role;

alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public grant all on tables to service_role;
