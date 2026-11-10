/* Evidence-first lexical question matching.
 * Not semantic retrieval, peer-review or a scientific truth verifier.
 * Runs offline in browsers/Node without credentials or network calls.
 */
(function(root){
"use strict";
const STOP=new Set("a an and are as at based be by can do for from how in into is it of on or the their this to use using via what when where which with we our improve new more does".split(" "));
const SYNONYMS=[
  [/智能体|代理系统|代理模型|agentic|agents?/g," agent "],
  [/长期记忆|记忆|记住|存储|memory/g," memory "],
  [/预测|预报|时间序列|时序|forecast|prediction/g," forecast "],
  [/可靠性|可信|验证|核验|安全|安全性|可靠|evaluation|verification/g," evaluation "],
  [/论文|科研|科学研究|paper|research/g," research "],
  [/多模态|视觉语言|multimodal/g," multimodal "],
  [/检索|搜索|召回|retrieval/g," retrieval "],
  [/错误|失败|幻觉|hallucination/g," failure "],
];
function normalize(x){
 let s=String(x||"").toLowerCase().normalize("NFKC");
 for(const [re,word] of SYNONYMS)s=s.replace(re,word);
 return s;
}
function tokens(question){
 const raw=normalize(question).match(/[\p{L}\p{N}]+/gu)||[];
 return [...new Set(raw.filter(w=>w.length>=3&&!STOP.has(w)).slice(0,16))];
}
const common=(words,text)=>{
 const lookup=new Set(tokens(text));
 return words.filter(w=>lookup.has(w));
};
function rank(question,papers,limit=3){
 const terms=tokens(question);
 if(terms.length===0)return {terms:[],results:[],coverage:"empty_query",matchedTerms:[],unmatchedTerms:[]};
 const rows=[];
 for(const paper of papers||[]){
   if(!paper||!paper.title||!paper.url)continue;
   const titleHits=common(terms,paper.title);
   const quoteHits=common(terms,paper.evidence_quote);
   const topicHits=common(terms,(paper.topics||[]).join(" "));
   const union=new Set([...titleHits,...quoteHits,...topicHits]);
   if(!union.size)continue;
   const score=titleHits.length*5+quoteHits.length*2+topicHits.length*3;
   rows.push({id:paper.id,url:paper.url,title:paper.title,score,
     matches:[...union],titleMatches:titleHits,quoteMatches:quoteHits,topicMatches:topicHits,
     reason:"标题 "+titleHits.length+" · 原文引句 "+quoteHits.length+" · 方向标签 "+topicHits.length+" 个词命中"});
 }
 rows.sort((a,b)=>b.score-a.score||String(a.id).localeCompare(String(b.id)));
 const results=rows.slice(0,Math.max(1,Math.min(5,limit)));
 const hit=new Set(results.flatMap(r=>r.matches));
 return {terms,results,coverage:results.length===0?"no_match":
   hit.size===terms.length?"all_terms_found":"partial_terms_only",
   matchedTerms:[...hit],unmatchedTerms:terms.filter(x=>!hit.has(x))};
}
const api={tokens,rank};
if(typeof module!=="undefined"&&module.exports)module.exports=api;
else root.TideLensRanking=api;
})(typeof window!=="undefined"?window:{});
