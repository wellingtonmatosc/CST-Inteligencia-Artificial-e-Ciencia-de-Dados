const a11yStylesheet=document.createElement('link');
a11yStylesheet.rel='stylesheet';a11yStylesheet.href='/static/css/accessibility.css';document.head.appendChild(a11yStylesheet);
const compactStylesheet=document.createElement('link');
compactStylesheet.rel='stylesheet';compactStylesheet.href='/static/css/compact.css';document.head.appendChild(compactStylesheet);
const aiThemeStylesheet=document.createElement('link');
aiThemeStylesheet.rel='stylesheet';aiThemeStylesheet.href='/static/css/ai-theme.css';document.head.appendChild(aiThemeStylesheet);

async function api(url, options={}){
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

const A11Y_STORAGE_KEY='gamificacao-a11y-v2';
const A11Y_DEFAULTS={fontScale:1,contrast:false,reducedMotion:false};

function loadA11y(){
  try{return {...A11Y_DEFAULTS,...JSON.parse(localStorage.getItem(A11Y_STORAGE_KEY)||'{}')}}catch(_){return {...A11Y_DEFAULTS}}
}

function saveA11y(prefs){localStorage.setItem(A11Y_STORAGE_KEY,JSON.stringify(prefs))}

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
  utterance.rate=0.95;
  window.speechSynthesis.speak(utterance);
  return true;
}

function stopSpeech(){if('speechSynthesis' in window)window.speechSynthesis.cancel()}

function isVisible(el){
  if(!el)return false;
  if(el.closest('[hidden],.hidden,[aria-hidden="true"]'))return false;
  const style=getComputedStyle(el);
  return style.display!=='none'&&style.visibility!=='hidden';
}

function pageSpeechText(){
  const root=document.querySelector('main')||document.body;
  const nodes=[...root.querySelectorAll('h1,h2,h3,p,label,button,a')];
  const seen=new Set();
  const parts=[];
  for(const el of nodes){
    if(!isVisible(el)||el.closest('#a11yPanel'))continue;
    const text=(el.textContent||'').replace(/\s+/g,' ').trim();
    if(!text||seen.has(text))continue;
    seen.add(text);parts.push(text);
  }
  return parts.join('. ');
}

function speakPage(){
  const text=pageSpeechText();
  return text?speakText(text):false;
}

function normalizeVoice(text){
  return String(text||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
}

function selectVoiceAlternative(index){
  const radios=[...document.querySelectorAll('#answerForm input[type="radio"][name="answer"]')];
  const radio=radios[index-1];
  if(!radio)return false;
  radio.checked=true;radio.focus();
  const label=radio.closest('label')?.textContent?.trim()||`alternativa ${index}`;
  speakText(`${label} selecionada.`);
  return true;
}

function initA11yPanel(){
  let prefs=loadA11y();applyA11y(prefs);
  let recognition=null;
  let listening=false;

  const toggle=document.createElement('button');
  toggle.type='button';toggle.id='a11yToggle';toggle.className='a11y-toggle';
  toggle.setAttribute('aria-haspopup','dialog');toggle.setAttribute('aria-expanded','false');
  toggle.textContent='Acessibilidade';

  const panel=document.createElement('section');
  panel.id='a11yPanel';panel.className='a11y-panel hidden';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','false');panel.setAttribute('aria-labelledby','a11yTitle');
  panel.innerHTML=`
    <div class="a11y-panel-head"><h2 id="a11yTitle">Acessibilidade</h2><button type="button" class="secondary compact" id="a11yClose" aria-label="Fechar acessibilidade">Fechar</button></div>
    <div class="a11y-voice-actions" aria-label="Áudio e voz">
      <button type="button" class="secondary" data-a11y="speak-page">Ouvir tela</button>
      <button type="button" class="secondary" data-a11y="stop-speech">Parar áudio</button>
      <button type="button" class="secondary" id="voiceCommandButton">Comando de voz</button>
    </div>
    <p id="voiceStatus" class="voice-status" role="status" aria-live="polite"></p>
    <div class="a11y-control"><strong>Texto</strong><div class="inline-actions"><button type="button" class="secondary compact" data-a11y="font-down" aria-label="Diminuir texto">A−</button><button type="button" class="secondary compact" data-a11y="font-up" aria-label="Aumentar texto">A+</button></div></div>
    <label class="switch-row"><input type="checkbox" data-a11y-check="contrast"><span><strong>Alto contraste</strong></span></label>
    <label class="switch-row"><input type="checkbox" data-a11y-check="reducedMotion"><span><strong>Reduzir animações</strong></span></label>
    <div class="a11y-footer"><button type="button" class="secondary" data-a11y="reset">Restaurar</button></div>`;

  document.body.append(toggle,panel);

  const status=panel.querySelector('#voiceStatus');
  const voiceButton=panel.querySelector('#voiceCommandButton');
  const setStatus=text=>{status.textContent=text||''};
  const sync=()=>{panel.querySelectorAll('[data-a11y-check]').forEach(input=>{input.checked=Boolean(prefs[input.dataset.a11yCheck])});applyA11y(prefs);saveA11y(prefs)};
  const open=()=>{panel.classList.remove('hidden');toggle.setAttribute('aria-expanded','true');panel.querySelector('#a11yClose').focus()};
  const close=()=>{panel.classList.add('hidden');toggle.setAttribute('aria-expanded','false');toggle.focus()};

  function runVoiceCommand(raw){
    const cmd=normalizeVoice(raw);
    setStatus(`Comando: ${raw}`);

    if(cmd.includes('ouvir tela')||cmd.includes('ler tela')){speakPage();return}
    if(cmd.includes('parar audio')||cmd.includes('parar leitura')||cmd==='parar'){stopSpeech();return}
    if(cmd.includes('criar conta')){document.querySelector('#showRegister')?.click();return}
    if(cmd.includes('recuperar acesso')||cmd.includes('esqueci meu pin')||cmd.includes('esqueci o pin')){document.querySelector('#showRecovery')?.click();return}
    if(cmd.includes('ranking')){window.location.assign('/ranking');return}
    if(cmd.includes('ler qr')||cmd.includes('qr code')||cmd.includes('abrir camera')){
      const qr=document.querySelector('#openQrScanner');
      if(qr){qr.click();return}
      speakText('Entre na sua conta para usar o leitor de QR Code.');return;
    }
    if(cmd==='entrar'||cmd.includes('fazer login')){document.querySelector('#login_nick')?.focus();speakText('Informe seu nick e PIN.');return}
    if(cmd.includes('aumentar texto')){prefs.fontScale=Math.min(1.4,Math.round((prefs.fontScale+0.1)*10)/10);sync();return}
    if(cmd.includes('diminuir texto')){prefs.fontScale=Math.max(0.9,Math.round((prefs.fontScale-0.1)*10)/10);sync();return}
    if(cmd.includes('alto contraste')||cmd.includes('ativar contraste')){prefs.contrast=true;sync();return}
    if(cmd.includes('desativar contraste')||cmd.includes('contraste normal')){prefs.contrast=false;sync();return}
    if(cmd.includes('ouvir pergunta')||cmd.includes('ler pergunta')){document.querySelector('#readQuestion')?.click();return}
    if(cmd.includes('ouvir alternativas')||cmd.includes('ler alternativas')||cmd.includes('ouvir tudo')){document.querySelector('#readOptions')?.click();return}
    if(cmd.includes('alternativa um')||cmd.includes('alternativa 1')){if(selectVoiceAlternative(1))return}
    if(cmd.includes('alternativa dois')||cmd.includes('alternativa 2')){if(selectVoiceAlternative(2))return}
    if(cmd.includes('alternativa tres')||cmd.includes('alternativa 3')){if(selectVoiceAlternative(3))return}
    if(cmd.includes('alternativa quatro')||cmd.includes('alternativa 4')){if(selectVoiceAlternative(4))return}
    if(cmd.includes('alternativa cinco')||cmd.includes('alternativa 5')){if(selectVoiceAlternative(5))return}
    if(cmd.includes('confirmar resposta')||cmd==='responder'){
      const form=document.querySelector('#answerForm');
      if(form){form.requestSubmit();return}
    }
    if(cmd==='voltar'){history.back();return}
    speakText('Comando não reconhecido.');
  }

  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(Recognition){
    recognition=new Recognition();recognition.lang='pt-BR';recognition.interimResults=false;recognition.maxAlternatives=1;
    recognition.onstart=()=>{listening=true;voiceButton.textContent='Ouvindo…';setStatus('Fale um comando.')};
    recognition.onresult=e=>runVoiceCommand(e.results[0][0].transcript);
    recognition.onerror=()=>setStatus('Não foi possível reconhecer a voz.');
    recognition.onend=()=>{listening=false;voiceButton.textContent='Comando de voz'};
    voiceButton.addEventListener('click',()=>{stopSpeech();if(!listening){try{recognition.start()}catch(_){}}});
  }else{
    voiceButton.disabled=true;voiceButton.textContent='Comando de voz indisponível';
  }

  toggle.addEventListener('click',()=>panel.classList.contains('hidden')?open():close());
  panel.querySelector('#a11yClose').addEventListener('click',close);
  panel.querySelectorAll('[data-a11y-check]').forEach(input=>input.addEventListener('change',()=>{prefs[input.dataset.a11yCheck]=input.checked;sync()}));
  panel.querySelectorAll('[data-a11y]').forEach(button=>button.addEventListener('click',()=>{
    const action=button.dataset.a11y;
    if(action==='speak-page'){if(!speakPage())setStatus('Áudio não disponível neste navegador.');return}
    if(action==='stop-speech'){stopSpeech();setStatus('Áudio interrompido.');return}
    if(action==='font-up')prefs.fontScale=Math.min(1.4,Math.round((prefs.fontScale+0.1)*10)/10);
    if(action==='font-down')prefs.fontScale=Math.max(0.9,Math.round((prefs.fontScale-0.1)*10)/10);
    if(action==='reset')prefs={...A11Y_DEFAULTS};
    sync();
  }));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.classList.contains('hidden'))close()});
  sync();

  window.openAccessibilityPanel=open;
}

function initAiTheme(){
  const reduceMotion=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const ambient=document.createElement('div');
  ambient.className='ai-ambient';
  ambient.setAttribute('aria-hidden','true');
  const colors=['#5b7cff','#8b5cf6','#22d3ee','#7aa2ff'];
  for(let i=0;i<12;i++){
    const node=document.createElement('span');
    node.className='ai-node';
    node.style.setProperty('--x',`${7+((i*23)%88)}%`);
    node.style.setProperty('--y',`${5+((i*31)%90)}%`);
    node.style.setProperty('--s',`${8+(i%4)*3}px`);
    node.style.setProperty('--c',colors[i%colors.length]);
    node.style.setProperty('--d',`${7+(i%5)*1.6}s`);
    node.style.setProperty('--delay',`${-(i%6)*1.2}s`);
    node.style.setProperty('--r',`${(i*37)%180-90}deg`);
    ambient.appendChild(node);
  }
  const scanline=document.createElement('span');scanline.className='ai-scanline';ambient.appendChild(scanline);
  document.body.prepend(ambient);

  document.querySelectorAll('.hero').forEach(hero=>{
    const stream=document.createElement('div');stream.className='ai-data-stream';stream.setAttribute('aria-hidden','true');
    [34,18,42,26,38,15,31,22,40].forEach((h,i)=>{
      const bar=document.createElement('span');bar.style.setProperty('--h',`${h}px`);bar.style.setProperty('--d',`${1.3+(i%4)*.35}s`);bar.style.setProperty('--delay',`${-(i%3)*.4}s`);stream.appendChild(bar);
    });
    hero.appendChild(stream);
    if(!reduceMotion&&window.matchMedia?.('(pointer:fine)').matches){
      hero.addEventListener('pointermove',event=>{
        if(document.documentElement.classList.contains('a11y-reduced-motion'))return;
        const rect=hero.getBoundingClientRect();
        const x=(event.clientX-rect.left)/rect.width-.5;
        const y=(event.clientY-rect.top)/rect.height-.5;
        hero.style.setProperty('--hero-ry',`${x*2.2}deg`);
        hero.style.setProperty('--hero-rx',`${y*-1.7}deg`);
      });
      hero.addEventListener('pointerleave',()=>{hero.style.setProperty('--hero-ry','0deg');hero.style.setProperty('--hero-rx','0deg')});
    }
  });

  if(!reduceMotion&&window.matchMedia?.('(pointer:fine)').matches){
    let frame=0;
    window.addEventListener('pointermove',event=>{
      cancelAnimationFrame(frame);
      frame=requestAnimationFrame(()=>{
        document.documentElement.style.setProperty('--mx',`${Math.round(event.clientX/window.innerWidth*100)}%`);
        document.documentElement.style.setProperty('--my',`${Math.round(event.clientY/window.innerHeight*100)}%`);
      });
    },{passive:true});
  }
}

window.speakText=speakText;
window.stopSpeech=stopSpeech;
window.speakPage=speakPage;
document.addEventListener('DOMContentLoaded',initA11yPanel);
document.addEventListener('DOMContentLoaded',initAiTheme);
