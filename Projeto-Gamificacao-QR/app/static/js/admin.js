const $=s=>document.querySelector(s);
const msg=$('#message');
let session=null;
let catalog={categories:[],zones:[],blocked_terms:[]};
let questions=[],stations=[],trails=[],participants=[],manualActions=[],ranking=[],dashboardStats={};

const labelStation=t=>({permanent:'Permanente',sequential:'Sequencial',temporary:'Temporária',special:'Especial'})[t]||t;
const optionRows=(rows,label='name')=>rows.map(x=>`<option value="${esc(x.id)}">${esc(x[label])}</option>`).join('');
const isoLocal=v=>{if(!v)return'';const d=new Date(v);if(Number.isNaN(d.getTime()))return'';const p=n=>String(n).padStart(2,'0');return`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`};
const participantType=t=>({student:'Aluno IFMT',staff:'Servidor IFMT',external:'Público externo'})[t]||t;

function showError(err){showMessage(msg,err.message||'Falha na operação.','error')}
function hideMessage(){msg.classList.add('hidden')}

function enforceFinalUiRules(){
  const kind=$('#questionKind');if(kind){kind.value='multiple_choice';const wrap=kind.closest('div');if(wrap)wrap.hidden=true}
  const points=$('#stationPoints');if(points){points.value='10';points.readOnly=true;points.setAttribute('aria-readonly','true')}
  const challenge=$('#contentQuestion');if(challenge){challenge.value='';const wrap=challenge.closest('div');if(wrap)wrap.hidden=true}
  const challengePoints=$('#challengePoints');if(challengePoints){challengePoints.value='10';challengePoints.readOnly=true;const wrap=challengePoints.closest('div');if(wrap)wrap.hidden=true}
  const rankingCopy=$('#rankingPanel .muted');if(rankingCopy)rankingCopy.textContent='Pontos; em empate: acertos, acertos na 1ª tentativa, QRs distintos, dias ativos e desempate supervisionado do Dia 7.';
}

function showTab(id){
  document.querySelectorAll('.admin-panel').forEach(p=>p.hidden=p.id!==id);
  document.querySelectorAll('[data-admin-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.adminTab===id)));
  if(location.hash!==`#${id}`)history.replaceState(null,'',`#${id}`);
}
document.querySelectorAll('[data-admin-tab]').forEach(b=>b.onclick=()=>showTab(b.dataset.adminTab));
document.querySelectorAll('[data-go-tab]').forEach(b=>b.onclick=()=>showTab(b.dataset.goTab));

function renderOverview(){
  const s=dashboardStats;
  const stats=[[s.participants_active||0,'participantes ativos'],[s.competitors_active||0,'na competição'],[s.points_total||0,'pontos acumulados'],[s.active_stations||0,'estações ativas'],[s.validations_total||0,'validações'],[s.pending_challenges||0,'desafios pendentes'],[s.active_questions||0,'desafios ativos'],[s.trails_total||0,'trilhas ativas']];
  $('#overview').innerHTML=stats.map(([value,label])=>`<div class="admin-stat"><strong>${Number(value).toLocaleString('pt-BR')}</strong><span>${esc(label)}</span></div>`).join('');
}

function buildAlerts(){
  const alerts=[],now=Date.now(),day=86400000;
  stations.filter(s=>s.active&&!s.has_physical_code).forEach(s=>alerts.push({title:`${s.code}: sem código físico`,text:'A estação está ativa sem validação física configurada.'}));
  stations.filter(s=>s.active&&!((Array.isArray(s.station_contents)?s.station_contents[0]:s.station_contents))).forEach(s=>alerts.push({title:`${s.code}: sem conteúdo`,text:'A estação está ativa, mas ainda não possui conteúdo cultural.'}));
  stations.filter(s=>s.active&&s.station_type==='temporary').forEach(s=>{if(!s.active_until)alerts.push({title:`${s.code}: temporária sem encerramento`,text:'Defina a data/hora final da estação temporária.'});else{const end=new Date(s.active_until).getTime();if(end>now&&end-now<=day)alerts.push({title:`${s.code}: expira em breve`,text:`Encerramento: ${new Date(s.active_until).toLocaleString('pt-BR')}.`})}});
  trails.filter(t=>t.active&&(t.steps||[]).length===0).forEach(t=>alerts.push({title:`${t.name}: trilha sem etapas`,text:'A trilha está ativa, mas ainda não possui estações vinculadas.'}));
  if((dashboardStats.pending_challenges||0)>0)alerts.push({title:`${dashboardStats.pending_challenges} desafio(s) pendente(s)`,text:'Há participantes que validaram a estação, mas ainda não finalizaram o desafio.'});
  return alerts.slice(0,12);
}
function renderAlerts(){const alerts=buildAlerts();$('#alertList').innerHTML=alerts.length?alerts.map(a=>`<div class="admin-alert"><strong>${esc(a.title)}</strong><span>${esc(a.text)}</span></div>`).join(''):'<div class="admin-empty">Nenhum alerta operacional no momento.</div>'}

function rankRow(r){
  const avatar=window.TrilhasAvatars?.avatarMarkup(r.avatar_key,'admin-avatar',`Avatar de ${r.nick}`)||'';
  return `<div class="admin-list-item admin-rank"><span class="admin-rank-position">${r.position?`${r.position}º`:'—'}</span><div>${avatar}<strong>${esc(r.nick)}</strong><div class="meta"><span class="pill">${Number(r.correct_answers||0)} acertos</span><span class="pill">${Number(r.first_try_correct||0)} de primeira</span><span class="pill">${Number(r.distinct_qrs||0)} QRs</span></div></div><span class="admin-rank-score">${Number(r.points||0)} pts</span></div>`;
}
function renderRanking(){const html=ranking.length?ranking.map(rankRow).join(''):'<div class="admin-empty">A classificação ainda não foi iniciada.</div>';$('#adminRankingList').innerHTML=html;$('#rankingPreview').innerHTML=ranking.length?ranking.slice(0,5).map(rankRow).join(''):'<div class="admin-empty">A classificação ainda não foi iniciada.</div>'}

function renderCatalog(){
  $('#questionCategory').innerHTML=optionRows(catalog.categories.filter(x=>x.active));
  $('#stationZone').innerHTML=optionRows(catalog.zones.filter(x=>x.active));
  $('#blockedList').innerHTML=catalog.blocked_terms.length?catalog.blocked_terms.map(x=>`<div class="admin-list-item"><div><strong>${esc(x.term)}</strong>${x.reason?`<br><span class="muted">${esc(x.reason)}</span>`:''}</div><div class="actions"><button class="secondary compact" data-term-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div></div>`).join(''):'<div class="admin-empty">Nenhum termo adicional.</div>';
  document.querySelectorAll('[data-term-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/blocked-terms/${b.dataset.termToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});
}

function renderQuestions(){
  $('#questionList').innerHTML=questions.length?questions.map(x=>`<div class="admin-list-item"><div><span class="pill">Múltipla escolha</span> <span class="pill">nível ${x.difficulty}</span><br><strong>${esc(x.prompt)}</strong>${x.explanation?`<br><span class="muted">${esc(x.explanation)}</span>`:''}</div><div class="actions"><button class="secondary compact" data-question-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div></div>`).join(''):'<div class="admin-empty">Nenhum desafio cadastrado.</div>';
  document.querySelectorAll('[data-question-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/questions/${b.dataset.questionToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});
}

function participantMatches(x,term){if(!term)return true;const hay=[x.nick,x.full_name,x.campus,x.course_name,participantType(x.participant_type)].filter(Boolean).join(' ').toLowerCase();return hay.includes(term.toLowerCase())}
function renderParticipants(){
  const search=$('#participantSearch')?.value?.trim()||'',visible=participants.filter(x=>participantMatches(x,search));
  $('#manualParticipant').innerHTML=participants.filter(x=>x.active&&!x.is_organizer).map(x=>`<option value="${x.id}">${esc(x.nick)} — ${esc(x.full_name)}</option>`).join('');
  $('#participantList').innerHTML=visible.length?visible.map(x=>{const detail=[participantType(x.participant_type),x.campus,x.course_name].filter(Boolean).join(' • '),state=x.is_organizer?'Organizador':(x.active?'Ativo':'Desativado');return `<div class="admin-list-item ${x.active?'':'participant-inactive'}"><div><strong>${esc(x.nick)}</strong> <span class="muted">${esc(x.full_name)}</span><br><span class="muted">${esc(detail)}</span><div class="meta"><span class="pill">${esc(state)}</span>${x.position?`<span class="pill">${x.position}º lugar</span>`:''}<span class="pill">${Number(x.stations_validated||0)} validação(ões)</span><span class="pill">${Number(x.distinct_qrs||0)} QR(s) distintos</span></div></div><div><div class="participant-score">${Number(x.points||0)} pts</div><div class="actions"><button class="secondary compact" data-active="${x.id}" data-value="${x.active?'false':'true'}">${x.active?'Desativar':'Reativar'}</button><button class="secondary compact" data-organizer="${x.id}" data-value="${x.is_organizer?'false':'true'}">${x.is_organizer?'Voltar à competição':'Marcar organizador'}</button></div></div></div>`}).join(''):'<div class="admin-empty">Nenhum participante encontrado.</div>';
  document.querySelectorAll('[data-active]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/participants/${b.dataset.active}/active`,{method:'POST',body:JSON.stringify({active:b.dataset.value==='true'})});await refresh()}catch(e){showError(e)}});
  document.querySelectorAll('[data-organizer]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/participants/${b.dataset.organizer}/organizer`,{method:'POST',body:JSON.stringify({is_organizer:b.dataset.value==='true'})});await refresh()}catch(e){showError(e)}});
}
$('#participantSearch')?.addEventListener('input',renderParticipants);

function stationOptionText(s){return`${s.code} — ${s.name} (${labelStation(s.station_type)})`}
function renderStations(){
  const opts=stations.map(s=>`<option value="${s.id}">${esc(stationOptionText(s))}</option>`).join('');$('#contentStation').innerHTML=opts;$('#stepsStations').innerHTML=stations.filter(s=>s.station_type==='sequential').map(s=>`<option value="${s.id}">${esc(stationOptionText(s))}</option>`).join('');
  $('#stationList').innerHTML=stations.length?stations.map(s=>{const content=Array.isArray(s.station_contents)?s.station_contents[0]:s.station_contents;return`<div class="admin-list-item"><div><strong>${esc(s.code)}</strong> — ${esc(s.name)}<div class="meta"><span class="pill">${esc(labelStation(s.station_type))}</span><span class="pill">10 pts por validação</span><span class="pill">${s.has_physical_code?'código físico':'sem código físico'}</span><span class="pill">${content?'conteúdo OK':'sem conteúdo'}</span>${s.active?'':'<span class="pill">inativa</span>'}</div></div><div class="actions"><button class="secondary compact" data-station-edit="${s.id}">Editar</button><button class="secondary compact" data-station-toggle="${s.id}">${s.active?'Desativar':'Ativar'}</button></div></div>`}).join(''):'<div class="admin-empty">Nenhuma estação.</div>';
  document.querySelectorAll('[data-station-toggle]').forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/stations/${b.dataset.stationToggle}/toggle`,{method:'POST'});await refresh()}catch(e){showError(e)}});document.querySelectorAll('[data-station-edit]').forEach(b=>b.onclick=()=>beginStationEdit(b.dataset.stationEdit));loadSelectedContent();
}
function beginStationEdit(id){const s=stations.find(x=>x.id===id);if(!s)return;$('#stationId').value=s.id;$('#stationCode').value=s.code;$('#stationName').value=s.name;$('#stationZone').value=s.zone_id;$('#stationType').value=s.station_type;$('#stationPoints').value='10';$('#physicalCode').value='';$('#activeFrom').value=isoLocal(s.active_from);$('#activeUntil').value=isoLocal(s.active_until);$('#locationHint').value=s.location_hint||'';$('#stationSubmit').textContent='Salvar estação';$('#stationCancelEdit').classList.remove('hidden');$('#stationCode').focus()}
function cancelStationEdit(){$('#stationForm').reset();$('#stationId').value='';$('#stationPoints').value='10';$('#stationSubmit').textContent='Criar estação';$('#stationCancelEdit').classList.add('hidden')}
$('#stationCancelEdit').onclick=cancelStationEdit;$('#stationType').onchange=()=>{$('#stationPoints').value='10'};
function loadSelectedContent(){const id=$('#contentStation').value;if(!id)return;const s=stations.find(x=>x.id===id),c=Array.isArray(s?.station_contents)?s.station_contents[0]:s?.station_contents;if(!c){$('#contentForm').reset();$('#contentStation').value=id;enforceFinalUiRules();return}$('#contentKind').value=c.content_kind||'mixed';$('#contentTitle').value=c.title||'';$('#contentAuthor').value=c.author_name||'';$('#contentBody').value=c.body||'';$('#contentMediaType').value=c.media_type||'';$('#contentMediaUrl').value=c.media_url||'';$('#contentAlt').value=c.accessibility?.alt_text||'';$('#contentTranscript').value=c.accessibility?.transcript||'';$('#completionBody').value=c.completion_body||'';enforceFinalUiRules()}
$('#contentStation').onchange=loadSelectedContent;

function renderTrails(){$('#stepsTrail').innerHTML=optionRows(trails);$('#trailList').innerHTML=trails.length?trails.map(t=>`<div class="admin-list-item"><div><strong>${esc(t.name)}</strong><br><span class="muted">${Number(t.completion_points)} pts de conclusão • ${(t.steps||[]).length} etapas</span>${(t.steps||[]).length?`<ol>${t.steps.map(s=>`<li>${esc(s.qr_points?.code||s.qr_point_id)}</li>`).join('')}</ol>`:''}</div></div>`).join(''):'<div class="admin-empty">Nenhuma trilha.</div>'}
function renderManual(){$('#manualList').innerHTML=manualActions.length?manualActions.map(a=>`<div class="admin-list-item"><div><strong>${esc(a.participants?.nick||'Participante')}</strong> • ${Number(a.points)} pts<br>${esc(a.description)}<br><span class="muted">${esc(a.action_type)} • ${a.status==='reversed'?'estornado':'aprovado'}</span></div>${a.status==='approved'?`<div class="actions"><button class="secondary compact" data-reverse="${a.id}">Estornar</button></div>`:''}</div>`).join(''):'<div class="admin-empty">Nenhum ponto extra lançado.</div>';document.querySelectorAll('[data-reverse]').forEach(b=>b.onclick=async()=>{const reason=prompt('Motivo do estorno:');if(!reason||reason.trim().length<3)return;try{await api(`/api/admin/manual-actions/${b.dataset.reverse}/reverse`,{method:'POST',body:JSON.stringify({reason})});await refresh()}catch(e){showError(e)}})}
function renderAudit(events){$('#auditList').innerHTML=events.length?events.slice(0,100).map(e=>`<div class="admin-list-item"><div><strong>${esc(e.action)}</strong><br><span class="muted">${esc(e.actor_username)} • ${new Date(e.created_at).toLocaleString('pt-BR')}</span></div></div>`).join(''):'<div class="admin-empty">Nenhum evento administrativo.</div>'}

async function refresh(){
  try{hideMessage();session=await api('/api/admin/session');const[d,c,q,st,tr,m,a]=await Promise.all([api('/api/admin/dashboard-data'),api('/api/admin/catalog'),api('/api/admin/questions'),api('/api/admin/stations'),api('/api/admin/trails'),api('/api/admin/manual-actions'),api('/api/admin/audit')]);dashboardStats=d.stats||{};participants=d.participants||[];ranking=d.ranking||[];catalog=c;questions=q.questions||[];stations=st.stations||[];trails=tr.trails||[];manualActions=m.actions||[];$('#loginCard').classList.add('hidden');$('#dashboard').classList.remove('hidden');$('#adminIdentity').textContent=`${session.username} • Administrador`;enforceFinalUiRules();renderOverview();renderCatalog();renderQuestions();renderParticipants();renderStations();renderTrails();renderManual();renderRanking();renderAlerts();renderAudit(a.events||[]);const requested=location.hash.slice(1);if(requested&&document.getElementById(requested)?.classList.contains('admin-panel'))showTab(requested)}catch(err){$('#dashboard').classList.add('hidden');$('#loginCard').classList.remove('hidden');if(!String(err.message||'').includes('não autorizado'))showError(err)}
}

$('#loginForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/login',{method:'POST',body:JSON.stringify({username:f.get('username'),password:f.get('password')})});e.target.reset();await refresh()}catch(err){showError(err)}});
$('#adminLogout').onclick=async()=>{try{await api('/api/admin/logout',{method:'POST'})}finally{session=null;$('#dashboard').classList.add('hidden');$('#loginCard').classList.remove('hidden');history.replaceState(null,'',location.pathname)}};
$('#blockedForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/blocked-terms',{method:'POST',body:JSON.stringify({term:f.get('term'),reason:f.get('reason')||null})});e.target.reset();await refresh()}catch(err){showError(err)}});
$('#questionForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),correct=String(f.get('correct')).trim(),raw=String(f.get('options')||'').split('\n').map(x=>x.trim()).filter(Boolean);if(raw.length!==4||new Set(raw).size!==4){showMessage(msg,'Cada questão deve ter exatamente 4 alternativas diferentes.','error');return}if(!raw.includes(correct)){showMessage(msg,'A resposta correta precisa ser exatamente uma das 4 alternativas.','error');return}const mediaType=f.get('media_type')||null,payload={category_id:f.get('category_id'),kind:'multiple_choice',prompt:f.get('prompt'),options:raw.map(v=>({value:v,label:v})),correct_answer:{value:correct},explanation:f.get('explanation')||null,difficulty:Number(f.get('difficulty')||1),media_type:mediaType,media_url:f.get('media_url')||null,accessibility:{instructions_clear:f.get('instructions_clear')==='on',depends_on_color_only:false,requires_speed:false,reading_level:f.get('reading_level')||'básica',simplified_prompt:f.get('simplified_prompt')||null,alt_text:f.get('alt_text')||null,transcript:f.get('transcript')||null,screen_reader_ready:true,equivalent_text:true},active:true};try{await api('/api/admin/questions',{method:'POST',body:JSON.stringify(payload)});e.target.reset();$('#instructionsClear').checked=true;enforceFinalUiRules();await refresh()}catch(err){showError(err)}});
$('#stationForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),id=f.get('station_id'),payload={code:f.get('code'),name:f.get('name'),zone_id:f.get('zone_id'),station_type:f.get('station_type'),base_points:10,physical_code:f.get('physical_code')||null,active_from:f.get('active_from')?new Date(f.get('active_from')).toISOString():null,active_until:f.get('active_until')?new Date(f.get('active_until')).toISOString():null,location_hint:f.get('location_hint')||null,active:true};try{await api(id?`/api/admin/stations/${id}`:'/api/admin/stations',{method:id?'PUT':'POST',body:JSON.stringify(payload)});cancelStationEdit();await refresh()}catch(err){showError(err)}});
$('#contentForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),stationId=f.get('station_id'),mediaType=f.get('media_type')||null,payload={content_kind:f.get('content_kind'),title:f.get('title'),body:f.get('body')||null,author_name:f.get('author_name')||null,media_type:mediaType,media_url:f.get('media_url')||null,accessibility:{plain_text:true,screen_reader_ready:true,alt_text:f.get('alt_text')||null,transcript:f.get('transcript')||null},challenge_question_id:null,challenge_points:10,completion_body:f.get('completion_body')||null};try{await api(`/api/admin/stations/${stationId}/content`,{method:'PUT',body:JSON.stringify(payload)});await refresh();showMessage(msg,'Conteúdo salvo.','success')}catch(err){showError(err)}});
$('#trailForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),payload={slug:String(f.get('slug')).trim().toLowerCase(),name:f.get('name'),description:f.get('description')||null,completion_points:Number(f.get('completion_points')||30),completion_title:null,completion_body:null,active:true};try{await api('/api/admin/trails',{method:'POST',body:JSON.stringify(payload)});e.target.reset();$('#trailCompletionPoints').value='30';await refresh()}catch(err){showError(err)}});
$('#trailStepsForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),ids=[...$('#stepsStations').selectedOptions].map(o=>o.value);if(!ids.length){showMessage(msg,'Selecione pelo menos uma estação sequencial.','error');return}try{await api(`/api/admin/trails/${f.get('trail_id')}/steps`,{method:'PUT',body:JSON.stringify({qr_point_ids:ids})});await refresh()}catch(err){showError(err)}});
$('#manualForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/manual-actions',{method:'POST',body:JSON.stringify({participant_id:f.get('participant_id'),action_type:f.get('action_type'),description:f.get('description'),evidence:f.get('evidence')||null,points:Number(f.get('points'))})});e.target.reset();$('#manualPoints').value='20';await refresh()}catch(err){showError(err)}});

enforceFinalUiRules();refresh();