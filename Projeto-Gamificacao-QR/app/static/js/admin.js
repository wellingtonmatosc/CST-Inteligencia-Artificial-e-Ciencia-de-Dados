const $=s=>document.querySelector(s);
const msg=$('#message');
let session=null,catalog={categories:[],zones:[],teams:[],blocked_terms:[]};
let questions=[],stations=[],trails=[],participants=[],manualActions=[];

const roleCan=(...roles)=>session&&roles.includes(session.role);
const labelRole=r=>({admin:'Administrador',operator:'Operador',validator:'Validador',viewer:'Consulta'})[r]||r;
const labelStation=t=>({permanent:'Permanente',sequential:'Sequencial',temporary:'Temporário',special:'Especial'})[t]||t;
const optionRows=(rows,label='name')=>rows.map(x=>`<option value="${esc(x.id)}">${esc(x[label])}</option>`).join('');
const isoLocal=v=>{if(!v)return'';const d=new Date(v);if(Number.isNaN(d.getTime()))return'';const p=n=>String(n).padStart(2,'0');return`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`};

function showError(err){showMessage(msg,err.message||'Falha na operação.','error')}
function formEnabled(id,enabled){document.querySelectorAll(`#${id} input,#${id} textarea,#${id} select,#${id} button`).forEach(el=>el.disabled=!enabled)}
function applyPermissions(){
  const manage=roleCan('admin','operator'),validate=roleCan('admin','operator','validator'),isAdmin=roleCan('admin');
  ['questionForm','stationForm','contentForm','trailForm','trailStepsForm','blockedForm'].forEach(id=>formEnabled(id,manage));
  formEnabled('manualForm',validate);formEnabled('adminUserForm',isAdmin);
  $('#adminUsersCard').classList.toggle('hidden',!isAdmin);
}

async function safeAdminUsers(){if(!roleCan('admin'))return{users:[]};return api('/api/admin/users')}
async function refresh(){
  try{
    const s=await api('/api/admin/session');session=s;
    const [o,c,q,st,tr,p,m,a,u]=await Promise.all([
      api('/api/admin/overview'),api('/api/admin/catalog'),api('/api/admin/questions'),api('/api/admin/stations'),
      api('/api/admin/trails'),api('/api/admin/participants'),api('/api/admin/manual-actions'),api('/api/admin/audit'),safeAdminUsers()
    ]);
    catalog=c;questions=q.questions||[];stations=st.stations||[];trails=tr.trails||[];participants=p.participants||[];manualActions=m.actions||[];
    $('#loginCard').classList.add('hidden');$('#dashboard').classList.remove('hidden');
    $('#adminIdentity').textContent=`${session.username} • ${labelRole(session.role)}`;
    $('#overview').innerHTML=`<div class="admin-stat"><strong>${o.participants}</strong><span>participantes</span></div><div class="admin-stat"><strong>${o.questions}</strong><span>desafios</span></div><div class="admin-stat"><strong>${o.stations}</strong><span>estações</span></div><div class="admin-stat"><strong>${o.trails}</strong><span>trilhas</span></div><div class="admin-stat"><strong>${o.visits}</strong><span>validações</span></div><div class="admin-stat"><strong>${o.manual_actions}</strong><span>extras</span></div>`;
    renderCatalog();renderQuestions();renderParticipants();renderStations();renderTrails();renderManual();renderAudit(a.events||[]);renderAdminUsers(u.users||[]);applyPermissions();
  }catch(err){
    $('#dashboard').classList.add('hidden');$('#loginCard').classList.remove('hidden');
    if(!String(err.message||'').includes('não autorizado'))showError(err);
  }
}

function renderCatalog(){
  $('#questionCategory').innerHTML=optionRows(catalog.categories.filter(x=>x.active));
  $('#stationZone').innerHTML=optionRows(catalog.zones.filter(x=>x.active));
  $('#blockedList').innerHTML=catalog.blocked_terms.length?catalog.blocked_terms.map(x=>`<div class="admin-list-item"><div><strong>${esc(x.term)}</strong>${x.reason?`<br><span class="muted">${esc(x.reason)}</span>`:''}</div><button class="secondary compact" data-term-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p class="muted">Nenhum termo adicional.</p>';
  document.querySelectorAll('[data-term-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/blocked-terms/${b.dataset.termToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});
}

function renderQuestions(){
  $('#contentQuestion').innerHTML='<option value="">Sem desafio</option>'+questions.filter(x=>x.active).map(x=>`<option value="${x.id}">${esc(x.prompt)}</option>`).join('');
  $('#questionList').innerHTML=questions.length?questions.map(x=>`<div class="admin-list-item"><div><span class="pill">${esc(x.kind)}</span> <span class="pill">nível ${x.difficulty}</span><br>${esc(x.prompt)}</div>${roleCan('admin','operator')?`<button class="secondary compact" data-question-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button>`:''}</div>`).join(''):'<p class="muted">Nenhum desafio cadastrado.</p>';
  document.querySelectorAll('[data-question-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/questions/${b.dataset.questionToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});
}

function renderParticipants(){
  $('#manualParticipant').innerHTML=participants.filter(x=>x.active&&!x.is_organizer).map(x=>`<option value="${x.id}">${esc(x.nick)} — ${esc(x.full_name)}</option>`).join('');
  $('#participantList').innerHTML=participants.length?participants.map(x=>{const team=x.teams?.name||'equipe ainda não definida';const status=x.is_organizer?'Organizador':team;return`<div class="admin-list-item"><div><strong>${esc(x.nick)}</strong> <span class="muted">${esc(x.full_name)}</span><br><span class="pill">${esc(x.participant_type)}</span> <span class="pill">${esc(status)}</span></div>${roleCan('admin')?`<button class="secondary compact" data-organizer="${x.id}" data-value="${x.is_organizer?'false':'true'}">${x.is_organizer?'Voltar à competição':'Marcar organizador'}</button>`:''}</div>`}).join(''):'<p class="muted">Nenhum participante.</p>';
  document.querySelectorAll('[data-organizer]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/participants/${b.dataset.organizer}/organizer`,{method:'POST',body:JSON.stringify({is_organizer:b.dataset.value==='true'})});await refresh()}catch(e){showError(e)}});
}

function stationOptionText(s){return`${s.code} — ${s.name} (${labelStation(s.station_type)})`}
function renderStations(){
  const opts=stations.map(s=>`<option value="${s.id}">${esc(stationOptionText(s))}</option>`).join('');
  $('#contentStation').innerHTML=opts;
  $('#stepsStations').innerHTML=stations.filter(s=>s.station_type==='sequential').map(s=>`<option value="${s.id}">${esc(stationOptionText(s))}</option>`).join('');
  $('#stationList').innerHTML=stations.length?stations.map(s=>`<div class="admin-list-item"><div><strong>${esc(s.code)}</strong> — ${esc(s.name)}<br><span class="pill">${esc(labelStation(s.station_type))}</span> <span class="pill">${Number(s.base_points)} pts</span> <span class="pill">${s.has_physical_code?'código físico':'sem código físico'}</span>${s.active?'':' <span class="pill">inativa</span>'}</div>${roleCan('admin','operator')?`<div class="inline-actions"><button class="secondary compact" data-station-edit="${s.id}">Editar</button><button class="secondary compact" data-station-toggle="${s.id}">${s.active?'Desativar':'Ativar'}</button></div>`:''}</div>`).join(''):'<p class="muted">Nenhuma estação.</p>';
  document.querySelectorAll('[data-station-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/stations/${b.dataset.stationToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});
  document.querySelectorAll('[data-station-edit]').forEach(b=>b.onclick=()=>beginStationEdit(b.dataset.stationEdit));
  loadSelectedContent();
}

function beginStationEdit(id){
  const s=stations.find(x=>x.id===id);if(!s)return;
  $('#stationId').value=s.id;$('#stationCode').value=s.code;$('#stationName').value=s.name;$('#stationZone').value=s.zone_id;$('#stationType').value=s.station_type;$('#stationPoints').value=s.base_points;$('#physicalCode').value='';$('#activeFrom').value=isoLocal(s.active_from);$('#activeUntil').value=isoLocal(s.active_until);$('#locationHint').value=s.location_hint||'';$('#stationSubmit').textContent='Salvar estação';$('#stationCancelEdit').classList.remove('hidden');$('#stationCode').focus();
}
function cancelStationEdit(){ $('#stationForm').reset();$('#stationId').value='';$('#stationPoints').value='10';$('#stationSubmit').textContent='Criar estação';$('#stationCancelEdit').classList.add('hidden') }
$('#stationCancelEdit').onclick=cancelStationEdit;
$('#stationType').onchange=e=>{const defaults={permanent:10,sequential:15,temporary:30,special:40};$('#stationPoints').value=defaults[e.target.value]??10};

function loadSelectedContent(){
  const id=$('#contentStation').value;if(!id)return;const s=stations.find(x=>x.id===id);const c=Array.isArray(s?.station_contents)?s.station_contents[0]:s?.station_contents;if(!c){$('#contentForm').reset();$('#contentStation').value=id;$('#challengePoints').value='10';return}
  $('#contentKind').value=c.content_kind||'mixed';$('#contentTitle').value=c.title||'';$('#contentAuthor').value=c.author_name||'';$('#contentBody').value=c.body||'';$('#contentMediaType').value=c.media_type||'';$('#contentMediaUrl').value=c.media_url||'';$('#contentAlt').value=c.accessibility?.alt_text||'';$('#contentTranscript').value=c.accessibility?.transcript||'';$('#contentQuestion').value=c.challenge_question_id||'';$('#challengePoints').value=c.challenge_points??10;$('#completionBody').value=c.completion_body||'';
}
$('#contentStation').onchange=loadSelectedContent;

function renderTrails(){
  $('#stepsTrail').innerHTML=optionRows(trails);
  $('#trailList').innerHTML=trails.length?trails.map(t=>`<div class="admin-list-item"><div><strong>${esc(t.name)}</strong><br><span class="muted">${Number(t.completion_points)} pts de conclusão • ${(t.steps||[]).length} etapas</span>${(t.steps||[]).length?`<ol>${t.steps.map(s=>`<li>${esc(s.qr_points?.code||s.qr_point_id)}</li>`).join('')}</ol>`:''}</div></div>`).join(''):'<p class="muted">Nenhuma trilha.</p>';
}

function renderManual(){
  $('#manualList').innerHTML=manualActions.length?manualActions.map(a=>`<div class="admin-list-item"><div><strong>${esc(a.participants?.nick||'Participante')}</strong> • ${Number(a.points)} pts<br>${esc(a.description)}<br><span class="muted">${esc(a.action_type)} • ${esc(a.approved_by)} • ${a.status==='reversed'?'estornado':'aprovado'}</span></div>${a.status==='approved'&&roleCan('admin','operator','validator')?`<button class="secondary compact" data-reverse="${a.id}">Estornar</button>`:''}</div>`).join(''):'<p class="muted">Nenhum ponto extra lançado.</p>';
  document.querySelectorAll('[data-reverse]').forEach(b=>b.onclick=async()=>{const reason=prompt('Motivo do estorno:');if(!reason||reason.trim().length<3)return;try{await api(`/api/admin/manual-actions/${b.dataset.reverse}/reverse`,{method:'POST',body:JSON.stringify({reason})});await refresh()}catch(e){showError(e)}});
}

function renderAudit(events){
  $('#auditList').innerHTML=events.length?events.slice(0,40).map(e=>`<p><strong>${esc(e.action)}</strong><br><span class="muted">${esc(e.actor_username)} • ${esc(e.actor_role)} • ${new Date(e.created_at).toLocaleString('pt-BR')}</span></p>`).join(''):'<p class="muted">Nenhum evento administrativo.</p>';
}
function renderAdminUsers(users){
  $('#adminUserList').innerHTML=users.length?users.map(u=>`<div class="admin-list-item"><div><strong>${esc(u.username)}</strong><br><span class="muted">${esc(labelRole(u.role))} • ${u.active?'ativo':'inativo'}</span></div><button class="secondary compact" data-admin-toggle="${u.id}">${u.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p class="muted">Nenhum usuário cadastrado no banco. O administrador de ambiente continua disponível como bootstrap.</p>';
  document.querySelectorAll('[data-admin-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/users/${b.dataset.adminToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});
}

$('#loginForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/login',{method:'POST',body:JSON.stringify({username:f.get('username'),password:f.get('password')})});e.target.reset();await refresh()}catch(err){showError(err)}});
$('#adminLogout').onclick=async()=>{try{await api('/api/admin/logout',{method:'POST'})}finally{session=null;$('#dashboard').classList.add('hidden');$('#loginCard').classList.remove('hidden')}};

$('#blockedForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/blocked-terms',{method:'POST',body:JSON.stringify({term:f.get('term'),reason:f.get('reason')||null})});e.target.reset();await refresh()}catch(err){showError(err)}});

$('#questionForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),kind=f.get('kind'),correct=String(f.get('correct')).trim();let raw=String(f.get('options')||'').split('\n').map(x=>x.trim()).filter(Boolean);if(kind==='true_false'&&raw.length===0)raw=['Verdadeiro','Falso'];if(kind==='multiple_choice'&&raw.length<2){showMessage(msg,'Múltipla escolha precisa de pelo menos duas alternativas.','error');return}const mediaType=f.get('media_type')||null;const payload={category_id:f.get('category_id'),kind,prompt:f.get('prompt'),options:raw.map(v=>({value:v,label:v})),correct_answer:kind==='short_text'?{value:correct,accepted:correct.split('|').map(x=>x.trim()).filter(Boolean)}:{value:correct},explanation:f.get('explanation')||null,difficulty:Number(f.get('difficulty')||1),media_type:mediaType,media_url:f.get('media_url')||null,accessibility:{instructions_clear:f.get('instructions_clear')==='on',depends_on_color_only:false,requires_speed:false,reading_level:f.get('reading_level')||'básica',simplified_prompt:f.get('simplified_prompt')||null,alt_text:f.get('alt_text')||null,transcript:f.get('transcript')||null,screen_reader_ready:true,equivalent_text:true},active:true};try{await api('/api/admin/questions',{method:'POST',body:JSON.stringify(payload)});e.target.reset();$('#instructionsClear').checked=true;await refresh()}catch(err){showError(err)}});

$('#stationForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),id=f.get('station_id');const payload={code:f.get('code'),name:f.get('name'),zone_id:f.get('zone_id'),station_type:f.get('station_type'),base_points:Number(f.get('base_points')),physical_code:f.get('physical_code')||null,active_from:f.get('active_from')?new Date(f.get('active_from')).toISOString():null,active_until:f.get('active_until')?new Date(f.get('active_until')).toISOString():null,location_hint:f.get('location_hint')||null,active:true};try{await api(id?`/api/admin/stations/${id}`:'/api/admin/stations',{method:id?'PUT':'POST',body:JSON.stringify(payload)});cancelStationEdit();await refresh()}catch(err){showError(err)}});

$('#contentForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),stationId=f.get('station_id'),mediaType=f.get('media_type')||null;const payload={content_kind:f.get('content_kind'),title:f.get('title'),body:f.get('body')||null,author_name:f.get('author_name')||null,media_type:mediaType,media_url:f.get('media_url')||null,accessibility:{plain_text:true,screen_reader_ready:true,alt_text:f.get('alt_text')||null,transcript:f.get('transcript')||null},challenge_question_id:f.get('challenge_question_id')||null,challenge_points:Number(f.get('challenge_points')||0),completion_body:f.get('completion_body')||null};try{await api(`/api/admin/stations/${stationId}/content`,{method:'PUT',body:JSON.stringify(payload)});await refresh();showMessage(msg,'Conteúdo salvo.','success')}catch(err){showError(err)}});

$('#trailForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);const payload={slug:String(f.get('slug')).trim().toLowerCase(),name:f.get('name'),description:f.get('description')||null,completion_points:Number(f.get('completion_points')||30),completion_title:null,completion_body:null,active:true};try{await api('/api/admin/trails',{method:'POST',body:JSON.stringify(payload)});e.target.reset();$('#trailCompletionPoints').value='30';await refresh()}catch(err){showError(err)}});
$('#trailStepsForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),ids=[...$('#stepsStations').selectedOptions].map(o=>o.value);if(!ids.length){showMessage(msg,'Selecione pelo menos uma estação sequencial.','error');return}try{await api(`/api/admin/trails/${f.get('trail_id')}/steps`,{method:'PUT',body:JSON.stringify({qr_point_ids:ids})});await refresh()}catch(err){showError(err)}});

$('#manualForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/manual-actions',{method:'POST',body:JSON.stringify({participant_id:f.get('participant_id'),action_type:f.get('action_type'),description:f.get('description'),evidence:f.get('evidence')||null,points:Number(f.get('points'))})});e.target.reset();$('#manualPoints').value='20';await refresh()}catch(err){showError(err)}});

$('#adminUserForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/users',{method:'POST',body:JSON.stringify({username:f.get('username'),password:f.get('password'),role:f.get('role')})});e.target.reset();await refresh()}catch(err){showError(err)}});

refresh();