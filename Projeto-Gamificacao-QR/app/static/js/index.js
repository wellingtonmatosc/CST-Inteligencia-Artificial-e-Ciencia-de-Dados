const reg=document.querySelector('#registerForm'),loginForm=document.querySelector('#loginForm'),rec=document.querySelector('#recoverForm'),msg=document.querySelector('#message'),profile=document.querySelector('#profile');
const type=document.querySelector('#participant_type'),student=document.querySelector('#studentFields'),external=document.querySelector('#externalFields');

function toggle(){
  student.classList.toggle('hidden',type.value!=='student');
  external.classList.toggle('hidden',type.value!=='external');
}
type.addEventListener('change',toggle);toggle();

function pinsMatch(a,b){
  if(!/^\d{4}$/.test(String(a||''))){showMessage(msg,'O PIN deve ter 4 dígitos.','error');return false}
  if(a!==b){showMessage(msg,'Os PINs não conferem.','error');return false}
  return true;
}

async function logout(){
  const button=document.querySelector('#logoutButton');
  if(button){button.disabled=true;button.textContent='Saindo…'}
  try{
    await api('/api/participants/logout',{method:'POST'});
    profile.classList.add('hidden');profile.innerHTML='';
    document.querySelector('#forms').classList.remove('hidden');
    reg.reset();loginForm.reset();rec.reset();toggle();
    showMessage(msg,'Sessão encerrada.','success');
  }catch(err){
    if(button){button.disabled=false;button.textContent='Sair'}
    showMessage(msg,err.message,'error');
  }
}

async function setPin(e){
  e.preventDefault();
  const form=e.target,f=new FormData(form),pin=f.get('pin'),confirm=f.get('pin_confirm');
  if(!pinsMatch(pin,confirm))return;
  const button=form.querySelector('button[type="submit"]');
  button.disabled=true;button.textContent='Salvando…';
  try{
    await api('/api/participants/pin',{method:'POST',body:JSON.stringify({pin})});
    showMessage(msg,'PIN definido.','success');
    await loadMe();
  }catch(err){
    button.disabled=false;button.textContent='Definir PIN';showMessage(msg,err.message,'error');
  }
}

async function loadMe(){
  try{
    const d=await api('/api/participants/me');
    const pinSetup=d.participant.has_pin?'':`<div class="notice warning setup-pin"><strong>Defina um PIN antes de sair.</strong><form id="setPinForm"><div class="grid two compact-grid"><div><label for="profile_pin">Novo PIN</label><input id="profile_pin" name="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="new-password" required placeholder="••••"></div><div><label for="profile_pin_confirm">Confirmar PIN</label><input id="profile_pin_confirm" name="pin_confirm" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="new-password" required placeholder="••••"></div></div><button type="submit">Definir PIN</button></form></div>`;
    profile.innerHTML=`<div class="profile-top"><div><h2>${esc(d.participant.nick)}</h2><p><strong class="score-number">${d.summary.points}</strong> pontos</p><p class="muted">${d.summary.normal_completed_today} concluídas hoje</p></div></div>${pinSetup}<div class="profile-actions"><button id="openQrScanner" type="button" class="compact">Ler QR Code</button><a class="button-link" href="/ranking">Ranking</a><button id="logoutButton" type="button" class="secondary compact">Sair</button></div>`;
    profile.classList.remove('hidden');
    document.querySelector('#forms').classList.add('hidden');
    msg.classList.add('hidden');
    document.querySelector('#logoutButton').addEventListener('click',logout);
    const setPinForm=document.querySelector('#setPinForm');if(setPinForm)setPinForm.addEventListener('submit',setPin);
  }catch(_){ }
}

loginForm.addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(loginForm);const pin=String(f.get('pin')||'');
  if(!/^\d{4}$/.test(pin)){showMessage(msg,'Informe um PIN de 4 dígitos.','error');return}
  try{
    await api('/api/participants/login',{method:'POST',body:JSON.stringify({nick:f.get('nick'),pin})});
    await loadMe();
  }catch(err){showMessage(msg,err.message,'error')}
});

reg.addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(reg);
  if(!pinsMatch(f.get('pin'),f.get('pin_confirm')))return;
  const payload=Object.fromEntries(f.entries());delete payload.pin_confirm;
  for(const k of Object.keys(payload))if(payload[k]==='')payload[k]=null;
  try{
    const d=await api('/api/participants/register',{method:'POST',body:JSON.stringify(payload)});
    showMessage(msg,`Cadastro concluído. Código de recuperação: ${d.access_code}`,'success');await loadMe();
  }catch(err){showMessage(msg,err.message,'error')}
});

rec.addEventListener('submit',async e=>{
  e.preventDefault();const f=new FormData(rec);
  if(!pinsMatch(f.get('new_pin'),f.get('new_pin_confirm')))return;
  try{
    const d=await api('/api/participants/recover',{method:'POST',body:JSON.stringify({access_code:f.get('access_code'),new_pin:f.get('new_pin')})});
    showMessage(msg,`PIN redefinido. Novo código de recuperação: ${d.access_code}`,'success');rec.reset();await loadMe();
  }catch(err){showMessage(msg,err.message,'error')}
});

loadMe();
