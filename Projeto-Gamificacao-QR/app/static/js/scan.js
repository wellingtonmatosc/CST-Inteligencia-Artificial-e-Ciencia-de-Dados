const box=document.querySelector('#activity'),msg=document.querySelector('#message');
const code=decodeURIComponent(location.pathname.split('/').pop());
let state;let submitting=false;

function attemptInfo(q){
  if(q.kind==='true_false') return '1 tentativa • 10 pontos';
  return 'Até 3 tentativas • 10 / 7 / 5 pontos';
}

function renderQuestion(q,submit){
  let options='';
  if(q.kind==='multiple_choice'||q.kind==='true_false'){
    options=(q.options||[]).map(o=>`<label><input type="radio" name="answer" value="${esc(o.value??o)}" required><span>${esc(o.label??o)}</span></label>`).join('');
  }else{
    options='<label for="answerText">Sua resposta</label><input id="answerText" name="answer" required autocomplete="off">';
  }
  box.innerHTML=`<div class="card question-card"><div class="question-eyebrow">Desafio</div><h1>${esc(state.qr.name)}</h1><p class="question-prompt">${esc(q.prompt)}</p><div class="question-meta">${attemptInfo(q)}</div>${q.accessibility?.alt_text?`<p class="muted">Descrição: ${esc(q.accessibility.alt_text)}</p>`:''}<form id="answerForm" class="choices">${options}<button type="submit">Responder</button></form></div>`;
  document.querySelector('#answerForm').addEventListener('submit',submit);
}

function setFormBusy(form,busy){
  submitting=busy;
  form.setAttribute('aria-busy',String(busy));
  form.querySelectorAll('button,input,select,textarea').forEach(el=>{el.disabled=busy});
  const button=form.querySelector('button[type="submit"]');
  if(button)button.textContent=busy?'Enviando resposta…':'Responder';
}

function renderCompleted(points,milestones=[]){
  const bonus=(milestones||[]).reduce((sum,item)=>sum+Number(item.points||0),0);
  const bonusText=bonus>0?`<p class="success notice">Bônus de progresso conquistado: <strong>+${bonus} pontos</strong>.</p>`:'';
  box.innerHTML=`<div class="card question-card"><div class="question-eyebrow">Concluído</div><h1>Atividade concluída.</h1><p>Esta atividade já foi registrada para hoje.</p><p><span class="result-points">+${points||0} pontos</span></p>${bonusText}<p><a href="/ranking">Ver ranking</a> · <a href="/">Meu perfil</a></p></div>`;
}

function renderFailed(kind){
  const text=kind==='true_false'
    ?'Questões de verdadeiro/falso permitem apenas uma tentativa.'
    :'As tentativas disponíveis para este ponto foram utilizadas hoje.';
  box.innerHTML=`<div class="card question-card"><div class="question-eyebrow">Finalizado</div><h1>Atividade encerrada</h1><p>${text}</p><p><a href="/">Voltar ao perfil</a></p></div>`;
}

async function load(){
  try{
    state=await api(`/api/q/${encodeURIComponent(code)}`);
    if(state.status==='completed'){renderCompleted(state.points_awarded);return}
    if(state.status==='failed'){renderFailed();return}
    if(state.mode==='bonus'&&state.status==='choosing'){
      box.innerHTML=`<div class="card question-card"><div class="question-eyebrow">Bônus</div><h1>${esc(state.campaign.name)}</h1><p class="question-prompt">Escolha um dos três desafios. Todas as opções valem a mesma pontuação-base.</p><div class="choices">${state.categories.map(c=>`<button type="button" data-cat="${c.id}">${esc(c.name)}</button>`).join('')}</div></div>`;
      document.querySelectorAll('[data-cat]').forEach(b=>b.onclick=()=>choose(b.dataset.cat,b));return;
    }
    if(state.question)renderQuestion(state.question,submitAnswer);
  }catch(err){showMessage(msg,err.message,'error')}
}

async function choose(category_id,button){
  if(submitting)return;
  submitting=true;
  const buttons=[...document.querySelectorAll('[data-cat]')];
  buttons.forEach(b=>b.disabled=true);
  const oldText=button.textContent;button.textContent='Carregando…';
  try{
    const d=await api(`/api/bonus/${state.bonus_run_id}/category`,{method:'POST',body:JSON.stringify({category_id})});
    state.status=d.status;state.question=d.question;submitting=false;renderQuestion(d.question,submitAnswer);
  }catch(err){
    submitting=false;buttons.forEach(b=>b.disabled=false);button.textContent=oldText;showMessage(msg,err.message,'error');
  }
}

async function submitAnswer(e){
  e.preventDefault();if(submitting)return;
  const form=e.target;const data=new FormData(form);const answer=data.get('answer');const kind=state.question?.kind;
  setFormBusy(form,true);
  try{
    const url=state.mode==='bonus'?`/api/bonus/${state.bonus_run_id}/answer`:`/api/activity/${state.run_id}/answer`;
    const d=await api(url,{method:'POST',body:JSON.stringify({answer})});
    if(d.correct){
      const bonus=(d.milestones||[]).reduce((sum,item)=>sum+Number(item.points||0),0);
      showMessage(msg,bonus>0?`Resposta correta! +${d.points} pontos e +${bonus} de bônus.`:`Resposta correta! +${d.points} pontos.`,'success');
      state.status='completed';state.points_awarded=d.points;submitting=false;renderCompleted(d.points,d.milestones||[]);return;
    }
    if(d.completed){
      const text=kind==='true_false'
        ?'Resposta incorreta. Questões de verdadeiro/falso têm apenas uma tentativa.'
        :'Atividade finalizada. Você poderá tentar este QR novamente em outro dia, com uma questão diferente.';
      showMessage(msg,text,'error');
      state.status='failed';submitting=false;renderFailed(kind);return;
    }
    showMessage(msg,`Resposta incorreta. Restam ${d.remaining} tentativa(s).`,'error');setFormBusy(form,false);
  }catch(err){setFormBusy(form,false);showMessage(msg,err.message,'error')}
}

load();