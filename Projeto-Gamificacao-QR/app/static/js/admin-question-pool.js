(()=>{
  const state={links:[],eventDays:[],stations:[],questions:[],categories:[]};
  let initialized=false;
  let loading=false;

  const byId=id=>document.getElementById(id);
  const message=()=>byId('message');
  const categoryName=id=>state.categories.find(x=>x.id===id)?.name||'Sem categoria';
  const stationName=id=>{const x=state.stations.find(s=>s.id===id);return x?`${x.code} — ${x.name}`:'Estação removida'};
  const questionName=id=>state.questions.find(q=>q.id===id)?.prompt||'Questão removida';
  const dayLabel=n=>n?state.eventDays.find(d=>Number(d.day_number)===Number(n))?.label||`Dia ${n}`:'Todos os dias';

  function injectUI(){
    if(initialized)return;
    const panel=byId('questionsPanel');
    if(!panel)return;
    const bank=panel.querySelector('section.card');

    const pool=document.createElement('details');
    pool.className='card form-card';
    pool.id='questionPoolCard';
    pool.open=true;
    pool.innerHTML=`<summary>Distribuir questões por estação e dia</summary>
      <p class="muted">Cada QR precisa ter um conjunto de questões. O sistema escolhe uma questão inédita para o participante, priorizando as menos usadas naquele QR/dia.</p>
      <form id="questionPoolForm" class="grid two">
        <div><label for="poolStation">Estação / QR Code</label><select id="poolStation" required></select></div>
        <div><label for="poolDay">Disponibilidade</label><select id="poolDay"><option value="">Todos os dias</option></select></div>
        <div style="grid-column:1/-1"><label for="poolQuestion">Questão</label><select id="poolQuestion" required></select></div>
        <div style="grid-column:1/-1"><button type="submit">Adicionar ao banco da estação</button></div>
      </form>
      <div id="questionPoolList" class="admin-list" aria-live="polite"></div>`;

    const calendar=document.createElement('details');
    calendar.className='card form-card';
    calendar.id='eventDaysCard';
    calendar.innerHTML=`<summary>Calendário da gamificação — 7 dias</summary>
      <p class="muted">Preencha as datas quando o período oficial for confirmado. A virada diária ocorre à 00:00 em America/Cuiaba. O Dia 7 é o evento principal.</p>
      <div id="eventDaysList" class="admin-list" aria-live="polite"></div>`;

    if(bank){panel.insertBefore(pool,bank);panel.insertBefore(calendar,bank)}else{panel.append(pool,calendar)}
    byId('questionPoolForm').addEventListener('submit',submitPoolLink);
    initialized=true;
  }

  function renderSelectors(){
    const station=byId('poolStation'),question=byId('poolQuestion'),day=byId('poolDay');
    if(!station||!question||!day)return;
    station.innerHTML=state.stations.filter(x=>x.active).map(x=>`<option value="${esc(x.id)}">${esc(x.code)} — ${esc(x.name)}</option>`).join('');
    question.innerHTML=state.questions.filter(x=>x.active).map(x=>`<option value="${esc(x.id)}">${esc(categoryName(x.category_id))} • nível ${Number(x.difficulty||1)} • ${esc(x.prompt)}</option>`).join('');
    day.innerHTML='<option value="">Todos os dias</option>'+state.eventDays.map(x=>`<option value="${Number(x.day_number)}">${esc(x.label)}${x.is_final_event?' — principal':''}</option>`).join('');
  }

  function renderPool(){
    const root=byId('questionPoolList');if(!root)return;
    if(!state.links.length){root.innerHTML='<div class="admin-empty">Nenhuma questão vinculada. As estações sem pool não podem ser validadas até receberem questões.</div>';return}
    const ordered=[...state.links].sort((a,b)=>stationName(a.qr_point_id).localeCompare(stationName(b.qr_point_id),'pt-BR')||(Number(a.day_number||0)-Number(b.day_number||0)));
    root.innerHTML=ordered.map(x=>`<div class="admin-list-item"><div><strong>${esc(stationName(x.qr_point_id))}</strong><br><span class="muted">${esc(dayLabel(x.day_number))}</span><br><span>${esc(questionName(x.question_id))}</span></div><div class="actions"><button type="button" class="secondary compact" data-pool-remove="${esc(x.id)}">Remover vínculo</button></div></div>`).join('');
    root.querySelectorAll('[data-pool-remove]').forEach(b=>b.addEventListener('click',()=>removePoolLink(b.dataset.poolRemove)));
  }

  function renderDays(){
    const root=byId('eventDaysList');if(!root)return;
    root.innerHTML=state.eventDays.map(d=>`<div class="admin-list-item"><div style="flex:1 1 100%"><strong>${esc(d.label)}${d.is_final_event?' • Evento principal':''}</strong><div class="grid two" style="margin-top:8px"><div><label for="eventLabel${Number(d.day_number)}">Nome do dia</label><input id="eventLabel${Number(d.day_number)}" value="${esc(d.label)}"></div><div><label for="eventDate${Number(d.day_number)}">Data</label><input id="eventDate${Number(d.day_number)}" type="date" value="${esc(d.event_date||'')}"></div></div><label class="switch-row" style="margin-top:8px"><input id="eventActive${Number(d.day_number)}" type="checkbox" ${d.active?'checked':''}><span>Dia ativo</span></label></div><div class="actions"><button type="button" class="secondary compact" data-day-save="${Number(d.day_number)}">Salvar dia</button></div></div>`).join('');
    root.querySelectorAll('[data-day-save]').forEach(b=>b.addEventListener('click',()=>saveEventDay(Number(b.dataset.daySave))));
  }

  async function loadPoolData(){
    if(loading)return;loading=true;
    try{
      const data=await api('/api/admin/question-pool');
      state.links=data.links||[];state.eventDays=data.event_days||[];state.stations=data.stations||[];state.questions=data.questions||[];state.categories=data.categories||[];
      renderSelectors();renderPool();renderDays();
    }catch(err){if(!String(err.message||'').includes('não autorizado'))showMessage(message(),err.message||'Não foi possível carregar o banco de questões.','error')}
    finally{loading=false}
  }

  async function submitPoolLink(event){
    event.preventDefault();
    const stationId=byId('poolStation').value,questionId=byId('poolQuestion').value,dayValue=byId('poolDay').value;
    if(!stationId||!questionId){showMessage(message(),'Selecione uma estação e uma questão.','error');return}
    try{await api('/api/admin/question-pool',{method:'POST',body:JSON.stringify({station_id:stationId,question_id:questionId,day_number:dayValue?Number(dayValue):null})});await loadPoolData();showMessage(message(),'Questão adicionada ao banco da estação.','success')}
    catch(err){showMessage(message(),err.message||'Não foi possível vincular a questão.','error')}
  }

  async function removePoolLink(id){
    try{await api(`/api/admin/question-pool/${encodeURIComponent(id)}`,{method:'DELETE'});await loadPoolData();showMessage(message(),'Vínculo removido. A questão original não foi excluída.','success')}
    catch(err){showMessage(message(),err.message||'Não foi possível remover o vínculo.','error')}
  }

  async function saveEventDay(dayNumber){
    const label=byId(`eventLabel${dayNumber}`).value.trim(),eventDate=byId(`eventDate${dayNumber}`).value||null,active=byId(`eventActive${dayNumber}`).checked;
    if(label.length<3){showMessage(message(),'Informe um nome para o dia.','error');return}
    try{await api(`/api/admin/event-days/${dayNumber}`,{method:'PUT',body:JSON.stringify({label,event_date:eventDate,active})});await loadPoolData();showMessage(message(),`Dia ${dayNumber} atualizado.`,'success')}
    catch(err){showMessage(message(),err.message||'Não foi possível atualizar o calendário.','error')}
  }

  function dashboardReady(){const dash=byId('dashboard');return dash&&!dash.classList.contains('hidden')}
  function start(){
    injectUI();if(dashboardReady())loadPoolData();const dash=byId('dashboard');
    if(dash)new MutationObserver(()=>{if(dashboardReady())loadPoolData()}).observe(dash,{attributes:true,attributeFilter:['class']});
    document.querySelectorAll('[data-admin-tab="questionsPanel"]').forEach(b=>b.addEventListener('click',()=>{if(dashboardReady())loadPoolData()}));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
