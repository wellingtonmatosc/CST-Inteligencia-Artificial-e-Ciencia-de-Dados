const box=document.querySelector('#activity'),msg=document.querySelector('#message');
const code=decodeURIComponent(location.pathname.split('/').pop());
let state;let submitting=false;

function attemptInfo(q){
  return q.kind==='true_false'?'1 tentativa':'2 tentativas';
}

function optionText(q){
  return (q.options||[]).map((o,i)=>`${i+1}. ${o.label??o}`).join('. ');
}

function questionSpeechText(q,includeOptions=false){
  const prompt=(document.querySelector('#questionPrompt')?.textContent||q.prompt||'').trim();
  if(!includeOptions)return prompt;
  const opts=optionText(q);
  return opts?`${prompt}. Alternativas: ${opts}`:prompt;
}

function bindQuestionTools(q){
  const read=document.querySelector('#readQuestion');
  const readAll=document.querySelector('#readOptions');
  const stop=document.querySelector('#stopAudio');
  const simple=document.querySelector('#simpleText');
  if(read)read.onclick=()=>{if(!window.speakText(questionSpeechText(q,false)))showMessage(msg,'Áudio indisponível.','warning')};
  if(readAll)readAll.onclick=()=>{if(!window.speakText(questionSpeechText(q,true)))showMessage(msg,'Áudio indisponível.','warning')};
  if(stop)stop.onclick=()=>window.stopSpeech?.();
  if(simple)simple.onclick=()=>{
    const prompt=document.querySelector('#questionPrompt');
    const usingSimple=simple.dataset.simple==='true';
    prompt.textContent=usingSimple?q.prompt:q.accessibility.simplified_prompt;
    simple.dataset.simple=String(!usingSimple);
    simple.textContent=usingSimple?'Texto simples':'Texto original';
  };
}

function renderQuestion(q,submit){
  let options='';
  if(q.kind==='multiple_choice'||q.kind==='true_false'){
    options=(q.options||[]).map(o=>`<label><input type="radio" name="answer" value="${esc(o.value??o)}" required><span>${esc(o.label??o)}</span></label>`).join('');
  }else{
    options='<label for="answerText">Resposta</label><input id="answerText" name="answer" required autocomplete="off">';
  }

  const a11y=q.accessibility||{};
  const support=[];
  if('speechSynthesis' in window){
    support.push('<button type="button" id="readQuestion">Ouvir pergunta</button>');
    if((q.options||[]).length)support.push('<button type="button" id="readOptions">Ouvir tudo</button>');
    support.push('<button type="button" id="stopAudio">Parar</button>');
  }
  if(a11y.simplified_prompt)support.push('<button type="button" id="simpleText" data-simple="false">Texto simples</button>');

  const equivalents=[];
  if(a11y.alt_text)equivalents.push(`<p class="alternative-description"><strong>Descrição:</strong> ${esc(a11y.alt_text)}</p>`);
  if(a11y.transcript)equivalents.push(`<p class="alternative-description"><strong>Transcrição:</strong> ${esc(a11y.transcript)}</p>`);

  box.innerHTML=`<div class="card question-card">
    <h1>${esc(state.qr.name)}</h1>
    <p id="questionPrompt" class="question-prompt">${esc(q.prompt)}</p>
    <div class="question-meta"><span class="meta-pill">${esc(attemptInfo(q))}</span></div>
    ${support.length?`<div class="question-tools" aria-label="Áudio e apoio de leitura">${support.join('')}</div>`:''}
    ${equivalents.join('')}
    <form id="answerForm" class="choices">${options}<button type="submit">Responder</button></form>
  </div>`;
  document.querySelector('#answerForm').addEventListener('submit',submit);
  bindQuestionTools(q);
}

function setFormBusy(form,busy){
  submitting=busy;form.setAttribute('aria-busy',String(busy));
  form.querySelectorAll('button,input,select,textarea').forEach(el=>{el.disabled=busy});
  const button=form.querySelector('button[type="submit"]');if(button)button.textContent=busy?'Enviando…':'Responder';
}

function renderCompleted(points,milestones=[]){
  window.stopSpeech?.();
  const bonus=(milestones||[]).reduce((sum,item)=>sum+Number(item.points||0),0);
  const bonusText=bonus>0?`<p class="success notice">Bônus: <strong>+${bonus}</strong></p>`:'';
  box.innerHTML=`<div class="card question-card"><h1>Resposta registrada</h1><p><span class="result-points">+${points||0} pontos</span></p>${bonusText}<div class="page-links"><a href="/ranking">Ranking</a><a href="/">Perfil</a></div></div>`;
}

function renderParticipation(points=2){
  window.stopSpeech?.();
  const label=points===1?'ponto':'pontos';
  box.innerHTML=`<div class="card question-card"><h1>Atividade encerrada</h1><p><span class="result-points">+${points} ${label}</span></p><div class="page-links"><a href="/ranking">Ranking</a><a href="/">Perfil</a></div></div>`;
}

async function load(){
  try{
    state=await api(`/api/q/${encodeURIComponent(code)}`);
    if(state.status==='completed'){renderCompleted(state.points_awarded);return}
    if(state.status==='failed'){renderParticipation(state.points_awarded||2);return}
    if(state.mode==='bonus'&&state.status==='choosing'){
      box.innerHTML=`<div class="card question-card bonus-card"><h1>${esc(state.campaign.name)}</h1><p class="question-prompt">Escolha um desafio.</p><div class="choices">${state.categories.map(c=>`<button type="button" data-cat="${c.id}">${esc(c.name)}</button>`).join('')}</div></div>`;
      document.querySelectorAll('[data-cat]').forEach(b=>b.onclick=()=>choose(b.dataset.cat,b));return;
    }
    if(state.question)renderQuestion(state.question,submitAnswer);
  }catch(err){showMessage(msg,err.message,'error')}
}

async function choose(category_id,button){
  if(submitting)return;submitting=true;
  const buttons=[...document.querySelectorAll('[data-cat]')];buttons.forEach(b=>b.disabled=true);
  const oldText=button.textContent;button.textContent='Carregando…';
  try{
    const d=await api(`/api/bonus/${state.bonus_run_id}/category`,{method:'POST',body:JSON.stringify({category_id})});
    state.status=d.status;state.question=d.question;submitting=false;renderQuestion(d.question,submitAnswer);
  }catch(err){submitting=false;buttons.forEach(b=>b.disabled=false);button.textContent=oldText;showMessage(msg,err.message,'error')}
}

async function submitAnswer(e){
  e.preventDefault();if(submitting)return;
  const form=e.target,data=new FormData(form),answer=data.get('answer');setFormBusy(form,true);window.stopSpeech?.();
  try{
    const url=state.mode==='bonus'?`/api/bonus/${state.bonus_run_id}/answer`:`/api/activity/${state.run_id}/answer`;
    const d=await api(url,{method:'POST',body:JSON.stringify({answer})});
    if(d.correct){
      const bonus=(d.milestones||[]).reduce((sum,item)=>sum+Number(item.points||0),0);
      showMessage(msg,bonus>0?`Correto! +${d.points} e bônus +${bonus}.`:`Correto! +${d.points}.`,'success');
      state.status='completed';state.points_awarded=d.points;submitting=false;renderCompleted(d.points,d.milestones||[]);return;
    }
    if(d.completed){
      const participationPoints=Number(d.points||2);showMessage(msg,`Incorreto. +${participationPoints} por participação.`,'error');
      state.status='failed';state.points_awarded=participationPoints;submitting=false;renderParticipation(participationPoints);return;
    }
    showMessage(msg,`Incorreto. Resta ${d.remaining} tentativa.`,'error');setFormBusy(form,false);
  }catch(err){setFormBusy(form,false);showMessage(msg,err.message,'error')}
}

load();
