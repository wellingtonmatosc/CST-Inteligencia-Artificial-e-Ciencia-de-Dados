(()=>{
  const catalog=[
    {key:'avatar-01',label:'Avatar 1',skin:'#8d5524',hair:'#171717',shirt:'#062f4f',bg:'#f3c77b',style:'curly',glasses:true},
    {key:'avatar-02',label:'Avatar 2',skin:'#c68642',hair:'#2a1625',shirt:'#813772',bg:'#ead6e6',style:'long'},
    {key:'avatar-03',label:'Avatar 3',skin:'#f1c27d',hair:'#9f3c24',shirt:'#b82601',bg:'#f6d4c8',style:'bob'},
    {key:'avatar-04',label:'Avatar 4',skin:'#6f3b1f',hair:'#151515',shirt:'#365f91',bg:'#d6e2ef',style:'cap'},
    {key:'avatar-05',label:'Avatar 5',skin:'#e0ac69',hair:'#c47b18',shirt:'#813772',bg:'#f6e0b3',style:'short'},
    {key:'avatar-06',label:'Avatar 6',skin:'#7a4a2a',hair:'#21131d',shirt:'#b82601',bg:'#e5c8dd',style:'braid'},
    {key:'avatar-07',label:'Avatar 7',skin:'#b56c3f',hair:'#191919',shirt:'#1f4f82',bg:'#d7e5f2',style:'fade',glasses:true},
    {key:'avatar-08',label:'Avatar 8',skin:'#f0bd8a',hair:'#70452a',shirt:'#813772',bg:'#f4d9cc',style:'wave'},
    {key:'avatar-09',label:'Avatar 9',skin:'#5d301e',hair:'#111111',shirt:'#b82601',bg:'#ead0e4',style:'afro'},
    {key:'avatar-10',label:'Avatar 10',skin:'#d99763',hair:'#3a211a',shirt:'#062f4f',bg:'#f3dfc0',style:'side'},
    {key:'avatar-11',label:'Avatar 11',skin:'#9a5a35',hair:'#24131e',shirt:'#813772',bg:'#d9e2ee',style:'long'},
    {key:'avatar-12',label:'Avatar 12',skin:'#f3c08e',hair:'#1a1a1a',shirt:'#b82601',bg:'#ead8e8',style:'curly'}
  ];
  const byKey=new Map(catalog.map(item=>[item.key,item]));
  const defaultKey='avatar-01';
  const escAttr=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  function safeKey(value){return byKey.has(String(value||''))?String(value):defaultKey}
  function hairPath(style){
    const paths={
      curly:'<circle cx="32" cy="24" r="15"/><circle cx="22" cy="25" r="8"/><circle cx="42" cy="24" r="8"/><circle cx="27" cy="17" r="8"/><circle cx="38" cy="17" r="8"/>',
      long:'<path d="M18 33c0-18 7-25 18-25s19 7 19 25v19H17Z"/>',
      bob:'<path d="M16 29C16 14 24 8 36 8s20 7 20 22l-4 16H20Z"/>',
      cap:'<path d="M18 28c1-12 8-19 20-19 10 0 17 6 19 15l-6 1c-8-4-20-5-33 3Z"/><path d="M51 23c8 0 12 2 14 5-6 2-11 2-16 0Z"/>',
      short:'<path d="M18 27C20 14 27 9 37 9c11 0 17 6 19 17-11-6-24-7-38 1Z"/>',
      braid:'<path d="M18 31C18 16 25 8 36 8s19 8 19 23v11H18Z"/><circle cx="52" cy="44" r="5"/><circle cx="55" cy="51" r="4"/>',
      fade:'<path d="M20 25C23 13 29 9 39 10c8 1 13 6 15 15-12-5-23-5-34 0Z"/>',
      wave:'<path d="M17 28C19 14 26 8 37 8c13 0 19 8 20 21-8-6-14-8-20-7-8 1-13 4-20 6Z"/>',
      afro:'<circle cx="36" cy="22" r="17"/><circle cx="20" cy="26" r="9"/><circle cx="52" cy="26" r="9"/><circle cx="27" cy="13" r="9"/><circle cx="45" cy="13" r="9"/>',
      side:'<path d="M17 29C19 16 26 9 37 9c10 0 17 6 20 16-12-6-20-6-26-3-5 2-9 5-14 7Z"/>'
    };
    return paths[style]||paths.short;
  }
  function svg(item){
    const glasses=item.glasses?'<g fill="none" stroke="#172033" stroke-width="2"><circle cx="29" cy="34" r="5"/><circle cx="43" cy="34" r="5"/><path d="M34 34h4"/></g>':'';
    return `<svg viewBox="0 0 72 72" role="img" aria-label="${escAttr(item.label)}" focusable="false"><circle cx="36" cy="36" r="35" fill="${item.bg}"/><path d="M13 72c2-16 12-24 23-24s21 8 23 24Z" fill="${item.shirt}"/><g fill="${item.hair}">${hairPath(item.style)}</g><ellipse cx="36" cy="35" rx="15" ry="18" fill="${item.skin}"/><g fill="${item.hair}">${item.style==='long'?'<path d="M18 32c1-16 7-23 18-23 12 0 18 8 19 23-6-7-12-10-19-10-8 0-13 3-18 10Z"/>':hairPath(item.style)}</g><circle cx="30" cy="35" r="1.5" fill="#211a20"/><circle cx="42" cy="35" r="1.5" fill="#211a20"/><path d="M31 42c3 3 7 3 10 0" fill="none" stroke="#7b3340" stroke-width="1.8" stroke-linecap="round"/>${glasses}</svg>`;
  }
  function avatarMarkup(key,className='avatar',label=''){
    const item=byKey.get(safeKey(key));
    const aria=escAttr(label||item.label);
    return `<span class="${className}" data-avatar-key="${item.key}" role="img" aria-label="${aria}">${svg(item)}</span>`;
  }
  function pickerMarkup(selected=defaultKey){
    const current=safeKey(selected);
    return catalog.map(item=>`<button type="button" class="avatar-choice${item.key===current?' is-selected':''}" data-avatar-choice="${item.key}" aria-pressed="${item.key===current?'true':'false'}" aria-label="Selecionar ${escAttr(item.label)}">${avatarMarkup(item.key,'avatar-choice-art')}<span class="avatar-check" aria-hidden="true">✓</span></button>`).join('');
  }
  function mountPicker(container,{selected=defaultKey,onChange}={}){
    if(!container)return null;
    let current=safeKey(selected);
    const render=()=>{
      container.innerHTML=pickerMarkup(current);
      container.querySelectorAll('[data-avatar-choice]').forEach(button=>{
        button.addEventListener('click',()=>{
          current=safeKey(button.dataset.avatarChoice);
          render();
          onChange?.(current);
        });
      });
    };
    render();
    return {get value(){return current},set value(value){current=safeKey(value);render()}};
  }
  window.TrilhasAvatars={catalog,keys:catalog.map(item=>item.key),defaultKey,safeKey,avatarMarkup,pickerMarkup,mountPicker};
  document.dispatchEvent(new CustomEvent('trilhas:avatars-ready'));
})();
