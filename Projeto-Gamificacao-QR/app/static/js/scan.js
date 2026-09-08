const box=document.querySelector('#activity'),msg=document.querySelector('#message');
const code=decodeURIComponent(location.pathname.split('/').pop());
let state;let submitting=false;let authRedirecting=false;

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

function redirectToAccess(){
  if(authRedirecting)return;
  authRedirecting=true;
  const next=`${location.pathname}${location.search}`;
  location.replace(`/?next=${encodeURIComponent(next)}`);
}

async function gameApi(url,options={}){
  const res=await fetch(url,{credentials:'include',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
  let data={};
  try{data=await res.json()}catch(_){data={detail:'Resposta inválida do servidor.'}}
  if(res.status===401){redirectToAccess();throw new Error('AUTH_REDIRECT')}
  if(!res.ok)throw new Error(data.detail||'Não foi possível concluir a operação.');
  return data;
}

function showAnswerFeedback(text,type='error'){
  const feedback=document.querySelector('#answerFeedback');
  if(!feedback){showMessage(msg,text,type);return}
  feedback.className=`answer-feedback notice ${type}`;
  feedback.textContent=text;
  feedback.classList.remove('hidden');
  msg.classList.add('hidden');
  requestAnimationFrame(()=>feedback.scrollIntoView({behavior:document.documentElement.classList.contains('a11y-reduced-motion')?'auto':'smooth',block:'nearest'}));
}

function clearAnswerFeedback(){
  const feedback=document.querySelector('#answerFeedback');
  if(feedback){feedback.className='answer-feedback hidden';feedback.textContent=''}
}

function showRecoveryCodeOnce(){
  const recoveryCode=sessionStorage.getItem('event_recovery_code_once');
  if(!recoveryCode)return;
  sessionStorage.removeItem('event_recovery_code_once');

  const notice=document.createElement('aside');
  notice.className='recovery-code-toast';
  notice.setAttribute('role','status');
  notice.setAttribute('aria-live','polite');

  const text=document.createElement('div');
  const title=document.createElement('strong');title.textContent='Guarde seu código de recuperação';
  const value=document.createElement('code');value.textContent=recoveryCode;
  text.append(title,value);

  const actions=document.createElement('div');actions.className='recovery-code-actions';
  const copy=document.createElement('button');copy.type='button';copy.className='secondary compact';copy.textContent='Copiar';
  const close=document.createElement('button');close.type='button';close.className='secondary compact';close.textContent='Fechar';
  actions.append(copy,close);
  notice.append(text,actions);
  document.body.appendChild(notice);

  copy.addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(recoveryCode);copy.textContent='Copiado'}catch(_){copy.textContent='Código acima'}
  });
  close.addEventListener('click',()=>notice.remove());
}

function bindQuestionTools(q){
  const read=document.querySelector('#readQuestion');
  const readAll=document.querySelector('#readOptions');
  const stop=document.querySelector('#stopAudio');
  const simple=document.querySelector('#simpleText');
  if(read)read.onclick=()=>{if(!window.speakText(questionSpeechText(q,false)))showAnswerFeedback('Áudio indisponível.','warning')};
  if(readAll)readAll.onclick=()=>{if(!window.speakText(questionSpeechText(q,true)))showAnswerFeedback('Áudio indisponível.','warning')};
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
    <form id="answerForm" class="choices">${options}<button type="submit">Responder</button><div id="answerFeedback" class="answer-feedback hidden" role="alert" aria-live="assertive"></div></form>
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
  box.innerHTML=`<div class="card question-card"><h1>Resposta correta</h1><p><span class="result-points">+${points||0} pontos</span></p>${bonusText}<div class="page-links"><a href="/ranking">Ranking</a><a href="/">Perfil</a></div></div>`;
  box.scrollIntoView({behavior:document.documentElement.classList.contains('a11y-reduced-motion')?'auto':'smooth',block:'start'});
}

function renderParticipation(points=2){
  window.stopSpeech?.();
  const label=points===1?'ponto':'pontos';
  box.innerHTML=`<div class="card question-card"><h1>Resposta incorreta</h1><p>Você recebeu pontos pela participação.</p><p><span class="result-points">+${points} ${label}</span></p><div class="page-links"><a href="/ranking">Ranking</a><a href="/">Perfil</a></div></div>`;
  box.scrollIntoView({behavior:document.documentElement.classList.contains('a11y-reduced-motion')?'auto':'smooth',block:'start'});
}

async function load(){
  try{
    state=await gameApi(`/api/q/${encodeURIComponent(code)}`);
    showRecoveryCodeOnce();
    if(state.status==='completed'){renderCompleted(state.points_awarded);return}
    if(state.status==='failed'){renderParticipation(state.points_awarded||2);return}
    if(state.mode==='bonus'&&state.status==='choosing'){
      box.innerHTML=`<div class="card question-card bonus-card"><h1>${esc(state.campaign.name)}</h1><p class="question-prompt">Escolha um desafio.</p><div class="choices">${state.categories.map(c=>`<button type="button" data-cat="${c.id}">${esc(c.name)}</button>`).join('')}</div></div>`;
      document.querySelectorAll('[data-cat]').forEach(b=>b.onclick=()=>choose(b.dataset.cat,b));return;
    }
    if(state.question)renderQuestion(state.question,submitAnswer);
  }catch(err){if(err.message!=='AUTH_REDIRECT')showMessage(msg,err.message,'error')}
}

async function choose(category_id,button){
  if(submitting)return;submitting=true;
  const buttons=[...document.querySelectorAll('[data-cat]')];buttons.forEach(b=>b.disabled=true);
  const oldText=button.textContent;button.textContent='Carregando…';
  try{
    const d=await gameApi(`/api/bonus/${state.bonus_run_id}/category`,{method:'POST',body:JSON.stringify({category_id})});
    state.status=d.status;state.question=d.question;submitting=false;renderQuestion(d.question,submitAnswer);
  }catch(err){
    submitting=false;buttons.forEach(b=>b.disabled=false);button.textContent=oldText;
    if(err.message!=='AUTH_REDIRECT')showMessage(msg,err.message,'error');
  }
}

async function submitAnswer(e){
  e.preventDefault();if(submitting)return;
  const form=e.target,data=new FormData(form),answer=data.get('answer');clearAnswerFeedback();setFormBusy(form,true);window.stopSpeech?.();
  try{
    const url=state.mode==='bonus'?`/api/bonus/${state.bonus_run_id}/answer`:`/api/activity/${state.run_id}/answer`;
    const d=await gameApi(url,{method:'POST',body:JSON.stringify({answer})});
    if(d.correct){
      state.status='completed';state.points_awarded=d.points;submitting=false;renderCompleted(d.points,d.milestones||[]);return;
    }
    if(d.completed){
      const participationPoints=Number(d.points||2);
      state.status='failed';state.points_awarded=participationPoints;submitting=false;renderParticipation(participationPoints);return;
    }
    setFormBusy(form,false);
    showAnswerFeedback(`Resposta incorreta. Você ainda tem ${d.remaining} tentativa.`,'error');
  }catch(err){
    setFormBusy(form,false);
    if(err.message!=='AUTH_REDIRECT')showAnswerFeedback(err.message,'error');
  }
}

load();
