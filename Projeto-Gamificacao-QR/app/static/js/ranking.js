const list=document.querySelector('#rankingList'),status=document.querySelector('#status');
function podiumLabel(position){const p=Number(position);if(p===1)return'<span class="podium-label first" aria-label="Primeiro colocado">Ouro • 1º lugar</span>';if(p===2)return'<span class="podium-label second" aria-label="Segundo colocado">Prata • 2º lugar</span>';if(p===3)return'<span class="podium-label third" aria-label="Terceiro colocado">Bronze • 3º lugar</span>';return'<span class="eyebrow">Participante</span>'}
function avatar(r){return window.TrilhasAvatars?.avatarMarkup(r.avatar_key,'rank-avatar',`Avatar de ${r.nick}`)||'<span class="rank-avatar" aria-hidden="true"></span>'}
function metrics(r){return `<div class="rank-metrics" aria-label="Critérios de desempate do participante"><div class="rank-metric"><strong>${Number(r.trails_completed||0)}</strong><span>trilhas concluídas</span></div><div class="rank-metric"><strong>${Number(r.stations_validated||0)}</strong><span>estações realizadas</span></div></div>`}
function note(r){return Number(r.tie_count||1)>1?'<div class="rank-note"><span class="pill">empate • mesma posição</span></div>':''}
async function loadRanking(){
  try{
    const data=await api('/api/ranking');
    const rows=data.ranking||[];
    if(!rows.length){list.innerHTML='';status.textContent='Classificação ainda não iniciada. As posições aparecem após a primeira atividade válida.';return}
    list.innerHTML=rows.map(r=>`<article class="individual-ranking-card" data-position="${Number(r.position)}"><div class="rank-top"><div class="individual-rank-position" aria-label="${Number(r.position)}º lugar">${Number(r.position)}º</div>${avatar(r)}<div class="rank-identity">${podiumLabel(r.position)}<h3 title="${esc(r.nick)}">${esc(r.nick)}</h3></div><div class="rank-score-pill" aria-label="${Number(r.points||0)} pontos"><strong>${Number(r.points||0)}</strong><span>pts</span></div></div>${metrics(r)}${note(r)}</article>`).join('');
    status.textContent='';
  }catch(err){status.textContent=err.message}
}
loadRanking();
