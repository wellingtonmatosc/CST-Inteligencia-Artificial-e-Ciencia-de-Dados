const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
function podiumLabel(position){const p=Number(position);if(p===1)return'<span class="podium-label first" aria-label="Primeiro colocado">Ouro • 1º lugar</span>';if(p===2)return'<span class="podium-label second" aria-label="Segundo colocado">Prata • 2º lugar</span>';if(p===3)return'<span class="podium-label third" aria-label="Terceiro colocado">Bronze • 3º lugar</span>';return'<span class="eyebrow">Participante</span>'}
function metrics(r){return `<div class="rank-metrics" aria-label="Indicadores do participante"><div class="rank-metric"><strong>${Number(r.correct_answers||0)}</strong><span>acertos</span></div><div class="rank-metric"><strong>${Number(r.first_try_correct||0)}</strong><span>1ª tentativa</span></div><div class="rank-metric"><strong>${Number(r.distinct_qrs||0)}</strong><span>QRs distintos</span></div><div class="rank-metric"><strong>${Number(r.active_days||0)}/7</strong><span>dias</span></div><div class="rank-metric"><strong>${Number(r.best_correct_streak||0)}</strong><span>sequência</span></div></div>`}
function note(r){if(r.unresolved_tie)return'<div class="rank-note"><span class="pill">empate técnico</span></div>';if(r.final_tiebreak_resolved)return'<div class="rank-note"><span class="pill">desempate final concluído</span></div>';return''}
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){list.innerHTML='';status.textContent='Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';return}
    list.innerHTML=rows.map(r=>`<article class="individual-ranking-card" data-position="${Number(r.position)}"><div class="rank-top"><div class="individual-rank-position" aria-label="${Number(r.position)}º lugar">${Number(r.position)}º</div><div class="rank-identity">${podiumLabel(r.position)}<h3>${esc(r.nick)}</h3></div><div class="rank-score-pill" aria-label="${Number(r.points||0)} pontos"><strong>${Number(r.points||0)}</strong><span>pts</span></div></div>${metrics(r)}${note(r)}</article>`).join('');
    status.textContent='';
  }catch(err){status.textContent=err.message}
}
loadRanking();
