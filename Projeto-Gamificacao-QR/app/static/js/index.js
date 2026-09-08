const reg=document.querySelector('#registerForm'), rec=document.querySelector('#recoverForm'), msg=document.querySelector('#message'), profile=document.querySelector('#profile');
const type=document.querySelector('#participant_type'), student=document.querySelector('#studentFields'), external=document.querySelector('#externalFields');
function toggle(){student.classList.toggle('hidden',type.value!=='student');external.classList.toggle('hidden',type.value!=='external')}
type.addEventListener('change',toggle);toggle();

async function logout(){
  const button=document.querySelector('#logoutButton');
  if(button){button.disabled=true;button.textContent='Saindo…'}
  try{
    await api('/api/participants/logout',{method:'POST'});
    profile.classList.add('hidden');
    profile.innerHTML='';
    document.querySelector('#forms').classList.remove('hidden');
    reg.reset();rec.reset();toggle();
    showMessage(msg,'Sessão encerrada com segurança. Use seu código de recuperação para entrar novamente.','success');
  }catch(err){
    if(button){button.disabled=false;button.textContent='Sair'}
    showMessage(msg,err.message,'error');
  }
}

async function loadMe(){
  try{
    const d=await api('/api/participants/me');
    profile.innerHTML=`<h2>Olá, ${esc(d.participant.nick)}</h2><p><strong>${d.summary.points}</strong> pontos • ${d.summary.normal_completed_today} atividades normais concluídas hoje</p><div class="profile-actions"><a href="/ranking">Ver ranking</a><button id="logoutButton" type="button" class="secondary compact">Sair</button></div>`;
    profile.classList.remove('hidden');
    document.querySelector('#forms').classList.add('hidden');
    document.querySelector('#logoutButton').addEventListener('click',logout);
  }catch(_){}}

reg.addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(reg);const payload=Object.fromEntries(f.entries());for(const k of Object.keys(payload))if(payload[k]==='')payload[k]=null;try{const d=await api('/api/participants/register',{method:'POST',body:JSON.stringify(payload)});showMessage(msg,`Cadastro concluído. Guarde seu código de recuperação: ${d.access_code}`,'success');await loadMe()}catch(err){showMessage(msg,err.message,'error')}});
rec.addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/participants/recover',{method:'POST',body:JSON.stringify({access_code:new FormData(rec).get('access_code')})});await loadMe()}catch(err){showMessage(msg,err.message,'error')}});
loadMe();
