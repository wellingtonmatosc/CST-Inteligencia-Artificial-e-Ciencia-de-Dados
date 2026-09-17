const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
function itemLabel(value,singular,plural){const n=Number(value||0);return `${n} ${n===1?singular:plural}`}
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){list.innerHTML='';status.textContent='Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';return}
    list.innerHTML=rows.map(r=>`<article class="individual-ranking-card"><div class="individual-rank-position" aria-label="${Number(r.position)}º lugar">${Number(r.position)}º</div><div class="individual-rank-main"><span class="eyebrow">Participante</span><h3>${esc(r.nick)}</h3><p>${itemLabel(r.stations_validated,'estação validada','estações validadas')} • ${itemLabel(r.trails_completed,'trilha concluída','trilhas concluídas')}</p></div><div class="individual-rank-score"><strong>${Number(r.points||0)}</strong><span>pontos</span></div></article>`).join('');
    status.textContent='Critério: pontos acumulados. Em empate, trilhas concluídas e estações validadas. Desempenhos idênticos compartilham a mesma posição.';
  }catch(err){status.textContent=err.message}
}
loadRanking();