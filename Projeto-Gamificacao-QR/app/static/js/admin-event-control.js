(()=>{
  let current=null;

  function hideTab(panelId){
    document.querySelector(`[data-admin-tab="${panelId}"]`)?.setAttribute('hidden','');
    const panel=document.querySelector(`#${panelId}`);if(panel)panel.hidden=true;
  }

  function cleanOperationalNoise(){
    document.querySelectorAll('#alertList .admin-alert').forEach(alert=>{
      const text=(alert.textContent||'').toLowerCase();
      if((text.includes('sem conteúdo')||text.includes('trilha sem etapas'))&&!alert.hidden)alert.hidden=true;
    });
    document.querySelectorAll('#stationList .pill').forEach(pill=>{
      if((pill.textContent||'').trim().toLowerCase()==='sem conteúdo'&&!pill.hidden)pill.hidden=true;
    });
    document.querySelectorAll('#trailList .muted').forEach(el=>{
      const text=el.textContent||'';
      if(/\d+\s*pts de conclusão/i.test(text))el.textContent=text.replace(/\d+\s*pts de conclusão/i,'sem bônus de pontos');
    });
  }

  function observeLegacyRenders(){
    ['alertList','stationList','trailList'].forEach(id=>{
      const host=document.querySelector(`#${id}`);if(!host)return;
      new MutationObserver(cleanOperationalNoise).observe(host,{childList:true,subtree:true,characterData:true});
    });
    cleanOperationalNoise();
  }

  function simplifyAdmin(){
    hideTab('pointsPanel');
    hideTab('settingsPanel');
    const stationsTab=document.querySelector('[data-admin-tab="stationsPanel"]');if(stationsTab)stationsTab.textContent='QRs';
    const trailsTab=document.querySelector('[data-admin-tab="trailsPanel"]');if(trailsTab)trailsTab.textContent='Trilhas (opcional)';
    const hero=document.querySelector('.admin-hero p');if(hero)hero.textContent='Controle dos testes e da competição individual de 1 a 7 dias.';

    const contentCard=document.querySelector('#contentForm')?.closest('details');if(contentCard)contentCard.hidden=true;
    const questionCreate=document.querySelector('#questionForm')?.closest('details');if(questionCreate)questionCreate.hidden=true;

    const stationCard=document.querySelector('#stationForm')?.closest('details');
    if(stationCard){stationCard.hidden=true;stationCard.open=false;const summary=stationCard.querySelector('summary');if(summary)summary.textContent='Editar QR selecionado'}
    const stationCode=document.querySelector('#stationCode');if(stationCode)stationCode.readOnly=true;
    ['stationType','stationPoints','activeFrom','activeUntil'].forEach(id=>{const el=document.querySelector(`#${id}`);const wrap=el?.closest('div');if(wrap)wrap.hidden=true});

    const trailPoints=document.querySelector('#trailCompletionPoints');
    if(trailPoints){trailPoints.value='0';trailPoints.readOnly=true;const label=document.querySelector('label[for="trailCompletionPoints"]');if(label)label.textContent='Bônus de conclusão (desativado)'}

    document.addEventListener('click',event=>{
      const edit=event.target.closest('[data-station-edit]');
      if(edit&&stationCard){stationCard.hidden=false;stationCard.open=true;setTimeout(()=>document.querySelector('#stationName')?.focus(),0)}
      if(event.target.closest('#stationCancelEdit')&&stationCard){stationCard.hidden=true;stationCard.open=false}
    });
    observeLegacyRenders();
  }

  function statusText(control){
    const labels={draft:'Não iniciado',testing:'Modo de teste',running:'Evento oficial em andamento',ended:'Encerrado'};
    return labels[control?.status]||'Carregando';
  }

  function readiness(r,duration){
    const min=Number(r?.min_eligible_questions_per_qr||0);
    const items=[
      [Number(r?.qrs_active||0)===15,`${Number(r?.qrs_active||0)}/15 QRs ativos`],
      [Number(r?.qrs_with_physical_code||0)===15,`${Number(r?.qrs_with_physical_code||0)}/15 códigos físicos`],
      [Number(r?.questions_active||0)>0,`${Number(r?.questions_active||0)} questões ativas`],
      [min>=duration,`mínimo de ${min} questões elegíveis por QR`],
    ];
    return `<div class="meta">${items.map(([ok,text])=>`<span class="pill">${ok?'✓':'!'} ${esc(text)}</span>`).join('')}</div>`;
  }

  function ensureCard(){
    let card=document.querySelector('#eventControlCard');if(card)return card;
    const host=document.querySelector('#overviewPanel');if(!host)return null;
    card=document.createElement('section');card.id='eventControlCard';card.className='card';host.prepend(card);return card;
  }

  function render(data){
    current=data;const card=ensureCard();if(!card)return;
    const c=data.control||{},r=data.readiness||{},duration=Number(c.duration_days||7),testDay=Number(c.test_day||1);
    const durationOptions=Array.from({length:7},(_,i)=>i+1).map(n=>`<option value="${n}"${n===duration?' selected':''}>${n} dia${n>1?'s':''}</option>`).join('');
    const dayOptions=Array.from({length:duration},(_,i)=>i+1).map(n=>`<option value="${n}"${n===testDay?' selected':''}>Dia ${n}</option>`).join('');
    card.innerHTML=`<div class="admin-section-head"><div><span class="eyebrow">Evento e homologação</span><h2>${esc(statusText(c))}</h2><p class="muted">O modo de teste usa o sistema real. O início oficial zera somente pontuação e interações de teste; cadastros dos participantes permanecem.</p></div><span class="pill">${esc(String(c.status||'draft'))}</span></div>
      <div class="grid two"><div><label for="eventDuration">Duração</label><select id="eventDuration">${durationOptions}</select></div><div><label for="eventTestDay">Dia simulado no teste</label><select id="eventTestDay">${dayOptions}</select></div></div>
      ${readiness(r,duration)}
      <div class="inline-actions" style="margin-top:1rem"><button type="button" id="startTesting">Iniciar/atualizar testes</button><button type="button" class="secondary" id="clearTesting">Limpar dados de teste</button><button type="button" id="startOfficial">Iniciar evento oficial</button><button type="button" class="secondary" id="endOfficial">Encerrar evento</button></div>
      <p class="muted">No evento oficial, o dia é calculado automaticamente em <strong>America/Cuiaba</strong> a partir do momento em que você clicar em iniciar.</p>`;

    const durationEl=card.querySelector('#eventDuration'),dayEl=card.querySelector('#eventTestDay');
    durationEl.onchange=()=>{const d=Number(durationEl.value);dayEl.innerHTML=Array.from({length:d},(_,i)=>`<option value="${i+1}">Dia ${i+1}</option>`).join('')};
    card.querySelector('#startTesting').onclick=async()=>{try{await api('/api/admin/event-control/testing',{method:'PUT',body:JSON.stringify({duration_days:Number(durationEl.value),test_day:Number(dayEl.value)})});await refresh()}catch(err){showMessage(document.querySelector('#message'),err.message,'error')}};
    card.querySelector('#clearTesting').onclick=async()=>{const confirmation=prompt('Para apagar pontuação e interações de TESTE, digite: LIMPAR TESTES');if(!confirmation)return;try{await api('/api/admin/event-control/clear-tests',{method:'POST',body:JSON.stringify({confirmation})});await refresh();location.reload()}catch(err){showMessage(document.querySelector('#message'),err.message,'error')}};
    card.querySelector('#startOfficial').onclick=async()=>{const confirmation=prompt('O início oficial apagará os resultados de teste e manterá os cadastros. Digite: INICIAR');if(!confirmation)return;try{await api('/api/admin/event-control/start',{method:'POST',body:JSON.stringify({duration_days:Number(durationEl.value),confirmation})});await refresh();location.reload()}catch(err){showMessage(document.querySelector('#message'),err.message,'error')}};
    card.querySelector('#endOfficial').onclick=async()=>{const confirmation=prompt('Para encerrar a competição, digite: ENCERRAR');if(!confirmation)return;try{await api('/api/admin/event-control/end',{method:'POST',body:JSON.stringify({confirmation})});await refresh()}catch(err){showMessage(document.querySelector('#message'),err.message,'error')}};
  }

  async function refresh(){
    try{const response=await fetch('/api/admin/event-control',{credentials:'include'});if(response.status===401||response.status===403)return;if(!response.ok)return;render(await response.json())}catch(_){}
  }

  function start(){simplifyAdmin();refresh()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
