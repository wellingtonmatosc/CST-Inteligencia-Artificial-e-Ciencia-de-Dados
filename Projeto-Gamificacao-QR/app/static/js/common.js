async function api(url,options={}){
  const res=await fetch(url,{credentials:'include',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
  let data={};
  try{data=await res.json()}catch(_){data={detail:'Resposta inválida do servidor.'}}
  if(!res.ok)throw new Error(data.detail||'Não foi possível concluir a operação.');
  return data;
}

function showMessage(el,msg,type='notice'){
  el.className=`notice ${type}`;
  el.textContent=msg;
  el.classList.remove('hidden');
}

function esc(s){
  return String(s??'').replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));
}

const A11Y_STORAGE_KEY='gamificacao-a11y-v3';
const A11Y_DEFAULTS={fontScale:1,contrast:false,reducedMotion:false};

function loadA11y(){
  try{return {...A11Y_DEFAULTS,...JSON.parse(localStorage.getItem(A11Y_STORAGE_KEY)||'{}')}}catch(_){return {...A11Y_DEFAULTS}}
}
function saveA11y(prefs){try{localStorage.setItem(A11Y_STORAGE_KEY,JSON.stringify(prefs))}catch(_){}}
function applyA11y(prefs){
  const root=document.documentElement;
  root.style.fontSize=`${Math.round(prefs.fontScale*100)}%`;
  root.classList.toggle('a11y-contrast',Boolean(prefs.contrast));
  root.classList.toggle('a11y-reduced-motion',Boolean(prefs.reducedMotion));
}

function speakText(text){
  if(!('speechSynthesis' in window))return false;
  window.speechSynthesis.cancel();
  const utterance=new SpeechSynthesisUtterance(String(text||''));
  utterance.lang='pt-BR';
  utterance.rate=.95;
  window.speechSynthesis.speak(utterance);
  return true;
}
function stopSpeech(){if('speechSynthesis' in window)window.speechSynthesis.cancel()}
function pageSpeechText(){
  const root=document.querySelector('main')||document.body;
  return [...root.querySelectorAll('h1,h2,h3,p,label,button,a')]
    .filter(el=>!el.closest('[hidden],.hidden,[aria-hidden="true"],#a11yPanel'))
    .map(el=>(el.textContent||'').replace(/\s+/g,' ').trim())
    .filter(Boolean)
    .filter((v,i,a)=>a.indexOf(v)===i)
    .join('. ');
}
function speakPage(){const text=pageSpeechText();return text?speakText(text):false}

function initA11yPanel(){
  let prefs=loadA11y();
  applyA11y(prefs);

  const toggle=document.createElement('button');
  toggle.type='button';toggle.id='a11yToggle';toggle.className='a11y-toggle';
  toggle.setAttribute('aria-haspopup','dialog');toggle.setAttribute('aria-expanded','false');
  toggle.textContent='Acessibilidade';

  const panel=document.createElement('section');
  panel.id='a11yPanel';panel.className='a11y-panel hidden';panel.setAttribute('role','dialog');panel.setAttribute('aria-labelledby','a11yTitle');
  panel.innerHTML=`<div class="a11y-panel-head"><h2 id="a11yTitle">Acessibilidade</h2><button type="button" class="secondary compact" id="a11yClose">Fechar</button></div>
  <div class="a11y-voice-actions"><button type="button" class="secondary" data-a11y="speak-page">Ouvir tela</button><button type="button" class="secondary" data-a11y="stop-speech">Parar áudio</button><button type="button" class="secondary" id="voiceCommandButton">Comando de voz</button></div>
  <p id="voiceStatus" class="voice-status" role="status" aria-live="polite"></p>
  <div class="a11y-control"><strong>Texto</strong><div class="inline-actions"><button type="button" class="secondary compact" data-a11y="font-down">A−</button><button type="button" class="secondary compact" data-a11y="font-up">A+</button></div></div>
  <label class="switch-row"><input type="checkbox" data-a11y-check="contrast"><span><strong>Alto contraste</strong></span></label>
  <label class="switch-row"><input type="checkbox" data-a11y-check="reducedMotion"><span><strong>Reduzir animações</strong></span></label>
  <div class="a11y-footer"><button type="button" class="secondary" data-a11y="reset">Restaurar</button></div>`;
  document.body.append(toggle,panel);

  const status=panel.querySelector('#voiceStatus');
  const voiceButton=panel.querySelector('#voiceCommandButton');
  const sync=()=>{panel.querySelectorAll('[data-a11y-check]').forEach(i=>i.checked=Boolean(prefs[i.dataset.a11yCheck]));applyA11y(prefs);saveA11y(prefs)};
  const open=()=>{panel.classList.remove('hidden');toggle.setAttribute('aria-expanded','true');panel.querySelector('#a11yClose').focus()};
  const close=()=>{panel.classList.add('hidden');toggle.setAttribute('aria-expanded','false');toggle.focus()};

  toggle.onclick=()=>panel.classList.contains('hidden')?open():close();
  panel.querySelector('#a11yClose').onclick=close;
  panel.querySelectorAll('[data-a11y-check]').forEach(i=>i.onchange=()=>{prefs[i.dataset.a11yCheck]=i.checked;sync()});
  panel.querySelectorAll('[data-a11y]').forEach(b=>b.onclick=()=>{
    const action=b.dataset.a11y;
    if(action==='speak-page'){if(!speakPage())status.textContent='Áudio não disponível neste navegador.';return}
    if(action==='stop-speech'){stopSpeech();status.textContent='Áudio interrompido.';return}
    if(action==='font-up')prefs.fontScale=Math.min(1.4,Math.round((prefs.fontScale+.1)*10)/10);
    if(action==='font-down')prefs.fontScale=Math.max(.9,Math.round((prefs.fontScale-.1)*10)/10);
    if(action==='reset')prefs={...A11Y_DEFAULTS};
    sync();
  });

  voiceButton.onclick=()=>{
    const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!Recognition){status.textContent='Comando de voz indisponível neste navegador.';return}
    stopSpeech();
    const recognition=new Recognition();recognition.lang='pt-BR';recognition.interimResults=false;recognition.maxAlternatives=1;
    recognition.onstart=()=>{voiceButton.disabled=true;voiceButton.textContent='Ouvindo…';status.textContent='Fale um comando.'};
    recognition.onerror=()=>{status.textContent='Não foi possível reconhecer a voz.'};
    recognition.onend=()=>{voiceButton.disabled=false;voiceButton.textContent='Comando de voz'};
    recognition.onresult=e=>{
      const raw=e.results[0][0].transcript;
      const cmd=raw.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
      status.textContent=`Comando: ${raw}`;
      if(cmd.includes('ranking'))location.assign('/ranking');
      else if(cmd.includes('ouvir')||cmd.includes('ler tela'))speakPage();
      else if(cmd.includes('parar'))stopSpeech();
      else if(cmd.includes('aumentar texto')){prefs.fontScale=Math.min(1.4,prefs.fontScale+.1);sync()}
      else if(cmd.includes('diminuir texto')){prefs.fontScale=Math.max(.9,prefs.fontScale-.1);sync()}
      else if(cmd.includes('contraste')){prefs.contrast=!prefs.contrast;sync()}
      else if(cmd.includes('ler qr')||cmd.includes('abrir camera'))document.querySelector('#openQrScanner')?.click();
      else if(cmd.includes('criar conta'))document.querySelector('#showRegister')?.click();
      else if(cmd.includes('recuperar'))document.querySelector('#showRecovery')?.click();
      else if(cmd.includes('ouvir desafio')||cmd.includes('ouvir pergunta'))document.querySelector('#readQuestion')?.click();
      else if(cmd.includes('responder'))document.querySelector('#answerForm')?.requestSubmit();
      else speakText('Comando não reconhecido.');
    };
    try{recognition.start()}catch(_){status.textContent='Não foi possível iniciar o comando de voz.'}
  };

  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.classList.contains('hidden'))close()});
  sync();
  window.openAccessibilityPanel=open;
}

window.speakText=speakText;
window.stopSpeech=stopSpeech;
window.speakPage=speakPage;
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initA11yPanel,{once:true});else initA11yPanel();
