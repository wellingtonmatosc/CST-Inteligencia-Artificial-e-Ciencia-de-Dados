const $=s=>document.querySelector(s);
const msg=$('#message');
let catalog={categories:[],zones:[],blocked_terms:[]},questions=[],qrs=[];

function optionsHtml(rows,label='name'){return rows.map(x=>`<option value="${esc(x.id)}">${esc(x[label])}</option>`).join('')}
function kindLabel(kind){return ({multiple_choice:'Múltipla escolha',true_false:'Verdadeiro/Falso',short_text:'Resposta curta',association:'Associação',ordering:'Ordenação'})[kind]||kind}

async function refresh(){
  try{
    const [o,q,qr,b,c,a]=await Promise.all([api('/api/admin/overview'),api('/api/admin/questions'),api('/api/admin/qrs'),api('/api/admin/bonus'),api('/api/admin/catalog'),api('/api/admin/analytics')]);
    catalog=c;questions=q.questions;qrs=qr.qrs;
    $('#loginCard').classList.add('hidden');$('#dashboard').classList.remove('hidden');
    $('#overview').innerHTML=`<div class="admin-stat"><strong>${o.participants}</strong><span>participantes</span></div><div class="admin-stat"><strong>${o.questions}</strong><span>questões</span></div><div class="admin-stat"><strong>${o.qr_points}</strong><span>QR Codes</span></div><div class="admin-stat"><strong>${o.attempts}</strong><span>tentativas</span></div><div class="admin-stat"><strong>${o.correct_attempts}</strong><span>acertos</span></div>`;
    $('#questionCategory').innerHTML=optionsHtml(c.categories.filter(x=>x.active));$('#qrZone').innerHTML=optionsHtml(c.zones.filter(x=>x.active));
    $('#linkQr').innerHTML=optionsHtml(qr.qrs.filter(x=>x.kind==='normal'&&x.active),'name');$('#linkQuestion').innerHTML=optionsHtml(q.questions.filter(x=>x.active),'prompt');
    $('#questionList').innerHTML=q.questions.length?q.questions.map(x=>`<div class="admin-list-item"><div><span class="pill">${esc(kindLabel(x.kind))}</span><span class="pill">Nível ${x.difficulty}</span><br>${esc(x.prompt)}</div><button class="secondary compact" data-question-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p>Nenhuma questão cadastrada.</p>';
    $('#qrList').innerHTML=qr.qrs.length?qr.qrs.map(x=>`<div class="admin-list-item"><div><strong>${esc(x.code)}</strong><br><span class="muted">${esc(x.name)} · ${esc(x.kind)}</span></div><button class="secondary compact" data-qr-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p>Nenhum QR cadastrado.</p>';
    $('#blockedList').innerHTML=c.blocked_terms.length?c.blocked_terms.map(x=>`<div class="admin-list-item"><span>${esc(x.term)}</span><button class="secondary compact" data-term-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p>Nenhum termo adicional cadastrado.</p>';
    $('#bonusList').innerHTML=b.campaigns.length?b.campaigns.map(x=>`<p><strong>${esc(x.event_date)}</strong> · ${esc(x.name)} · ${esc(x.bonus_type)} · ${x.points} pts</p>`).join(''):'<p>Nenhum bônus configurado.</p>';
    const byType=Object.entries(a.participants_by_type).map(([k,v])=>`<li>${esc(k)}: ${v}</li>`).join('');
    const byCat=Object.entries(a.questions_by_category).map(([k,v])=>`<li>${esc(k)}: ${v.correct}/${v.attempts} acertos</li>`).join('');
    $('#analytics').innerHTML=`<h3>Participantes por tipo</h3><ul>${byType||'<li>Sem dados</li>'}</ul><h3>Desempenho por categoria</h3><ul>${byCat||'<li>Sem dados</li>'}</ul>`;
    bindToggles();
  }catch(_){$('#dashboard').classList.add('hidden');$('#loginCard').classList.remove('hidden')}
}

function bindToggles(){
  document.querySelectorAll('[data-question-toggle]').forEach(b=>b.onclick=()=>toggle(`/api/admin/questions/${b.dataset.questionToggle}/toggle`));
  document.querySelectorAll('[data-qr-toggle]').forEach(b=>b.onclick=()=>toggle(`/api/admin/qrs/${b.dataset.qrToggle}/toggle`));
  document.querySelectorAll('[data-term-toggle]').forEach(b=>b.onclick=()=>toggle(`/api/admin/blocked-terms/${b.dataset.termToggle}/toggle`));
}

async function toggle(url){try{await api(url,{method:'POST'});await refresh()}catch(e){showMessage(msg,e.message,'error')}}

$('#loginForm').addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(e.target);
  try{await api('/api/admin/login',{method:'POST',body:JSON.stringify({username:f.get('username'),password:f.get('password')})});showMessage(msg,'Acesso liberado.','success');await refresh()}catch(err){showMessage(msg,err.message,'error')}
});

$('#blockedForm').addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(e.target);
  try{await api('/api/admin/blocked-terms',{method:'POST',body:JSON.stringify({term:f.get('term'),reason:f.get('reason')||null})});e.target.reset();await refresh()}catch(err){showMessage(msg,err.message,'error')}
});

$('#questionForm').addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(e.target),kind=f.get('kind'),correct=String(f.get('correct')).trim();
  let raw=String(f.get('options')||'').split('\n').map(x=>x.trim()).filter(Boolean);
  if(kind==='true_false'&&raw.length===0)raw=['Verdadeiro','Falso'];
  if(kind==='multiple_choice'&&raw.length<2){showMessage(msg,'Múltipla escolha precisa de pelo menos duas alternativas.','error');return}
  const mediaType=f.get('media_type')||null;
  const payload={
    category_id:f.get('category_id'),kind,prompt:f.get('prompt'),
    options:raw.map(v=>({value:v,label:v})),
    correct_answer:kind==='short_text'?{value:correct,accepted:correct.split('|').map(x=>x.trim()).filter(Boolean)}:{value:correct},
    explanation:f.get('explanation')||null,difficulty:Number(f.get('difficulty')||1),
    media_type:mediaType,media_url:f.get('media_url')||null,
    accessibility:{
      instructions_clear:f.get('instructions_clear')==='on',
      depends_on_color_only:false,requires_speed:false,
      reading_level:f.get('reading_level')||'básica',
      simplified_prompt:f.get('simplified_prompt')||null,
      alt_text:f.get('alt_text')||null,
      transcript:f.get('transcript')||null,
    },
    active:true
  };
  try{await api('/api/admin/questions',{method:'POST',body:JSON.stringify(payload)});e.target.reset();$('#instructionsClear').checked=true;showMessage(msg,'Questão criada e validada.','success');await refresh()}catch(err){showMessage(msg,err.message,'error')}
});

$('#qrForm').addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(e.target);
  try{await api('/api/admin/qrs',{method:'POST',body:JSON.stringify({code:f.get('code'),name:f.get('name'),zone_id:f.get('zone_id'),kind:f.get('kind'),active:true})});e.target.reset();showMessage(msg,'QR cadastrado.','success');await refresh()}catch(err){showMessage(msg,err.message,'error')}
});

$('#linkForm').addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(e.target);
  try{await api(`/api/admin/qrs/${f.get('qr_id')}/questions/${f.get('question_id')}`,{method:'POST'});showMessage(msg,'Questão vinculada ao QR.','success')}catch(err){showMessage(msg,err.message,'error')}
});

refresh();
