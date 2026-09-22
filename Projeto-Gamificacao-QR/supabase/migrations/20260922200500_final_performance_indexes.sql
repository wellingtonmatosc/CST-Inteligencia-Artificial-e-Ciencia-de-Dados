create index if not exists qr_points_zone_id_idx on public.qr_points(zone_id);
create index if not exists station_attempts_participant_id_idx on public.station_attempts(participant_id);
create index if not exists station_attempts_question_id_idx on public.station_attempts(question_id);
create index if not exists station_question_pool_day_number_idx on public.station_question_pool(day_number);
create index if not exists station_visits_assigned_event_day_idx on public.station_visits(assigned_event_day);
create index if not exists station_visits_question_id_idx on public.station_visits(question_id);
create index if not exists trail_completions_trail_id_idx on public.trail_completions(trail_id);
