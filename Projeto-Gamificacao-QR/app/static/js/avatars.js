(()=>{
  const assetBase='/static/assets/avatars';
  const catalog=[
    {key:'avatar-01',label:'Capivara — Rocky',file:'01_capivara_rocky.webp'},
    {key:'avatar-02',label:'Onça — Matrix',file:'02_onca_matrix.webp'},
    {key:'avatar-03',label:'Jacaré — Back to the Future',file:'03_jacare_back_future.webp'},
    {key:'avatar-04',label:'Arara — Terminator',file:'04_arara_terminator.webp'},
    {key:'avatar-05',label:'Lobo-guará — Jurassic',file:'05_lobo_guara_jurassic.webp'},
    {key:'avatar-06',label:'Veado — Star Wars',file:'06_veado_star_wars.webp'},
    {key:'avatar-07',label:'Ariranha — Karate Kid',file:'07_ariranha_karate_kid.webp'},
    {key:'avatar-08',label:'Cobra — O Poderoso Chefão',file:'09_cobra_godfather.webp'},
    {key:'avatar-09',label:'Tatu — Ghostbusters',file:'11_tatu_ghostbusters.webp'},
    {key:'avatar-10',label:'Garça — Blade Runner',file:'12_garca_blade_runner.webp'},
    {key:'avatar-11',label:'Jaguatirica — Mulher-Maravilha',file:'16_jaguatirica_mulher_maravilha.webp'},
    {key:'avatar-12',label:'Quati — Kill Bill',file:'17_quati_kill_bill.webp'},
    {key:'avatar-13',label:'Tuiuiú — Tomb Raider',file:'18_tuiuia_tomb_raider.webp'},
    {key:'avatar-14',label:'Coruja — Jogos Vorazes',file:'19_coruja_hunger_games.webp'},
    {key:'avatar-15',label:'Borboleta — Alice no País das Maravilhas',file:'20_borboleta_alice_wonderland.webp'},
    {key:'avatar-16',label:'Anta — Mad Max',file:'21_anta_mad_max.webp'},
    {key:'avatar-17',label:'Mutum — Viúva Negra',file:'22_mutum_black_widow.webp'},
    {key:'avatar-18',label:'Bugio — Piratas do Caribe',file:'23_bugio_piratas_caribe.webp'},
    {key:'avatar-19',label:'Mão-pelada — Mulan',file:'24_mao_pelada_mulan.webp'},
    {key:'avatar-20',label:'Seriema — Malévola',file:'25_seriema_maleficent.webp'}
  ];
  const byKey=new Map(catalog.map(item=>[item.key,item]));
  const defaultKey='avatar-01';
  const escAttr=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  function safeKey(value){return byKey.has(String(value||''))?String(value):defaultKey}
  function imageUrl(item){return `${assetBase}/${item.file}`}
  function avatarMarkup(key,className='avatar',label=''){
    const item=byKey.get(safeKey(key));
    const aria=escAttr(label||item.label);
    const src=escAttr(imageUrl(item));
    return `<span class="${escAttr(className)}" data-avatar-key="${item.key}" role="img" aria-label="${aria}"><img class="avatar-image" src="${src}" alt="" aria-hidden="true" width="512" height="512" loading="lazy" decoding="async" draggable="false" style="width:100%;height:100%;display:block;object-fit:contain"></span>`;
  }
  function pickerMarkup(selected=defaultKey){
    const current=safeKey(selected);
    return catalog.map(item=>`<button type="button" class="avatar-choice${item.key===current?' is-selected':''}" data-avatar-choice="${item.key}" aria-pressed="${item.key===current?'true':'false'}" aria-label="Selecionar ${escAttr(item.label)}" title="${escAttr(item.label)}">${avatarMarkup(item.key,'avatar-choice-art')}<span class="avatar-check" aria-hidden="true">✓</span></button>`).join('');
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
