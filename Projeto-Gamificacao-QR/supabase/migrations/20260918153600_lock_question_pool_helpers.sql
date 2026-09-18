-- Helpers internos: somente o backend com service role pode executá-los diretamente.
revoke all on function public.trilhas_current_event_day() from public, anon, authenticated;
revoke all on function public.trilhas_select_station_question(uuid,uuid) from public, anon, authenticated;
grant execute on function public.trilhas_current_event_day() to service_role;
grant execute on function public.trilhas_select_station_question(uuid,uuid) to service_role;
