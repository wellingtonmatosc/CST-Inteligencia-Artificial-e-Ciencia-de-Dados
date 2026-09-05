async function api(url, options={}){
  const res = await fetch(url,{credentials:'include',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
  let data={}; try{data=await res.json()}catch(_){data={detail:'Resposta inválida do servidor.'}}
  if(!res.ok) throw new Error(data.detail||'Não foi possível concluir a operação.');
  return data;
}
function showMessage(el,msg,type='notice'){el.className=`notice ${type}`;el.textContent=msg;el.classList.remove('hidden')}
function esc(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
