-- Trilhas Poéticas — competição individual
-- Aplicada em produção como migration Supabase 20260917153330.
-- Estruturas históricas de equipe permanecem para auditoria; novas pontuações são individuais.

update public.teams set active=false where active=true;
update public.participants
set team_id=null, team_revealed_at=null, updated_at=now()
where team_id is not null or team_revealed_at is not null;

create or replace function public.trilhas_assign_team(p_participant_id uuid)
returns uuid language sql security definer set search_path=public
as $$ select null::uuid; $$;

create or replace function public.trilhas_individual_ranking()
returns jsonb language sql security definer set search_path=public
as $$
with stats as (
  select p.id,p.nick,
    coalesce((select sum(pl.points)::int from public.point_ledger pl where pl.participant_id=p.id and pl.event_type in ('station_validation','challenge','trail_completion','manual_action','manual_reversal')),0) points,
    coalesce((select count(*)::int from public.trail_completions tc where tc.participant_id=p.id),0) trails_completed,
    coalesce((select count(*)::int from public.station_visits sv where sv.participant_id=p.id),0) stations_validated
  from public.participants p where p.active and not p.is_organizer
), active_stats as (
  select * from stats where points<>0 or trails_completed>0 or stations_validated>0
), ranked as (
  select s.*,rank() over(order by points desc,trails_completed desc,stations_validated desc)::int position
  from active_stats s
)
select coalesce(jsonb_agg(jsonb_build_object(
  'position',position,'id',id,'nick',nick,'points',points,
  'trails_completed',trails_completed,'stations_validated',stations_validated
) order by position,lower(nick),id),'[]'::jsonb) from ranked;
$$;

create or replace function public.trilhas_participant_summary(p_participant_id uuid)
returns jsonb language plpgsql security definer set search_path=public
as $$
declare v_p public.participants%rowtype; v_points int:=0; v_stations int:=0; v_trails int:=0; v_pending int:=0; v_active int:=0; v_rank jsonb; v_pos int;
begin
  select * into v_p from public.participants where id=p_participant_id;
  if v_p.id is null then return jsonb_build_object('ok',false,'error','participant_not_found'); end if;
  select coalesce(sum(points),0)::int into v_points from public.point_ledger where participant_id=p_participant_id and event_type in('station_validation','challenge','trail_completion','manual_action','manual_reversal');
  select count(*)::int into v_stations from public.station_visits where participant_id=p_participant_id;
  select count(*)::int into v_trails from public.trail_completions where participant_id=p_participant_id;
  select count(*)::int into v_pending from public.station_visits where participant_id=p_participant_id and status='validated';
  select count(*)::int into v_active from public.qr_points q where q.active and q.station_type in('temporary','special') and (q.active_from is null or now()>=q.active_from) and (q.active_until is null or now()<q.active_until);
  if not v_p.is_organizer then
    v_rank:=public.trilhas_individual_ranking();
    select nullif(item->>'position','')::int into v_pos from jsonb_array_elements(v_rank) e(item) where item->>'id'=v_p.id::text limit 1;
  end if;
  return jsonb_build_object('ok',true,'points',v_points,'stations_validated',v_stations,'trails_completed',v_trails,'pending_challenges',v_pending,'active_specials',v_active,'competitive',not v_p.is_organizer,'individual_position',v_pos);
end $$;

-- As funções de validação, pontos manuais e estorno foram atualizadas no banco para
-- registrar team_id NULL nas novas ações competitivas, preservando team_id histórico
-- em eventos anteriores. Consulte a migration aplicada no histórico Supabase.

revoke all on function public.trilhas_assign_team(uuid) from public,anon,authenticated;
revoke all on function public.trilhas_individual_ranking() from public,anon,authenticated;
revoke all on function public.trilhas_participant_summary(uuid) from public,anon,authenticated;
grant execute on function public.trilhas_assign_team(uuid) to service_role;
grant execute on function public.trilhas_individual_ranking() to service_role;
grant execute on function public.trilhas_participant_summary(uuid) to service_role;
