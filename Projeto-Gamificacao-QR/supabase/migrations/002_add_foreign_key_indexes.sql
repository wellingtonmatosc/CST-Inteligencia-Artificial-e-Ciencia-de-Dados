-- Índices adicionais recomendados pelo Supabase Database Advisor.
-- Mantêm as chaves estrangeiras usadas pelas rotinas de gamificação cobertas.

create index if not exists activity_runs_qr_point_idx
    on public.activity_runs(qr_point_id);

create index if not exists activity_runs_question_idx
    on public.activity_runs(question_id);

create index if not exists attempts_activity_run_idx
    on public.attempts(activity_run_id)
    where activity_run_id is not null;

create index if not exists attempts_bonus_run_idx
    on public.attempts(bonus_run_id)
    where bonus_run_id is not null;

create index if not exists bonus_locations_zone_idx
    on public.bonus_locations(zone_id);

create index if not exists bonus_runs_bonus_location_idx
    on public.bonus_runs(bonus_location_id);

create index if not exists bonus_runs_campaign_idx
    on public.bonus_runs(campaign_id);

create index if not exists bonus_runs_category_idx
    on public.bonus_runs(category_id)
    where category_id is not null;

create index if not exists bonus_runs_question_idx
    on public.bonus_runs(question_id)
    where question_id is not null;

create index if not exists participant_question_history_question_idx
    on public.participant_question_history(question_id);

create index if not exists participant_question_history_source_bonus_idx
    on public.participant_question_history(source_bonus_run_id)
    where source_bonus_run_id is not null;

create index if not exists participant_question_history_source_qr_idx
    on public.participant_question_history(source_qr_point_id)
    where source_qr_point_id is not null;

create index if not exists qr_question_pool_question_idx
    on public.qr_question_pool(question_id);
