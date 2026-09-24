(()=>{
  const REFRESH_MS=60000;
  let timer=null;

  function ensureCard(){
    const panel=document.querySelector('#rankingPanel');
    if(!panel)return null;
    const legacyDescription=panel.querySelector('.admin-section-head .muted');
    if(legacyDescription)legacyDescription.textContent='Ordem oficial: pontos, trilhas concluídas e estações realizadas. Empates reais compartilham posição.';
    let card=document.querySelector('#rankingRulesCard');
    if(card)return card;
    card=document.createElement('section');
    card.id='rankingRulesCard';
    card.className='card';
    card.innerHTML=`<div class="admin-section-head"><div><span class="eyebrow">Ranking oficial</span><h2>Critérios competitivos</h2><p class="muted">Ordem: pontos acumulados, trilhas concluídas e estações realizadas. Indicadores como acertos, dias ativos e sequência podem ser acompanhados como mérito, mas não alteram a classificação. Se todos os critérios oficiais permanecerem iguais, os participantes compartilham a posição.</p></div><button type="button" class="secondary compact" id="refreshRankingRules">Atualizar</button></div><div id="rankingRuleStatus" class="notice"><strong>Pontuação oficial:</strong> QR +10; acerto na 1ª tentativa +10; acerto na 2ª +6; erro +0 de bônus. Trilhas não geram pontos extras.</div><div id="rankingMeritList" class="admin-list"></div>`;
    panel.prepend(card);
    card.querySelector('#refreshRankingRules')?.addEventListener('click',refresh);
    return card;
  }

  function metricLine(row){
    return `${Number(row.trails_completed||0)} trilhas concluídas • ${Number(row.stations_validated||0)} estações realizadas`;
  }

  function render(data){
    const card=ensureCard();
    if(!card)return;
    const ranking=Array.isArray(data.ranking)?data.ranking:[];
    const meritList=card.querySelector('#rankingMeritList');
    meritList.innerHTML=ranking.length?ranking.slice(0,20).map(row=>`<div class="admin-list-item"><div><strong>${Number(row.position)}º — ${esc(row.nick)}</strong><br><span class="muted">${esc(metricLine(row))}</span></div><div><span class="pill">${Number(row.points||0)} pts</span>${Number(row.tie_count||1)>1?'<span class="pill">posição compartilhada</span>':''}</div></div>`).join(''):'<div class="admin-empty">Ranking ainda não iniciado.</div>';
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
