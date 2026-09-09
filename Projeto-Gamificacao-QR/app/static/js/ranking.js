const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
function memberLabel(value){const n=Number(value||0);return `${n} ${n===1?'integrante atual':'integrantes atuais'}`}
function contributorLabel(value){const n=Number(value||0);return `${n} ${n===1?'participante pontuou':'participantes pontuaram'}`}
function itemLabel(value,singular,plural){const n=Number(value||0);return `${n} ${n===1?singular:plural}`}
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){status.textContent='Ranking ainda sem dados.';return}
    const started=rows.some(r=>r.position!==null&&r.position!==undefined);
    list.innerHTML=rows.map(r=>`<article class="team-ranking-card"><div class="team-rank-position" aria-label="${started?`${r.position}º lugar`:'classificação ainda não iniciada'}">${started?`${r.position}º`:'—'}</div><div class="team-rank-main"><span class="eyebrow">${esc(r.reference_name||'')}</span><h3>${esc(r.name)}</h3><p>${memberLabel(r.members)} • ${contributorLabel(r.contributors)} • ${Number(r.activation_rate||0)}% de ativação atual</p></div><div class="team-rank-score"><strong>${Number(r.avg_points_active||0)}</strong><span>média competitiva</span></div><div class="team-rank-details"><span>${Number(r.points||0)} pontos totais</span><span>${itemLabel(r.stations_validated,'estação','estações')}</span><span>${itemLabel(r.trails_completed,'trilha','trilhas')}</span></div></article>`).join('');
    status.textContent=started?'Classificação pela média de pontos por participante que contribuiu. Pontos totais, trilhas e estações são usados nos desempates.':'Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';
  }catch(err){status.textContent=err.message}
}
loadRanking();