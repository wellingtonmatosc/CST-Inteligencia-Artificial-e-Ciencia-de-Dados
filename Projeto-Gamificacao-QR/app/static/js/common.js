const a11yStylesheet=document.createElement('link');
a11yStylesheet.rel='stylesheet';a11yStylesheet.href='/static/css/accessibility.css';document.head.appendChild(a11yStylesheet);

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

const A11Y_STORAGE_KEY='gamificacao-a11y-v1';
const A11Y_DEFAULTS={fontScale:1,lightMode:false,contrast:false,reducedMotion:false,roomy:false,reading:false};

function loadA11y(){
  try{return {...A11Y_DEFAULTS,...JSON.parse(localStorage.getItem(A11Y_STORAGE_KEY)||'{}')}}catch(_){return {...A11Y_DEFAULTS}}
}

function saveA11y(prefs){localStorage.setItem(A11Y_STORAGE_KEY,JSON.stringify(prefs))}

function applyA11y(prefs){
  const root=document.documentElement;
  root.style.fontSize=`${Math.round(prefs.fontScale*100)}%`;
  root.classList.toggle('a11y-light',Boolean(prefs.lightMode));
  root.classList.toggle('a11y-contrast',Boolean(prefs.contrast));
  root.classList.toggle('a11y-reduced-motion',Boolean(prefs.reducedMotion));
  root.classList.toggle('a11y-roomy',Boolean(prefs.roomy));
  root.classList.toggle('a11y-reading',Boolean(prefs.reading));
}

function speakText(text){
  if(!('speechSynthesis' in window))return false;
  window.speechSynthesis.cancel();
  const utterance=new SpeechSynthesisUtterance(String(text||''));
  utterance.lang='pt-BR';utterance.rate=0.95;
  window.speechSynthesis.speak(utterance);return true;
}

function stopSpeech(){if('speechSynthesis' in window)window.speechSynthesis.cancel()}

function initA11yPanel(){
  let prefs=loadA11y();applyA11y(prefs);
  const toggle=document.createElement('button');
  toggle.type='button';toggle.id='a11yToggle';toggle.className='a11y-toggle';
  toggle.setAttribute('aria-haspopup','dialog');toggle.setAttribute('aria-expanded','false');
  toggle.innerHTML='<span aria-hidden="true">◉</span><span>Acessibilidade</span>';

  const panel=document.createElement('section');
  panel.id='a11yPanel';panel.className='a11y-panel hidden';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','false');panel.setAttribute('aria-labelledby','a11yTitle');
  panel.innerHTML=`
    <div class="a11y-panel-head"><div><span class="eyebrow">Preferências</span><h2 id="a11yTitle">Acessibilidade</h2></div><button type="button" class="secondary compact" id="a11yClose" aria-label="Fechar painel de acessibilidade">Fechar</button></div>
    <p class="muted">As preferências ficam salvas somente neste navegador.</p>
    <div class="a11y-control"><span><strong>Baixa visão</strong><small>Aumenta o texto, reforça o contraste, amplia o espaçamento e prioriza a leitura.</small></span><div class="inline-actions"><button type="button" class="secondary" data-a11y="low-vision">Ativar modo baixa visão</button></div></div>
    <div class="a11y-control"><span><strong>Tamanho do texto</strong><small id="a11yFontStatus" aria-live="polite"></small></span><div class="inline-actions"><button type="button" class="secondary compact" data-a11y="font-down" aria-label="Diminuir texto">A−</button><button type="button" class="secondary compact" data-a11y="font-up" aria-label="Aumentar texto">A+</button></div></div>
    <label class="switch-row"><input type="checkbox" data-a11y-check="lightMode"><span><strong>Modo claro</strong><small>Troca para fundo claro mantendo contraste.</small></span></label>
    <label class="switch-row"><input type="checkbox" data-a11y-check="contrast"><span><strong>Alto contraste</strong><small>Reforça contraste e contornos.</small></span></label>
    <label class="switch-row"><input type="checkbox" data-a11y-check="reducedMotion"><span><strong>Reduzir animações</strong><small>Remove movimentos e transições desnecessárias.</small></span></label>
    <label class="switch-row"><input type="checkbox" data-a11y-check="roomy"><span><strong>Mais espaçamento</strong><small>Aumenta áreas de toque e separação entre elementos.</small></span></label>
    <label class="switch-row"><input type="checkbox" data-a11y-check="reading"><span><strong>Modo leitura</strong><small>Remove elementos decorativos e prioriza o conteúdo.</small></span></label>
    <p class="muted"><small>A interface usa rótulos, foco visível e navegação por teclado para apoiar o uso com leitores de tela.</small></p>
    <div class="inline-actions a11y-footer"><button type="button" class="secondary" data-a11y="reset">Restaurar padrão</button></div>`;

  document.body.append(toggle,panel);
  const fontStatus=()=>{const el=panel.querySelector('#a11yFontStatus');if(el)el.textContent=` ${Math.round(prefs.fontScale*100)}%`};
  const sync=()=>{panel.querySelectorAll('[data-a11y-check]').forEach(input=>{input.checked=Boolean(prefs[input.dataset.a11yCheck])});fontStatus();applyA11y(prefs);saveA11y(prefs)};
  const open=()=>{panel.classList.remove('hidden');toggle.setAttribute('aria-expanded','true');panel.querySelector('#a11yClose').focus()};
  const close=()=>{panel.classList.add('hidden');toggle.setAttribute('aria-expanded','false');toggle.focus()};
  toggle.addEventListener('click',()=>panel.classList.contains('hidden')?open():close());panel.querySelector('#a11yClose').addEventListener('click',close);
  panel.querySelectorAll('[data-a11y-check]').forEach(input=>input.addEventListener('change',()=>{prefs[input.dataset.a11yCheck]=input.checked;sync()}));
  panel.querySelectorAll('[data-a11y]').forEach(button=>button.addEventListener('click',()=>{
    const action=button.dataset.a11y;
    if(action==='font-up')prefs.fontScale=Math.min(1.4,Math.round((prefs.fontScale+0.1)*10)/10);
    if(action==='font-down')prefs.fontScale=Math.max(0.9,Math.round((prefs.fontScale-0.1)*10)/10);
    if(action==='low-vision')prefs={...prefs,fontScale:1.3,contrast:true,reducedMotion:true,roomy:true,reading:true};
    if(action==='reset')prefs={...A11Y_DEFAULTS};
    sync();
  }));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.classList.contains('hidden'))close()});sync();
}

window.speakText=speakText;window.stopSpeech=stopSpeech;
document.addEventListener('DOMContentLoaded',initA11yPanel);
