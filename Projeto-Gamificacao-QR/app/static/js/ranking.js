const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){status.textContent='Ranking ainda sem dados.';return}
    const started=rows.some(r=>r.position!==null&&r.position!==undefined);
    list.innerHTML=rows.map(r=>`<article class="team-ranking-card"><div class="team-rank-position" aria-label="${started?`${r.position}º lugar`:'classificação ainda não iniciada'}">${started?`${r.position}º`:'—'}</div><div class="team-rank-main"><span class="eyebrow">${esc(r.reference_name||'')}</span><h3>${esc(r.name)}</h3><p>${Number(r.members||0)} integrantes atuais • ${Number(r.contributors||0)} participantes pontuaram • ${Number(r.activation_rate||0)}% de ativação atual</p></div><div class="team-rank-score"><strong>${Number(r.avg_points_active||0)}</strong><span>média competitiva</span></div><div class="team-rank-details"><span>${Number(r.points||0)} pontos totais</span><span>${Number(r.stations_validated||0)} estações</span><span>${Number(r.trails_completed||0)} trilhas</span></div></article>`).join('');
    status.textContent=started?'Classificação pela média de pontos por participante que contribuiu. Pontos totais, trilhas e estações são usados nos desempates.':'Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';
  }catch(err){status.textContent=err.message}
}
loadRanking();