const list=document.querySelector('#rankingList'),status=document.querySelector('#status');

function positionLabel(position){
  if(position===1)return '1º';
  if(position===2)return '2º';
  if(position===3)return '3º';
  return `${position}º`;
}

async function load(){
  try{
    const d=await api('/api/ranking');
    list.innerHTML=d.ranking.length?d.ranking.map(r=>`<div class="ranking-row" data-position="${r.position}"><strong>${positionLabel(r.position)}</strong><span>${esc(r.nick)}</span><strong>${r.points} pts</strong></div>`).join(''):'<p>Ainda não há pontuação registrada.</p>';
    status.textContent='Atualizado automaticamente a cada 15 segundos.';
  }catch(e){status.textContent=e.message}
}

load();setInterval(load,15000);
