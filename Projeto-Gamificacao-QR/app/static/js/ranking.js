const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
function itemLabel(value,singular,plural){const n=Number(value||0);return `${n} ${n===1?singular:plural}`}
function meritLine(r){const parts=[`${itemLabel(r.correct_answers,'acerto','acertos')}`,`${Number(r.first_try_correct||0)} na 1ª tentativa`,`${Number(r.distinct_qrs||0)} QRs distintos`,`${Number(r.active_days||0)}/7 dias`,`sequência ${Number(r.best_correct_streak||0)}`];if(r.final_tiebreak_resolved)parts.push(`desempate final ${Number(r.final_tiebreak_score||0)}`);return parts.join(' • ')}
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){list.innerHTML='';status.textContent='Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';return}
    list.innerHTML=rows.map(r=>`<article class="individual-ranking-card"><div class="individual-rank-position" aria-label="${Number(r.position)}º lugar">${Number(r.position)}º</div><div class="individual-rank-main"><span class="eyebrow">Participante</span><h3>${esc(r.nick)}</h3><p>${esc(meritLine(r))}</p>${r.unresolved_tie?'<span class="pill">empate técnico</span>':r.final_tiebreak_resolved?'<span class="pill">desempate final concluído</span>':''}</div><div class="individual-rank-score"><strong>${Number(r.points||0)}</strong><span>pontos</span></div></article>`).join('');
    status.textContent='Ordem de desempate: pontos, acertos, acertos na 1ª tentativa, QRs distintos e dias ativos. Persistindo igualdade, usa-se o desempate supervisionado do Dia 7. Velocidade não é critério.';
  }catch(err){status.textContent=err.message}
}
loadRanking();