const reg=document.querySelector('#registerForm'), loginForm=document.querySelector('#loginForm'), rec=document.querySelector('#recoverForm'), msg=document.querySelector('#message'), profile=document.querySelector('#profile');
const type=document.querySelector('#participant_type'), student=document.querySelector('#studentFields'), external=document.querySelector('#externalFields');

function toggle(){
  student.classList.toggle('hidden',type.value!=='student');
  external.classList.toggle('hidden',type.value!=='external');
}
type.addEventListener('change',toggle);toggle();

function passwordsMatch(a,b){
  if(a!==b){showMessage(msg,'As senhas digitadas não conferem.','error');return false}
  return true;
}

async function logout(){
  const button=document.querySelector('#logoutButton');
  if(button){button.disabled=true;button.textContent='Saindo…'}
  try{
    await api('/api/participants/logout',{method:'POST'});
    profile.classList.add('hidden');
    profile.innerHTML='';
    document.querySelector('#forms').classList.remove('hidden');
    reg.reset();loginForm.reset();rec.reset();toggle();
    showMessage(msg,'Sessão encerrada. Entre novamente com seu nick e senha.','success');
  }catch(err){
    if(button){button.disabled=false;button.textContent='Sair'}
    showMessage(msg,err.message,'error');
  }
}

async function setPassword(e){
  e.preventDefault();
  const form=e.target;
  const password=new FormData(form).get('password');
  const confirm=new FormData(form).get('password_confirm');
  if(!passwordsMatch(password,confirm))return;
  const button=form.querySelector('button[type="submit"]');
  button.disabled=true;button.textContent='Salvando…';
  try{
    await api('/api/participants/password',{method:'POST',body:JSON.stringify({password})});
    showMessage(msg,'Senha definida com sucesso. A partir de agora você pode entrar com seu nick e senha.','success');
    await loadMe();
  }catch(err){
    button.disabled=false;button.textContent='Definir senha';
    showMessage(msg,err.message,'error');
  }
}

async function loadMe(){
  try{
    const d=await api('/api/participants/me');
    const passwordSetup=d.participant.has_password?'':`<div class="notice warning"><strong>Defina uma senha para sua conta.</strong><p>Seu cadastro foi criado antes do login por senha. Você não perde pontos nem histórico.</p><form id="setPasswordForm"><label for="profile_password">Nova senha</label><input id="profile_password" name="password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required><label for="profile_password_confirm">Confirmar senha</label><input id="profile_password_confirm" name="password_confirm" type="password" autocomplete="new-password" minlength="8" maxlength="128" required><button type="submit">Definir senha</button></form></div>`;
    profile.innerHTML=`<h2>Olá, ${esc(d.participant.nick)}</h2><p><strong>${d.summary.points}</strong> pontos • ${d.summary.normal_completed_today} atividades normais concluídas hoje</p>${passwordSetup}<div class="profile-actions"><a href="/ranking">Ver ranking</a><button id="logoutButton" type="button" class="secondary compact">Sair</button></div>`;
    profile.classList.remove('hidden');
    document.querySelector('#forms').classList.add('hidden');
    document.querySelector('#logoutButton').addEventListener('click',logout);
    const setPasswordForm=document.querySelector('#setPasswordForm');
    if(setPasswordForm)setPasswordForm.addEventListener('submit',setPassword);
  }catch(_){}}

loginForm.addEventListener('submit',async e=>{
  e.preventDefault();
  const f=new FormData(loginForm);
  const payload={nick:f.get('nick'),password:f.get('password')};
  try{
    await api('/api/participants/login',{method:'POST',body:JSON.stringify(payload)});
    showMessage(msg,'Login realizado com sucesso.','success');
    await loadMe();
  }catch(err){showMessage(msg,err.message,'error')}
});

reg.addEventListener('submit',async e=>{
  e.preventDefault();
  const f=new FormData(reg);
  if(!passwordsMatch(f.get('password'),f.get('password_confirm')))return;
  const payload=Object.fromEntries(f.entries());
  delete payload.password_confirm;
  for(const k of Object.keys(payload))if(payload[k]==='')payload[k]=null;
  try{
    const d=await api('/api/participants/register',{method:'POST',body:JSON.stringify(payload)});
    showMessage(msg,`Cadastro concluído. Seu login é o nick escolhido. Guarde também o código de recuperação: ${d.access_code}`,'success');
    await loadMe();
  }catch(err){showMessage(msg,err.message,'error')}
});

rec.addEventListener('submit',async e=>{
  e.preventDefault();
  const f=new FormData(rec);
  if(!passwordsMatch(f.get('new_password'),f.get('new_password_confirm')))return;
  try{
    const d=await api('/api/participants/recover',{method:'POST',body:JSON.stringify({access_code:f.get('access_code'),new_password:f.get('new_password')})});
    showMessage(msg,`Senha redefinida. Guarde o NOVO código de recuperação: ${d.access_code}`,'success');
    rec.reset();
    await loadMe();
  }catch(err){showMessage(msg,err.message,'error')}
});

loadMe();
