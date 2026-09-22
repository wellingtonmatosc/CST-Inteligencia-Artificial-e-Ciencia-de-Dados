(()=>{
  const REFRESH_MS=60000;
  let timer=null;

  function ensureCard(){
    const panel=document.querySelector('#rankingPanel');
    if(!panel)return null;
    const legacyDescription=panel.querySelector('.admin-section-head .muted');
    if(legacyDescription)legacyDescription.textContent='Pontos acumulados; em empate, acertos, acertos na 1ª tentativa, QRs distintos e dias ativos. O Dia 7 é o último desempate.';
    let card=document.querySelector('#rankingRulesCard');
    if(card)return card;
    card=document.createElement('section');
    card.id='rankingRulesCard';
    card.className='card';
    card.innerHTML=`<div class="admin-section-head"><div><span class="eyebrow">Méritos e desempate</span><h2>Critérios competitivos</h2><p class="muted">Ordem: pontos, acertos, acertos na 1ª tentativa, QRs distintos, dias ativos e, somente se o empate persistir, resultado supervisionado do Dia 7. Velocidade não é usada.</p></div><button type="button" class="secondary compact" id="refreshRankingRules">Atualizar</button></div><div id="finalDayStatus" class="notice"></div><div id="rankingMeritList" class="admin-list"></div><div id="finalTiebreakArea"></div>`;
    panel.prepend(card);
    card.querySelector('#refreshRankingRules')?.addEventListener('click',refresh);
    return card;
  }

  function metricLine(row){
    return `${Number(row.correct_answers||0)} acertos • ${Number(row.first_try_correct||0)} na 1ª tentativa • ${Number(row.distinct_qrs||0)} QRs distintos • ${Number(row.active_days||0)}/7 dias • sequência máxima ${Number(row.best_correct_streak||0)}`;
  }

  function render(data){
    const card=ensureCard();
    if(!card)return;
    const ranking=Array.isArray(data.ranking)?data.ranking:[];
    const finalDay=data.final_day||null;
    const finalStatus=card.querySelector('#finalDayStatus');
    if(finalDay?.event_date){
      finalStatus.className='notice';
      finalStatus.innerHTML=`<strong>${esc(finalDay.label||'Dia 7')}</strong><br>Data configurada: ${esc(new Date(`${finalDay.event_date}T12:00:00`).toLocaleDateString('pt-BR'))}. O desempate final só deve ser usado quando os critérios anteriores permanecerem iguais.`;
    }else{
      finalStatus.className='notice warning';
      finalStatus.innerHTML='<strong>Dia 7 ainda sem data definida.</strong><br>A estrutura de desempate está pronta, mas a data do evento principal precisa ser configurada antes da homologação.';
    }

    const meritList=card.querySelector('#rankingMeritList');
    meritList.innerHTML=ranking.length?ranking.slice(0,20).map(row=>`<div class="admin-list-item"><div><strong>${Number(row.position)}º — ${esc(row.nick)}</strong><br><span class="muted">${esc(metricLine(row))}</span></div><div><span class="pill">${Number(row.points||0)} pts</span>${row.unresolved_tie?'<span class="pill">empate técnico</span>':row.final_tiebreak_resolved?'<span class="pill">desempate concluído</span>':''}</div></div>`).join(''):'<div class="admin-empty">Ranking ainda não iniciado.</div>';

    const tiebreakGroup=ranking.filter(row=>row.needs_final_tiebreak);
    const area=card.querySelector('#finalTiebreakArea');
    if(!tiebreakGroup.length){
      area.innerHTML='<div class="notice"><strong>Desempate final:</strong> nenhum grupo empatado no momento.</div>';
      return;
    }

    const unresolved=tiebreakGroup.some(row=>row.unresolved_tie);
    area.innerHTML=`<h3>Desempate supervisionado — Dia 7</h3><p class="muted">${unresolved?'Registre o resultado de todos os participantes do grupo. O ranking só aplicará as notas quando o grupo inteiro estiver preenchido.':'O grupo já possui resultado completo. As notas podem ser corrigidas abaixo com registro na auditoria.'} A nota não soma pontos; ela atua apenas como último critério de classificação.</p>${tiebreakGroup.map(row=>`<form class="admin-list-item final-tiebreak-form" data-participant="${esc(row.id)}"><div><strong>${esc(row.nick)}</strong><br><span class="muted">${esc(metricLine(row))}</span>${row.final_tiebreak_recorded?`<br><span class="pill">nota registrada: ${Number(row.final_tiebreak_score||0)}</span>`:'<br><span class="pill">nota pendente</span>'}<label>Observação <input name="note" maxlength="500" placeholder="Ex.: desafio final supervisionado"></label></div><div><label>Nota 0–100 <input name="score" type="number" min="0" max="100" value="${row.final_tiebreak_recorded?Number(row.final_tiebreak_score||0):''}" required></label><div class="actions"><button type="submit" class="compact">Salvar</button>${row.final_tiebreak_recorded?'<button type="button" class="secondary compact" data-clear-final>Limpar</button>':''}</div></div></form>`).join('')}`;

    area.querySelectorAll('.final-tiebreak-form').forEach(form=>{
      form.addEventListener('submit',async event=>{
        event.preventDefault();
        const button=form.querySelector('button[type="submit"]');
        const dataForm=new FormData(form);
        const payload={score:Number(dataForm.get('score')),note:String(dataForm.get('note')||'').trim()||null};
        button.disabled=true;button.textContent='Salvando…';
        try{
          await api(`/api/admin/final-tiebreak/${encodeURIComponent(form.dataset.participant)}`,{method:'PUT',body:JSON.stringify(payload)});
          await refresh();
        }catch(err){button.disabled=false;button.textContent='Salvar';showMessage(document.querySelector('#message'),err.message,'error')}
      });
      form.querySelector('[data-clear-final]')?.addEventListener('click',async()=>{
        if(!confirm('Limpar o resultado de desempate deste participante?'))return;
        try{
          await api(`/api/admin/final-tiebreak/${encodeURIComponent(form.dataset.participant)}`,{method:'DELETE'});
          await refresh();
        }catch(err){showMessage(document.querySelector('#message'),err.message,'error')}
      });
    });
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
    ensureCard();
    refresh();
    clearInterval(timer);
    timer=setInterval(()=>{if(!document.hidden)refresh()},REFRESH_MS);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
