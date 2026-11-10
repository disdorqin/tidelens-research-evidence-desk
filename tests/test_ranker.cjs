"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const {tokens,rank}=require("../web/research-ranking.js");
const papers=[
 {id:"001",title:"Long-term Memory for Multimodal Agents",url:"https://arxiv.org/abs/2611.001v1",
  evidence_quote:"Memory improves retrieval for multimodal agents.",topics:["agents"]},
 {id:"002",title:"Forecasting Bots and Human Prediction",url:"https://arxiv.org/abs/2611.002v1",
  evidence_quote:"Forecast quality is evaluated from historical records.",topics:["forecast"]},
 {id:"003",title:"Evaluation of Robust AI Systems",url:"https://arxiv.org/abs/2611.003v1",
  evidence_quote:"Reliability and verification are evaluated in benchmarks.",topics:["evaluation"]}
];
test("Chinese/English agent questions normalize into comparable tokens",()=>{
 assert.deepEqual(tokens("How can 智能体 use 长期记忆?"),["agent","memory"]);
});
test("memory question selects a relevant primary title with explained matches",()=>{
 const r=rank("How do agents use memory?",papers);
 assert.equal(r.results[0].id,"001");
 assert.equal(r.coverage,"all_terms_found");
 assert.ok(r.results[0].score>=8);
 assert.match(r.results[0].reason,/标题/);
});
test("forecast question returns forecast paper with transparent incomplete coverage",()=>{
 const r=rank("How to improve forecasting?",papers);
 assert.equal(r.results[0].id,"002");
 assert.ok(["all_terms_found","partial_terms_only"].includes(r.coverage));
});
test("no matches is not filled with invented papers",()=>{
 const r=rank("quantum crystallography zebras",papers);
 assert.equal(r.results.length,0);
 assert.equal(r.coverage,"no_match");
});
test("empty/only stopword question returns no evidence",()=>{
 for(const question of ["","a to the and", "???"]){
  const r=rank(question,papers);
  assert.deepEqual(r.results,[]);
  assert.equal(r.coverage,"empty_query");
 }
});
test("limit is bounded and score ordering stable",()=>{
 const r=rank("agents memory forecasting evaluation",papers,999);
 assert.ok(r.results.length<=5);
 assert.ok(r.results.every((x,i)=>i===0||r.results[i-1].score>=x.score));
});
test("unmatched query terms are explicit",()=>{
 const r=rank("memory rhinoceros",papers);
 assert.ok(r.unmatchedTerms.includes("rhinoceros"));
 assert.notEqual(r.coverage,"all_terms_found");
});
test("does not make network calls or use dynamic execution",()=>{
 const {readFileSync}=require("node:fs");
 const code=readFileSync(require.resolve("../web/research-ranking.js"),"utf8");
 assert.doesNotMatch(code,/\bfetch\(/);
 assert.doesNotMatch(code,/\beval\(/);
 assert.doesNotMatch(code,/\bXMLHttpRequest\b/);
});
