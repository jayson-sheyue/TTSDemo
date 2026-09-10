'use strict';
const GLOBAL = new Set(['guide-content','source-content','source-links','show-guide','show-readme','voice-rules','compare-providers','compare-models','compare-classic','compare-why-classic','compare-age','compare-fit','api-out-of-demo','workspaces']);
let catalog, active='gemini', mode='single', busy=false, controller, audioContext, nextAudioTime=0, sources=[], pendingByte=null, voiceFilter='all';
let objectUrl=null, savedConfig=null, requestSerial=0;
const primed=new Set();
const $ = id => {
  if(GLOBAL.has(id)) return document.getElementById(id);
  const page=document.getElementById('page-'+active);
  if(page){const el=page.querySelector(`[data-id="${id}"]`); if(el) return el;}
  return document.getElementById(id);
};
function workspace(id){return (catalog.workspaces||[]).find(item=>item.id===id)||catalog.workspaces[0];}
function has(feature, spec){return ((spec||workspace(active)).features||[]).includes(feature);}
function val(id, fallback=''){const el=$(id); return el?el.value:fallback;}
function isOn(id){const el=$(id); return !!(el&&el.checked);}
function config(){
  const spec=workspace(active);
  const r={
    mode: spec.family==='classic'?'single':mode,
    provider: spec.family==='classic'?'classic':val('provider','vertex'),
    api: val('api','generate'),
    model: spec.family==='classic'?spec.model:val('model',spec.model),
    text: val('text'), style: val('style'), pace: val('pace','自然'), accent: val('accent'), scene: val('scene'),
    voice: val('voice','Kore'), voice2: val('voice2','Puck'), speaker: val('speaker','Host'), speaker2: val('speaker2','Guest'),
    language: val('language'), format: val('format','wav'),
    stream: isOn('stream'), chunk: isOn('chunk'), structured: isOn('structured'), ssml: isOn('ssml'),
    chunk_bytes: Number(val('chunk-bytes','1800'))||1800,
    pitch: Number(val('pitch','0'))||0,
  };
  return r;
}
function report(state, summary, detail=''){
  const box=$('log-box'); if(!box) return;
  box.className='log-box '+state;
  $('log-state').textContent={idle:'待命',loading:'进行中',ok:'成功',error:'失败'}[state]||state;
  $('log-summary').textContent=summary;
  $('log-spinner').hidden=state!=='loading';
  const pre=$('log-detail');
  if(detail){pre.hidden=false;pre.textContent=detail;}else{pre.hidden=true;pre.textContent='';}
  if(state!=='idle') box.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function fail(error, fallback){
  const summary=error&&error.name==='AbortError'?'已停止接收与播放，已提交的请求仍可能计费。':((error&&error.message)||fallback||'操作失败');
  report('error', summary, error&&error.detail||'');
}
function count(){const t=$('text'); if(!t||!$('count'))return; $('count').textContent=`${[...t.value].length} 字符 · ${new TextEncoder().encode(t.value).length} UTF-8 字节`;}
function setMode(value){
  const prev=mode;
  mode=value;
  const single=$('single'), dialogue=$('dialogue'), second=$('second-voice');
  if(single) single.classList.toggle('selected',value==='single');
  if(dialogue) dialogue.classList.toggle('selected',value==='dialogue');
  if(second) second.hidden=value!=='dialogue';
  if(value==='single'&&$('structured')) $('structured').checked=false;
  if(value==='dialogue'){
    fillVoiceSelects(false);
    if(prev!=='dialogue' && $('voice2')){
      const g=profileGender(val('voice')), g2=profileGender(val('voice2'));
      if(g && g===g2){
        const next=preferredVoice(g==='female'?'male':'female', val('voice'));
        if(next) $('voice2').value=next;
      }
    }
  }
}
function options(select,entries){if(!select)return; select.replaceChildren(); entries.forEach(([value,label])=>select.add(new Option(label,value)));}
function pageFamilies(spec){
  const map=catalog.classic_page_families||{};
  return map[spec.model]||[spec.model];
}
function profiles(){
  const spec=workspace(active);
  if(spec.family==='classic'&&spec.model!=='chirp3-hd'){
    const fam=new Set(pageFamilies(spec));
    const lang=val('language');
    return (catalog.classic_voices||[]).filter(item=>fam.has(item.family)&&(!lang||item.language===lang));
  }
  return catalog.voice_profiles||[];
}
function voiceLabel(p){return p.gender_zh?`${p.name} · ${p.gender_zh} · ${p.style_zh}`:`${p.name} · ${p.style_zh}`;}
function describeVoice(name){
  const hint=$('voice-hint'); if(!hint) return;
  const p=profiles().find(v=>v.name===name);
  if(!p){hint.textContent='';return;}
  const spec=workspace(active);
  if(spec.family==='classic'){
    const def=spec.model==='chirp3-hd'
      ? `默认声将请求 ${val('language','cmn-CN')}-Chirp3-HD-${name}。未用 <voice> 包住的句子走它。`
      : `默认声是 ${name}（${p.gender_zh} · ${p.style_zh}）。未用 <voice> 包住的句子走它。`;
    hint.textContent=isOn('ssml')
      ? def+' SSML 标签要包住那段字，不是加在全文后面。<voice> 只覆盖标签内；<lang> 尽量同声换语（日文汉字官方不支持）。'
      : def+' 停顿和读法请勾选 SSML。提示词不会发送。';
    if(spec.age_note) hint.textContent+=' '+spec.age_note;
    return;
  }
  let text=`当前主声音：${p.name} · ${p.gender_zh} · ${p.style_zh}${p.style_en?`（${p.style_en}）`:''}。请求里没有 gender 字段。`;
  text+=p.age_hint?` ${p.age_hint}`:' 官方没有少年、壮年、老年档。';
  hint.textContent=text;
}
function preferredVoice(gender,exclude=''){
  const prefer=gender==='female'?['Kore','Aoede','Leda','Sulafat','Zephyr','cmn-CN-Wavenet-A','cmn-CN-Standard-A','en-US-Neural2-C','en-US-Studio-O']:['Puck','Charon','Orus','cmn-CN-Wavenet-B','cmn-CN-Standard-B','en-US-Neural2-J','en-US-Studio-Q'];
  const names=profiles().filter(p=>p.gender===gender&&p.name!==exclude).map(p=>p.name);
  return prefer.find(n=>names.includes(n))||names[0]||'';
}
function profileGender(name){const p=profiles().find(v=>v.name===name); return p&&p.gender||'';}
function fillLanguageSelect(){
  const spec=workspace(active);
  const sel=$('language');
  if(!sel||spec.family!=='classic'||sel.tagName!=='SELECT') return;
  const keep=val('language');
  let locales;
  if(spec.model==='chirp3-hd'){
    locales=(catalog.chirp_locales||[]).map(item=>({code:item.code,label:item.label,count:30}));
  }else{
    const fam=new Set(pageFamilies(spec));
    const map=new Map();
    (catalog.classic_voices||[]).filter(item=>fam.has(item.family)).forEach(item=>{
      if(!map.has(item.language)) map.set(item.language,{code:item.language,label:item.language_label||item.language,count:0});
      map.get(item.language).count+=1;
    });
    locales=[...map.values()].sort((a,b)=>a.label.localeCompare(b.label,'en'));
  }
  options(sel, locales.map(item=>[item.code, `${item.label} · ${item.code} · ${item.count} 个`]));
  const prefer=keep && locales.some(item=>item.code===keep) ? keep
    : (['neural2','studio'].includes(spec.model)?'en-US':'cmn-CN');
  sel.value=locales.some(item=>item.code===prefer)?prefer:(locales[0]&&locales[0].code||'');
}
function fillVoiceSelect(select,keep,filter='all'){
  if(!select) return;
  const list=filter==='all'?profiles():profiles().filter(p=>p.gender===filter);
  select.replaceChildren();
  const families=[...new Set(list.map(p=>p.family).filter(Boolean))];
  const famLabel={neural2:'Neural2',news:'News',polyglot:'Polyglot',casual:'Casual','chirp-hd':'Chirp HD（旧版）',wavenet:'WaveNet',standard:'Standard',studio:'Studio'};
  function addOptions(target, items){
    if(filter==='all'){
      [['女声','female'],['男声','male']].forEach(([label,gender])=>{
        const group=document.createElement('optgroup'); group.label=label;
        items.filter(p=>p.gender===gender).forEach(p=>group.append(new Option(voiceLabel(p),p.name)));
        if(group.childElementCount) target.append(group);
      });
    }else items.forEach(p=>target.append(new Option(voiceLabel(p),p.name)));
  }
  if(families.length>1){
    families.forEach(family=>{
      const group=document.createElement('optgroup');
      group.label=famLabel[family]||family;
      list.filter(p=>p.family===family).forEach(p=>group.append(new Option(voiceLabel(p),p.name)));
      if(group.childElementCount) select.append(group);
    });
  }else addOptions(select, list);
  if(keep&&[...select.options].some(o=>o.value===keep)) select.value=keep;
  else if(select.options.length) select.selectedIndex=0;
}
function fillVoiceSelects(snap=false){
  let keep=val('voice')||preferredVoice('female');
  let keep2=val('voice2')||preferredVoice(profileGender(keep)==='female'?'male':'female', keep);
  if(voiceFilter!=='all' && (snap||profileGender(keep)!==voiceFilter))
    keep=preferredVoice(voiceFilter, keep2);
  if(keep2===keep) keep2=preferredVoice(profileGender(keep)==='female'?'male':'female', keep);
  fillVoiceSelect($('voice'), keep, voiceFilter);
  fillVoiceSelect($('voice2'), keep2, 'all');
  describeVoice(val('voice'));
  checkStyleConflict();
  const countEl=$('voice-count');
  if(countEl){
    const spec=workspace(active);
    const n=profiles().length;
    countEl.textContent=spec.model==='chirp3-hd'
      ? `当前 locale 使用 30 个短名；Chirp 3 HD 声音表共 ${(catalog.chirp_locales||[]).length} 种语言。`
      : `当前语言 ${n} 个声音。这是官方全表快照，不是抽查。`;
  }
}
function setVoiceFilter(value,snap=true){
  voiceFilter=value;
  document.querySelectorAll(`#page-${active} [data-voice-filter]`).forEach(item=>item.classList.toggle('selected',item.dataset.voiceFilter===value));
  fillVoiceSelects(snap);
}
function checkStyleConflict(){
  const box=$('style-warn'); if(!box||!has('style')) return;
  const p=profiles().find(v=>v.name===val('voice'));
  const blob=`${val('style')} ${val('scene')}`;
  let msg='';
  if(p&&p.gender==='female'&&/黑社会|头目|大哥|汉子|男声|男性/.test(blob)&&!/女/.test(blob))
    msg='这段语气像在指定男性角色，模型可能把女声读成男声。请写成「成年女性，保持女声线，语气凶狠」。';
  if(p&&p.gender==='male'&&/小女孩|少女|女声|女性/.test(blob)&&!/男/.test(blob))
    msg='这段语气像在指定女性角色，模型可能把男声读成女声。';
  box.hidden=!msg; box.textContent=msg;
}
function fitModel(name){
  const spec=workspace(active);
  if(spec.family==='classic') return spec.model;
  const list=(catalog.models[val('provider','vertex')])||[];
  if(list.includes(name)) return name;
  const aliases={'gemini-2.5-pro-tts':'gemini-2.5-pro-preview-tts','gemini-2.5-pro-preview-tts':'gemini-2.5-pro-tts','gemini-2.5-flash-tts':'gemini-2.5-flash-preview-tts','gemini-2.5-flash-preview-tts':'gemini-2.5-flash-tts'};
  if(aliases[name]&&list.includes(aliases[name])) return aliases[name];
  return '';
}
function applySample(sample,button,quiet=false){
  if(busy) return;
  const c=sample.config||{};
  if(c.mode) setMode(c.mode);
    ['text','style','pace','accent','scene','speaker','speaker2','language'].forEach(id=>{
    if(!$(id)) return;
    if(c[id]!=null) $(id).value=c[id];
    else if(['accent','scene','language'].includes(id) && workspace(active).family==='gemini') $(id).value='';
  });
  if(workspace(active).family==='classic') fillLanguageSelect();
  if(c.language&&$('language')) $('language').value=c.language;
  if($('pitch')) $('pitch').value=c.pitch!=null?String(c.pitch):'0';
  ['stream','chunk','structured','ssml'].forEach(id=>{if($(id)) $(id).checked=!!c[id];});
  if(c.chunk_bytes&&$('chunk-bytes')) $('chunk-bytes').value=c.chunk_bytes;
  if(c.provider&&$('provider')){ $('provider').value=c.provider; capabilities(true); }
  const fitted=c.model&&fitModel(c.model); if(fitted&&$('model')) $('model').value=fitted;
  const g1=profileGender(c.voice||val('voice')), g2=profileGender(c.voice2||val('voice2'));
  voiceFilter=(c.mode==='dialogue'&&g1&&g2&&g1!==g2)?'all':(g1||'all');
  document.querySelectorAll(`#page-${active} [data-voice-filter]`).forEach(item=>item.classList.toggle('selected',item.dataset.voiceFilter===voiceFilter));
  fillVoiceSelects(false);
  if(c.voice&&$('voice')&&[...$('voice').options].some(o=>o.value===c.voice)) $('voice').value=c.voice;
  if(c.voice2&&$('voice2')&&[...$('voice2').options].some(o=>o.value===c.voice2)) $('voice2').value=c.voice2;
  describeVoice(val('voice')); checkStyleConflict();
  if($('sample-note')) $('sample-note').textContent=sample.note||'';
  document.querySelectorAll(`#page-${active} [data-id="samples"] button`).forEach(item=>item.classList.toggle('selected',item===button));
  count(); capabilities();
  if(!quiet) report('ok',`已导入「${sample.title}」。这是 ${workspace(active).nav} 页的样例。`,sample.note||'');
}
function renderSamples(){
  const root=$('samples'); if(!root) return;
  root.replaceChildren();
  const mine=(catalog.samples||[]).filter(sample=>sample.engine===active);
  const groups=new Map();
  mine.forEach(sample=>{const name=sample.group||'本页样例'; if(!groups.has(name)) groups.set(name,[]); groups.get(name).push(sample);});
  groups.forEach((items,name)=>{
    const block=document.createElement('div'); block.className='sample-group';
    const heading=document.createElement('small'); heading.textContent=name; block.append(heading);
    const chips=document.createElement('div'); chips.className='examples';
    items.forEach(sample=>{
      const button=document.createElement('button'); button.type='button'; button.textContent=sample.title;
      button.onclick=()=>applySample(sample,button); chips.append(button);
    });
    block.append(chips); root.append(block);
  });
  if(!mine.length){const p=document.createElement('p'); p.className='hint'; p.textContent='这一页还没有样例。'; root.append(p); return;}
  applySample(mine[0], root.querySelector('button'), true);
}
function htmlTable(rows){
  if(!rows||!rows.length) return '';
  const head=rows[0].map(cell=>`<th>${escapeHtml(String(cell))}</th>`).join('');
  const body=rows.slice(1).map(row=>'<tr>'+row.map(cell=>`<td>${escapeHtml(String(cell))}</td>`).join('')+'</tr>').join('');
  return `<div class="compare-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
function capabilities(reset=false){
  const spec=workspace(active);
  if(spec.family==='gemini'){
    const p=val('provider','vertex');
    if(reset&&$('model')) options($('model'), (catalog.models[p]||[]).map(m=>[m,m]));
    if($('api')){$('api').disabled=p!=='gemini'; if(p!=='gemini') $('api').value='generate';}
    const model=val('model');
    const streamAllowed=p!=='gemini'||model.includes('3.1');
    if($('stream')){$('stream').disabled=!streamAllowed; if(!streamAllowed) $('stream').checked=false;}
    const encoded=p==='cloud'&&!isOn('stream')&&!isOn('chunk');
    if($('format')){$('format').disabled=!encoded; if(!encoded) $('format').value='wav';}
    if($('structured')){$('structured').disabled=p!=='cloud'||mode!=='dialogue'||isOn('stream'); if($('structured').disabled) $('structured').checked=false;}
    if($('language')) $('language').placeholder=p==='cloud'?'必填，如 cmn-CN、en-US':'可留空；短码如 cmn、en';
    const card=catalog.model_cards&&catalog.model_cards[model];
    if($('capability')) $('capability').textContent=(card||'')+(p==='gemini'?' 使用 API Key。':' 使用 ADC + Cloud 项目。')+(p!=='gemini'&&model.includes('3.1')?' 3.1 目前主要在 global 区域。':'');
    return;
  }
  if($('stream')){
    const allowed=has('stream')&&!isOn('ssml');
    $('stream').disabled=!allowed; if(!allowed) $('stream').checked=false;
  }
  if($('format')) $('format').disabled=isOn('stream')||isOn('chunk');
  fillLanguageSelect();
  if($('capability')) $('capability').textContent=(catalog.model_cards&&catalog.model_cards[spec.model])||'';
}
function bindTags(root, spec){
  const box=root.querySelector('[data-id="tags"]'); if(!box) return;
  const items=spec.family==='gemini'?catalog.tags:(catalog.ssml_tags&&(catalog.ssml_tags[spec.model]||catalog.ssml_tags.ssml))||[];
  items.forEach(([tag,label])=>{
    const button=document.createElement('button'); button.type='button'; button.dataset.tag=tag; button.textContent=label;
    button.onclick=()=>{const t=$('text'); if(!t)return; t.setRangeText(tag+' ', t.selectionStart, t.selectionEnd, 'end'); t.focus(); count();};
    box.append(button);
  });
  const note=document.createElement('small');
  note.textContent=spec.family==='gemini'?'3.1 更适合；英语标签；效果需试听':'插入到台词中；Chirp 流式时不要开 SSML';
  box.append(note);
}
function pageIntro(spec){
  const fit=(spec.fit||[]).map(item=>`<article class="fit-item"><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.body)}</p></article>`).join('');
  const surface=(spec.surface||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join('');
  return `<section class="card page-intro"><div class="fit-row">${fit}</div>${spec.coverage?`<p class="hint coverage">${escapeHtml(spec.coverage)}</p>`:''}${spec.age_note?`<p class="hint">${escapeHtml(spec.age_note)}</p>`:''}${surface?`<div class="surface"><small>本页可试的 API 能力</small><ul>${surface}</ul></div>`:''}</section>`;
}
function pageDocs(spec){
  const docs=spec.docs||[];
  if(!docs.length) return '';
  const items=docs.map(d=>`<a class="doc-link" href="${escapeHtml(d.url)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(d.title)}</strong><small>${escapeHtml(d.why||'')}</small></a>`).join('');
  return `<section class="card docs-footer"><div class="card-heading"><h2>测通以后：接入你们系统</h2><span class="muted">官方文档</span></div><p class="hint">效果满意后再打开这些链接。本 Demo 不是 Google 产品；请求字段以对应页面为准。</p><div class="doc-grid">${items}</div></section>`;
}
function workspaceHTML(spec){
  const ok=feature=>has(feature, spec);
  const classic=spec.family==='classic';
  const pace=classic
    ? '<option>自然</option><option>缓慢，留出思考的停顿</option><option>轻快，保持吐字清晰</option>'
    : '<option>自然</option><option>缓慢，留出思考的停顿</option><option>轻快，保持吐字清晰</option><option>逐渐加快，最后放慢</option>';
  const langs='<datalist id="languages-'+spec.id+'"><option value="cmn-CN"><option value="en-US"><option value="en-GB"><option value="ja-JP"><option value="ko-KR"><option value="fr-FR"><option value="de-DE"><option value="es-ES"></datalist>';
  const mode=ok('dialogue')?`<div class="segmented" role="group"><button class="selected" data-id="single" type="button">◉ 单人朗读</button><button data-id="dialogue" type="button">◉ ◉ 双人对话</button></div>`:'<p class="hint">本页只做单人。双人请到 Gemini-TTS 页。</p>';
  const tags=ok('tags')||ok('ssml')?`<div class="tags" data-id="tags"><span>${ok('tags')?'表演标签':'SSML 片段'}</span></div>`:'';
  const draft=ok('draft')?`<details><summary>没有台词？让文字模型帮你起草</summary><div class="draft-row"><label>主题<input data-id="topic" placeholder="例如：用生活例子解释什么是 TTS"></label><label>文字模型<input data-id="text-model" value="gemini-2.5-flash"></label></div><button class="secondary" data-id="draft" type="button">生成草稿，供我检查</button><p class="hint">会写入台词（含英语表演标签），并填入语气、语速、口音和场景。先检查再生成语音。</p></details>`:'';
  const style=ok('style')?`<section class="card"><div class="card-heading"><h2><span class="step">02</span> 给声音一点方向</h2><span class="muted">像指导配音演员</span></div><label>语气与表演</label><textarea data-id="style" rows="2" placeholder="温暖、自然，像在向一位朋友讲故事。"></textarea><p data-id="style-warn" class="hint warn" hidden></p><div class="grid2"><label>语速<select data-id="pace">${pace}</select></label><label>口音 / 发音方向<input data-id="accent" placeholder="如：标准普通话、British English"></label></div><details><summary>场景与长文设置</summary><label>场景 / 声音角色<input data-id="scene" placeholder="如：安静书店里的讲述者"></label>${ok('chunk')?`<label class="check"><input data-id="chunk" type="checkbox"> 长文按段生成并拼接</label><label>每段上限（UTF-8 字节）<input data-id="chunk-bytes" type="number" min="300" max="3000" value="1800"></label>`:''}</details></section>`:'';
  const advList=(spec.advantages||[]).map(item=>`<li>${item}</li>`).join('');
  const advBox=advList?`<ul class="advantage-list">${advList}</ul>`:'';
  const classicControls=classic?`<section class="card"><div class="card-heading"><h2><span class="step">02</span> 本页相对 Gemini 多出来的</h2><span class="muted">${spec.nav}</span></div>${advBox}<p class="hint">选这一页，是因为读法可以写成 SSML 契约。Gemini 提示词、音频标签、双人不会出现在这里。</p>${ok('ssml')?`<label class="check"><input data-id="ssml" type="checkbox"> 按 SSML 合成</label><p class="hint">${spec.model==='chirp3-hd'?'Chirp 没有 <lang>。外语片段用 <voice name="en-US-Chirp3-HD-同一短名"> 包住，不要写在全文后面。不能和流式同时开。':'标签包住要改读法的那段字。下拉框仍是默认声；<voice> 换人，<lang> 尽量同声换语（日文汉字不行）。'}</p>${tags}`:''}<label>语速（speaking_rate）<select data-id="pace">${pace}</select></label>${ok('pitch')?`<label>音高 pitch（半音，不是年龄档）<select data-id="pitch"><option value="0" selected>0 · 原声</option><option value="4">+4 · 更尖（不是童声档）</option><option value="8">+8 · 明显更高</option><option value="-4">-4 · 更沉（不是老年档）</option><option value="-8">-8 · 明显更低</option></select></label><p class="hint">AudioConfig.pitch。官方声音表没有年龄列。要换「听起来不同的人」请换 A/B/C/D，不要指望把同一把声提示成小孩。</p>`:''}${ok('chunk')?`<label class="check"><input data-id="chunk" type="checkbox"> 长文按段生成并拼接</label><label>每段上限<input data-id="chunk-bytes" type="number" min="300" max="3000" value="1800"></label>`:''}</section>`:'';
  const provider=classic?'':`<label>服务入口<select data-id="provider"><option value="vertex" selected>Vertex AI · ADC 推荐</option><option value="cloud">Cloud TTS · Gemini 模型</option><option value="gemini">Gemini API · API Key</option></select></label><label>语音模型<select data-id="model"></select></label>`;
  const extras=classic?`<label>语言 / locale<select data-id="language"></select></label><p data-id="voice-count" class="hint">换语言后，声音下拉会列出该 locale 的官方全表。</p><label>下载格式<select data-id="format"><option value="wav">WAV</option><option value="mp3">MP3</option><option value="ogg">OGG Opus</option></select></label>${ok('stream')?`<label class="check stream-switch"><input data-id="stream" type="checkbox"> 边生成边播放 <span class="pill">流式</span></label>`:''}`:`<details><summary>连接与音频格式</summary><label>Gemini API 调用方式<select data-id="api"><option value="generate">GenerateContent</option><option value="interactions">Interactions</option></select></label><label>语言代码<input data-id="language" list="languages-${spec.id}" placeholder="可留空">${langs}</label><label>下载格式<select data-id="format"><option value="wav">WAV</option><option value="mp3">MP3 · Cloud 非流式</option><option value="ogg">OGG · Cloud 非流式</option></select></label>${ok('structured')?`<label class="check"><input data-id="structured" type="checkbox"> Cloud Gemini 结构化双人（非流式）</label>`:''}</details>${ok('stream')?`<label class="check stream-switch"><input data-id="stream" type="checkbox"> 边生成边播放 <span class="pill">流式</span></label>`:''}`;
  const voices=`<section class="card"><div class="card-heading"><h2><span class="step">03</span> 选择声音</h2><span class="pill">${classic&&spec.model!=='chirp3-hd'?'本页声库':'30 种预置'}</span></div><div class="segmented voice-filters"><button class="selected" type="button" data-voice-filter="all">全部</button><button type="button" data-voice-filter="female">女声</button><button type="button" data-voice-filter="male">男声</button></div><label>${classic?'默认声音（未标记的句子）':'主声音'}<select data-id="voice"></select></label><p data-id="voice-hint" class="hint"></p>${ok('dialogue')?`<div data-id="second-voice" hidden><div class="grid2"><label>角色 A<input data-id="speaker" value="Host"></label><label>角色 B<input data-id="speaker2" value="Guest"></label></div><label>角色 B 声音<select data-id="voice2"></select></label></div>`:''}${ok('dialogue')?`<p class="hint">女声/男声只改角色 A（主声音）。角色 B 始终显示全部声线，可一男一女。</p>`:''}<p class="hint">${classic?'这一页不会出现 Gemini 提示词或 [whispers] 标签。':'点女声/男声会切换主声音。女声要凶，先写成年女性再写情绪。'}</p><hr>${provider}${extras}<p data-id="capability" class="hint"></p><button class="primary" data-id="generate" type="button"><span class="spinner" aria-hidden="true"></span><span class="btn-text">▶ 生成语音</span></button><div class="button-row"><button class="secondary" data-id="preview" type="button">预览请求 · 不收费</button><button class="secondary" data-id="stop" type="button" disabled>停止</button></div><div data-id="log-box" class="log-box idle"><div class="log-head"><span data-id="log-spinner" class="spinner" hidden></span><strong>操作记录</strong><span data-id="log-state">待命</span></div><p data-id="log-summary">本页只提交 ${spec.nav} 的请求。</p><pre data-id="log-detail" hidden></pre></div></section>`;
  return `<section class="engine-page" id="page-${spec.id}" ${spec.id==='gemini'?'':'hidden'}><div class="hero"><div><div class="eyebrow">${spec.eyebrow}</div><h1>${spec.title}</h1><p>${spec.lead}</p></div></div><div class="notice" data-id="connection">正在读取配置…</div>${classic?'':advBox}${pageIntro(spec)}<div class="workspace"><div class="editor-col"><section class="card"><div class="card-heading"><h2><span class="step">01</span> ${classic?'台词或 SSML':'写下你想说的'}</h2><span class="muted">${spec.nav}</span></div>${mode}<div class="sample-panel"><div class="sample-head"><strong>本页场景样例</strong><span class="muted">只导入 ${spec.nav}</span></div><div data-id="samples"></div><p data-id="sample-note" class="hint sample-note">样例不会跨页共用。</p></div><label>朗读台词</label><textarea data-id="text" rows="8" spellcheck="false"></textarea><div class="editor-footer"><span data-id="count">0 字符</span><label class="file-button">导入 .txt<input data-id="upload" type="file" accept=".txt,text/plain"></label></div>${ok('tags')?tags:''}${draft}</section>${style}${classicControls}</div><aside>${voices}</aside></div><section class="card output"><div class="card-heading"><h2>你的声音作品</h2><span data-id="status">等待第一段声音</span></div><div data-id="empty-output" class="empty"><span>▁ ▃ ▆ ▂ ▅ ▇ ▃ ▁</span><p>在 ${spec.nav} 页生成的音频只出现在这里。</p></div><div data-id="result" hidden><audio data-id="audio" controls></audio><div class="button-row"><a data-id="download" class="secondary" download="tts.wav">下载音频 ↓</a><button class="secondary" data-id="export" type="button">导出本次配置</button></div><p data-id="metrics" class="hint"></p></div><details data-id="preview-panel"><summary>请求预览</summary><p data-id="plan-info"></p><pre data-id="request-preview"></pre></details></section>${pageDocs(spec)}</section>`;
}
function bindWorkspace(root, spec){
  const click=(id, fn)=>{const el=root.querySelector(`[data-id="${id}"]`); if(el) el.onclick=fn;};
  click('single',()=>{setMode('single');capabilities();});
  click('dialogue',()=>{setMode('dialogue');capabilities();});
  click('generate',generate); click('preview',preview); click('draft',draft);
  click('stop',()=>{controller?.abort();stopPlayback();});
  click('export',()=>{if(!savedConfig)return; const u=URL.createObjectURL(new Blob([JSON.stringify(savedConfig,null,2)],{type:'application/json'})); const a=document.createElement('a'); a.href=u; a.download=`${spec.id}-config.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(u),1000);});
  const provider=root.querySelector('[data-id="provider"]'); if(provider) provider.onchange=()=>{capabilities(true);fillVoiceSelects(true);};
  ['model','stream','chunk','ssml','language'].forEach(id=>{const el=root.querySelector(`[data-id="${id}"]`); if(el) el.onchange=()=>{capabilities();fillVoiceSelects(id==='language');};});
  const voice=root.querySelector('[data-id="voice"]'); if(voice) voice.onchange=()=>{describeVoice(voice.value);checkStyleConflict();};
  root.querySelectorAll('[data-voice-filter]').forEach(button=>button.onclick=()=>setVoiceFilter(button.dataset.voiceFilter,true));
  const text=root.querySelector('[data-id="text"]'); if(text) text.oninput=count;
  ['style','scene'].forEach(id=>{const el=root.querySelector(`[data-id="${id}"]`); if(el) el.addEventListener('input',checkStyleConflict);});
  const audio=root.querySelector('[data-id="audio"]'); if(audio) audio.onplay=stopPlayback;
  const upload=root.querySelector('[data-id="upload"]');
  if(upload) upload.onchange=async()=>{const f=upload.files[0]; if(!f)return; if(f.size>90000){report('error','文件过大，请使用小于 90 KB 的 UTF-8 文本。');return;} try{$('text').value=new TextDecoder('utf-8',{fatal:true}).decode(await f.arrayBuffer()); count(); report('ok',`已导入 ${f.name}。`);}catch(e){fail(e,'请将文本文件保存为 UTF-8 编码后再导入。');} upload.value='';};
  bindTags(root, spec);
}
async function post(path,data,signal){
  const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal});
  if(!response.ok){
    let body; try{body=await response.json();}catch{}
    const d=body&&body.detail;
    const err=Error(typeof d==='string'?d:(d&&d.message)||`请求失败（${response.status}）`);
    err.detail=typeof d==='string'?d:(d&&d.detail)||(body?JSON.stringify(body,null,2):'HTTP '+response.status);
    throw err;
  }
  return response;
}
function setBusy(value){busy=value; ['generate','draft','preview','upload'].forEach(id=>{if($(id)) $(id).disabled=value;}); if($('stop')) $('stop').disabled=!value; if($('generate')) $('generate').classList.toggle('busy',value);}
function stopPlayback(){sources.forEach(s=>{try{s.stop();}catch{}}); sources=[]; pendingByte=null; if(audioContext){audioContext.close().catch(()=>{}); audioContext=null;}}
async function preparePlayback(){stopPlayback(); audioContext=new(window.AudioContext||window.webkitAudioContext)({sampleRate:24000}); await audioContext.resume(); nextAudioTime=audioContext.currentTime+.08;}
function playPCM(bytes){
  if(!audioContext) return;
  if(pendingByte!==null){const joined=new Uint8Array(bytes.length+1); joined[0]=pendingByte; joined.set(bytes,1); bytes=joined; pendingByte=null;}
  if(bytes.length%2){pendingByte=bytes[bytes.length-1]; bytes=bytes.slice(0,-1);} if(!bytes.length) return;
  const data=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength), buffer=audioContext.createBuffer(1,bytes.length/2,24000), floats=buffer.getChannelData(0);
  for(let i=0;i<floats.length;i++) floats[i]=data.getInt16(i*2,true)/32768;
  const node=audioContext.createBufferSource(); node.buffer=buffer; node.connect(audioContext.destination); nextAudioTime=Math.max(nextAudioTime,audioContext.currentTime+.015); node.start(nextAudioTime); nextAudioTime+=buffer.duration; sources.push(node); node.onended=()=>{sources=sources.filter(s=>s!==node);};
}
function waveBlob(chunks){const length=chunks.reduce((n,b)=>n+b.length,0), header=new ArrayBuffer(44), v=new DataView(header); function str(o,s){[...s].forEach((c,i)=>v.setUint8(o+i,c.charCodeAt(0)));} str(0,'RIFF'); v.setUint32(4,length+36,true); str(8,'WAVE'); str(12,'fmt '); v.setUint32(16,16,true); v.setUint16(20,1,true); v.setUint16(22,1,true); v.setUint32(24,24000,true); v.setUint32(28,48000,true); v.setUint16(32,2,true); v.setUint16(34,16,true); str(36,'data'); v.setUint32(40,length,true); return new Blob([header,...chunks],{type:'audio/wav'});}
async function preview(){
  if(busy) return; setBusy(true); report('loading','正在预览请求，不会调用语音模型…');
  try{
    const p=await(await post('/api/preview',config())).json();
    if($('plan-info')) $('plan-info').textContent=`预计 ${p.requests} 次语音请求 · 正文 ${p.text_bytes} 字节。${p.warnings.join(' ')}`;
    if($('request-preview')) $('request-preview').textContent=JSON.stringify({page:active,config:config(),first_prompt:p.prompt,segments:p.chunks},null,2);
    if($('preview-panel')) $('preview-panel').open=true;
    report('ok',`预览成功：预计 ${p.requests} 次语音请求。`,p.warnings.join('\n'));
  }catch(e){fail(e,'预览失败');}
  finally{setBusy(false);}
}
async function generate(){
  if(busy) return; const r=config(); controller=new AbortController(); const serial=++requestSerial; setBusy(true); report('loading','正在连接并生成语音…'); if($('status')) $('status').textContent='检查输入并连接…'; if($('result')) $('result').hidden=true; if($('empty-output')) $('empty-output').hidden=false; if($('audio')) $('audio').pause(); const chunks=[]; let done=false;
  try{
    if(r.stream) await preparePlayback(); else stopPlayback();
    const response=await post('/api/synthesize',r,controller.signal), reader=response.body.getReader(), decoder=new TextDecoder(); let pending='';
    function handle(line){
      if(!line.trim()) return;
      let e; try{e=JSON.parse(line);}catch{const err=Error('服务器返回无法解析的数据。'); err.detail=line.slice(0,4000); throw err;}
      if(e.type==='error'){const err=Error(e.message||'生成失败'); err.detail=e.detail||''; throw err;}
      if(e.type==='start') report('loading',`已连接，共 ${e.segments} 段，正在生成…`,(e.warnings||[]).filter(w=>/男声|女声|传统|SSML/.test(w)).join('\n'));
      if(e.type==='segment'){if($('status')) $('status').textContent=`正在生成第 ${e.index} / ${e.total} 段…`; report('loading',`正在生成第 ${e.index} / ${e.total} 段…`);}
      if(e.type==='audio'){const b=Uint8Array.from(atob(e.data),c=>c.charCodeAt(0)); chunks.push(b); if(r.stream&&r.format==='wav') playPCM(b);}
      if(e.type==='done'){
        if(!chunks.length) throw Error('没有收到音频。'); if(pendingByte!==null) throw Error('音频数据不完整，请重试。'); done=true;
        const blob=r.format==='wav'?waveBlob(chunks):new Blob(chunks,{type:r.format==='mp3'?'audio/mpeg':'audio/ogg'});
        if(objectUrl) URL.revokeObjectURL(objectUrl); objectUrl=URL.createObjectURL(blob);
        if($('audio')) $('audio').src=objectUrl; if($('download')){$('download').href=objectUrl; $('download').download=`${active}-${Date.now()}.${r.format}`;}
        savedConfig=Object.assign({page:active},r); if($('result')) $('result').hidden=false; if($('empty-output')) $('empty-output').hidden=true; if($('status')) $('status').textContent='生成完成 · 请试听核对';
        const metrics=`首段音频 ${e.first_audio} 秒 · 总耗时 ${e.seconds} 秒${e.duration!==null?` · 音频时长 ${e.duration} 秒`:''} · ${(e.bytes/1024).toFixed(1)} KB。`;
        if($('metrics')) $('metrics').textContent=metrics; report('ok','生成成功。请试听并核对是否漏字。',metrics);
      }
    }
    while(true){const {value,done:ended}=await reader.read(); if(ended) break; pending+=decoder.decode(value,{stream:true}); const lines=pending.split('\n'); pending=lines.pop(); for(const line of lines) handle(line);} pending+=decoder.decode(); if(pending.trim()) handle(pending); if(!done) throw Error('连接提前结束，没有收到完成标记。请重新生成。');
  }catch(e){controller.abort(); stopPlayback(); if($('result')) $('result').hidden=true; if($('empty-output')) $('empty-output').hidden=false; if($('status')) $('status').textContent=e.name==='AbortError'?'已停止':'未完成'; fail(e,'生成失败');}
  finally{if(serial===requestSerial) setBusy(false);}
}
function applyDraft(result){
  if($('text')&&result.text) $('text').value=result.text;
  if($('style')&&result.style) $('style').value=result.style;
  if($('pace')&&result.pace){
    const sel=$('pace');
    if([...sel.options].some(o=>o.value===result.pace)) sel.value=result.pace;
  }
  if($('accent')&&result.accent!=null) $('accent').value=result.accent;
  if($('scene')&&result.scene!=null){
    $('scene').value=result.scene;
    const wrap=$('scene').closest('details');
    if(wrap&&result.scene) wrap.open=true;
  }
  count(); checkStyleConflict();
}
async function draft(){
  if(busy||!$('topic')) return; setBusy(true); controller=new AbortController(); report('loading','文字模型正在起草台词和表演提示…');
  try{
    const result=await(await post('/api/draft',{
      topic:$('topic').value, model:val('text-model','gemini-2.5-flash'),
      dialogue:mode==='dialogue', speaker:val('speaker','Host'), speaker2:val('speaker2','Guest'),
      voice:val('voice','Kore'), voice2:val('voice2','Puck'),
    },controller.signal)).json();
    applyDraft(result);
    report('ok','草稿已放入台词，并填入「给声音一点方向」。请先检查标签和提示词再生成。');
  }catch(e){fail(e,'写稿失败');}
  finally{setBusy(false);}
}
function escapeHtml(value){return value.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function inlineMarkdown(value){return escapeHtml(value).replace(/\[([^\]]+)\]\((https:\/\/[^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');}
function renderMarkdown(src){
  const lines=src.replace(/\r\n/g,'\n').split('\n'), out=[]; let i=0;
  while(i<lines.length){
    const line=lines[i];
    if(line.startsWith('```')){const buf=[]; i++; while(i<lines.length&&!lines[i].startsWith('```')){buf.push(escapeHtml(lines[i])); i++;} i++; out.push('<pre><code>'+buf.join('\n')+'</code></pre>'); continue;}
    if(line.startsWith('|')&&lines[i+1]&&/^\|?\s*-+/.test(lines[i+1])){
      const rows=[]; while(i<lines.length&&lines[i].startsWith('|')){if(!/^\|?\s*-+/.test(lines[i])) rows.push(lines[i]); i++;}
      out.push('<table>'+rows.map((row,index)=>{const cells=row.split('|').slice(1,-1).map(cell=>inlineMarkdown(cell.trim())); const tag=index?'td':'th'; return '<tr>'+cells.map(cell=>`<${tag}>${cell}</${tag}>`).join('')+'</tr>';}).join('')+'</table>'); continue;
    }
    if(/^---+$/.test(line.trim())){out.push('<hr>'); i++; continue;}
    const heading=line.match(/^(#{1,3})\s+(.*)$/); if(heading){out.push(`<h${heading[1].length}>${inlineMarkdown(heading[2])}</h${heading[1].length}>`); i++; continue;}
    if(/^\s*[-*]\s+/.test(line)){const items=[]; while(i<lines.length&&/^\s*[-*]\s+/.test(lines[i])){items.push('<li>'+inlineMarkdown(lines[i].replace(/^\s*[-*]\s+/,''))+'</li>'); i++;} out.push('<ul>'+items.join('')+'</ul>'); continue;}
    if(/^\s*\d+\.\s+/.test(line)){const items=[]; while(i<lines.length&&/^\s*\d+\.\s+/.test(lines[i])){items.push('<li>'+inlineMarkdown(lines[i].replace(/^\s*\d+\.\s+/,''))+'</li>'); i++;} out.push('<ol>'+items.join('')+'</ol>'); continue;}
    if(!line.trim()){i++; continue;}
    const buf=[line]; i++; while(i<lines.length&&lines[i].trim()&&!/^(#{1,3}\s|```|\||---|[-*]\s|\d+\.\s)/.test(lines[i])) buf.push(lines[i++]);
    out.push('<p>'+inlineMarkdown(buf.join(' '))+'</p>');
  }
  return out.join('');
}
async function loadDoc(kind,target){const response=await fetch('/api/doc/'+kind); if(!response.ok) throw Error('文档加载失败'); const data=await response.json(); $(target).innerHTML=renderMarkdown(data.text); return data.text;}
function page(name){
  if(!catalog) return;
  const engines=(catalog.workspaces||[]).map(item=>item.id);
  const isEngine=engines.includes(name);
  document.querySelectorAll('.engine-page').forEach(el=>el.hidden=el.id!=='page-'+name);
  ['learn','sources'].forEach(id=>{const el=document.getElementById(id); if(el) el.hidden=name!==id;});
  document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.page===name));
  if(isEngine){
    active=name;
    if(!primed.has(name)){
      primed.add(name); mode='single'; voiceFilter='all';
      capabilities(true); fillVoiceSelects(true); renderSamples();
      const notice=$('connection'); if(notice) notice.textContent=connectionText();
    }
  }
  window.scrollTo({top:0,behavior:'smooth'});
}
function connectionText(){
  const ready=catalog.project_configured&&catalog.adc_configured;
  if(ready) return '✓ 已配置 Cloud 项目与 ADC。本页按当前引擎单独提交请求。';
  if(catalog.project_configured) return '○ 已填项目，但未检测到 ADC。请运行 gcloud auth application-default login 后重启。';
  if(catalog.adc_configured) return '○ 已有 ADC，请在 .env 填写 GOOGLE_CLOUD_PROJECT 并重启。';
  if(catalog.key_configured) return '✓ 已配置 Gemini API Key。传统 Cloud 页仍需要 ADC。';
  return '○ 预览不需要凭据。生成请配置 ADC 与项目。';
}
async function init(){
  try{
    catalog=await(await fetch('/api/catalog')).json();
    const host=$('workspaces');
    (catalog.workspaces||[]).forEach(spec=>{
      host.insertAdjacentHTML('beforeend', workspaceHTML(spec));
      bindWorkspace(document.getElementById('page-'+spec.id), spec);
    });
    $('voice-rules').innerHTML=htmlTable(catalog.voice_rules);
    $('compare-providers').innerHTML=htmlTable(catalog.compare_providers);
    $('compare-models').innerHTML=htmlTable(catalog.compare_models);
    $('compare-classic').innerHTML=htmlTable(catalog.compare_classic);
    $('compare-why-classic').innerHTML=htmlTable(catalog.why_classic);
    $('compare-age').innerHTML=htmlTable(catalog.age_control);
    $('compare-fit').innerHTML=htmlTable(catalog.fit_guide);
    $('api-out-of-demo').innerHTML=htmlTable(catalog.api_out_of_demo);
    page('gemini');
    try{await loadDoc('guide','guide-content');}catch(e){$('guide-content').textContent='学习指南加载失败：'+e.message;}
    try{
      const text=await loadDoc('sources','source-content'); const seen=new Set();
      for(const match of text.matchAll(/\[([^\]]+)\]\((https:\/\/[^)]+)\)/g)){
        if(seen.has(match[2])) continue; seen.add(match[2]);
        const a=document.createElement('a'); a.className='source-link'; a.href=match[2]; a.target='_blank'; a.rel='noopener noreferrer'; a.textContent=match[1]+' ↗';
        const sub=document.createElement('small'); sub.textContent=new URL(match[2]).hostname; a.append(sub); $('source-links').append(a);
      }
    }catch(e){$('source-content').textContent='官方资料加载失败：'+e.message;}
  }catch(e){fail(e,'初始化失败');}
}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>page(b.dataset.page));
$('show-guide').onclick=()=>loadDoc('guide','guide-content').catch(e=>fail(e,'文档加载失败'));
$('show-readme').onclick=()=>loadDoc('readme','guide-content').catch(e=>fail(e,'文档加载失败'));
window.addEventListener('beforeunload',()=>{controller?.abort(); if(objectUrl) URL.revokeObjectURL(objectUrl);});
init();
