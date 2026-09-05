const $=s=>document.querySelector(s); const msg=$('#message'); let catalog={categories:[],zones:[],blocked_terms:[]}, questions=[], qrs=[];
function optionsHtml(rows,label='name'){return rows.map(x=>`<option value="${esc(x.id)}">${esc(x[label])}</option>`).join('')}
async function refresh(){
  try{
    const [o,q,qr,b,c,a]=await Promise.all([api('/api/admin/overview'),api('/api/admin/questions'),api('/api/admin/qrs'),api('/api/admin/bonus'),api('/api/admin/catalog'),api('/api/admin/analytics')]);
    catalog=c; questions=q.questions; qrs=qr.qrs;
    $('#loginCard').classList.add('hidden'); $('#dashboard').classList.remove('hidden');
    $('#overview').innerHTML=`<p><strong>${o.participants}</strong> participantes</p><p><strong>${o.questions}</strong> questões</p><p><strong>${o.qr_points}</strong> QR Codes</p><p><strong>${o.attempts}</strong> tentativas (${o.correct_attempts} corretas)</p>`;
    $('#questionCategory').innerHTML=optionsHtml(c.categories.filter(x=>x.active)); $('#qrZone').innerHTML=optionsHtml(c.zones.filter(x=>x.active));
    $('#linkQr').innerHTML=optionsHtml(qr.qrs.filter(x=>x.kind==='normal'&&x.active),'name'); $('#linkQuestion').innerHTML=optionsHtml(q.questions.filter(x=>x.active),'prompt');
    $('#questionList').innerHTML=q.questions.length?q.questions.map(x=>`<div class="notice"><span class="pill">${esc(x.kind)}</span> ${esc(x.prompt)} <button class="secondary" data-question-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p>Nenhuma questão cadastrada.</p>';
    $('#qrList').innerHTML=qr.qrs.length?qr.qrs.map(x=>`<div class="notice"><strong>${esc(x.code)}</strong> — ${esc(x.name)} · ${esc(x.kind)} <button class="secondary" data-qr-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p>Nenhum QR cadastrado.</p>';
    $('#blockedList').innerHTML=c.blocked_terms.length?c.blocked_terms.map(x=>`<div class="notice">${esc(x.term)} <button class="secondary" data-term-toggle="${x.id}">${x.active?'Desativar':'Ativar'}</button></div>`).join(''):'<p>Nenhum termo adicional cadastrado.</p>';
    $('#bonusList').innerHTML=b.campaigns.length?b.campaigns.map(x=>`<p><strong>${esc(x.event_date)}</strong> · ${esc(x.name)} · ${esc(x.bonus_type)} · ${x.points} pts</p>`).join(''):'<p>Nenhum bônus configurado.</p>';
    const byType=Object.entries(a.participants_by_type).map(([k,v])=>`<li>${esc(k)}: ${v}</li>`).join(''); const byCat=Object.entries(a.questions_by_category).map(([k,v])=>`<li>${esc(k)}: ${v.correct}/${v.attempts} acertos</li>`).join('');
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
$('#loginForm').addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/admin/login',{method:'POST',body:JSON.stringify({password:new FormData(e.target).get('password')})});showMessage(msg,'Acesso liberado.','success');await refresh()}catch(err){showMessage(msg,err.message,'error')}});
$('#blockedForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/blocked-terms',{method:'POST',body:JSON.stringify({term:f.get('term'),reason:f.get('reason')||null})});e.target.reset();await refresh()}catch(err){showMessage(msg,err.message,'error')}});
$('#questionForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target),kind=f.get('kind'),correct=String(f.get('correct')).trim();let raw=String(f.get('options')||'').split('\n').map(x=>x.trim()).filter(Boolean);if(kind==='true_false'&&raw.length===0)raw=['Verdadeiro','Falso'];const payload={category_id:f.get('category_id'),kind,prompt:f.get('prompt'),options:raw.map(v=>({value:v,label:v})),correct_answer:kind==='short_text'?{value:correct,accepted:correct.split('|').map(x=>x.trim()).filter(Boolean)}:{value:correct},difficulty:Number(f.get('difficulty')||1),media_type:null,media_url:null,accessibility:{instructions_clear:true,depends_on_color_only:false,requires_speed:false},active:true};try{await api('/api/admin/questions',{method:'POST',body:JSON.stringify(payload)});e.target.reset();showMessage(msg,'Questão criada.','success');await refresh()}catch(err){showMessage(msg,err.message,'error')}});
$('#qrForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/admin/qrs',{method:'POST',body:JSON.stringify({code:f.get('code'),name:f.get('name'),zone_id:f.get('zone_id'),kind:f.get('kind'),active:true})});e.target.reset();showMessage(msg,'QR cadastrado.','success');await refresh()}catch(err){showMessage(msg,err.message,'error')}});
$('#linkForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api(`/api/admin/qrs/${f.get('qr_id')}/questions/${f.get('question_id')}`,{method:'POST'});showMessage(msg,'Questão vinculada ao QR.','success')}catch(err){showMessage(msg,err.message,'error')}});
refresh();
