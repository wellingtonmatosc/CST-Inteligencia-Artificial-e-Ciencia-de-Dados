(()=>{
  const REFRESH_MS=60000;
  let timer=null;

  function applyFinalRulesToForms(){
    const kind=document.querySelector('#questionKind');
    if(kind){
      kind.innerHTML='<option value="multiple_choice">Múltipla escolha — 4 alternativas</option>';
      kind.value='multiple_choice';
      kind.setAttribute('aria-describedby','questionKindRule');
      if(!document.querySelector('#questionKindRule')){
        const note=document.createElement('small');
        note.id='questionKindRule';
        note.className='muted';
        note.textContent='Regra do evento: o banco final utiliza somente múltipla escolha.';
        kind.insertAdjacentElement('afterend',note);
      }
    }

    const points=document.querySelector('#stationPoints');
    const type=document.querySelector('#stationType');
    if(points){
      points.value='10';
      points.readOnly=true;
      points.setAttribute('aria-describedby','stationPointsRule');
      if(!document.querySelector('#stationPointsRule')){
        const note=document.createElement('small');
        note.id='stationPointsRule';
        note.className='muted';
        note.textContent='Pontuação-base oficial: 10 pontos por QR, independentemente do tipo.';
        points.insertAdjacentElement('afterend',note);
      }
    }
    if(type){
      type.onchange=()=>{if(points)points.value='10'};
    }
  }

  function formatLocal(value){
    if(!value)return 'Horário indisponível';
    try{
      return new Intl.DateTimeFormat('pt-BR',{
        dateStyle:'short',timeStyle:'medium',timeZone:'America/Cuiaba'
      }).format(new Date(value));
    }catch(_){return String(value)}
  }

  function pointsText(row){
    const station=Number(row.station_points||0),challenge=Number(row.challenge_points||0);
    return `${station+challenge} pts`;
  }

  function ensureMonitoringCard(){
    const panel=document.querySelector('#overviewPanel');
    if(!panel)return null;
    let card=document.querySelector('#accessMonitoringCard');
    if(card)return card;
    card=document.createElement('section');
    card.id='accessMonitoringCard';
    card.className='card';
    card.innerHTML=`<div class="admin-section-head"><div><span class="eyebrow">Monitoramento</span><h2>Acessos aos QR Codes</h2><p class="muted">Os horários são registrados no fuso de Cuiabá. Atividades de madrugada são apenas sinalizadas para conferência; nenhuma pontuação é bloqueada automaticamente.</p></div><button type="button" class="secondary compact" id="refreshAccessMonitoring">Atualizar</button></div><div id="accessMonitoringSummary" class="admin-stat-grid"></div><div id="accessMonitoringList" class="admin-list"></div>`;
    panel.appendChild(card);
    card.querySelector('#refreshAccessMonitoring')?.addEventListener('click',refresh);
    return card;
  }

  function augmentParticipants(rows){
    const byId=new Map((rows||[]).map(row=>[String(row.id),row]));
    document.querySelectorAll('#participantList [data-active]').forEach(button=>{
      const id=button.dataset.active,row=byId.get(String(id));
      if(!row)return;
      const item=button.closest('.admin-list-item');
      if(!item||item.querySelector('.participant-academic'))return;
      const values=[row.campus,row.course_name].filter(Boolean);
      if(!values.length)return;
      const line=document.createElement('div');
      line.className='participant-academic muted';
      line.textContent=values.join(' • ');
      const first=item.querySelector('div');
      first?.appendChild(line);
    });
  }

  function render(data){
    const card=ensureMonitoringCard();
    if(!card)return;
    const activity=Array.isArray(data.recent_activity)?data.recent_activity:[];
    const unusual=activity.filter(row=>row.unusual_hour);
    const monitoring=data.monitoring||{};
    const summary=card.querySelector('#accessMonitoringSummary');
    const list=card.querySelector('#accessMonitoringList');

    summary.innerHTML=`<div class="admin-stat"><strong>${activity.length}</strong><span>acessos recentes exibidos</span></div><div class="admin-stat"><strong>${unusual.length}</strong><span>sinalizados entre ${esc(monitoring.unusual_window||'00:00–05:59')}</span></div><div class="admin-stat"><strong>0</strong><span>bloqueios automáticos</span></div>`;

    list.innerHTML=activity.length?activity.slice(0,20).map(row=>{
      const participant=row.participants||{},qr=row.qr_points||{};
      return `<div class="admin-list-item"><div><strong>${esc(participant.nick||participant.full_name||'Participante')}</strong> • ${esc(qr.code||'QR')}<br><span class="muted">${esc(qr.name||'')} • ${esc(formatLocal(row.validated_at))}</span>${row.unusual_hour?'<div class="notice warning"><strong>Horário incomum.</strong> Apenas sinalizado para conferência.</div>':''}</div><div><span class="pill">${esc(pointsText(row))}</span></div></div>`;
    }).join(''):'<div class="admin-empty">Nenhum acesso registrado ainda.</div>';

    augmentParticipants(data.participants);
  }

  async function refresh(){
    try{
      const response=await fetch('/api/admin/dashboard-data',{credentials:'include'});
      if(response.status===401||response.status===403)return;
      if(!response.ok)return;
      render(await response.json());
    }catch(_){}
  }

  function start(){
    applyFinalRulesToForms();
    refresh();
    clearInterval(timer);
    timer=setInterval(()=>{if(!document.hidden)refresh()},REFRESH_MS);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
    const observer=new MutationObserver(()=>{
      applyFinalRulesToForms();
      if(!document.querySelector('#dashboard.hidden'))refresh();
    });
    const dashboard=document.querySelector('#dashboard');
    if(dashboard)observer.observe(dashboard,{attributes:true,attributeFilter:['class'],subtree:true,childList:true});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
