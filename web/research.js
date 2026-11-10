"use strict";

/* STEM2Connect Scientific Research candidate. Client only renders previously
 * collected public arXiv metadata and quote checks; it never calls external
 * accounts, LLM APIs or sends private information. */
const model = {papers:[], filtered:[], selected:null, topic:"all", sort:"recent", search:""};
const $ = id => document.getElementById(id);
const topicNames = {agents:"智能体 / 记忆",forecast:"预测 / 时序",evaluation:"评测 / 可信",general:"其他科研"};
const make=(tag,cls,value)=>{
 const n=document.createElement(tag);
 if(cls)n.className=cls;
 if(value!==undefined)n.textContent=String(value);
 return n;
};
const safeArxiv = raw => {
 try {const url=new URL(raw);return url.protocol==="https:" && url.hostname==="arxiv.org" && /^\/abs\/\d{4}\.\d{4,5}v\d+$/.test(url.pathname) ? url.href : "";}
 catch{return "";}
};
const valid = x => x && safeArxiv(x.url) && typeof x.title==="string" &&
 typeof x.evidence_quote==="string" && x.evidence_quote.length>=15 &&
 /^[0-9a-f]{64}$/.test(x.abstract_sha256) &&
 x.quote_exact_match===true && x.evidence_level==="author_submitted_arxiv_abstract" &&
 x.peer_review_confirmed===false && Array.isArray(x.topics);
const fmt = iso => {
 const d=new Date(iso);
 return isNaN(d.getTime())?"未知时间":new Intl.DateTimeFormat("zh-CN",{month:"2-digit",day:"2-digit",year:"numeric",timeZone:"UTC"}).format(d);
};
function filterPapers(){
 const q=model.search.trim().toLocaleLowerCase();
 let docs=model.papers.filter(x=>(model.topic==="all"||x.topics.includes(model.topic))&&
 (!q||[x.title,...x.authors,x.topics.join(" ")]
 .some(y=>String(y).toLocaleLowerCase().includes(q))));
 docs.sort(model.sort==="name"?(a,b)=>a.title.localeCompare(b.title): (a,b)=>
 Date.parse(b.published_utc)-Date.parse(a.published_utc));
 model.filtered=docs;
 return docs;
}
function drawPapers(){
 const docs=filterPapers();
 $("resultcount").textContent="展示 "+docs.length+" / "+model.papers.length+" 篇原始论文快照";
 const root=$("paperlist");
 root.replaceChildren();
 if(!docs.length){root.append(make("div","empty","该方向暂时没有匹配论文。调整筛选或搜索条件。"));detail(null);return;}
 if(!docs.some(x=>x.id===model.selected))model.selected=docs[0].id;
 for(const x of docs){
   const b=make("button","paper"+(model.selected===x.id?" selected":""));
   b.type="button";
   b.setAttribute("role","listitem");
   b.setAttribute("aria-pressed",String(model.selected===x.id));
   const h=make("div","paperhead");
   h.append(make("span","category",topicNames[x.topics[0]]||"研究论文"),
            make("span","paperdate",fmt(x.published_utc)));
   const foot=make("div","paperfoot");
   foot.append(make("span","pending","arXiv 作者投稿摘要"),
               make("span","verified","✓ 原文引句匹配"));
   b.append(h,make("h3","",x.title),
            make("p","",x.authors.slice(0,3).join("、")||"作者未列出"),foot);
   b.addEventListener("click",()=>{
      model.selected=x.id;
      drawPapers();
      if(matchMedia("(max-width:1080px)").matches)$("papertitle").scrollIntoView({behavior:"smooth",block:"center"});
   });
   root.append(b);
 }
 detail(docs.find(x=>x.id===model.selected));
}
function detail(x){
 $("claim").value="";
 $("claimresult").textContent="尚未核对。";
 $("claimresult").className="claimresult";
 const block=$("modelblock");
 block.hidden=true;
 if(!x){
  $("papertitle").textContent="没有选中的论文";
  $("paperid").textContent="—";$("authors").textContent="";
  $("quote").textContent="—";$("hash").textContent="—";
  $("original-status").textContent="未读取";
  $("match-status").textContent="未检查";
  $("model-status").textContent="未运行";
  $("original").href="https://arxiv.org/";
  return;
 }
 $("papertitle").textContent=x.title;
 $("paperid").textContent=x.id;
 $("authors").textContent=x.authors.join("、")+" · "+fmt(x.published_utc);
 $("original-status").textContent="arXiv 官方公开 API 元数据，原始链接保留。";
 $("match-status").textContent="采集时与作者投稿摘要逐字匹配；只验证文字来源。";
 $("quote").textContent=x.evidence_quote;
 $("hash").textContent=x.abstract_sha256.slice(0,18)+"…";
 $("original").href=safeArxiv(x.url);
 const ai=x.ai||{};
 if(ai.status==="quote_checked"&&ai.source_quote_verified&&
    typeof ai.summary==="string"&&typeof ai.quote==="string"&&ai.quote.length<=80){
    $("model-status").textContent="真实模型已调用，输出引句经摘要原文校验；语义仍未独立复核。";
    $("modelsummary").textContent=ai.summary;
    $("modelprovenance").textContent="证据引句："+ai.quote+" · Provider: "+(ai.provider||"未记录");
    block.hidden=false;
 }else{
    $("model-status").textContent=ai.status==="unavailable_or_unverified"?
     "模型调用未通过证据校验，未展示不可信回答。" :
     "此论文未进行模型推断；未使用模板冒充 AI。";
 }
}
function check(){
 const x=model.papers.find(p=>p.id===model.selected);
 const input=$("claim").value.trim();
 const result=$("claimresult");
 result.className="claimresult";
 if(!x||!input){result.textContent="请先输入待验证的连续原文。";return;}
 // This checks only the visible short quotation. It never implies full-text
 // entailment or independent scientific validation.
 if(input.length>=5&&x.evidence_quote.includes(input)){
    result.classList.add("good");
    result.textContent="✓ 引句片段逐字出现于当前展示的原文证据。仍不能据此认定科学结论真实。";
 }else{
    result.classList.add("bad");
    result.textContent="证据不足：当前展示的短引句未逐字包含这段话。请打开 arXiv 原文再核对。";
 }
}
function topicFilter(tag){
 model.topic=tag;
 document.querySelectorAll(".filter").forEach(b=>{
   const chosen=b.dataset.topic===tag;
   b.classList.toggle("active",chosen);
   b.setAttribute("aria-pressed",String(chosen));
 });
 drawPapers();
}
async function load(){
 try{
  const res=await fetch("./research-data.json",{cache:"no-store"});
  if(!res.ok)throw Error("snapshot_http_error");
  const data=await res.json();
  if(data.schema!=="tidelens-scientific-research/v1" ||
     data.source!=="arxiv_public_api" || data.is_live_source_snapshot!==true ||
     !Array.isArray(data.papers))throw Error("snapshot_schema_error");
  model.papers=data.papers.filter(valid);
  if(!model.papers.length)throw Error("empty_valid_papers");
  $("count").textContent=model.papers.length;
  $("quoted").textContent=model.papers.filter(x=>x.quote_exact_match).length;
  $("aicount").textContent=model.papers.filter(x=>x.ai?.status==="quote_checked"&&x.ai.source_quote_verified===true).length;
  $("snapshot").textContent="官方接口快照 · "+fmt(data.snapshot_utc)+" UTC";
  drawPapers();
 }catch{
  $("resultcount").textContent="科研数据加载失败";
  $("paperlist").replaceChildren(make("div","empty",
  "无法读取研究快照。请在 web/ 所在目录启动静态 HTTP 服务，并确认 research-data.json 存在。"));
 }
}
$("search").addEventListener("input",e=>{model.search=e.target.value;drawPapers()});
$("sort").addEventListener("change",e=>{model.sort=e.target.value;drawPapers()});
document.querySelectorAll(".filter").forEach(b=>b.addEventListener("click",()=>topicFilter(b.dataset.topic)));
$("verify").addEventListener("click",check);
$("claim").addEventListener("keydown",e=>{if(e.key==="Enter")check()});
$("explore").addEventListener("click",()=>$("workbench").scrollIntoView({behavior:"smooth"}));
$("copy").addEventListener("click",async()=>{
 const x=model.papers.find(p=>p.id===model.selected);
 if(!x)return;
 const cite=x.authors.join(", ")+". "+x.title+". arXiv ("+x.published_utc.slice(0,10)+"). "+x.url;
 const btn=$("copy");
 try{
   if(!navigator.clipboard?.writeText)throw Error("clipboard_not_available");
   await navigator.clipboard.writeText(cite);
   btn.textContent="引用已复制";
 }catch{
   const result=$("claimresult");
   result.className="claimresult";
   result.textContent="本地引用文本："+cite;
 }
});
load();
