(()=>{
let data=null,loading=false,workspaceReady=false;
const root=id=>document.getElementById(id);
const empty=(el,text='Sem dados suficientes ainda.')=>{if(el)el.innerHTML=`<div class="analytics-empty">${esc(text)}</div>`};
const percent=(value,max)=>max>0?Math.max(2,Math.min(100,(Number(value||0)/max)*100)):0;
const number=value=>Number(value||0).toLocaleString('pt-BR');

const ANALYSES={
  general:{label:'Ranking geral',group:'Competição',orientation:'horizontal'},
  dailyRanking:{label:'Ranking por dia',group:'Competição',orientation:'horizontal',needsDay:true},
  questionRanking:{label:'Ranking por questões',group:'Competição',orientation:'horizontal'},
  qrRanking:{label:'Ranking por QRs',group:'Competição',orientation:'horizontal'},
  firstTry:{label:'Ranking por acertos na 1ª tentativa',group:'Competição',orientation:'horizontal'},
  secondTry:{label:'Ranking por acertos na 2ª tentativa',group:'Competição',orientation:'horizontal'},
  qrUsage:{label:'Uso por QR',group:'Uso dos QRs',orientation:'vertical'},
  dailyUsage:{label:'QRs utilizados por dia',group:'Uso dos QRs',orientation:'vertical'},
  qrAccuracy:{label:'Taxa de acerto por QR',group:'Qualidade das questões',orientation:'vertical'},
  questionErrors:{label:'Questões com mais dificuldade',group:'Qualidade das questões',orientation:'horizontal'}
};

function ensureWorkspace(){
  if(workspaceReady)return;
  const grid=document.querySelector('#analyticsPanel .analytics-grid');
  if(!grid)return;
  workspaceReady=true;
  const groups={};
  Object.entries(ANALYSES).forEach(([key,item])=>{(groups[item.group]??=[]).push([key,item])});
  const options=Object.entries(groups).map(([group,items])=>`<optgroup label="${esc(group)}">${items.map(([key,item])=>`<option value="${key}">${esc(item.label)}</option>`).join('')}</optgroup>`).join('');
  grid.innerHTML=`
    <section class="card analytics-workspace">
      <div class="analytics-controls" aria-label="Filtros das análises">
        <div><label for="analysisType">Análise</label><select id="analysisType">${options}</select></div>
        <div><label for="analysisDay">Dia</label><select id="analysisDay" disabled><option value="">Evento completo</option></select></div>
        <div><label for="analysisLimit">Exibir</label><select id="analysisLimit"><option value="5">Top 5</option><option value="10" selected>Top 10</option><option value="20">Top 20</option><option value="0">Todos</option></select></div>
      </div>
      <div class="analytics-chart-head">
        <div><span class="eyebrow" id="analysisGroup">Competição</span><h3 id="analysisTitle">Ranking geral</h3><p class="muted" id="analysisDescription"></p></div>
        <div class="analysis-summary" id="analysisSummary" aria-live="polite"></div>
      </div>
      <div id="analysisChart" class="analysis-chart" role="img" aria-live="polite"></div>
    </section>`;
  root('analysisType')?.addEventListener('change',()=>{syncDayFilter();renderSelected()});
  root('analysisDay')?.addEventListener('change',renderSelected);
  root('analysisLimit')?.addEventListener('change',renderSelected);
}

function allDays(){
  const values=new Set();
  (data?.daily_usage||[]).forEach(r=>{if(r.activity_date)values.add(r.activity_date)});
  (data?.daily_ranking||[]).forEach(r=>{if(r.activity_date)values.add(r.activity_date)});
  return [...values].sort();
}

function fillDays(){
  const select=root('analysisDay');if(!select)return;
  const current=select.value;
  select.innerHTML='<option value="">Evento completo</option>'+allDays().map(d=>`<option value="${esc(d)}">${esc(d)}</option>`).join('');
  if([...select.options].some(o=>o.value===current))select.value=current;
  syncDayFilter();
}

function syncDayFilter(){
  const type=root('analysisType')?.value||'general',needsDay=!!ANALYSES[type]?.needsDay,select=root('analysisDay');
  if(!select)return;
  select.disabled=!needsDay;
  if(!needsDay)select.value='';
}

function limited(rows){
  const limit=Number(root('analysisLimit')?.value||10);
  return limit>0?(rows||[]).slice(0,limit):(rows||[]);
}

function horizontalBars(el,rows,{label,value,suffix='',sub=null}={}){
  const list=limited(rows);if(!list.length){empty(el);return}
  const max=Math.max(...list.map(x=>Number(value(x)||0)),1);
  el.className='analysis-chart horizontal-chart';
  el.innerHTML=list.map(x=>`<div class="chart-row"><div class="chart-label">${esc(label(x))}${sub?`<span class="chart-sub">${esc(sub(x))}</span>`:''}</div><div class="chart-track"><div class="chart-fill" style="width:${percent(value(x),max)}%"></div></div><div class="chart-value">${number(value(x))}${suffix}</div></div>`).join('');
}

function verticalColumns(el,rows,{label,value,suffix='',sub=null}={}){
  const list=limited(rows);if(!list.length){empty(el);return}
  const max=Math.max(...list.map(x=>Number(value(x)||0)),1);
  el.className='analysis-chart vertical-chart';
  el.innerHTML=`<div class="column-chart">${list.map(x=>`<div class="column-item"><div class="column-value">${number(value(x))}${suffix}</div><div class="column-track"><div class="column-fill" style="height:${percent(value(x),max)}%"></div></div><div class="column-label">${esc(label(x))}</div>${sub?`<div class="column-sub">${esc(sub(x))}</div>`:''}</div>`).join('')}</div>`;
}

function setHeading(type,description,summary=''){
  const item=ANALYSES[type];
  root('analysisGroup').textContent=item.group;
  root('analysisTitle').textContent=item.label;
  root('analysisDescription').textContent=description;
  root('analysisSummary').textContent=summary;
}

function renderGeneral(el){
  const rows=[...(data?.general_ranking||[])].sort((a,b)=>Number(a.position||999)-Number(b.position||999));
  setHeading('general','Classificação oficial acumulada por pontos, com estações e acertos de primeira como critérios de desempate.',`${rows.length} participante(s)`);
  horizontalBars(el,rows,{label:r=>`${r.position}º ${r.nick}`,value:r=>r.points,suffix:' pts',sub:r=>`${r.stations_validated} estações • ${r.first_try_correct} de 1ª`});
}

function renderDailyRanking(el){
  const day=root('analysisDay')?.value;
  if(!day){setHeading('dailyRanking','Selecione um dia para visualizar a classificação daquele período.');empty(el,'Selecione um dia no filtro acima.');return}
  const rows=(data?.daily_ranking||[]).filter(r=>r.activity_date===day).sort((a,b)=>Number(a.position||999)-Number(b.position||999));
  setHeading('dailyRanking',`Pontuação obtida somente em ${day}.`,`${rows.length} participante(s)`);
  horizontalBars(el,rows,{label:r=>`${r.position}º ${r.nick}`,value:r=>r.points,suffix:' pts',sub:r=>`${r.stations} estações • ${r.first_try_correct} de 1ª`});
}

function renderQuestionRanking(el){
  const rows=[...(data?.question_ranking||[])].sort((a,b)=>Number(b.challenge_points||0)-Number(a.challenge_points||0));
  setHeading('questionRanking','Compara apenas o desempenho obtido nas questões, sem confundir com os +10 da validação do QR.',`${rows.reduce((s,r)=>s+Number(r.correct_answers||0),0)} acerto(s)`);
  horizontalBars(el,rows,{label:r=>r.nick,value:r=>r.challenge_points,suffix:' pts',sub:r=>`${r.correct_answers} acertos • ${r.first_try_correct} de 1ª`});
}

function renderQrRanking(el){
  const rows=[...(data?.qr_ranking||[])].sort((a,b)=>Number(b.distinct_qrs||0)-Number(a.distinct_qrs||0)||Number(b.stations_validated||0)-Number(a.stations_validated||0));
  setHeading('qrRanking','Mostra quem mais explorou estações e quantos QRs distintos foram encontrados.',`${rows.length} participante(s)`);
  horizontalBars(el,rows,{label:r=>r.nick,value:r=>r.distinct_qrs,sub:r=>`${r.stations_validated} validações • ${r.station_points} pts de QR`});
}

function renderAttemptRanking(el,field,type,labelText){
  const rows=[...(data?.attempt_ranking||[])].sort((a,b)=>Number(b[field]||0)-Number(a[field]||0));
  setHeading(type,`Classificação pela quantidade de ${labelText}.`,`${rows.reduce((s,r)=>s+Number(r[field]||0),0)} no total`);
  horizontalBars(el,rows,{label:r=>r.nick,value:r=>r[field],sub:r=>`${r.first_try_correct||0} de 1ª • ${r.second_try_correct||0} de 2ª • ${r.failed||0} sem acerto`});
}

function renderQrUsage(el){
  const rows=[...(data?.qr_usage||[])].sort((a,b)=>String(a.code||'').localeCompare(String(b.code||''),undefined,{numeric:true}));
  setHeading('qrUsage','Compara quantas validações ocorreram em cada um dos 15 pontos físicos.',`${rows.reduce((s,r)=>s+Number(r.validations||0),0)} validação(ões)`);
  verticalColumns(el,rows,{label:r=>r.code,value:r=>r.validations,sub:r=>`${r.participants} participante(s)`});
}

function renderDailyUsage(el){
  const rows=[...(data?.daily_usage||[])].sort((a,b)=>String(a.activity_date||'').localeCompare(String(b.activity_date||'')));
  setHeading('dailyUsage','Evolução do uso ao longo dos dias, com quantidade de validações, QRs distintos e participantes.',`${rows.length} dia(s) com atividade`);
  verticalColumns(el,rows,{label:r=>r.event_day?`Dia ${r.event_day}`:r.activity_date,value:r=>r.validations,sub:r=>`${r.distinct_qrs} QRs • ${r.participants} participantes`});
}

function renderQrAccuracy(el){
  const rows=(data?.qr_usage||[]).filter(r=>Number(r.validations||0)>0).map(r=>({...r,accuracy:Number(r.validations)?Math.round(((Number(r.first_try||0)+Number(r.second_try||0))/Number(r.validations))*100):0})).sort((a,b)=>String(a.code||'').localeCompare(String(b.code||''),undefined,{numeric:true}));
  const avg=rows.length?Math.round(rows.reduce((s,r)=>s+r.accuracy,0)/rows.length):0;
  setHeading('qrAccuracy','Ajuda a identificar estações cujo conjunto de questões esteja muito mais fácil ou difícil que os demais.',rows.length?`média ${avg}%`:'');
  verticalColumns(el,rows,{label:r=>r.code,value:r=>r.accuracy,suffix:'%',sub:r=>`${r.first_try} de 1ª • ${r.second_try} de 2ª`});
}

function renderQuestionErrors(el){
  const rows=(data?.question_performance||[]).filter(r=>Number(r.attempted||0)>0).map(r=>({...r,error_rate:Math.max(0,100-Number(r.success_rate||0))})).sort((a,b)=>b.error_rate-a.error_rate||Number(b.attempted||0)-Number(a.attempted||0));
  setHeading('questionErrors','Prioriza Qxxx com maior taxa de erro para orientar a revisão pedagógica durante a homologação.',`${rows.length} questão(ões) respondida(s)`);
  horizontalBars(el,rows,{label:r=>r.review_code,value:r=>r.error_rate,suffix:'%',sub:r=>`${r.attempted} resposta(s) • ${String(r.prompt||'').slice(0,90)}`});
}

function renderSelected(){
  if(!data)return;
  const el=root('analysisChart');if(!el)return;
  const type=root('analysisType')?.value||'general';
  if(type==='general')return renderGeneral(el);
  if(type==='dailyRanking')return renderDailyRanking(el);
  if(type==='questionRanking')return renderQuestionRanking(el);
  if(type==='qrRanking')return renderQrRanking(el);
  if(type==='firstTry')return renderAttemptRanking(el,'first_try_correct','firstTry','acertos na 1ª tentativa');
  if(type==='secondTry')return renderAttemptRanking(el,'second_try_correct','secondTry','acertos na 2ª tentativa');
  if(type==='qrUsage')return renderQrUsage(el);
  if(type==='dailyUsage')return renderDailyUsage(el);
  if(type==='qrAccuracy')return renderQrAccuracy(el);
  if(type==='questionErrors')return renderQuestionErrors(el);
}

function render(){ensureWorkspace();fillDays();renderSelected()}
async function load(){
  if(loading)return;loading=true;ensureWorkspace();
  try{const res=await fetch('/api/admin/analytics',{credentials:'include'});if(res.status===401||res.status===403)return;if(!res.ok)throw new Error('Não foi possível carregar as análises.');data=await res.json();render()}
  catch(err){empty(root('analysisChart'),err.message)}
  finally{loading=false}
}
root('refreshAnalytics')?.addEventListener('click',load);
document.querySelector('[data-admin-tab="analyticsPanel"]')?.addEventListener('click',load);
document.addEventListener('admin:ready',load);
ensureWorkspace();
if(!document.getElementById('dashboard')?.classList.contains('hidden'))load();
})();
