-- Reinicializacao destrutiva autorizada: remove dados de homologacao/teste
-- e preserva a estrutura/configuracao final do evento.

truncate table
  public.station_attempts,
  public.station_visits,
  public.station_question_pool,
  public.final_tiebreak_results,
  public.trail_completions,
  public.trail_steps,
  public.station_contents,
  public.point_ledger,
  public.manual_point_actions,
  public.participant_sessions,
  public.participants,
  public.qr_points,
  public.questions,
  public.trails,
  public.audit_log,
  public.teams
restart identity cascade;

update public.event_days
set event_date = null,
    active = true,
    is_final_event = (day_number = 7),
    label = case
      when day_number = 7 then 'Dia 7 — Evento principal'
      else 'Dia ' || day_number::text
    end,
    updated_at = now();
