const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
function itemLabel(value,singular,plural){const n=Number(value||0);return `${n} ${n===1?singular:plural}`}
function podiumLabel(position){const p=Number(position);if(p===1)return'<span class="podium-label first" aria-label="Primeiro colocado">★ Liderança</span>';if(p===2)return'<span class="podium-label second" aria-label="Segundo colocado">◆ 2º colocado</span>';if(p===3)return'<span class="podium-label third" aria-label="Terceiro colocado">● 3º colocado</span>';return'<span class="eyebrow">Participante</span>'}
function metrics(r){return `<div class="rank-metrics" aria-label="Indicadores do participante"><div class="rank-metric"><strong>${Number(r.correct_answers||0)}</strong><span>acertos</span></div><div class="rank-metric"><strong>${Number(r.first_try_correct||0)}</strong><span>1ª tentativa</span></div><div class="rank-metric"><strong>${Number(r.distinct_qrs||0)}</strong><span>QRs distintos</span></div><div class="rank-metric"><strong>${Number(r.active_days||0)}/7</strong><span>dias</span></div><div class="rank-metric"><strong>${Number(r.best_correct_streak||0)}</strong><span>sequência</span></div></div>`}
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){list.innerHTML='';status.textContent='Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';return}
    list.innerHTML=rows.map(r=>`<article class="individual-ranking-card" data-position="${Number(r.position)}"><div class="individual-rank-position" aria-label="${Number(r.position)}º lugar">${Number(r.position)}º</div><div class="individual-rank-main">${podiumLabel(r.position)}<h3>${esc(r.nick)}</h3>${metrics(r)}${r.unresolved_tie?'<span class="pill">empate técnico</span>':r.final_tiebreak_resolved?'<span class="pill">desempate final concluído</span>':''}</div><div class="individual-rank-score"><strong>${Number(r.points||0)}</strong><span>pontos</span></div></article>`).join('');
    status.textContent='Ordem de desempate: pontos, acertos, acertos na 1ª tentativa, QRs distintos e dias ativos. Persistindo igualdade, usa-se o desempate supervisionado do Dia 7. Velocidade não é critério.';
  }catch(err){status.textContent=err.message}
}
loadRanking();
