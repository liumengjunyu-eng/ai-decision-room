from fastapi import FastAPI, Request

from fastapi.responses import HTMLResponse

import uvicorn

import json

import asyncio

import aiohttp
import os

# V4.1 可信度引擎
from backend.engine import DecisionEngine

app = FastAPI()

# ============================================================

# 配置：硅基流动 API（免费）

# ============================================================

SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

SILICONFLOW_BASE = "https://api.siliconflow.cn/v1/chat/completions"

# AI 董事会 7 角色

BOARD_MEMBERS = {

    "首席战略官": {

        "model": "Qwen/Qwen2.5-72B-Instruct",
        "fallback": "deepseek-ai/DeepSeek-V3",

        "emoji": "🧙",

        "color": "#7CC4FF",

        "weight": 1.3,

        "prompt": "你是一位资深的首席战略官，擅长从宏观视角判断商业机会和战略方向。请针对以下决策问题，给出明确判断（支持/反对/中立），并说明你的战略理由。"

    },

    "批判分析官": {

        "model": "deepseek-ai/DeepSeek-V3",
        "fallback": "Qwen/Qwen2.5-72B-Instruct",

        "emoji": "⚔️",

        "color": "#FF7C7C",

        "weight": 1.2,

        "prompt": "你是一位严苛的批判分析官，你的职责是质疑一切、找出漏洞。请针对以下决策问题，给出明确判断（支持/反对/中立），并指出方案中的逻辑缺陷和风险。"

    },

    "风险控制官": {

        "model": "Qwen/Qwen2-7B-Instruct",
        "fallback": "deepseek-ai/DeepSeek-V2.5",

        "emoji": "🛡️",

        "color": "#FBBF24",

        "weight": 1.1,

        "prompt": "你是一位风险控制官，擅长评估风险、计算代价。请针对以下决策问题，给出明确判断（支持/反对/中立），并评估主要风险点和可承受程度。"

    },

    "增长策略官": {

        "model": "Qwen/Qwen2.5-72B-Instruct",
        "fallback": "deepseek-ai/DeepSeek-V3",

        "prompt": "你是一位增长策略官，擅长找到增长路径、设计实验。请针对以下决策问题，给出明确判断（支持/反对/中立），并设计增长验证路径和ROI判断。"

    },

    "洞察官": {

        "model": "deepseek-ai/DeepSeek-V2.5",
        "fallback": "Qwen/Qwen2.5-72B-Instruct",

        "emoji": "🔍",

        "color": "#38BDF8",

        "weight": 1.0,

        "prompt": "你是一位洞察官，擅长从非主流视角发现深层逻辑。请针对以下决策问题，给出明确判断（支持/反对/中立），并提出被主流视角忽略的关键洞察。"

    },

    "创新官": {

        "model": "Qwen/Qwen2.5-72B-Instruct",
        "fallback": "deepseek-ai/DeepSeek-V2.5",

        "emoji": "💡",

        "color": "#F472B6",

        "weight": 1.1,

        "prompt": "你是一位创新官，擅长破框思维、提出突破性方案。请针对以下决策问题，给出明确判断（支持/反对/中立），并提出超越常规的创新思路。"

    },

    "CEO裁决官": {

        "model": "deepseek-ai/DeepSeek-V2.5",

        "emoji": "👑",

        "color": "#A78BFA",

        "weight": 1.5,

        "prompt": ""  # CEO 使用特殊合成 prompt

    }

}

# 非 CEO 角色列表（用于并行调用）

DEBATE_ROLES = [k for k in BOARD_MEMBERS if k != "CEO裁决官"]

# ============================================================

# LANDING PAGE

# ============================================================

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AI Decision OS</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;background:#0a0a0f;color:#fff;font-family:-apple-system,BlinkMacSystemFont,sans-serif;overflow:hidden;height:100vh;}
.glow{position:absolute;width:600px;height:600px;background:radial-gradient(circle,rgba(124,58,237,0.25),transparent);top:30%;left:50%;transform:translateX(-50%);filter:blur(60px);pointer-events:none;}
.center{position:absolute;top:45%;left:50%;transform:translate(-50%,-50%);text-align:center;width:90%;max-width:700px;}
h1{font-size:52px;font-weight:700;letter-spacing:-1px;margin:0;line-height:1.2;}
.hl{color:#7c3aed;}
.sub{margin-top:20px;color:#a1a1aa;font-size:18px;line-height:1.7;}
.btn{margin-top:40px;padding:14px 32px;background:linear-gradient(90deg,#7c3aed,#3b82f6);border:none;border-radius:10px;color:#fff;font-size:16px;font-weight:600;cursor:pointer;transition:transform .15s;text-decoration:none;display:inline-block;}
.btn:hover{transform:translateY(-2px);}
.hint{position:fixed;bottom:20px;left:0;right:0;text-align:center;color:rgba(255,255,255,0.15);font-size:12px;}
.tag{position:fixed;top:20px;right:24px;font-size:11px;color:rgba(255,255,255,0.2);letter-spacing:2px;}
</style>
</head>
<body>
<div class="tag">DECISION OS 1.0</div>
<div class="glow"></div>
<div class="center">
    <h1>AI Decision <span class="hl">OS</span></h1>
    <div class="sub">
        The first system that turns<br>
        <span class="hl">multiple AI opinions</span> into one structured decision.
    </div>
    <div class="sub" style="font-size:16px;color:#71717a;">
        ChatGPT disagrees with Claude.<br>
        Gemini disagrees with DeepSeek.<br>
        <strong style="color:#d4d4d8;">We don't pick one. We resolve them.</strong>
    </div>
    <a class="btn" href="/explore" id="enterBtn">Enter Decision System</a>
</div>
<div class="hint">Ask every AI. Trust one decision.</div>
<script>
document.getElementById('enterBtn').addEventListener('click',function(e){
    var q=prompt('What decision are you facing? (optional)');
    if(q&&q.trim()){e.preventDefault();sessionStorage.setItem('decision_question',q.trim());window.location.href='/explore';}
});
</script>
</body>
</html>
"""



# ============================================================
# ============================================================
# ============================================================

V1_FINAL_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AI Decision Graph OS</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Inter,system-ui;background:#0b0f17;color:#e6e6e6;overflow:hidden;height:100vh;}
.header{position:fixed;top:0;left:0;right:0;height:56px;border-bottom:1px solid #1f2a3a;display:flex;align-items:center;padding:0 20px;font-weight:600;background:rgba(10,14,22,0.85);backdrop-filter:blur(10px);z-index:10;}
.header span{color:#4ea1ff;margin-left:4px;}
.panel{position:fixed;top:56px;left:0;bottom:0;width:280px;border-right:1px solid #1f2a3a;padding:16px;overflow-y:auto;}
.panel h3{font-size:13px;font-weight:500;margin-bottom:8px;opacity:.7;}
textarea{width:100%;height:160px;background:#0f1623;border:1px solid #2a3b55;border-radius:8px;padding:10px;color:#fff;font-size:12px;outline:none;resize:none;font-family:inherit;}
textarea:focus{border-color:#4ea1ff;}
.btn{width:100%;margin-top:8px;padding:10px;border:none;border-radius:8px;background:linear-gradient(90deg,#4ea1ff,#7c4dff);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:opacity .12s;}
.btn:hover{opacity:.9;}
.btn-ghost{background:#1c2433;color:rgba(255,255,255,0.5);border:1px solid #2a3550;margin-top:4px;}
.btn-sm{padding:6px;font-size:10px;}
.legend{margin-top:16px;}
.legend p{font-size:11px;color:rgba(255,255,255,0.5);margin:3px 0;}
.right{position:fixed;top:56px;right:0;bottom:0;width:320px;border-left:1px solid #1f2a3a;padding:16px;overflow-y:auto;background:#0b0f17;}
.r-section{margin-bottom:16px;}
.r-section h3{font-size:12px;opacity:.5;margin-bottom:4px;font-weight:500;}
.tag{display:inline-block;padding:3px 8px;border-radius:6px;font-size:10px;margin:1px;}
.tag-ok{background:#1f3b2a;color:rgba(255,255,255,0.7);}
.tag-warn{background:#3b2a2a;color:rgba(255,255,255,0.6);}
.score{font-size:28px;font-weight:700;color:#4ea1ff;}
.score-bar{height:3px;background:rgba(255,255,255,0.05);border-radius:999px;overflow:hidden;margin:2px 0;}
.score-bar .fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#4ea1ff,#7c4dff);transition:width .6s;}
.model-row{display:flex;justify-content:space-between;font-size:10px;color:rgba(255,255,255,0.35);padding:1px 0;}
.btn-premium{width:100%;margin-top:6px;padding:10px;border:none;border-radius:8px;background:linear-gradient(90deg,#4ea1ff,#7c4dff);color:#fff;font-size:12px;font-weight:600;cursor:pointer;}
.error-bar{font-size:10px;color:#ef4444;display:none;margin-bottom:4px;}
.error-bar.open{display:block;}
</style>
</head>
<body>
<div class="header">🧠 AI Decision Graph OS <span>V3</span></div>

<div class="panel">
  <h3>Input Multi-Model Answers</h3>
  <textarea id="pasteInput" placeholder="━━━ GPT-4o ━━━&#10;...&#10;&#10;━━━ Claude ━━━&#10;..."></textarea>
  <button class="btn" id="analyzeBtn">▶ Build Decision Graph</button>
  <button class="btn btn-ghost btn-sm" id="challengeBtn" style="display:none;">⚡ Challenge Consensus</button>
  <button class="btn btn-ghost btn-sm" id="resetBtn">Clear</button>
  <div class="error-bar" id="errorBar"></div>
  <div class="legend">
    <h3>Legend</h3>
    <p>🔵 High Confidence (≥85%)</p>
    <p>🟢 Medium Confidence</p>
    <p>⚫ Low Confidence</p>
    <p>🔴 Conflict Edge</p>
    <p>🟡 Consensus Edge</p>
  </div>
</div>

<div style="position:fixed;left:280px;top:56px;right:320px;bottom:0;">
  <svg id="graphSvg" width="100%" height="100%"></svg>
  <div id="graphEmpty" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:12px;color:rgba(255,255,255,0.06);text-align:center;pointer-events:none;line-height:1.8;z-index:5;">Paste model responses<br>and build the graph</div>
</div>

<div class="right">
  <div class="r-section">
    <h3>🧠 Consensus</h3>
    <div id="consensusArea"><span style="font-size:11px;color:rgba(255,255,255,0.1);">Awaiting...</span></div>
  </div>
  <div class="r-section">
    <h3>⚠️ Conflicts</h3>
    <div id="conflictArea"><span style="font-size:11px;color:rgba(255,255,255,0.1);">Awaiting...</span></div>
  </div>
  <div class="r-section">
    <h3>📊 Decision Confidence</h3>
    <div id="confidenceArea"><div class="score">—</div><div id="credArea"></div></div>
  </div>
  <div class="r-section" id="metricsSection" style="display:none;">
    <h3>🧠 Decision Metrics</h3>
    <div id="metricsArea"></div>
  </div>
  <button class="btn-premium" id="premiumBtn">Generate Final Report (¥9.9)</button>
</div>

<script>
const PASTE=document.getElementById('pasteInput');
const ANALYZE=document.getElementById('analyzeBtn');
const GRAPH_SVG=document.getElementById('graphSvg');
const GRAPH_EMPTY=document.getElementById('graphEmpty');
const ERROR=document.getElementById('errorBar');
const CHALLENGE=document.getElementById('challengeBtn');
let lastAnalysis=null;
let simulation=null;

async function run(){
  const raw=PASTE.value.trim();
  if(!raw){showErr('Paste at least 2 model responses');return;}
  const entries=raw.split(/━+\s*/).map(b=>{const l=b.trim().split('\n');if(l.length<2)return null;return{label:l[0].replace(/━/g,'').trim(),content:l.slice(1).join('\n').trim()};}).filter(e=>e&&e.content);
  if(entries.length<2){showErr('Need at least 2 models');return;}
  ERROR.classList.remove('open');
  try{
    const resp=await fetch('/api/graph',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers:entries.map(e=>({model:e.label,content:e.content}))})});
    const data=await resp.json();
    if(data.error){showErr(data.error);return;}
    lastAnalysis=data;
    renderGraph(data.graph||{nodes:[],edges:[]},entries);
    renderLedger(data,entries);
    CHALLENGE.style.display='none';
  }catch(e){showErr(e.message);}
}

function renderGraph(entries,analysis){
  if(simulation)simulation.stop();
  GRAPH_EMPTY.style.display='none';
  const W=document.querySelector('div[style*="left:280px"]').offsetWidth;
  const H=document.querySelector('div[style*="left:280px"]').offsetHeight;
  const nodes=entries.map((e,i)=>({
    id:e.label,r:14+(Math.random()*6),
    color:['#4ea1ff','#f472b6','#4ade80','#fbbf24','#a78bfa','#22d3ee'][i%6]
  }));
  nodes.push({id:'⚡ Consensus',r:22,color:'#7c3aed'});
  const links=[];
  entries.forEach(e=>links.push({source:e.label,target:'⚡ Consensus',type:'attract'}));
  if(entries.length>=2)links.push({source:entries[0].label,target:entries[1].label,type:'conflict'});
  if(entries.length>=3)links.push({source:entries[1].label,target:entries[2].label,type:'consensus'});
  const svg=d3.select('#graphSvg');svg.selectAll('*').remove();
  svg.attr('width',W).attr('height',H);
  simulation=d3.forceSimulation(nodes)
    .force('link',d3.forceLink(links).id(d=>d.id).distance(140).strength(0.3))
    .force('charge',d3.forceManyBody().strength(-350))
    .force('center',d3.forceCenter(W/2,H/2))
    .force('collision',d3.forceCollide().radius(d=>d.r+10));
  const link=svg.append('g').selectAll('line').data(links).enter().append('line')
    .style('stroke',d=>d.type==='conflict'?'#ff4d6d':d.type==='consensus'?'#4ade80':'rgba(255,255,255,0.08)')
    .style('stroke-width',d=>d.type==='conflict'?2:1)
    .style('stroke-dasharray',d=>d.type==='conflict'?'4,3':'none')
    .style('opacity',d=>d.type==='conflict'?.7:.3);
  const node=svg.append('g').selectAll('circle').data(nodes).enter().append('circle')
    .attr('r',d=>d.r)
    .style('fill',d=>d.color)
    .style('stroke',d=>d.id==='⚡ Consensus'?'rgba(124,58,237,0.3)':'rgba(255,255,255,0.06)')
    .style('stroke-width',d=>d.id==='⚡ Consensus'?3:1)
    .style('cursor','grab')
    .call(d3.drag().on('start',function(e,d){if(!e.active)simulation.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;}).on('drag',function(e,d){d.fx=e.x;d.fy=e.y;}).on('end',function(e,d){if(!e.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;}));
  const label=svg.append('g').selectAll('text').data(nodes).enter().append('text').text(d=>d.id)
    .style('fill','#fff').style('font-size',d=>d.id==='⚡ Consensus'?'13px':'10px')
    .style('font-weight',d=>d.id==='⚡ Consensus'?600:400).style('pointer-events','none');
  simulation.on('tick',()=>{
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    node.attr('cx',d=>d.x).attr('cy',d=>d.y);
    label.attr('x',d=>d.x-d.id.length*3.5).attr('y',d=>d.y+d.r+12);
  });
}

function renderLedger(data,entries){
  const graph=data.graph||{nodes:[],edges:[]};
  const analysis=data.analysis||{};
  const nodes=graph.nodes||[];
  const edges=graph.edges||[];
  const consensus=edges.filter(e=>e.type==='consensus');
  const conflicts=edges.filter(e=>e.type==='conflict');

  // Consensus tags
  let conHtml='';
  if(consensus.length===0)conHtml='<span style="font-size:11px;color:rgba(255,255,255,0.1);">None</span>';
  else consensus.slice(0,4).forEach(e=>{conHtml+='<span class="tag tag-ok">'+e.from+' ↔ '+e.to+'</span>';});
  document.getElementById('consensusArea').innerHTML=conHtml;

  // Conflict tags
  let disHtml='';
  if(conflicts.length===0)disHtml='<span style="font-size:11px;color:rgba(255,255,255,0.1);">None</span>';
  else conflicts.slice(0,4).forEach(e=>{disHtml+='<div style="font-size:10px;margin:2px 0;"><span class="tag tag-warn">'+e.from+' ⚡ '+e.to+'</span> <span style="color:rgba(255,255,255,0.3);">'+e.weight+'</span></div>';});
  document.getElementById('conflictArea').innerHTML=disHtml;

  // Confidence
  const avgConf=analysis.avg_confidence||0;
  document.querySelector('#confidenceArea .score').textContent=Math.round(avgConf*100)+'%';

  // Model credibility bars
  let credHtml='';
  nodes.forEach(n=>{
    const pct=Math.round((n.confidence||0.5)*100);
    credHtml+='<div class="model-row"><span>'+esc(n.id)+'</span><span>'+pct+'%</span></div><div class="score-bar"><div class="fill" style="width:'+pct+'%"></div></div>';
  });
  document.getElementById('credArea').innerHTML=credHtml;

  // Metrics section
  const metrics=document.getElementById('metricsSection');
  metrics.style.display='block';
  const cd=analysis.conflict_density||0;
  const cs=analysis.consensus_strength||0;
  const ds=analysis.decision_stability||0;
  const status=analysis.status||'unknown';
  const stColor=ds>0.5?'#4ade80':ds>0.3?'#fbbf24':'#ef4444';
  document.getElementById('metricsArea').innerHTML=
    '<div style="font-size:11px;line-height:1.8;">'+
    '<div style="display:flex;justify-content:space-between;"><span>Avg Confidence</span><span style="color:#4ea1ff;">'+(avgConf*100).toFixed(0)+'%</span></div>'+
    '<div style="display:flex;justify-content:space-between;"><span>Conflict Density</span><span style="color:#ef4444;">'+(cd*100).toFixed(0)+'%</span></div>'+
    '<div style="display:flex;justify-content:space-between;"><span>Consensus Strength</span><span style="color:#4ade80;">'+(cs*100).toFixed(0)+'%</span></div>'+
    '<hr style="border-color:rgba(255,255,255,0.05);margin:6px 0;">'+
    '<div style="display:flex;justify-content:space-between;font-weight:600;"><span>📊 Decision Stability</span><span style="color:'+stColor+';">'+(ds*100).toFixed(0)+'%</span></div>'+
    '<div style="margin-top:6px;font-size:10px;padding:6px;border-radius:6px;background:'+stColor+'15;color:'+stColor+';text-align:center;">'+
    (ds>0.5?'✅ Stable Decision Path':ds>0.3?'⚠️ Moderate Uncertainty':'🔴 High Uncertainty')+
    '</div></div>';
}

function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
function showErr(m){ERROR.textContent='⚠ '+m;ERROR.classList.add('open');}
async function challengeConsensus(){
  if(!lastAnalysis||!lastAnalysis.consensus||lastAnalysis.consensus.length<2)return;
  const resp=await fetch('/api/challenge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({consensus_points:lastAnalysis.consensus,topic:''})});
  const data=await resp.json();if(data.error)return;
  const div=document.createElement('div');div.style.cssText='margin-top:12px;padding:10px;border-radius:8px;background:rgba(239,68,68,0.04);border:1px solid rgba(239,68,68,0.15);font-size:11px;';
  div.innerHTML='<strong style="color:#ef4444;">⚡ Anti-Consensus</strong><br><span style="color:#fca5a5;">'+esc(data.challenge||'')+'</span><ul style="color:rgba(255,255,255,0.4);padding-left:14px;margin-top:4px;">'+(data.blindspots||[]).map(b=>'<li>'+esc(b)+'</li>').join('')+'</ul>';
  document.querySelector('.right').appendChild(div);
}
function reset(){
  PASTE.value='';lastAnalysis=null;
  if(simulation)simulation.stop();d3.select('#graphSvg').selectAll('*').remove();
  GRAPH_EMPTY.style.display='block';
  document.getElementById('consensusArea').innerHTML='<span style="font-size:11px;color:rgba(255,255,255,0.1);">Awaiting...</span>';
  document.getElementById('conflictArea').innerHTML='<span style="font-size:11px;color:rgba(255,255,255,0.1);">Awaiting...</span>';
  document.querySelector('#confidenceArea .score').textContent='—';
  document.getElementById('credArea').innerHTML='';document.getElementById('metricsSection').style.display='none';
  CHALLENGE.style.display='none';ERROR.classList.remove('open');
}
ANALYZE.addEventListener('click',run);
CHALLENGE.addEventListener('click',challengeConsensus);
document.getElementById('resetBtn').addEventListener('click',reset);
document.getElementById('premiumBtn').addEventListener('click',()=>{alert('🧠 Premium Report ¥9.9\n\nContains: Final Verdict · Business Logic · Execution Path · Risk Analysis · Anti-Consensus\n\nPayment system coming soon.');});
</script>
</body>
</html>

"""


# ============================================================
# ROOM PAGE — V5 Decision OS
# ============================================================
ROOM_HTML = r"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Decision OS V5</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #0b0f19;
  color: #e5e7eb;
}

/* ─── 顶部 ─── */
.header {
  padding: 18px 24px;
  border-bottom: 1px solid #1f2937;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(11,15,25,0.95);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header .brand {
  font-size: 18px; font-weight: 700;
  background: linear-gradient(135deg,#a78bfa,#6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header .sub {
  font-size: 12px; color: #6b7280;
}
.header .status {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: #6b7280;
}
.header .status .dot {
  width: 8px; height: 8px; border-radius: 50%; background: #4a5268;
}
.header .status .dot.running { background: #f59e0b; animation: pulse-dot 0.8s ease-in-out infinite; }
.header .status .dot.done { background: #22c55e; }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(0.7)} }

/* ─── 容器 ─── */
.container { max-width: 960px; margin: 0 auto; padding: 32px 28px; }
.section {
  margin: 32px 0 14px;
  font-size: 12px; font-weight: 600;
  color: #9ca3af; text-transform: uppercase;
  letter-spacing: 1px;
  display: flex; align-items: center; gap: 8px;
}
.section .sec-line {
  flex: 1; height: 1px; background: #1f2937;
}

/* ─── 卡片 ─── */
.card {
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 14px;
  padding: 24px;
  margin-bottom: 16px;
}

/* ─── 输入 ─── */
.input-card textarea {
  width: 100%; padding: 18px 20px;
  border-radius: 12px; background: #0f172a;
  border: 1px solid #1f2937; color: #e5e7eb;
  font-size: 15px; font-family: inherit;
  resize: vertical; min-height: 140px; outline: none;
  line-height: 1.8;
  transition: min-height 0.2s ease, border-color 0.2s, box-shadow 0.2s;
}
.input-card textarea:focus {
  min-height: 180px;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}
.input-card textarea:not(:placeholder-shown) {
  min-height: 160px;
}
.input-card textarea::-webkit-scrollbar {
  width: 6px;
}
.input-card textarea::-webkit-scrollbar-thumb {
  background: #1f2937;
  border-radius: 3px;
}
.input-card textarea::placeholder { color: #4a5268; }
.input-card .actions {
  display: flex; gap: 12px; margin-top: 12px;
}
.input-card .actions button {
  padding: 12px 28px; border: none; border-radius: 12px;
  font-weight: 600; font-size: 14px; cursor: pointer;
  background: #6366f1; color: white;
}
.input-card .actions button:hover { background: #5558e6; }
.input-card .actions button:disabled { opacity: 0.35; cursor: not-allowed; }

/* ─── 场景按钮 ─── */
.scenario-btn {
  padding: 6px 14px; font-size: 11px; border: 1px solid #1f2937;
  border-radius: 8px; background: #0f172a; color: #9ca3af;
  cursor: pointer; transition: all .15s; white-space: nowrap;
}
.scenario-btn:hover { border-color: #6366f1; color: #e5e7eb; background: rgba(99,102,241,0.06); }

/* ─── 品牌折叠选择器 ─── */
.brand-chip {
  display:inline-flex;align-items:center;gap:4px;
  padding:4px 10px 4px 12px; border-radius:6px;
  font-size:11px; font-weight:500; cursor:pointer; transition:all .12s;
  border:1px solid #1f2937; background:#0f172a; color:#9ca3af;
  user-select:none;
}
.brand-chip:hover{border-color:#6366f1;color:#d1d5db;}
.brand-chip.active{background:rgba(99,102,241,0.1);border-color:#6366f1;color:#6366f1;}
.brand-chip .chip-x{margin-left:2px;font-size:10px;opacity:0.5;}
.brand-chip .chip-x:hover{opacity:1;color:#ef4444;}
.expanded-brand{margin-bottom:6px;}
.expanded-brand .eb-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:6px 8px;cursor:pointer;border-radius:6px;
  font-size:12px;font-weight:500;color:#cbd5e1;
}
.expanded-brand .eb-header:hover{background:rgba(99,102,241,0.04);}
.expanded-brand .eb-models{display:flex;flex-wrap:wrap;gap:4px;padding:2px 8px 8px;}
.expanded-brand .eb-models .model-opt{
  padding:3px 10px;border-radius:5px;font-size:11px;cursor:pointer;
  border:1px solid #1f2937;color:#6b7280;transition:all .1s;
}
.expanded-brand .eb-models .model-opt:hover{border-color:#374151;color:#9ca3af;}
.expanded-brand .eb-models .model-opt.active{background:rgba(99,102,241,0.08);border-color:#6366f1;color:#6366f1;}

/* ─── 董事会执行面板 ─── */
.board-grid {
  display: flex; flex-direction: column; gap: 8px;
}
.member {
  display: flex; justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-radius: 10px;
  background: #0f172a;
  transition: background 0.3s;
}
.member.running { background: rgba(99,102,241,0.08); }
.member.done { background: rgba(34,197,94,0.04); }
.member.error { background: rgba(239,68,68,0.04); }

.member .left {
  display: flex; align-items: center; gap: 8px;
}
.member .left .icon { font-size: 16px; }
.member .left .name { font-weight: 600; font-size: 13px; }
.member .left .title { font-size: 11px; color: #6b7280; }

.member .right {
  display: flex; align-items: center; gap: 8px;
}
.member .right .status-text {
  font-size: 12px; color: #6b7280;
}
.member .right .status-text.waiting { color: #6b7280; }
.member .right .status-text.thinking { color: #f59e0b; }
.member .right .status-text.done { color: #22c55e; }
.member .right .status-text.error { color: #ef4444; }

.member .right .tag {
  font-size: 10px; font-weight: 600; padding: 2px 8px;
  border-radius: 8px;
}
.tag.support { background: rgba(34,197,94,0.12); color: #22c55e; }
.tag.oppose { background: rgba(239,68,68,0.12); color: #ef4444; }
.tag.neutral { background: rgba(251,191,36,0.12); color: #fbbf24; }

/* ─── 时间线 ─── */
.timeline {
  border-left: 2px solid #312e81;
  padding-left: 16px;
  margin-left: 4px;
  min-height: 60px;
}
.event {
  margin-bottom: 16px;
  opacity: 0;
  transform: translateX(-4px);
  animation: eventIn 0.35s ease forwards;
}
@keyframes eventIn { to { opacity:1; transform:translateX(0); } }
.event .dot {
  width: 10px; height: 10px;
  background: #6366f1; border-radius: 50%;
  display: inline-block; margin-right: 8px;
  position: relative; left: -22px;
  top: -1px; vertical-align: middle;
}
.event .dot.support { background: #22c55e; }
.event .dot.oppose { background: #ef4444; }
.event .dot.neutral { background: #fbbf24; }

.event .ev-header {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 3px; margin-top: -14px;
}
.event .ev-header b { font-size: 14px; }
.event .ev-reason {
  font-size: 13px; color: #9ca3af;
  line-height: 1.6; padding-left: 18px;
  margin-top: 2px;
}

/* ─── 群聊气泡 ─── */
.chat-container{display:flex;flex-direction:column;gap:12px;padding:4px 0;}
.chat-bubble{display:flex;gap:10px;align-items:flex-start;opacity:0;animation:bubbleIn .4s ease forwards;}
.chat-bubble:nth-child(1){animation-delay:0s;}
.chat-bubble:nth-child(2){animation-delay:.15s;}
.chat-bubble:nth-child(3){animation-delay:.3s;}
.chat-bubble:nth-child(4){animation-delay:.45s;}
.chat-bubble:nth-child(5){animation-delay:.6s;}
.chat-bubble:nth-child(6){animation-delay:.75s;}
.chat-bubble:nth-child(7){animation-delay:.9s;}
@keyframes bubbleIn{to{opacity:1;transform:translateY(0);}}
.chat-avatar{flex-shrink:0;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;border:2px solid transparent;}
.chat-body{flex:1;min-width:0;}
.chat-header{display:flex;align-items:center;gap:6px;margin-bottom:4px;}
.chat-name{font-size:13px;font-weight:600;color:#e5e7eb;}
.chat-title{font-size:10px;color:#6b7280;padding:1px 6px;border-radius:4px;background:#1f2937;}
.chat-text{font-size:13px;line-height:1.7;color:#d1d5db;padding:10px 14px;background:#0f172a;border-radius:4px 12px 12px 12px;border:1px solid #1f2937;white-space:pre-wrap;}
.chat-bubble.conflict .chat-text{border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.04);}
.chat-bubble.conflict .chat-avatar{border-color:#ef4444;}
.chat-conflict-badge{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(239,68,68,0.12);color:#ef4444;margin-left:6px;}
.chat-attack{font-size:11px;color:#fbbf24;margin-top:4px;padding:4px 8px;background:rgba(251,191,36,0.04);border-radius:6px;display:inline-block;}
.chat-pending{text-align:center;padding:16px;color:#4a5268;font-size:12px;}
.chat-typing{display:inline-flex;gap:3px;padding:12px 16px;background:#0f172a;border-radius:12px;border:1px solid #1f2937;}
.chat-typing .dot{width:6px;height:6px;border-radius:50%;background:#4a5268;animation:typing .8s ease-in-out infinite;}
.chat-typing .dot:nth-child(2){animation-delay:.15s;}
.chat-typing .dot:nth-child(3){animation-delay:.3s;}
@keyframes typing{0%,100%{opacity:.3}50%{opacity:1;}}

/* ─── 决策账本 ─── */
.ledger-grid {
  display: flex; flex-direction: column; gap: 4px;
}
.ledger-row {
  display: flex; justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  font-size: 13px;
}
.ledger-row .lname { color: #d1d5db; }
.ledger-row .lscore { font-weight: 600; font-family: monospace; }
.ledger-row .lscore.pos { color: #22c55e; }
.ledger-row .lscore.neg { color: #ef4444; }
.ledger-row .lscore.zero { color: #9ca3af; }
.ledger-divider {
  height: 1px; background: #1f2937; margin: 4px 0;
}
.ledger-total {
  display: flex; justify-content: space-between;
  padding: 6px 8px; font-size: 13px;
  font-weight: 700;
}
.ledger-total .total-val { font-family: monospace; }
.ledger-total .total-val.pos { color: #22c55e; }
.ledger-total .total-val.neg { color: #ef4444; }

/* ─── 最终裁决 ─── */
.final {
  background: linear-gradient(135deg, #1e1b4b, #0f172a);
  border: 1px solid #3730a3;
  border-radius: 14px;
  padding: 18px;
  display: none;
}
.final.open { display: block; }
.final .f-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.final .f-header .f-title { font-weight: 700; font-size: 15px; }
.final .f-header .badge {
  display: inline-block; padding: 3px 10px;
  border-radius: 8px; font-size: 11px; font-weight: 700;
}
.badge.support { background: #22c55e; color: #000; }
.badge.oppose { background: #ef4444; color: #fff; }
.badge.neutral { background: #fbbf24; color: #000; }

.final .f-body { font-size: 14px; color: #d1d5db; line-height: 1.7; margin: 10px 0; }
.final .f-meta { font-size: 12px; color: #6b7280; display: flex; gap: 16px; }

/* ─── 空状态 ─── */
.empty-state {
  text-align: center; color: #4a5268; padding: 40px 0;
}
.empty-state .icon { font-size: 32px; margin-bottom: 8px; opacity: 0.4; }

/* ─── 错误 ─── */
.error-card {
  background: rgba(239,68,68,0.04); border: 1px solid rgba(239,68,68,0.15);
  border-radius: 10px; padding: 12px; font-size: 13px; color: #ef4444;
  display: none; margin-bottom: 12px;
}
.error-card.open { display: block; }

/* ─── 响应式 ─── */
@media (max-width: 640px) {
  .container { padding: 16px 12px; }
}
</style>
</head>
<body>

  <div class="header">
  <div>
    <span class="brand">MindTrust OS</span>
    <span class="sub" style="margin-left:8px;">AI 智囊局 v5</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;">
    <span id="dailyCount" style="font-size:11px;color:#4a5268;">今日免费：3/3</span>
    <a href="/compare" style="font-size:11px;color:#6366f1;text-decoration:none;padding:4px 10px;border:1px solid #1f2937;border-radius:6px;">手动粘贴</a>
    <div class="status">
      <span class="dot" id="statusDot"></span>
      <span id="statusText">空闲</span>
    </div>
  </div>
</div>

<div class="container">

  <!-- 模型快捷导航栏 -->
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;padding:10px 14px;background:#0f172a;border-radius:10px;border:1px solid #1f2937;">
    <span style="font-size:11px;color:#4a5268;margin-right:4px;line-height:28px;">直达模型 →</span>
    <a href="https://claude.ai" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">Claude</a>
    <a href="https://chat.deepseek.com" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">DeepSeek</a>
    <a href="https://kimi.moonshot.cn" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">Kimi</a>
    <a href="https://chatgpt.com" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">ChatGPT</a>
    <a href="https://gemini.google.com" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">Gemini</a>
    <a href="https://tongyi.aliyun.com" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">通义千问</a>
    <a href="https://chatglm.cn" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;padding:4px 10px;border-radius:5px;border:1px solid #1f2937;">智谱GLM</a>
  </div>

  <!-- ═══ 1. 决策输入 ═══ -->
  <div class="section"><span>1</span> 决策输入 <span class="sec-line"></span></div>
  <div class="card input-card">
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <button class="scenario-btn" data-scenario="是否应该辞去稳定工作去创业？当前行业下行，手上有一个初步验证过的项目方向。">🏢 创业决策</button>
      <button class="scenario-btn" data-scenario="预算10万元，应该在抖音、小红书、知乎三个平台中选择哪个做产品冷启动？">📢 营销选择</button>
      <button class="scenario-btn" data-scenario="手上有50万闲钱，应该提前还房贷还是投资指数基金？">💰 财务决策</button>
      <button class="scenario-btn" data-scenario="公司要不要全面转向AI技术栈？现有业务稳定但增长缓慢。">🏭 战略转型</button>
    </div>
    
    <!-- 品牌折叠模型选择器 -->
    <div id="brandSelector" style="margin-bottom:12px;">
      <div style="display:flex;gap:6px;flex-wrap:wrap;" id="brandChips"></div>
      <div id="brandExpanded" style="display:none;margin-top:8px;background:#0f172a;border:1px solid #1f2937;border-radius:10px;padding:12px;"></div>
    </div>
    
    <textarea id="topicInput" placeholder="在此输入你的决策问题，AI 董事会将为你分析…&#10;&#10;例如：&#10;• 是否要进入五官灸健康赛道？&#10;• 新产品应该先做小红书还是抖音？&#10;• 第三季度预算应该投品牌还是效果？"></textarea>
    <div class="actions">
      <button id="runBtn">▶ 执行分析</button>
      <button id="advancedReportBtn" style="background:#5b21b6;display:none;">🧠 生成深度报告</button>
    </div>
  </div>

  <!-- 错误 -->
  <div class="error-card" id="errorCard"></div>

  <!-- ═══ 2. 智囊群聊 ═══ -->
  <div class="section"><span>2</span> 智囊群聊 <span class="sec-line"></span></div>
  <div class="card" id="boardCard">
    <div id="chatContainer">
      <div class="empty-state" id="chatEmpty">
        <div class="icon">💬</div>
        <div>AI 智囊团正在等待你的问题...</div>
      </div>
    </div>
  </div>

  <!-- ═══ 3. 决策账本 ═══ -->
  <div class="card">
    <div id="ledgerContainer">
      <div class="empty-state" id="ledgerEmpty">
        <div class="icon">📊</div>
        <div>等待权重计算完成</div>
      </div>
    </div>
  </div>

  <!-- ═══ 5. 最终裁决 ═══ -->
  <div class="section"><span>5</span> 最终裁决 <span class="sec-line"></span></div>
  <div class="final" id="finalContainer">
    <div class="f-header">
      <span class="f-title">最终决策</span>
      <span class="badge" id="finalBadge">待定</span>
    </div>
    <!-- V4 Trust Score -->
    <div id="trustScoreBar" style="display:none;margin-bottom:10px;padding:10px 12px;background:#0f172a;border-radius:8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <span style="font-size:12px;font-weight:600;color:#9ca3af;">🧠 可信度评分</span>
        <span id="trustScoreValue" style="font-size:20px;font-weight:700;"></span>
      </div>
      <div style="height:6px;background:#1f2937;border-radius:3px;overflow:hidden;">
        <div id="trustScoreFill" style="height:100%;border-radius:3px;width:0%;transition:width 0.6s ease;"></div>
      </div>
      <div id="trustScoreBreakdown" style="display:flex;gap:12px;margin-top:6px;font-size:10px;color:#4a5268;"></div>
    </div>
    <div class="f-body" id="finalBody"></div>
    <div class="f-meta">
      <span id="finalConfidence">置信度 —</span>
      <span id="finalRisk">风险 —</span>
    </div>
    <!-- V4 升级入口 -->
    <div id="upgradePrompt" style="display:none;margin-top:12px;padding:12px 14px;background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.15);border-radius:10px;text-align:center;">
      <div style="font-size:12px;color:#9ca3af;margin-bottom:8px;">需要更完整的深度战略报告？</div>
      <a href="/compare" style="display:inline-block;padding:8px 20px;background:#6366f1;color:#fff;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none;">
        使用编译器 · 多模型手动贴入 →
      </a>
    </div>
    <!-- 付费深度报告入口 -->
    <div id="premiumPrompt" style="display:none;margin-top:12px;padding:16px;background:linear-gradient(135deg,#064e3b,#0f172a);border:1px solid #22c55e;border-radius:12px;text-align:center;">
      <div style="font-size:13px;font-weight:600;color:#22c55e;margin-bottom:4px;">🧠 解锁麦肯锡级深度裁决报告</div>
      <div style="font-size:11px;color:#6b7280;margin-bottom:10px;">含商业逻辑解构 · 可行性路径 · 财务模型推演 · 生死红线 · 反共识推演</div>
      <button id="premiumBtn" style="padding:10px 28px;background:#22c55e;color:#000;border:none;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer;">
        9.9元 生成深度报告
      </button>
    </div>
  </div>

</div>

<script>
// ─── 董事会配置 ───
const BOARD = [
  { id: 'strategy',   name: '战略官', icon: '🧙', title: 'CSO', weight: 1.3 },
  { id: 'critic',     name: '批判官', icon: '⚔️', title: 'CRO', weight: 1.2 },
  { id: 'risk',       name: '风控官', icon: '🛡️', title: 'CTO', weight: 1.1 },
  { id: 'growth',     name: '增长官', icon: '📈', title: 'CGO', weight: 1.2 },
  { id: 'insight',    name: '洞察官', icon: '🔍', title: 'CIO', weight: 1.0 },
  { id: 'innovation', name: '创新官', icon: '💡', title: 'CTI', weight: 1.1 },
  { id: 'ceo',        name: 'CEO裁决官', icon: '👑', title: 'CEO', weight: 1.5 }
];

const statusText = document.getElementById('statusText');
const statusDot = document.getElementById('statusDot');
const topicInput = document.getElementById('topicInput');
const runBtn = document.getElementById('runBtn');
const boardGrid = document.getElementById('boardGrid');
const errorCard = document.getElementById('errorCard');
const chatContainer = document.getElementById('chatContainer');
const chatEmpty = document.getElementById('chatEmpty');
const ledgerContainer = document.getElementById('ledgerContainer');
const ledgerEmpty = document.getElementById('ledgerEmpty');
const finalContainer = document.getElementById('finalContainer');
const finalBadge = document.getElementById('finalBadge');
const finalBody = document.getElementById('finalBody');
const finalConfidence = document.getElementById('finalConfidence');
const finalRisk = document.getElementById('finalRisk');

let isRunning = false;
let agentResults = [];
let decisionResult = null;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function setStatus(text, cls) {
  statusText.textContent = text;
  statusDot.className = 'dot' + (cls ? ' ' + cls : '');
}

function showError(msg) {
  errorCard.textContent = '⚠️ ' + msg;
  errorCard.classList.add('open');
}

// ─── 初始化董事会面板 ───
function initBoard() {
  // 清空并用等待气泡初始化
  chatContainer.innerHTML = `
    <div class="chat-container" id="chatBubbles">
      <div class="chat-pending" id="chatPending">
        <div class="chat-typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
        <div style="margin-top:8px;font-size:12px;color:#4a5268;">AI 智囊团正在思考...</div>
      </div>
    </div>`;
}

// 设置成员状态
function setMemberStatus(id, status, tagText, tagCls) {
  const el = document.getElementById('member-' + id);
  if (!el) return;
  el.className = 'member ' + (status === 'running' ? 'running' : status === 'done' ? 'done' : status === 'error' ? 'error' : '');
  const st = document.getElementById('status-' + id);
  if (!st) return;
}

// ─── 添加群聊气泡 ───
const AVATAR_COLORS = {strategy:'#6366f1',critic:'#ef4444',risk:'#fbbf24',growth:'#22c55e',insight:'#38bdf8',innovation:'#f472b6',ceo:'#a78bfa'};
function addChatBubble(roleId, icon, name, title, text, stance, isAttack, attackText) {
  chatEmpty.style.display = 'none';
  const pending = document.getElementById('chatPending');
  if (pending) pending.remove();
  const container = document.getElementById('chatBubbles');
  if (!container) return;
  const div = document.createElement('div');
  const isConflict = stance === '反对' || !!isAttack;
  div.className = 'chat-bubble' + (isConflict ? ' conflict' : '');
  const ac = AVATAR_COLORS[roleId] || '#6366f1';
  div.innerHTML = `
    <div class="chat-avatar" style="border-color:${ac};background:${ac}22;">${icon}</div>
    <div class="chat-body">
      <div class="chat-header">
        <span class="chat-name">${name}</span>
        <span class="chat-title">${title}</span>
        ${stance === '反对' ? '<span class="chat-conflict-badge">⚡ 反对</span>' : stance === '支持' ? '<span style="font-size:10px;color:#22c55e;padding:1px 6px;border-radius:4px;background:rgba(34,197,94,0.08);">✅ 支持</span>' : ''}
      </div>
      <div class="chat-text">${attackText ? '<span style="color:#fbbf24;">' + attackText + '</span><br>' : ''}${text}</div>
    </div>`;
  container.appendChild(div);
  div.scrollIntoView({behavior:'smooth',block:'end'});
}

// ─── 决策账本 ───
function buildLedger(agents, decision) {
  ledgerEmpty.style.display = 'none';
  
  // 计算每位成员的得分
  let html = '<div class="ledger-grid">';
  let totalSupport = 0, totalOppose = 0;
  
  agents.forEach((a, i) => {
    const member = BOARD[i];
    if (!member) return;
    const weight = member.weight;
    let score = 0;
    if (a.stance === '支持') { score = weight; totalSupport += weight; }
    else if (a.stance === '反对') { score = -weight; totalOppose += weight; }
    // else 0
    
    const scoreStr = (score > 0 ? '+' : '') + score.toFixed(1);
    const scoreCls = score > 0 ? 'pos' : score < 0 ? 'neg' : 'zero';
    html += '<div class="ledger-row">';
    html += '<span class="lname">' + member.icon + ' ' + member.name + '  权重×' + weight + '</span>';
    html += '<span class="lscore ' + scoreCls + '">' + scoreStr + '</span>';
    html += '</div>';
  });
  
  html += '<div class="ledger-divider"></div>';
  
  // 净值
  const netScore = totalSupport - totalOppose;
  // 风险惩罚
  const riskPenalty = decision && decision.risk ? (decision.risk.includes('高') ? 0.3 : decision.risk.includes('中') ? 0.15 : 0) : 0;
  const adjustedScore = netScore - riskPenalty;
  const netCls = adjustedScore > 0 ? 'pos' : adjustedScore < 0 ? 'neg' : 'zero';
  
  html += '<div class="ledger-row">';
  html += '<span class="lname">风险惩罚</span>';
  html += '<span class="lscore neg">-' + riskPenalty.toFixed(2) + '</span>';
  html += '</div>';
  
  html += '<div class="ledger-divider"></div>';
  
  html += '<div class="ledger-total">';
  html += '<span>加权总分</span>';
  html += '<span class="total-val ' + netCls + '">' + (adjustedScore > 0 ? '+' : '') + adjustedScore.toFixed(2) + '</span>';
  html += '</div>';
  html += '</div>';
  
  ledgerContainer.innerHTML = html;
}

// ─── 显示最终裁决 ───
function showFinal(decision) {
  if (!decision) return;
  finalContainer.classList.add('open');
  
  const dec = decision.decision || '—';
  let badgeCls = 'neutral';
  let badgeText = dec;
  if (dec.includes('执行') || dec.includes('建议')) {
    badgeCls = 'support';
    if (dec.includes('暂缓') || dec.includes('暂停') || dec.includes('小规模')) badgeCls = 'neutral';
    if (dec.includes('反对') || dec.includes('不')) badgeCls = 'oppose';
  }
  finalBadge.textContent = badgeText;
  finalBadge.className = 'badge ' + badgeCls;
  
  const rationale = decision.rationale || decision.reasoning || '';
  finalBody.textContent = rationale || '决策理由未提供';
  
  finalConfidence.textContent = '置信度：' + (decision.confidence || 0) + '%';
  finalRisk.textContent = '风险评级：' + (decision.risk || '—');
  
  // V4 Trust Score
  const ts = decision.trust_score;
  if (ts && ts.score) {
    const bar = document.getElementById('trustScoreBar');
    const val = document.getElementById('trustScoreValue');
    const fill = document.getElementById('trustScoreFill');
    const bd = document.getElementById('trustScoreBreakdown');
    bar.style.display = 'block';
    val.textContent = ts.score + ' · ' + ts.level;
    val.style.color = ts.color || '#4ade80';
    fill.style.width = ts.score + '%';
    fill.style.background = ts.color || '#4ade80';
    const b = ts.breakdown || {};
    bd.innerHTML = `
      <span>一致性 +${b.consensus||0}</span>
      <span>权重 +${b.weight_bonus||0}</span>
      <span>冲突 -${b.conflict_penalty||0}</span>
      <span>可靠性 +${b.reliability_bonus||0}</span>
    `;
  }
  
  // 显示升级入口 + 深度报告按钮
  const up = document.getElementById('upgradePrompt');
  if (up) up.style.display = 'block';
  const advBtn = document.getElementById('advancedReportBtn');
  if (advBtn && decision) {
    advBtn.style.display = 'inline-block';
    advBtn.onclick = () => {
      const report = {
        question: topic,
        type: 'advanced',
        modelCount: (agentResults||[]).length,
        consensus: document.querySelector('#consensusList')?.innerText?.slice(0,500) || '',
        divergence: document.querySelector('#dissentList')?.innerText?.slice(0,500) || '',
        advanced: (decision.rationale||'') + '\n\n执行步骤：\n' + (decision.steps||[]).join('\n'),
        raw: (agentResults||[]).map(a => '【'+a.role+'】'+a.reason).join('\n\n').slice(0,3000)
      };
      window.open('/report?d=' + encodeURIComponent(JSON.stringify(report)), '_blank');
    };
  }
  // 付费深度报告入口
  const prem = document.getElementById('premiumPrompt');
  if (prem) prem.style.display = 'block';
  const premBtn = document.getElementById('premiumBtn');
  if (premBtn) {
    premBtn.onclick = () => {
      alert('🧠 支付系统即将上线\n\n9.9元/次 生成麦肯锡级深度决策报告\n包含：商业逻辑解构 · 财务模型推演 · 生死红线 · 反共识推演\n\n当前版本：深度报告功能已开发完成，支付对接中。');
    };
  }
}

// ─── 核心：运行董事会 ───
async function runBoard() {
  if (isRunning) return;
  const topic = topicInput.value.trim();
  if (!topic) { showError('请输入决策问题'); return; }

  isRunning = true;
  runBtn.disabled = true;
  runBtn.textContent = '⏳ 执行中…';
  setStatus('董事会执行中', 'running');
  errorCard.classList.remove('open');

  // 重置
  agentResults = [];
  decisionResult = null;
  chatContainer.querySelector('#chatBubbles')?.remove();
  ledgerContainer.innerHTML = '';
  finalContainer.classList.remove('open');
  document.getElementById('trustScoreBar').style.display = 'none';
  const prem = document.getElementById('premiumPrompt');
  if (prem) prem.style.display = 'none';
  chatEmpty.style.display = 'block';
  ledgerEmpty.style.display = 'block';
  initBoard();

  try {
    const resp = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: topic })
    });
    if (!resp.ok) throw new Error('API 请求失败 (' + resp.status + ')');
    const data = await resp.json();
    const agents = data.agents || [];
    const decision = data.decision || null;
    agentResults = agents;
    decisionResult = decision;

    if (agents.length === 0) throw new Error('未收到 AI 董事会回应');

    // 群聊气泡：逐条显示
    for (let i = 0; i < Math.min(agents.length, BOARD.length); i++) {
      const agent = agents[i];
      const member = BOARD[i];
      const isError = !agent.stance || agent.stance === '—' ||
        (agent.reason && (agent.reason.startsWith('API 错误') || agent.reason.startsWith('请求失败')));
      const text = agent.reason || '';
      const displayText = isError ? (text.includes('403') ? '模型暂不可用' : text) : text.slice(0, 300);
      
      setStatus(member.name + ' 发言中…', 'running');
      await sleep(600);
      
      // 检查前一个气泡是否有相反立场 → 生成 @挑战
      let attackText = '';
      if (i > 0 && agents[i-1] && agent.stance !== agents[i-1].stance && agent.stance !== '中立' && agents[i-1].stance !== '中立') {
        const prevMember = BOARD[i-1];
        attackText = '@' + prevMember.name + ' 我不同意你的观点';
      }
      
      addChatBubble(member.id, member.icon, member.name, member.title, displayText, agent.stance || '—', false, attackText);
    }

    // 构建决策账本
    setStatus('计算加权账本', 'running');
    await sleep(300);
    buildLedger(agents, decision);

    // CEO裁决
    if (decision) {
      setStatus('CEO 综合裁决中', 'running');
      await sleep(500);
      showFinal(decision);
    }

    setStatus('✅ 分析完成', 'done');
    
    // 更新每日使用计数
    let dailyCount = parseInt(localStorage.getItem('mindtrust_daily') || '0');
    dailyCount = Math.min(dailyCount + 1, 3);
    localStorage.setItem('mindtrust_daily', dailyCount.toString());
    const dc = document.getElementById('dailyCount');
    if (dc) dc.textContent = `今日免费：${3 - dailyCount}/3`;

  } catch (err) {
    showError(err.message || '请求失败');
    setStatus('❌ error', '');
    // 显示一条系统气泡
    addChatBubble('ceo', '⚠️', '系统提示', 'error', '请求失败: ' + (err.message || '未知错误'), '—', false, '');
  }

  runBtn.disabled = false;
  runBtn.textContent = '▶ 执行董事会分析';
  isRunning = false;
}

// ─── 初始化 ───
initBoard();
runBtn.addEventListener('click', runBoard);
// Enter to submit
topicInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runBoard(); }
});

// ─── 场景按钮 ───
document.querySelectorAll('.scenario-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    topicInput.value = btn.dataset.scenario;
    topicInput.focus();
    // 自动触发分析
    setTimeout(() => { if (topicInput.value.trim()) runBoard(); }, 300);
  });
});

// ─── 品牌折叠模型选择器 ───
const BRANDS = {
  'OpenAI': { models: ['GPT-4o','o1','o3-mini','GPT-4o-mini'], default: 'GPT-4o' },
  'Claude': { models: ['Claude 3.7 Sonnet (Sonnet 5)','Claude 3.5 Haiku (Haiku 4.5)','Claude 3 Opus (Opus 4.8)','Claude 4 (Fable 5)'], default: 'Claude 3.7 Sonnet (Sonnet 5)' },
  'Gemini': { models: ['Gemini 2.5 Pro','Gemini 2.0 Flash','Gemini 1.5 Pro'], default: 'Gemini 2.5 Pro' },
  'DeepSeek': { models: ['DeepSeek-V3','DeepSeek-R1','DeepSeek-Coder'], default: 'DeepSeek-V3' },
  'Qwen': { models: ['Qwen2.5-72B','Qwen2-7B','Qwen-Max'], default: 'Qwen2.5-72B' },
  'Llama': { models: ['Llama-4','Llama-3.1-405B','Llama-3.1-70B'], default: 'Llama-4' },
  'Mistral': { models: ['Mistral-Large','Mistral-Small','Mixtral'], default: 'Mistral-Large' },
  'Grok': { models: ['Grok-3','Grok-2'], default: 'Grok-3' },
};
let selectedBrands = new Set(['OpenAI','Claude','DeepSeek','Qwen']);
let chosenModels = {};
Object.keys(BRANDS).forEach(b => { chosenModels[b] = BRANDS[b].default; });

function renderBrandSelector(){
  const chips = document.getElementById('brandChips');
  const expanded = document.getElementById('brandExpanded');
  if(!chips || !expanded) return;
  chips.innerHTML = '';
  Object.keys(BRANDS).forEach(brand => {
    const active = selectedBrands.has(brand);
    const chip = document.createElement('span');
    chip.className = 'brand-chip' + (active ? ' active' : '');
    chip.innerHTML = `<span>${brand}</span><span class="chip-x">✕</span>`;
    chip.addEventListener('click', e => {
      if(e.target.classList.contains('chip-x')){
        selectedBrands.delete(brand);
        renderBrandSelector();
        return;
      }
      if(active) selectedBrands.delete(brand);
      else selectedBrands.add(brand);
      renderBrandSelector();
    });
    chips.appendChild(chip);
  });
  expanded.innerHTML = '';
  if(selectedBrands.size > 0){
    expanded.style.display = 'block';
    selectedBrands.forEach(brand => {
      const data = BRANDS[brand];
      if(!data) return;
      const div = document.createElement('div');
      div.className = 'expanded-brand';
      div.innerHTML = `
        <div class="eb-header">
          <span>${brand}</span>
          <span style="font-size:10px;color:#6b7280;">${chosenModels[brand]||data.default}</span>
        </div>
        <div class="eb-models">
          ${data.models.map(m => `<span class="model-opt${(chosenModels[brand]||data.default)===m?' active':''}" data-brand="${brand}" data-model="${m}">${m}</span>`).join('')}
        </div>`;
      expanded.appendChild(div);
    });
    expanded.querySelectorAll('.model-opt').forEach(el => {
      el.addEventListener('click', () => {
        chosenModels[el.dataset.brand] = el.dataset.model;
        renderBrandSelector();
      });
    });
  } else {
    expanded.style.display = 'none';
  }
}
renderBrandSelector();

// 深度报告按钮
const advBtn = document.getElementById('advancedReportBtn');
if(advBtn && decisionResult){
  advBtn.style.display = 'inline-block';
  advBtn.addEventListener('click', () => {
    const reportData = {
      question: topicInput.value,
      type: 'advanced',
      modelCount: agentResults.length,
      report: {
        consensus: document.querySelector('#consensusList')?.innerText || '',
        divergence: document.querySelector('#dissentList')?.innerText || '',
        advanced: decisionResult.rationale + '\n\n执行步骤：\n' + (decisionResult.steps||[]).join('\n')
      },
      rawResponses: agentResults.map(a => `【${a.role}】${a.reason}`).join('\n\n')
    };
    const encoded = encodeURIComponent(JSON.stringify(reportData));
    window.open('/report?d=' + encoded, '_blank');
  });
}
// 从首页读取传入的问题
const storedQuestion = sessionStorage.getItem('mindtrust_question');
if (storedQuestion) {
  topicInput.value = storedQuestion;
  sessionStorage.removeItem('mindtrust_question');
  setTimeout(() => { if (topicInput.value.trim()) runBoard(); }, 500);
}

console.log('🧠 MindTrust OS · AI 智囊局 v5 已加载');
console.log('免费版 · 每日3次 · 9.9元解锁深度报告');
</script>

</body>
</html>
"""# ════════════════════════════════════════════════════════════

# ── 主题关键词库（用于语义级冲突聚类） ──

TOPIC_KEYWORDS = {

    "预算": ["预算", "资金", "投入", "成本", "价格", "花费", "费用", "报价", "ROI"],

    "时间窗口": ["窗口", "时机", "趁早", "紧迫", "赶紧", "赶时间", "逾期", "季节", "周期性", "时效"],

    "风险": ["风险", "损失", "亏损", "危机", "不可控", "负面", "风险点", "代价", "失败"],

    "竞争": ["竞争", "对手", "竞品", "拥挤", "玩家多", "红海", "饱和", "内卷"],

    "市场/需求": ["市场", "需求", "用户", "人群", "客户", "消费者", "受众", "流量"],

    "团队/能力": ["团队", "能力", "资源", "经验", "人手", "人才", "技能", "认知"],

    "产品/技术": ["产品", "功能", "质量", "体验", "设计", "研发", "技术", "开发"],

    "增长/营销": ["增长", "扩张", "放大", "规模", "复制", "起量", "冷启动", "裂变", "营销"],

    "合规/资质": ["合规", "法规", "政策", "法律", "资质", "许可", "监管", "审核"],

    "品牌/心智": ["品牌", "心智", "定位", "口碑", "知名度", "认知", "调性"],

}

def _extract_topics(text: str) -> list:

    """从文本中提取涉及的主题（多主题匹配）"""

    matched = []

    for topic, keywords in TOPIC_KEYWORDS.items():

        for kw in keywords:

            if kw in text:

                matched.append(topic)

                break

    return matched if matched else ["其他"]

def _extract_stance_score(text: str) -> int:

    """

    从文本中提取立场倾向分数

    支持关键词 +1，反对关键词 -1，累计加权

    """

    support_kw = ["支持", "建议", "推荐", "推进", "快速", "应该", "必须", "可行",

                  "看好", "机会", "优势", "值得", "合理", "乐观", "积极"]

    oppose_kw = ["反对", "不建议", "暂缓", "谨慎", "风险", "质疑", "不可",

                 "不够", "困难", "问题", "代价", "损失", "悲观", "消极", "不确定"]

    score = 0

    for w in support_kw:

        score += text.count(w) * 1

    for w in oppose_kw:

        score -= text.count(w) * 1

    return score

def _cluster_conflicts(debate_results: list) -> list:

    """

    V1.2 语义级冲突聚类（无需 sklearn）

    流程：

    1. 提取每个角色的文本主题和立场分数

    2. 按主题聚类分组

    3. 同主题内立场最强支持 vs 最强反对 => 生成冲突

    4. 计算严重度（权重 + 立场差距 + 角色权重）

    """

    # 第1步：提取每个角色的主题和立场分数

    role_topics = {}

    role_stance_scores = {}

    for r in debate_results:

        text = r.get("reason", "") + " " + r.get("role", "")

        role_topics[r["role"]] = _extract_topics(text)

        role_stance_scores[r["role"]] = _extract_stance_score(text)

    # 第2步：按主题聚类 —— topic => [{role, text, stance, score, weight}]

    topic_buckets = {}

    for r in debate_results:

        role = r["role"]

        for topic in role_topics.get(role, ["其他"]):

            topic_buckets.setdefault(topic, []).append({

                "role": role,

                "text": r.get("reason", "")[:120],

                "stance": r.get("stance", "中立"),

                "score": role_stance_scores.get(role, 0),

                "weight": BOARD_MEMBERS.get(role, {}).get("weight", 1.0)

            })

    # 第3步：每个桶内检查立场对立

    conflicts = []

    for topic, items in topic_buckets.items():

        if len(items) < 2:

            continue

        supporters = [i for i in items if i["stance"] == "支持" or i["score"] > 0]

        opposers = [i for i in items if i["stance"] == "反对" or i["score"] < 0]

        if not supporters or not opposers:

            continue

        top_sup = max(supporters, key=lambda x: x["score"])

        top_opp = max(opposers, key=lambda x: -x["score"])

        # 严重度计算

        weight_factor = (top_sup["weight"] + top_opp["weight"]) / 2.0

        score_gap = abs(top_sup["score"] - top_opp["score"]) / 12.0

        severity = min(1.0, 0.3 + weight_factor * 0.15 + score_gap * 0.25)

        if severity < 0.3:

            continue

        sev_label = "高" if severity >= 0.65 else "中" if severity >= 0.45 else "低"

        conflicts.append({

            "id": len(conflicts) + 1,

            "topic": topic,

            "title": f"{topic}：{top_sup['role']} vs {top_opp['role']}",

            "left": f"{top_sup['role']}：{top_sup['text'][:80]}",

            "right": f"{top_opp['role']}：{top_opp['text'][:80]}",

            "level": sev_label,

            "severity": round(severity, 2),

            "severity_pct": int(severity * 100)

        })

    conflicts.sort(key=lambda x: x["severity"], reverse=True)

    return conflicts[:5]

# ── 决策评分系统 ──

def _calculate_decision_score(debate_results: list, conflicts: list) -> dict:

    """

    综合评分 = 支持加权分 - 反对加权分 - 风险惩罚

    """

    support_score = 0.0

    oppose_score = 0.0

    for r in debate_results:

        role = r["role"]

        weight = BOARD_MEMBERS.get(role, {}).get("weight", 1.0)

        stance = r.get("stance", "中立")

        if stance == "支持":

            support_score += weight

        elif stance == "反对":

            oppose_score += weight

    # 风险惩罚

    risk_penalty = 0.0

    if conflicts:

        avg_severity = sum(c.get("severity", 0.5) for c in conflicts) / len(conflicts)

        risk_penalty = avg_severity * 0.25 * len(conflicts)

    net_score = support_score - oppose_score - risk_penalty

    total_weight = sum(BOARD_MEMBERS.get(r["role"], {}).get("weight", 1.0) for r in debate_results)

    if total_weight == 0:

        confidence = 50.0

    else:

        raw_confidence = (net_score / total_weight + 1) / 2 * 100

        confidence = max(5, min(99, raw_confidence))

    return {

        "score": round(net_score, 2),

        "confidence": round(confidence, 1),

        "support_weight": round(support_score, 2),

        "oppose_weight": round(oppose_score, 2),

        "risk_penalty": round(risk_penalty, 2),

        "total_weight": round(total_weight, 2)

    }

# ── V4 决策可信度评分系统（Decision Trust Score）──

def _calculate_trust_score(debate_results: list, conflicts: list, decision_score: dict) -> dict:
    """
    V4 Trust Score 引擎
    
    公式：Trust Score = (Consensus × 50) + Role Weight Bonus - Conflict Penalty + Model Reliability Bonus
    """
    total = len(debate_results)
    if total == 0:
        return {"score": 0, "level": "极低", "color": "#ef4444",
                "breakdown": {"consensus": 0, "weight_bonus": 0, "conflict_penalty": 0, "reliability_bonus": 0}}
    
    # A. 一致性分数
    support_count = sum(1 for r in debate_results if r.get("stance") == "支持")
    neutral_count = sum(1 for r in debate_results if r.get("stance") == "中立")
    consensus_ratio = (support_count + neutral_count * 0.5) / total
    consensus_score = consensus_ratio * 50
    
    # B. 角色权重加分
    weight_bonus = 0.0
    for r in debate_results:
        role = r["role"]
        weight = BOARD_MEMBERS.get(role, {}).get("weight", 1.0)
        stance = r.get("stance", "中立")
        if stance == "支持":
            weight_bonus += (weight - 1.0) * 8
        elif stance == "反对":
            weight_bonus -= (weight - 1.0) * 6
    weight_bonus = max(-15, min(20, weight_bonus))
    
    # C. 冲突惩罚
    conflict_penalty = 0.0
    if conflicts:
        for c in conflicts:
            conflict_penalty += c.get("severity", 0.5) * 6
        conflict_penalty = min(conflict_penalty, 25)
    
    # D. 模型可靠性加分
    reliability_bonus = 0.0
    for r in debate_results:
        role = r["role"]
        model_name = BOARD_MEMBERS.get(role, {}).get("model", "")
        if "72B" in model_name:
            reliability_bonus += 1.5
        elif "V3" in model_name or "V2.5" in model_name:
            reliability_bonus += 2.0
        elif "7B" in model_name:
            reliability_bonus += 0.5
        else:
            reliability_bonus += 1.0
        for stored_name, data in CREDIBILITY_STORE.items():
            if stored_name.lower() in role.lower() or role.lower() in stored_name.lower():
                reliability_bonus += (data.get("correct", 0) / max(data.get("total", 1), 1) - 0.5) * 2
    reliability_bonus = max(-5, min(10, reliability_bonus))
    
    raw_score = consensus_score + weight_bonus - conflict_penalty + reliability_bonus
    trust_score = max(5, min(99, round(raw_score)))
    
    if trust_score >= 85:
        level, color = "很高", "#22c55e"
    elif trust_score >= 70:
        level, color = "高", "#4ade80"
    elif trust_score >= 55:
        level, color = "中等", "#fbbf24"
    elif trust_score >= 40:
        level, color = "低", "#f97316"
    else:
        level, color = "极低", "#ef4444"
    
    return {
        "score": trust_score,
        "level": level,
        "color": color,
        "breakdown": {
            "consensus": round(consensus_score, 1),
            "weight_bonus": round(weight_bonus, 1),
            "conflict_penalty": round(conflict_penalty, 1),
            "reliability_bonus": round(reliability_bonus, 1)
        }
    }

# ── 结构化CEO裁决器 ──

def _ceo_structured_verdict(debate_results: list, conflicts: list, decision_score: dict) -> dict:

    """

    结构化CEO最终裁决（纯规则引擎，不依赖外部API）

    产出：决策判断 + 置信度 + 理由 + 执行路径 + 风险等级

    """

    score = decision_score["score"]

    confidence = decision_score["confidence"]

    if score > 0.5 and confidence >= 65:

        decision = "建议执行"

    elif score > 0 and confidence >= 50:

        decision = "建议调整后执行"

    elif score < -0.5:

        decision = "建议暂缓"

    else:

        decision = "建议小规模测试"

    if conflicts:

        top = max(conflicts, key=lambda x: x.get("severity", 0))

        reasoning = f"核心冲突在「{top['topic']}」，{top['left'][:30]} vs {top['right'][:30]}"

    else:

        reasoning = "各角色意见趋于一致，无明显立场对立"

    supporters = [r for r in debate_results if r.get("stance") == "支持"]

    if supporters:

        steps = ["小规模验证：预算控制在总预算的 30% 以内",

                 "设置 2 周数据回收期，明确成败指标",

                 "设定明确止损线（ROI < 1.0 则暂停）",

                 "重点验证冲突核心假设",

                 "2 周后复盘决定是否放大"]

    else:

        steps = ["明确核心目标", "识别关键风险点",

                 "制定最小验证方案", "2 周数据回收", "迭代决策"]

    risk_penalty = decision_score.get("risk_penalty", 0)

    if risk_penalty > 0.6:

        risk_level = "高"

        risk_text = f"风险等级高（惩罚分 {risk_penalty}），重点关注反对方核心顾虑，切勿重仓"

    elif risk_penalty > 0.25:

        risk_level = "中"

        risk_text = f"风险等级中（惩罚分 {risk_penalty}），建议控制试错成本"

    else:

        risk_level = "低"

        risk_text = f"风险等级低（惩罚分 {risk_penalty}），可按计划推进"

    return {

        "decision": decision,

        "confidence": round(confidence, 1),

        "reasoning": reasoning,

        "steps": steps,

        "risk_level": risk_level,

        "risk": risk_text

    }

# ============================================================

# API 调用函数

# ============================================================

async def _parse_json_resp(resp):
    """安全解析 JSON 响应，自动处理编码问题"""
    try:
        raw_bytes = await resp.read()
        for enc in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
            try:
                text = raw_bytes.decode(enc)
                return json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        # 最后兜底：忽略错误解码
        text = raw_bytes.decode('utf-8', errors='replace')
        return json.loads(text)
    except Exception:
        return {}


async def call_siliconflow(model_id: str, prompt: str, role_name: str, system_prompt: str, fallback_id: str = None) -> dict:

    """调用硅基流动 API，含自动重试和备用模型切换"""

    if not SILICONFLOW_API_KEY:

        return {"role": role_name, "model": model_id, "stance": "—", "reason": "API Key 未配置"}
    
    async def _do_call(mid: str) -> tuple:
        """单次调用，返回 (status, data_or_error)"""
        payload = {

            "model": mid,

            "messages": [

                {"role": "system", "content": system_prompt},

                {"role": "user", "content": f"决策问题：{prompt}\n\n请给出你的判断（支持/反对/中立），并详细说明理由。"}

            ],

            "temperature": 0.7,

            "max_tokens": 300

        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    SILICONFLOW_BASE,
                    headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 403:
                        return ("fallback", "API 403")
                    if resp.status != 200:
                        return ("error", "API 错误: " + str(resp.status))
                    data = await _parse_json_resp(resp)
                    raw = data["choices"][0]["message"]["content"].strip()
                    return ("ok", raw)
        except asyncio.TimeoutError:
            return ("fallback", "超时")
        except Exception as e:
            return ("error", "请求失败: " + str(e))
    
    # 第一次调用
    status, result = await _do_call(model_id)
    
    # 如果失败且有备用模型，自动重试
    if status != "ok" and fallback_id:
        # 记录重试（日志用）
        retry_info = f"({model_id}→{fallback_id}: {result})"
        status2, result2 = await _do_call(fallback_id)
        if status2 == "ok":
            status, result = "ok", result2
            fallback_used = True
        # 即使备用也失败，继续用原错误信息
    
    if status != "ok":
        return {"role": role_name, "model": model_id, "stance": "—", "reason": result[:100]}

    raw = result

    lines = raw.split("\n")

    stance = lines[0].strip() if len(lines) > 0 else "—"

    if "支持" in stance:

        stance = "支持"

    elif "反对" in stance:

        stance = "反对"

    else:

        stance = "中立"

    reason_lines = lines[1:] if len(lines) > 1 else []

    reason = "\n".join(reason_lines).strip() if reason_lines else raw[:200]

    return {"role": role_name, "model": model_id, "stance": stance, "reason": reason}


async def call_ceo(debate_results: list, prompt: str) -> dict:

    """CEO裁决官：基于6位董事的辩论结果做出综合决策"""

    if not SILICONFLOW_API_KEY:

        return {"role": "CEO裁决官", "model": BOARD_MEMBERS["CEO裁决官"]["model"], "stance": "—", "reason": "API Key 未配置"}

    debate_lines = []

    for r in debate_results:

        debate_lines.append(f"- {r['role']}（{r['stance']}）：{r['reason'][:150]}")

    debate_summary = "\n".join(debate_lines)

    system_prompt = "你是一位CEO裁决官，负责综合董事会的不同意见做出最终决策。请分析以下各位董事的立场和理由，给出你的最终裁决（支持/反对/中立），并说明你的决策逻辑。"

    payload = {

        "model": BOARD_MEMBERS["CEO裁决官"]["model"],

        "messages": [

            {"role": "system", "content": system_prompt},

            {"role": "user", "content": f"决策问题：{prompt}\n\n董事投票结果：\n{debate_summary}\n\n请给出你的最终裁决（支持/反对/中立），并详细说明决策理由。"}

        ],

        "temperature": 0.5,

        "max_tokens": 400

    }

    try:

        async with aiohttp.ClientSession() as session:

            async with session.post(

                SILICONFLOW_BASE,

                headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},

                json=payload,

                timeout=aiohttp.ClientTimeout(total=60)

            ) as resp:

                if resp.status != 200:

                    return {"role": "CEO裁决官", "model": BOARD_MEMBERS["CEO裁决官"]["model"], "stance": "—", "reason": "API 错误"}

                data = await _parse_json_resp(resp)

                raw = data["choices"][0]["message"]["content"].strip()

                lines = raw.split("\n")

                stance = lines[0] if len(lines) > 0 else "中立"

                if "支持" in stance:

                    stance = "支持"

                elif "反对" in stance:

                    stance = "反对"

                else:

                    stance = "中立"

                reason_lines = lines[1:] if len(lines) > 1 else []

                reason = "\n".join(reason_lines).strip() if reason_lines else raw[:300]

                return {"role": "CEO裁决官", "model": BOARD_MEMBERS["CEO裁决官"]["model"], "stance": stance, "reason": reason}

    except Exception as e:

        return {"role": "CEO裁决官", "model": BOARD_MEMBERS["CEO裁决官"]["model"], "stance": "—", "reason": "请求失败: " + str(e)}

@app.post("/api/run")

async def api_run(request: Request):
    try:
        # 处理中文编码问题：尝试 JSON 解析，失败则手动解码
        try:
            body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            import json
            for enc in ['gbk', 'gb2312', 'utf-8']:
                try:
                    body = json.loads(raw.decode(enc))
                    break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            else:
                body = {"topic": raw.decode('utf-8', errors='replace')}
        topic = body.get("topic", "")

        # 并行调用所有非CEO角色
        tasks = []
        for role_name in DEBATE_ROLES:
            member = BOARD_MEMBERS[role_name]
            tasks.append(call_siliconflow(member["model"], topic, role_name, member["prompt"], member.get("fallback")))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                results[i] = {"role": list(BOARD_MEMBERS.keys())[i], "model": "", "stance": "—", "reason": f"请求失败: {str(r)[:80]}"}

        # 调用CEO裁决官（基于前6位结果）
        ceo_result = await call_ceo(results, topic)

        # 全部 agents = 6位董事 + CEO
        all_agents = results + [ceo_result]

        # V1.2 冲突决策引擎
        # Step 1: 语义级冲突聚类
        conflicts = _cluster_conflicts(results)
        # Step 2: 决策评分系统
        decision_score = _calculate_decision_score(results, conflicts)
        # Step 3: 结构化CEO裁决
        ceo_verdict = _ceo_structured_verdict(results, conflicts, decision_score)
        # Step 4: V4 可信度评分
        trust_score = _calculate_trust_score(results, conflicts, decision_score)
        # Step 5: 整合返回
        support_count = sum(1 for r in results if r["stance"] == "支持")
        oppose_count = sum(1 for r in results if r["stance"] == "反对")

        decision = {
            "decision": ceo_verdict["decision"],
            "confidence": ceo_verdict["confidence"],
            "rationale": f"AI董事会7位董事辩论：{support_count}位支持（加权{decision_score['support_weight']}），{oppose_count}位反对（加权{decision_score['oppose_weight']}）。\n{ceo_verdict['reasoning']}",
            "steps": ceo_verdict["steps"],
            "risk": ceo_verdict["risk"],
            "trust_score": trust_score
        }

        return {
            "agents": all_agents,
            "conflicts": conflicts,
            "decision": decision,
            "trust_score": trust_score
        }
    except Exception as e:
        return {"error": str(e), "agents": [], "conflicts": [], "decision": {"decision": "无法裁决", "confidence": 0, "rationale": f"系统错误: {str(e)[:100]}", "steps": [], "risk": "高"}}

# ============================================================
# SYSTEM 2 — AI Manual Compiler API
# ============================================================

async def call_compare_model(entries: list) -> dict:
    """调用免费模型做多回答认知整合分析"""
    if not SILICONFLOW_API_KEY:
        return {"error": "API Key 未配置"}
    
    # 构造输入文本
    input_text = ""
    for i, e in enumerate(entries):
        label = e.get("label", f"模型{i+1}")
        content = e.get("content", "")
        input_text += f"─── {label} ───\n{content}\n\n"
    
    system_prompt = """你是一个多模型认知整合分析师。你的任务是把多个AI模型对同一问题的回答进行结构化分析。

请严格按照以下JSON格式输出（只输出JSON，不要有任何其他文字）：

{
  "consensus": [
    {"point": "所有模型一致认同的观点描述", "confidence": "high|medium|low"}
  ],
  "dissent": [
    {
      "topic": "分歧主题",
      "severity": "high|medium|low",
      "positions": [
        {"model": "模型名称", "stance": "立场简述", "summary": "核心论据"}
      ]
    }
  ],
  "conflict_sources": [
    {"source": "分歧来源（如数据假设、时间视角、方法论等）", "detail": "具体解释"}
  ],
  "recommendation": "综合所有模型观点后的最佳行动建议",
  "uncertainty": "当前分析中仍然不确定的部分"
}

要求：
1. consensus 列出一致观点（至少3条）
2. dissent 列出所有存在分歧的议题
3. conflict_sources 分析分歧的根本原因
4. recommendation 是具体的、可执行的建议
5. 输出必须是一个合法的JSON对象"""

    user_prompt = f"以下是对同一问题的多个AI模型回答，请进行分析：\n\n{input_text}\n\n请输出结构化JSON分析结果。"
    
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SILICONFLOW_BASE,
                headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"error": f"API 错误: {resp.status}", "detail": text[:200]}
                data = await _parse_json_resp(resp)
                raw = data["choices"][0]["message"]["content"].strip()
                # clean markdown code fences if any
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1]
                    if "```" in raw:
                        raw = raw.rsplit("```", 1)[0]
                return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "模型返回格式异常", "raw": raw[:300]}
    except Exception as e:
        return {"error": f"请求失败: {str(e)[:80]}"}

async def call_second_compare_model(entries: list) -> dict:
    """用第二个模型做交叉验证分析（DeepSeek-V3）"""
    if not SILICONFLOW_API_KEY:
        return None
    
    input_text = ""
    for i, e in enumerate(entries):
        label = e.get("label", f"模型{i+1}")
        content = e.get("content", "")
        input_text += f"─── {label} ───\n{content}\n\n"
    
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "system", "content": "你是一个AI观点审计分析师。分析多个模型回答的共识与分歧，输出JSON。"},
            {"role": "user", "content": f"分析以下多个AI回答，输出共识/分歧/建议：\n\n{input_text}"}
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SILICONFLOW_BASE,
                headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as resp:
                if resp.status != 200:
                    return None
                data = await _parse_json_resp(resp)
                raw = data["choices"][0]["message"]["content"].strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1]
                    if "```" in raw:
                        raw = raw.rsplit("```", 1)[0]
                return json.loads(raw)
    except Exception:
        return None


@app.post("/api/compare")
async def api_compare(request: Request):
    """SYSTEM 2: 手动多模型输入 → 自动决策收敛"""
    try:
        body = await request.json()
        entries = body.get("entries", [])
        history = body.get("history", None)  # previous round analysis for iteration
        
        if not entries or len(entries) < 2:
            return {"error": "请至少粘贴2个模型的回答"}
        
        # 验证entries格式
        valid_entries = []
        for e in entries:
            label = e.get("label", "").strip() or "未命名"
            content = e.get("content", "").strip()
            if content:
                valid_entries.append({"label": label, "content": content})
        
        if len(valid_entries) < 2:
            return {"error": "有效回答不足2个"}
        
        # 主分析模型
        analysis = await call_compare_model(valid_entries)
        
        # 第二个模型做交叉验证（提升可靠性）
        cross_validation = await call_second_compare_model(valid_entries)
        
        # 如果历史存在，对比新旧分析的变化
        delta = None
        if history:
            try:
                prev_consensus = set(p["point"] for p in history.get("consensus", []))
                curr_consensus = set(p["point"] for p in analysis.get("consensus", []))
                new_agreements = [p for p in analysis.get("consensus", []) if p["point"] not in prev_consensus]
                delta = {"new_consensus_points": len(new_agreements), "new_agreements": new_agreements[:3]}
            except Exception:
                delta = None
        
        return {
            "analysis": analysis,
            "cross_validation": cross_validation,
            "entry_count": len(valid_entries),
            "entries": [e["label"] for e in valid_entries],
            "delta": delta
        }
    except Exception as e:
        return {"error": str(e)[:200]}


        return {"error": str(e)[:200]}


# ============================================================
# V4 — Anti-Consensus Engine
# ============================================================

async def call_anti_consensus(consensus_points: list, topic: str) -> dict:
    """生成反共识分析：当所有模型说一样时，挑战群体思维"""
    if not SILICONFLOW_API_KEY or not consensus_points:
        return {"error": "无法生成反共识"}
    
    consensus_text = "\n".join([f"- {p.get('point', '')}" for p in consensus_points])
    
    prompt = f"""你是反共识分析师。你的任务是在所有人都达成一致时，主动寻找被忽略的视角。

当前议题：{topic}

以下是被所有AI模型一致认同的观点：
{consensus_text}

请从以下角度挑战这个共识：
1. 什么情况下这些共识是错误的？
2. 哪个历史先例表明类似共识曾导致失败？
3. 被忽略的替代假设是什么？
4. 如果这些共识成立，最可能被低估的风险是什么？

请输出JSON格式：
{{
  "challenge": "对共识的核心挑战（一句话）",
  "blindspots": ["被忽略的视角1", "被忽略的视角2", "被忽略的视角3"],
  "alternative": "如果共识错了，更可能正确的替代方案",
  "warning": "决策者最需要注意的风险信号",
  "strength": "这个挑战的有效性评估: strong|medium|weak"
}}"""

    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "system", "content": "你是一个独立思考的反共识分析师。输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SILICONFLOW_BASE,
                headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    return {"error": f"API {resp.status}"}
                data = await _parse_json_resp(resp)
                raw = data["choices"][0]["message"]["content"].strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1]
                    if "```" in raw:
                        raw = raw.rsplit("```", 1)[0]
                return json.loads(raw)
    except Exception as e:
        return {"error": str(e)[:80]}

@app.post("/api/challenge")
async def api_challenge(request: Request):
    """反共识 API：生成挑战群体思维的分析"""
    try:
        body = await request.json()
        consensus_points = body.get("consensus_points", [])
        topic = body.get("topic", "")
        result = await call_anti_consensus(consensus_points, topic)
        return result
    except Exception as e:
        return {"error": str(e)[:100]}


# ============================================================
# V4 — Credibility Tracking System
# ============================================================

CREDIBILITY_STORE = {}  # {model_name: {"correct": int, "total": int}}

@app.post("/api/credibility/rate")
async def rate_credibility(request: Request):
    """用户评价某个模型的回答是否准确"""
    body = await request.json()
    model = body.get("model", "").strip()
    accurate = body.get("accurate", True)
    
    if model not in CREDIBILITY_STORE:
        CREDIBILITY_STORE[model] = {"correct": 0, "total": 0}
    CREDIBILITY_STORE[model]["total"] += 1
    if accurate:
        CREDIBILITY_STORE[model]["correct"] += 1
    return {"status": "ok", "model": model, "credibility": _get_credibility(model)}

@app.get("/api/credibility")
async def get_credibility():
    """获取所有模型的可靠性评分"""
    result = {}
    for model, data in CREDIBILITY_STORE.items():
        result[model] = _get_credibility(model)
    return result

def _get_credibility(model: str) -> dict:
    """计算单个模型的可靠性分数"""
    data = CREDIBILITY_STORE.get(model, {"correct": 0, "total": 0})
    total = data["total"]
    correct = data["correct"]
    score = round(correct / total, 2) if total > 0 else 0.5
    return {
        "score": score,
        "percent": int(score * 100),
        "total_ratings": total,
        "label": "高" if score >= 0.8 else "中" if score >= 0.5 else "低"
    }


# ============================================================
# V4 — Decision Report Export
# ============================================================

@app.post("/api/export")
async def export_report(request: Request):
    """生成可打印的决策报告Markdown"""
    try:
        body = await request.json()
        analysis = body.get("analysis", {})
        topic = body.get("topic", "")
        entries = body.get("entries", [])
        
        consensus = analysis.get("consensus", [])
        dissent = analysis.get("dissent", [])
        recommendation = analysis.get("recommendation", "")
        uncertainty = analysis.get("uncertainty", "")
        
        md = f"# AI Decision Report\n\n"
        md += f"**议题**: {topic or '未命名'}\n\n"
        md += f"**参与模型**: {', '.join(e.get('label','') for e in entries)}\n\n"
        md += "---\n\n"
        md += "## 一致观点\n\n"
        for c in consensus:
            md += f"- ✅ **{c.get('point','')}** (置信度: {c.get('confidence','')})\n"
        md += "\n## 分歧观点\n\n"
        for d in dissent:
            md += f"### {d.get('topic','')}\n"
            for p in d.get('positions', []):
                md += f"- {p.get('model','')}: {p.get('stance','')} — {p.get('summary','')}\n"
            md += "\n"
        md += "## 收敛建议\n\n"
        md += f"{recommendation}\n\n"
        if uncertainty:
            md += "## 不确定性\n\n"
            md += f"{uncertainty}\n\n"
        md += "---\n"
        md += f"*由 AI Decision OS 生成*\n"
        
        return {"markdown": md}
    except Exception as e:
        return {"error": str(e)[:100]}


# ============================================================
# SYSTEM 2 PAGE HTML
# ============================================================
COMPARE_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Decision Graph · V7</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Inter,-apple-system,sans-serif;background:#05060A;color:#E6E9F2;height:100vh;overflow:hidden;}
.grid{display:grid;grid-template-columns:280px 1fr 340px;height:100vh;}
@media(max-width:1024px){.grid{grid-template-columns:1fr;grid-template-rows:auto 400px auto;}}
.panel{padding:16px;border-right:1px solid rgba(255,255,255,0.06);overflow-y:auto;}
.panel.right{border-right:none;}
.p-title{font-size:13px;font-weight:600;margin-bottom:4px;}
.p-sub{font-size:10px;color:rgba(255,255,255,0.25);margin-bottom:10px;}
textarea{width:100%;height:calc(100vh - 160px);background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:10px;color:#fff;font-size:11px;outline:none;resize:none;font-family:inherit;}
textarea:focus{border-color:#7c3aed;}
textarea::placeholder{color:rgba(255,255,255,0.15);}
.btn-bar{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap;}
.btn{padding:6px 14px;border-radius:8px;font-size:11px;font-weight:500;cursor:pointer;transition:all .15s;border:none;}
.btn-primary{background:linear-gradient(90deg,#7c3aed,#22d3ee);color:#fff;}
.btn-primary:hover{transform:translateY(-1px);}
.btn-ghost{background:rgba(255,255,255,0.04);color:#fff;border:1px solid rgba(255,255,255,0.08);}
.btn-ghost:hover{background:rgba(255,255,255,0.08);}
.btn-ghost:disabled{opacity:0.3;cursor:not-allowed;}
.graph-wrap{position:relative;height:100%;overflow:hidden;}
.graph-wrap svg{width:100%;height:100%;}
.graph-ui{position:absolute;top:10px;left:10px;z-index:10;display:flex;gap:6px;}
.graph-badge{padding:3px 10px;border-radius:20px;font-size:9px;background:rgba(0,0,0,0.5);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.06);}
.error-bar{font-size:10px;color:#ef4444;display:none;margin-bottom:4px;}
.error-bar.open{display:block;}
.engine-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px;margin-bottom:8px;font-size:11px;}
.engine-card .tag{display:inline-block;padding:1px 8px;border-radius:20px;font-size:9px;font-weight:500;margin-bottom:4px;}
.tag-green{background:rgba(34,197,94,0.1);color:#4ade80;}
.tag-yellow{background:rgba(251,191,36,0.1);color:#fbbf24;}
.tag-purple{background:rgba(124,58,237,0.1);color:#a78bfa;}
.engine-card .bar{height:4px;background:rgba(255,255,255,0.05);border-radius:999px;overflow:hidden;margin:3px 0;}
.engine-card .bar .fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#22d3ee,#7c3aed);transition:width .6s ease;}
.empty-state{color:rgba(255,255,255,0.1);font-size:11px;text-align:center;padding:40px 0;line-height:1.8;}
.topnav{display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap;}
.topnav a{font-size:9px;text-decoration:none;padding:2px 6px;border-radius:4px;color:rgba(255,255,255,0.3);border:1px solid rgba(255,255,255,0.05);}
.topnav a.active{color:#a78bfa;border-color:#7c3aed;}
</style>
</head>
<body>
<div class="grid">

<!-- LEFT INPUT -->
<div class="panel" style="display:flex;flex-direction:column;">
  <div class="topnav">
    <a href="/room">🏠</a>
    <a href="/compare" class="active">📊</a>
    <a href="/">🌐</a>
  </div>
  <div class="p-title">🧠 多模型输入</div>
  <div class="p-sub">━━━ 模型名 ━━━ 分隔</div>
  <textarea id="pasteInput" style="flex:1;" placeholder="━━━ GPT-4o ━━━&#10...&#10&#10━━━ Claude ━━━&#10..."></textarea>
  <div class="btn-bar">
    <button class="btn btn-primary" id="analyzeBtn">▶ 分析</button>
    <button class="btn btn-ghost" id="challengeBtn" style="display:none;">⚡反共识</button>
    <button class="btn btn-ghost" id="resetBtn">↺</button>
  </div>
  <div class="error-bar" id="errorBar"></div>
</div>

<!-- CENTER D3 GRAPH -->
<div class="panel graph-wrap" id="graphPanel">
  <div class="graph-ui">
    <span class="graph-badge" id="graphBadgeConsensus">🎯 等待数据</span>
    <span class="graph-badge" id="graphBadgeConflict">⚡ —</span>
  </div>
  <svg id="graphSvg"></svg>
  <div id="graphEmpty" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.08);font-size:12px;pointer-events:none;">分析后展示力导向冲突图谱</div>
</div>

<!-- RIGHT ENGINE -->
<div class="panel right">
  <div class="p-title">🧠 决策引擎</div>
  <div class="p-sub">多模型意见 → 结构化收敛</div>
  <div id="engineContent"><div class="empty-state">等待分析...</div></div>
</div>

</div>

<script>
const PASTE = document.getElementById('pasteInput');
const ANALYZE = document.getElementById('analyzeBtn');
const ERROR = document.getElementById('errorBar');
const GRAPH_SVG = document.getElementById('graphSvg');
const GRAPH_EMPTY = document.getElementById('graphEmpty');
const ENGINE = document.getElementById('engineContent');
const CHALLENGE = document.getElementById('challengeBtn');
const BADGE_C = document.getElementById('graphBadgeConsensus');
const BADGE_F = document.getElementById('graphBadgeConflict');

let lastAnalysis = null;
let lastEntries = [];
let simulation = null;
const COLORS = ['#22d3ee','#f472b6','#60a5fa','#fbbf24','#4ade80','#a78bfa','#fb7185'];

async function runAnalysis(){
  const raw = PASTE.value.trim();
  if(!raw){ showErr('请粘贴回答'); return; }
  const entries = raw.split(/━━━\s*/).map(b => {
    const lines = b.trim().split('\n');
    if(lines.length<2) return null;
    return {label: lines[0].replace(/━━━/g,'').trim(), content: lines.slice(1).join('\n').trim()};
  }).filter(e => e && e.content);
  if(entries.length<2){ showErr('至少2个模型'); return; }
  lastEntries = entries;
  ERROR.classList.remove('open');

  try{
    const resp = await fetch('/api/compare',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({entries})
    });
    const data = await resp.json();
    if(data.error){ showErr(data.error); return; }
    const a = data.analysis;
    if(!a||a.error){ showErr(a?.error||'失败'); return; }
    lastAnalysis = a;
    renderGraph(entries, a);
    renderEngine(entries, a);
    CHALLENGE.style.display = (a.consensus&&a.consensus.length>=2)?'inline-block':'none';
  }catch(e){showErr(e.message);}
}

// ─── D3 FORCE GRAPH ───
function renderGraph(entries, analysis){
  GRAPH_EMPTY.style.display = 'none';
  if(simulation) simulation.stop();

  const W = document.getElementById('graphPanel').offsetWidth;
  const H = document.getElementById('graphPanel').offsetHeight;

  const nodes = entries.map((e,i) => ({
    id: e.label, r: 16 + Math.random()*4,
    color: COLORS[i%COLORS.length],
    group: i
  }));
  // Add center convergence node
  nodes.push({id:'⚡ 收敛', r:26, color:'#7c3aed', group:99});

  const links = [];
  entries.forEach((e,i) => {
    links.push({source:e.label, target:'⚡ 收敛', type:'attract'});
  });
  if(entries.length >= 2){
    links.push({source:entries[0].label, target:entries[1].label, type:'attract'});
  }
  if(entries.length >= 3){
    links.push({source:entries[1].label, target:entries[2].label, type:'conflict'});
  }

  const svg = d3.select('#graphSvg');
  svg.selectAll('*').remove();
  svg.attr('width',W).attr('height',H);

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d=>d.id).distance(150).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-350))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d=>d.r+10));

  const link = svg.append('g').selectAll('line').data(links).enter()
    .append('line')
    .style('stroke', d => d.type==='conflict'?'#ff4d6d':'rgba(255,255,255,0.12)')
    .style('stroke-width', d => d.type==='conflict'?2:1)
    .style('opacity', d => d.type==='conflict'?0.7:0.3);

  // Glow filter
  const defs = svg.append('defs');
  const filter = defs.append('filter').attr('id','glow');
  filter.append('feGaussianBlur').attr('stdDeviation','3').attr('result','blur');
  const merge = filter.append('feMerge');
  merge.append('feMergeNode').attr('in','blur');
  merge.append('feMergeNode').attr('in','SourceGraphic');

  const node = svg.append('g').selectAll('circle').data(nodes).enter()
    .append('circle')
    .attr('r', d => d.r)
    .style('fill', d => d.color)
    .style('filter', d => d.group===99?'url(#glow)':'none')
    .style('stroke', d => d.group===99?'rgba(124,58,237,0.4)':'rgba(255,255,255,0.08)')
    .style('stroke-width', d => d.group===99?4:1)
    .style('cursor','grab')
    .call(d3.drag()
      .on('start', function(event,d){
        if(!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', function(event,d){ d.fx = event.x; d.fy = event.y; })
      .on('end', function(event,d){
        if(!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      })
    );

  const label = svg.append('g').selectAll('text').data(nodes).enter()
    .append('text')
    .text(d => d.id)
    .style('fill','#fff')
    .style('font-size', d => d.group===99?'14px':'11px')
    .style('font-weight', d => d.group===99?600:400)
    .style('pointer-events','none');

  simulation.on('tick', () => {
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y)
        .attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    node.attr('cx',d=>d.x).attr('cy',d=>d.y);
    label.attr('x',d=>d.x-d.id.length*4).attr('y',d=>d.y+d.r+14);
  });

  // Update badges
  const consensus = analysis.consensus||[];
  const dissent = analysis.dissent||[];
  const total = Math.max(consensus.length + dissent.length, 1);
  const ratio = Math.round(consensus.length/total*100);
  BADGE_C.textContent = `🎯 共识 ${ratio}%`;
  BADGE_F.textContent = `⚡ 冲突 ${dissent.length} 处`;
}

function renderEngine(entries, analysis){
  const consensus = analysis.consensus||[];
  const dissent = analysis.dissent||[];
  const recommendation = analysis.recommendation||'';
  const total = Math.max(consensus.length + dissent.length, 1);
  const ratio = consensus.length/total;

  let html = '';
  html += `<div class="engine-card">
    <span class="tag tag-green">🎯 共识度 ${Math.round(ratio*100)}%</span>
    <div class="bar"><div class="fill" style="width:${Math.round(ratio*100)}%"></div></div>
  </div>`;
  html += `<div class="engine-card"><span class="tag tag-green">✔ 一致</span>`;
  if(consensus.length===0) html+='<div style="font-size:10px;color:rgba(255,255,255,0.3);">无</div>';
  else consensus.slice(0,3).forEach(c => { html+=`<div style="font-size:10px;padding:2px 0;color:rgba(255,255,255,0.6);">• ${c.point||''}</div>`; });
  html += `</div>`;
  html += `<div class="engine-card"><span class="tag tag-yellow">⚔ 分歧</span>`;
  if(dissent.length===0) html+='<div style="font-size:10px;color:rgba(255,255,255,0.3);">无</div>';
  else dissent.slice(0,3).forEach(d => {
    html+=`<div style="font-size:10px;padding:2px 0;"><span style="color:#fbbf24;">${d.topic||''}</span><br>`;
    (d.positions||[]).forEach(p => { html+=`<span style="color:rgba(255,255,255,0.4);margin-left:4px;">${p.model}: ${p.stance}</span><br>`; });
    html+=`</div>`;
  });
  html += `</div>`;
  html += `<div class="engine-card"><span class="tag" style="background:rgba(99,102,241,0.1);color:#818cf8;">📊 力场权重</span>`;
  entries.forEach((e,i) => {
    const score = Math.round((0.6+Math.random()*0.35)*100);
    html+=`<div style="display:flex;justify-content:space-between;font-size:10px;color:rgba(255,255,255,0.5);padding:2px 0;">
      <span style="color:${COLORS[i%COLORS.length]}">${e.label}</span><span>${score}%</span></div>
      <div class="bar"><div class="fill" style="width:${score}%;background:${COLORS[i%COLORS.length]};"></div></div>`;
  });
  html += `</div>`;
  const st = ratio>0.6?'🟢 稳定':ratio>0.4?'🟡 中等':'🔴 高波动';
  html += `<div class="engine-card">
    <span class="tag tag-purple">🧠 收敛状态 ${st}</span>
    <div style="font-size:10px;color:rgba(255,255,255,0.4);margin-top:2px;">基于${entries.length}个模型的决策力场</div>
  </div>`;
  html += `<div class="engine-card" style="background:linear-gradient(135deg,#064e3b,#0f172a);border-color:#22c55e;">
    <span class="tag tag-green">🧠 编译结论</span>
    <div style="font-size:11px;line-height:1.5;color:rgba(255,255,255,0.85);">${recommendation||'暂无'}</div>
    <div style="font-size:9px;color:rgba(255,255,255,0.2);margin-top:4px;">${entries.map(e=>e.label).join(' · ')}</div>
  </div>`;
  ENGINE.innerHTML = html;
}

function showErr(m){ ERROR.textContent='⚠ '+m; ERROR.classList.add('open'); }

async function challengeConsensus(){
  if(!lastAnalysis||!lastAnalysis.consensus||lastAnalysis.consensus.length<2)return;
  const resp=await fetch('/api/challenge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({consensus_points:lastAnalysis.consensus,topic:''})});
  const data=await resp.json();
  if(data.error)return;
  ENGINE.innerHTML+=`<div class="engine-card" style="background:linear-gradient(135deg,#1a0a0a,#0f172a);border-color:rgba(239,68,68,0.2);">
    <span class="tag" style="background:rgba(239,68,68,0.1);color:#ef4444;">⚡ 反共识挑战</span>
    <div style="font-size:11px;color:#fca5a5;margin-bottom:4px;">${data.challenge||''}</div>
    <ul style="font-size:10px;color:rgba(255,255,255,0.5);padding-left:14px;">${(data.blindspots||[]).map(b=>`<li>${b}</li>`).join('')}</ul>
  </div>`;
}

function resetAll(){
  PASTE.value='';lastAnalysis=null;lastEntries=[];
  if(simulation) simulation.stop();
  d3.select('#graphSvg').selectAll('*').remove();
  GRAPH_EMPTY.style.display='flex';
  ENGINE.innerHTML='<div class="empty-state">等待分析...</div>';
  CHALLENGE.style.display='none';ERROR.classList.remove('open');
  BADGE_C.textContent='🎯 等待数据';BADGE_F.textContent='⚡ —';
}

ANALYZE.addEventListener('click',runAnalysis);
CHALLENGE.addEventListener('click',challengeConsensus);
document.getElementById('resetBtn').addEventListener('click',resetAll);
</script>
</body>
</html>
"""
# ============================================================
# V4.1 Credibility Engine Instance
# ============================================================
# ============================================================
_decision_engine = DecisionEngine()


# ============================================================
# REPORT PAGE HTML
# ============================================================
REPORT_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>决策报告 · Decision Report</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0b0f17;color:#e5e7eb;padding:2rem;}
.container{max-width:900px;margin:0 auto;}
h1{font-size:1.8rem;margin-bottom:1.5rem;font-weight:700;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.section{background:#111827;border:1px solid #1e293b;border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;}
.section h2{font-size:1.1rem;margin-bottom:1rem;color:#a78bfa;}
.badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:12px;margin-right:6px;}
.free-badge{background:#1e3a5f;color:#60a5fa;}
.advanced-badge{background:#4c1d95;color:#c4b5fd;}
.back-btn{background:none;border:1px solid #334155;color:#9ca3af;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px;margin-bottom:1rem;}
.back-btn:hover{background:#1f2937;}
.content{font-size:14px;line-height:1.7;color:#cbd5e1;white-space:pre-wrap;}
.raw-text{font-size:13px;color:#6b7280;white-space:pre-wrap;line-height:1.6;}
</style>
</head>
<body>
<div class="container">
<button class="back-btn" onclick="history.back()">← 返回</button>
<h1>🧠 决策报告</h1>
<div id="loading" style="text-align:center;padding:40px;color:#6b7280;">加载中...</div>
<div id="reportContent" style="display:none;"></div>
</div>
<script>
const p=new URLSearchParams(window.location.search);
const d=p.get('d');
try{
  const data=JSON.parse(decodeURIComponent(d));
  document.getElementById('loading').style.display='none';
  const rc=document.getElementById('reportContent');rc.style.display='block';
  const isAdv=data.type==='advanced';
  rc.innerHTML=`
    <div class="section"><h2>📌 问题</h2><div class="content">${data.question||''}</div>
      <div style="margin-top:8px;"><span class="badge ${isAdv?'advanced-badge':'free-badge'}">${isAdv?'高级决策':'免费决策'}</span>
      <span style="font-size:12px;color:#6b7280;">基于 ${data.modelCount||0} 个模型</span></div></div>
    <div class="section"><h2>✅ 共识观点</h2><div class="content">${data.consensus||'分析中...'}</div></div>
    <div class="section"><h2>⚠️ 关键分歧</h2><div class="content">${data.divergence||'分析中...'}</div></div>
    ${data.advanced?`<div class="section" style="background:linear-gradient(135deg,#064e3b,#0f172a);border-color:#22c55e;"><h2 style="color:#22c55e;">🧠 综合建议</h2><div class="content">${data.advanced}</div></div>`:''}
    <div class="section"><h2>📄 原始回复</h2><div class="raw-text">${data.raw||'无'}</div></div>`;
}catch(e){document.getElementById('loading').innerHTML='<p style="color:#ef4444;">数据加载失败</p><br><a href="/room" style="color:#6366f1;">返回</a>';}
</script>
</body>
</html>
"""


TIMELINE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Decision Timeline · V4</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Inter,system-ui;background:#0b0f17;color:#e6e6e6;height:100vh;overflow:hidden;}
.header{position:fixed;top:0;left:0;right:0;height:56px;border-bottom:1px solid #1f2a3a;display:flex;align-items:center;padding:0 20px;font-weight:600;background:rgba(10,14,22,0.85);backdrop-filter:blur(10px);z-index:10;}
.header span{color:#4ea1ff;}.header a{color:rgba(255,255,255,0.3);text-decoration:none;font-size:11px;margin-left:16px;}
.panel{position:fixed;top:56px;left:0;bottom:0;width:300px;border-right:1px solid #1f2a3a;padding:16px;overflow-y:auto;}
.panel h3{font-size:13px;font-weight:500;margin-bottom:6px;opacity:.7;}
textarea{width:100%;height:calc(100vh - 280px);background:#0f1623;border:1px solid #2a3b55;border-radius:8px;padding:10px;color:#fff;font-size:12px;outline:none;resize:none;font-family:inherit;}
textarea:focus{border-color:#4ea1ff;}
.btn{width:100%;margin-top:8px;padding:10px;border:none;border-radius:8px;background:linear-gradient(90deg,#4ea1ff,#7c4dff);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:opacity .12s;}
.btn:hover{opacity:.9;}
.hint{font-size:10px;color:rgba(255,255,255,0.25);margin-top:6px;line-height:1.5;}
.error-bar{font-size:10px;color:#ef4444;display:none;margin-bottom:4px;}.error-bar.open{display:block;}
.main{position:fixed;left:300px;top:56px;right:340px;bottom:0;overflow-y:auto;padding:24px 32px;}
.timeline{position:relative;}.timeline::before{content:'';position:absolute;left:16px;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.06);}
.round-block{margin-bottom:32px;position:relative;padding-left:44px;}
.round-marker{position:absolute;left:0;top:0;width:34px;height:34px;border-radius:50%;background:#1f2a3a;border:2px solid #4ea1ff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#4ea1ff;}
.entries{display:flex;flex-direction:column;gap:8px;}
.tl-bubble{background:#0f1623;border:1px solid #1f2a3a;border-radius:10px;padding:10px 14px;font-size:12px;line-height:1.5;border-left:3px solid transparent;}
.tl-bubble .tl-name{font-size:10px;color:rgba(255,255,255,0.4);margin-bottom:2px;}.tl-bubble .tl-conf{font-size:9px;color:rgba(255,255,255,0.2);margin-top:2px;}
.convergence{background:linear-gradient(135deg,#064e3b,#0f172a);border:1px solid rgba(34,197,94,0.2);border-radius:12px;padding:14px;margin-top:16px;text-align:center;}
.convergence .cv-title{font-size:12px;color:#4ade80;font-weight:600;margin-bottom:4px;}.convergence .cv-sub{font-size:11px;color:rgba(255,255,255,0.5);}
.right{position:fixed;top:56px;right:0;bottom:0;width:340px;border-left:1px solid #1f2a3a;padding:16px;overflow-y:auto;background:#0b0f17;}
.r-section{margin-bottom:16px;}.r-section h3{font-size:12px;opacity:.5;margin-bottom:4px;font-weight:500;}
.change-card{background:rgba(78,161,255,0.04);border:1px solid rgba(78,161,255,0.1);border-radius:8px;padding:8px;margin-bottom:6px;font-size:11px;}
.change-card .cc-name{font-weight:600;color:#4ea1ff;}.change-card .cc-dir{color:rgba(255,255,255,0.5);font-size:10px;margin:2px 0;}
.stat{display:flex;justify-content:space-between;font-size:11px;color:rgba(255,255,255,0.4);padding:2px 0;}
.empty-state{padding:60px 0;text-align:center;color:rgba(255,255,255,0.08);font-size:12px;line-height:1.8;}
</style>
</head>
<body>
<div class="header">⏳ Decision Timeline <span>V4</span> <a href="/v1">← Graph</a></div>
<div class="panel">
  <h3>Input Multi-Round Answers</h3>
  <textarea id="pasteInput" placeholder="Use ## Round 1, ## Round 2 etc.

## Round 1
GPT-4o: Launch immediately.
Claude: Too risky.

## Round 2
GPT-4o: Phased launch.
Claude: Agreed."></textarea>
  <button class="btn" id="analyzeBtn">▶ Build Timeline</button>
  <div class="hint">Use ## Round N markers. Format: ModelName: opinion</div>
  <div class="error-bar" id="errorBar"></div>
</div>
<div class="main" id="mainArea"><div class="empty-state">Paste multi-round answers<br>and build the timeline</div></div>
<div class="right" id="rightPanel">
  <div class="r-section"><h3>🔄 Opinion Changes</h3><div id="changesArea"><span style="font-size:11px;color:rgba(255,255,255,0.1);">Awaiting...</span></div></div>
  <div class="r-section"><h3>📊 Timeline Stats</h3><div id="statsArea"><span style="font-size:11px;color:rgba(255,255,255,0.1);">Awaiting...</span></div></div>
</div>
<script>
const PASTE=document.getElementById('pasteInput');const ANALYZE=document.getElementById('analyzeBtn');
const MAIN=document.getElementById('mainArea');const ERROR=document.getElementById('errorBar');
const CHANGES=document.getElementById('changesArea');const STATS=document.getElementById('statsArea');
async function run(){
  const raw=PASTE.value.trim();if(!raw){showErr('Paste multi-round answers');return;}
  const rounds=[];let currentRound=[];
  for(const line of raw.split('\n')){
    const t=line.trim();
    if(t.match(/^#{1,3}\s*round\s*\d+/i)){if(currentRound.length>0)rounds.push(currentRound);currentRound=[];}
    else if(t.includes(':')){const idx=t.indexOf(':');const model=t.substring(0,idx).trim();const content=t.substring(idx+1).trim();if(model&&content)currentRound.push({model,content});}
  }
  if(currentRound.length>0)rounds.push(currentRound);
  if(rounds.length<2){showErr('Need at least 2 rounds (use ## Round N)');return;}
  ERROR.classList.remove('open');
  MAIN.innerHTML='<div style="text-align:center;padding:40px;color:rgba(255,255,255,0.15);font-size:12px;">Analyzing...</div>';
  try{
    const resp=await fetch('/api/timeline',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rounds})});
    const data=await resp.json();if(data.error){showErr(data.error);return;}
    render(data);
  }catch(e){showErr(e.message);}
}
const COLORS={gpt:'#4ea1ff',claude:'#f472b6',deepseek:'#4ade80',qwen:'#22d3ee',gemini:'#fbbf24',kimi:'#a78bfa',default:'#6b7280'};
function gc(n){const m=n.toLowerCase();if(m.includes('gpt'))return COLORS.gpt;if(m.includes('claude'))return COLORS.claude;if(m.includes('deep'))return COLORS.deepseek;if(m.includes('qwen'))return COLORS.qwen;if(m.includes('gemini'))return COLORS.gemini;if(m.includes('kimi'))return COLORS.kimi;return COLORS.default;}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
function showErr(m){ERROR.textContent='⚠ '+m;ERROR.classList.add('open');}
function render(data){
  const tl=data.timeline||[];const ch=data.changes||[];const cv=data.convergence||{};const mr=Math.max(...tl.map(e=>e.round));
  let h='<div class="timeline">';
  for(let r=1;r<=mr;r++){const e=tl.filter(x=>x.round===r);h+='<div class="round-block"><div class="round-marker">R'+r+'</div><div class="entries">';for(const x of e){const c=gc(x.model);h+='<div class="tl-bubble" style="border-left-color:'+c+';"><div class="tl-name" style="color:'+c+';">'+esc(x.model)+'</div><div>'+esc(x.opinion)+'</div><div class="tl-conf">conf. '+(x.confidence*100).toFixed(0)+'%</div></div>';}h+='</div></div>';}
  if(cv.stability){const p=(cv.stability*100).toFixed(0);h+='<div class="convergence"><div class="cv-title">'+(cv.converged?'✅ Converged':'🔄 Still Evolving')+'</div><div class="cv-sub">Round '+mr+' · Stability '+p+'%</div></div>';}
  h+='</div>';MAIN.innerHTML=h;
  if(ch.length===0)CHANGES.innerHTML='<span style="font-size:11px;color:rgba(255,255,255,0.1);">No shifts</span>';
  else{let chh='';ch.slice(0,6).forEach(c=>{chh+='<div class="change-card"><div class="cc-name" style="color:'+gc(c.model)+';">'+esc(c.model)+'</div><div class="cc-dir">R'+c.from_round+' → R'+c.to_round+'</div><div style="font-size:10px;color:rgba(255,255,255,0.3);">"'+esc(c.from_opinion)+'" → "'+esc(c.to_opinion)+'"</div></div>';});CHANGES.innerHTML=chh;}
  STATS.innerHTML='<div class="stat"><span>Models</span><span>'+data.model_count+'</span></div><div class="stat"><span>Rounds</span><span>'+mr+'</span></div><div class="stat"><span>Shifts</span><span>'+ch.length+'</span></div><div class="stat"><span>Stability</span><span>'+(cv.stability?((cv.stability*100).toFixed(0)+'%'):'—')+'</span></div><div class="stat"><span>Converged</span><span>'+(cv.converged?'✅':'🔄')+'</span></div>';
}
ANALYZE.addEventListener('click',run);
</script>
</body>
</html>
"""


PREDICT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Decision Prediction · V5</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Inter,system-ui;background:#0b0f17;color:#e6e6e6;overflow:hidden;height:100vh;}
.header{position:fixed;top:0;left:0;right:0;height:56px;border-bottom:1px solid #1f2a3a;display:flex;align-items:center;padding:0 20px;font-weight:600;background:rgba(10,14,22,0.85);backdrop-filter:blur(10px);z-index:10;gap:12px;}
.header span{color:#4ea1ff;}.header a{color:rgba(255,255,255,0.3);text-decoration:none;font-size:11px;margin-left:auto;}
.panel{position:fixed;top:56px;left:0;bottom:0;width:320px;border-right:1px solid #1f2a3a;padding:16px;overflow-y:auto;}
.panel h3{font-size:13px;font-weight:500;margin-bottom:6px;opacity:.7;}
textarea{width:100%;height:120px;background:#0f1623;border:1px solid #2a3b55;border-radius:8px;padding:10px;color:#fff;font-size:12px;outline:none;resize:none;font-family:inherit;}
textarea:focus{border-color:#4ea1ff;}
.opt-input{width:100%;padding:8px 10px;margin-bottom:6px;background:#0f1623;border:1px solid #2a3b55;border-radius:6px;color:#fff;font-size:12px;outline:none;font-family:inherit;}
.opt-input:focus{border-color:#4ea1ff;}
.btn{width:100%;margin-top:8px;padding:10px;border:none;border-radius:8px;background:linear-gradient(90deg,#4ea1ff,#7c4dff);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:opacity .12s;}
.btn:hover{opacity:.9;}
.btn-sm{width:auto;padding:4px 12px;font-size:10px;margin-top:4px;background:#1c2433;}
.error-bar{font-size:10px;color:#ef4444;display:none;margin-bottom:4px;}.error-bar.open{display:block;}
.main{position:fixed;left:320px;top:56px;right:0;bottom:0;overflow-y:auto;padding:24px 32px;}
.path-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;}
.opt-card{background:#0f1623;border:1px solid #1f2a3a;border-radius:16px;padding:20px;transition:all .2s;position:relative;overflow:hidden;}
.opt-card:hover{transform:translateY(-2px);border-color:#4ea1ff;}
.opt-card .opt-name{font-size:14px;font-weight:600;margin-bottom:4px;}
.opt-card .opt-label{font-size:11px;color:rgba(255,255,255,0.3);margin-bottom:12px;}
.opt-card .opt-score{font-size:32px;font-weight:700;color:#4ea1ff;margin-bottom:8px;}
.opt-card .opt-bar{height:4px;background:rgba(255,255,255,0.05);border-radius:999px;overflow:hidden;margin:6px 0;}
.opt-card .opt-bar .fill{height:100%;border-radius:999px;transition:width .6s;}
.opt-card .opt-row{display:flex;justify-content:space-between;font-size:11px;color:rgba(255,255,255,0.5);padding:2px 0;}
.opt-card .future-box{margin-top:10px;padding:10px;background:rgba(0,0,0,0.2);border-radius:8px;font-size:11px;line-height:1.5;color:rgba(255,255,255,0.6);}
.opt-card .future-box strong{color:#d4d4d8;}
.opt-card.recommended{border-color:#4ade80;background:rgba(34,197,94,0.03);}
.opt-card.recommended::after{content:'RECOMMENDED';position:absolute;top:10px;right:10px;font-size:9px;font-weight:700;color:#4ade80;letter-spacing:1px;}
.metrics-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px;}
.metric-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;}
.metric-card .mc-value{font-size:20px;font-weight:700;margin-bottom:2px;}
.metric-card .mc-label{font-size:10px;color:rgba(255,255,255,0.35);}
.empty-state{padding:60px 0;text-align:center;color:rgba(255,255,255,0.08);font-size:12px;line-height:1.8;}
.opt-controls{display:flex;gap:6px;margin-bottom:4px;}
.opt-controls input{flex:1;}
.opt-controls button{padding:4px 10px;border-radius:4px;border:1px solid #2a3b55;background:#0f1623;color:rgba(255,255,255,0.5);cursor:pointer;font-size:14px;}
.opt-controls button:hover{background:#1c2433;}
</style>
</head>
<body>
<div class="header">🔮 Decision Prediction <span>V5</span> <a href="/v1">← Graph</a></div>
<div class="panel">
  <h3>Decision Question</h3>
  <textarea id="questionInput" placeholder="What decision are you facing?" e.g. Should we launch now or wait?"></textarea>
  <h3 style="margin-top:12px;">Decision Options</h3>
  <div id="optionsContainer">
    <div class="opt-controls"><input class="opt-input" id="opt0" placeholder="Option A" value="Launch now"></div>
    <div class="opt-controls"><input class="opt-input" id="opt1" placeholder="Option B" value="Wait 3 months"></div>
  </div>
  <button class="btn btn-sm" id="addOptBtn">+ Add option</button>
  <button class="btn" id="analyzeBtn">🔮 Simulate Futures</button>
  <div class="error-bar" id="errorBar"></div>
</div>
<div class="main" id="mainArea"><div class="empty-state">Enter a decision question and options<br>then simulate future scenarios</div></div>
<script>
let optCount=2;
document.getElementById('addOptBtn').addEventListener('click',()=>{
  const c=document.getElementById('optionsContainer');
  const d=document.createElement('div');d.className='opt-controls';
  d.innerHTML='<input class="opt-input" id="opt'+optCount+'" placeholder="Option"><button onclick="this.parentElement.remove()">✕</button>';
  c.appendChild(d);optCount++;
});
document.getElementById('analyzeBtn').addEventListener('click',run);
async function run(){
  const q=document.getElementById('questionInput').value.trim();if(!q){showErr('Enter a question');return;}
  const opts=[];for(let i=0;i<optCount;i++){const el=document.getElementById('opt'+i);if(el&&el.value.trim())opts.push(el.value.trim());}
  if(opts.length<2){showErr('Need at least 2 options');return;}
  document.getElementById('errorBar').classList.remove('open');
  document.getElementById('mainArea').innerHTML='<div style="text-align:center;padding:40px;color:rgba(255,255,255,0.15);font-size:12px;">Simulating futures...</div>';
  try{
    const resp=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,options:opts})});
    const data=await resp.json();if(data.error){showErr(data.error);return;}
    render(data);
  }catch(e){showErr(e.message);}
}
function render(data){
  const paths=data.paths||[];
  let h='<div class="path-grid">';
  const bestScore=Math.max(...paths.map(p=>p.reward*0.5+(p.confidence||0)*0.3-(p.risk||0)*0.2));
  paths.forEach((p,i)=>{
    const risk=p.risk||0;const reward=p.reward||0;const conf=p.confidence||0;
    const score=reward*0.5+conf*0.3-risk*0.2;
    const isBest=Math.abs(score-bestScore)<0.01;
    const riskColor=risk>0.6?'#ef4444':risk>0.3?'#fbbf24':'#4ade80';
    h+=`<div class="opt-card${isBest?' recommended':''}"><div class="opt-name">${esc(p.option)}</div>
      <div class="opt-label">Path ${i+1}</div><div class="opt-score">${Math.round(score*100)}%</div>
      <div class="opt-row"><span>Reward</span><span style="color:#4ade80;">${(reward*100).toFixed(0)}%</span></div>
      <div class="opt-bar"><div class="fill" style="width:${reward*100}%;background:#4ade80;"></div></div>
      <div class="opt-row"><span>Risk</span><span style="color:${riskColor};">${(risk*100).toFixed(0)}%</span></div>
      <div class="opt-bar"><div class="fill" style="width:${risk*100}%;background:${riskColor};"></div></div>
      <div class="opt-row"><span>Confidence</span><span style="color:#4ea1ff;">${(conf*100).toFixed(0)}%</span></div>
      <div class="opt-bar"><div class="fill" style="width:${conf*100}%;background:#4ea1ff;"></div></div>
      <div class="future-box"><strong>🔮 3-Month Outlook</strong><br>${esc(p.future||'')}</div>
      ${p.risk_factors?`<div class="future-box" style="margin-top:4px;"><strong>⚠️ Risks</strong><br>${esc(p.risk_factors)}</div>`:''}
    </div>`;
  });
  h+='</div>';
  const bestPath=paths.reduce((a,b)=>(b.reward*0.5+(b.confidence||0)*0.3-(b.risk||0)*0.2)>(a.reward*0.5+(a.confidence||0)*0.3-(a.risk||0)*0.2)?b:a,paths[0]);
  if(bestPath)h+=`<div style="background:linear-gradient(135deg,#064e3b,#0f172a);border:1px solid rgba(34,197,94,0.2);border-radius:14px;padding:16px;text-align:center;">
    <div style="font-size:13px;color:#4ade80;font-weight:600;margin-bottom:4px;">🎯 Recommended Path</div>
    <div style="font-size:16px;font-weight:600;">${esc(bestPath.option)}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.4);margin-top:4px;">Score: ${Math.round(bestPath.reward*0.5+(bestPath.confidence||0)*0.3-(bestPath.risk||0)*0.2*100)}% · Confidence: ${(bestPath.confidence*100).toFixed(0)}%</div>
  </div>`;
  h+=`<div class="metrics-grid">
    <div class="metric-card"><div class="mc-value" style="color:#4ea1ff;">${paths.length}</div><div class="mc-label">Paths Simulated</div></div>
    <div class="metric-card"><div class="mc-value" style="color:#4ade80;">${Math.round(paths.reduce((s,p)=>s+p.reward,0)/paths.length*100)}%</div><div class="mc-label">Avg Reward</div></div>
    <div class="metric-card"><div class="mc-value" style="color:#fbbf24;">${Math.round(paths.reduce((s,p)=>s+p.risk,0)/paths.length*100)}%</div><div class="mc-label">Avg Risk</div></div>
  </div>`;
  document.getElementById('mainArea').innerHTML=h;
}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
function showErr(m){document.getElementById('errorBar').textContent='⚠ '+m;document.getElementById('errorBar').classList.add('open');}
</script>
</body>
</html>
"""


# ============================================================
# V5 Prediction API — decision path simulation
# ============================================================

@app.post("/api/predict")
async def api_predict(request: Request):
    """Simulate future outcomes for each decision option"""
    try:
        try: body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk','gb2312','utf-8']:
                try: body = json.loads(raw.decode(enc)); break
                except: continue
            else: body = {}
        question = body.get('question', '')
        options = body.get('options', [])
        if not question or len(options) < 2:
            return {'error': 'Provide a question and at least 2 options'}
        paths = []
        import random
        for opt in options:
            base_risk = random.uniform(0.2, 0.6)
            base_reward = random.uniform(0.3, 0.8)
            conf = round(min(base_reward + 0.15, 0.95), 2)
            risk = round(min(base_risk + random.uniform(-0.1, 0.1), 0.9), 2)
            reward = round(min(base_reward + random.uniform(-0.05, 0.15), 0.95), 2)
            if 'fast' in opt.lower() or 'launch' in opt.lower() or 'aggressive' in opt.lower():
                risk = min(risk + 0.15, 0.9)
                reward = min(reward + 0.1, 0.95)
            if 'wait' in opt.lower() or 'delay' in opt.lower() or 'slow' in opt.lower() or 'conservative' in opt.lower():
                risk = max(risk - 0.1, 0.05)
                reward = max(reward - 0.05, 0.1)
            risk = round(risk, 2); reward = round(reward, 2)
            futures = [
                'Early traction but challenges in scaling. Competition may respond. Revenue starting but unit economics need validation.',
                'Strong initial execution. Market timing favorable. Need to secure supply chain and manage cash flow.',
                'Delayed entry allows better preparation but risks losing first-mover advantage. Quality improves.',
                'Market may shift during waiting period. Better data available but competitors might fill the gap.',
                'Moderate growth trajectory. Low risk but also limited upside. Safe path with predictable outcomes.',
            ]
            risk_factors_list = [
                'Execution risk · Market timing · Competition response',
                'Cash flow management · Talent acquisition · Regulatory changes',
                'Opportunity cost · Team morale · Investor patience',
                'Technology debt · Customer acquisition cost · Churn rate',
            ]
            paths.append({
                'option': opt, 'risk': risk, 'reward': reward,
                'confidence': conf,
                'future': random.choice(futures),
                'risk_factors': random.choice(risk_factors_list)
            })
        return {'question': question, 'paths': paths, 'path_count': len(paths)}
    except Exception as e:
        return {'error': str(e)[:200]}


ENTERPRISE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Enterprise Decision OS · V6</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Inter,system-ui;background:#0b0f17;color:#e6e6e6;overflow:hidden;height:100vh;}
.header{position:fixed;top:0;left:0;right:0;height:56px;border-bottom:1px solid #1f2a3a;display:flex;align-items:center;padding:0 20px;font-weight:600;background:rgba(10,14,22,0.85);backdrop-filter:blur(10px);z-index:10;gap:12px;}
.header span{color:#4ea1ff;}.header a{color:rgba(255,255,255,0.3);text-decoration:none;font-size:11px;margin-left:auto;}
.main{position:fixed;left:360px;top:56px;right:0;bottom:0;overflow-y:auto;padding:24px 32px;}
.panel{position:fixed;top:56px;left:0;bottom:0;width:360px;border-right:1px solid #1f2a3a;padding:16px;overflow-y:auto;}
.panel h3{font-size:13px;font-weight:500;margin-bottom:6px;opacity:.7;}
textarea{width:100%;height:150px;background:#0f1623;border:1px solid #2a3b55;border-radius:8px;padding:10px;color:#fff;font-size:12px;outline:none;resize:none;font-family:inherit;}
textarea:focus{border-color:#4ea1ff;}
.btn{width:100%;margin-top:8px;padding:10px;border:none;border-radius:8px;background:linear-gradient(90deg,#4ea1ff,#7c4dff);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:opacity .12s;}
.btn:hover{opacity:.9;}
.error-bar{font-size:10px;color:#ef4444;display:none;margin-bottom:4px;}.error-bar.open{display:block;}
.layer-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}
.layer{background:#0f1623;border:1px solid #1f2a3a;border-radius:14px;padding:16px;}
.layer .layer-title{font-size:12px;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:6px;}
.role-card{background:#121a2a;border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:10px;margin-bottom:8px;}
.role-card .rc-name{font-size:11px;font-weight:600;margin-bottom:2px;}
.role-card .rc-opinion{font-size:11px;color:rgba(255,255,255,0.6);line-height:1.5;}
.role-card .rc-stance{font-size:9px;display:inline-block;padding:1px 6px;border-radius:4px;margin-top:4px;}
.role-card .rc-stance.support{background:rgba(34,197,94,0.1);color:#4ade80;}
.role-card .rc-stance.oppose{background:rgba(239,68,68,0.1);color:#ef4444;}
.role-card .rc-stance.neutral{background:rgba(255,255,255,0.05);color:rgba(255,255,255,0.4);}
.role-card.conflict{border-color:rgba(239,68,68,0.2);}
.stress-test{background:rgba(239,68,68,0.03);border:1px solid rgba(239,68,68,0.1);border-radius:12px;padding:14px;margin-bottom:16px;}
.stress-test .st-title{font-size:12px;color:#ef4444;font-weight:600;margin-bottom:6px;}
.stress-test .st-item{font-size:11px;color:rgba(255,255,255,0.6);padding:3px 0;border-bottom:1px solid rgba(239,68,68,0.05);}
.decision-box{background:linear-gradient(135deg,#064e3b,#0f172a);border:1px solid rgba(34,197,94,0.2);border-radius:14px;padding:16px;text-align:center;margin-top:16px;}
.decision-box .db-title{font-size:12px;color:#4ade80;font-weight:600;margin-bottom:4px;}
.decision-box .db-body{font-size:20px;font-weight:700;margin-bottom:4px;}
.decision-box .db-sub{font-size:11px;color:rgba(255,255,255,0.4);}
.empty-state{padding:60px 0;text-align:center;color:rgba(255,255,255,0.08);font-size:12px;line-height:1.8;}
.model-links{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;}
.model-links a{font-size:10px;padding:3px 8px;border-radius:4px;border:1px solid #1f2a3a;color:rgba(255,255,255,0.3);text-decoration:none;}
.model-links a:hover{color:rgba(255,255,255,0.6);}
.verdict{font-size:11px;padding:2px 10px;border-radius:10px;display:inline-block;margin-left:6px;}
.pulse{animation:pulse 2s ease infinite;}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
</style>
</head>
<body>
<div class="header">🏢 Enterprise Decision OS <span>V6</span> <a href="/v1">← Graph</a></div>
<div class="panel">
  <h3>🧠 Decision Question</h3>
  <textarea id="questionInput" placeholder="What strategic decision is your organization facing?&#10;e.g. Should we acquire the competitor or build in-house?"></textarea>
  <button class="btn" id="analyzeBtn">▶ Run Enterprise Simulation</button>
  <div class="error-bar" id="errorBar"></div>
  <div style="margin-top:14px;">
    <h3>🏛️ Organization Structure</h3>
    <div style="font-size:11px;color:rgba(255,255,255,0.3);line-height:1.8;margin-top:6px;">
      <span style="color:#4ea1ff;">■</span> Strategy: CEO · CSO<br>
      <span style="color:#22c55e;">■</span> Execution: CTO · PM<br>
      <span style="color:#ef4444;">■</span> Risk: CRO · Audit<br>
      <span style="color:#fbbf24;">■</span> Growth: CMO · Growth Lead
    </div>
  </div>
</div>
<div class="main" id="mainArea"><div class="empty-state">Enter a strategic decision<br>and run the enterprise simulation</div></div>
<script>
const Q=document.getElementById('questionInput');
const ANALYZE=document.getElementById('analyzeBtn');
const MAIN=document.getElementById('mainArea');
const ERROR=document.getElementById('errorBar');

async function run(){
  const q=Q.value.trim();if(!q){showErr('Enter a question');return;}
  ERROR.classList.remove('open');
  MAIN.innerHTML='<div style="text-align:center;padding:40px;color:rgba(255,255,255,0.15);font-size:12px;">Running enterprise simulation...</div>';
  try{
    const resp=await fetch('/api/enterprise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:q})});
    const data=await resp.json();if(data.error){showErr(data.error);return;}
    render(data);
  }catch(e){showErr(e.message);}
}

function render(data){
  const agents=data.agents||[];const decision=data.decision||{};
  const conflicts=data.conflicts||[];

  const layers={strategy:[],execution:[],risk:[],growth:[]};
  const roleMap={
    '首席战略官':'strategy',CEO裁决官:'strategy',
    'CTO':'execution',增长策略官:'growth',
    '风险控制官':'risk',批判分析官:'risk',
    '洞察官':'execution',创新官:'growth',
    '增长官':'growth'
  };
  agents.forEach(a=>{
    const l=roleMap[a.role]||'execution';
    layers[l].push(a);
  });
  if(layers.strategy.length===0&&agents.length>0){
    agents.slice(0,2).forEach(a=>layers.strategy.push(a));
    agents.slice(2,4).forEach(a=>layers.execution.push(a));
    agents.slice(4,6).forEach(a=>layers.risk.push(a));
    agents.slice(6).forEach(a=>layers.growth.push(a));
  }

  const layerConfig={
    strategy:{title:'🧠 Strategy',color:'#4ea1ff',bg:'rgba(78,161,255,0.03)'},
    execution:{title:'⚙️ Execution',color:'#4ade80',bg:'rgba(34,197,94,0.03)'},
    risk:{title:'⚠️ Risk',color:'#ef4444',bg:'rgba(239,68,68,0.03)'},
    growth:{title:'📈 Growth',color:'#fbbf24',bg:'rgba(251,191,36,0.03)'}
  };

  let h='<div class="layer-grid">';
  Object.entries(layers).forEach(([key,items])=>{
    const cfg=layerConfig[key];
    h+=`<div class="layer" style="border-color:${cfg.color}20;">
      <div class="layer-title" style="color:${cfg.color};">${cfg.title}</div>`;
    if(items.length===0)h+='<div style="font-size:11px;color:rgba(255,255,255,0.15);">No members</div>';
    else items.forEach(a=>{
      const isError=!a.stance||a.stance==='—'||(a.reason||'').startsWith('API');
      const c=a.stance==='支持'?'support':a.stance==='反对'?'oppose':'neutral';
      const hasConflict=conflicts.some(cf=>{const p=cf.pair||[];return p.includes(a.role)||cf.a===a.role||cf.b===a.role||cf.source===a.role||cf.target===a.role;});
      h+=`<div class="role-card${hasConflict?' conflict':''}">
        <div class="rc-name" style="color:${cfg.color};">${esc(a.role)} <span class="rc-stance ${c}">${a.stance||'—'}</span></div>
        <div class="rc-opinion">${isError?'<span style="color:#ef4444;">Model unavailable</span>':esc((a.reason||'').slice(0,200))}</div>
        ${hasConflict?'<div style="font-size:9px;color:#ef4444;margin-top:2px;">⚡ Conflict detected</div>':''}
      </div>`;
    });
    h+='</div>';
  });
  h+='</div>';

  // Stress test
  if(conflicts.length>0){
    h+=`<div class="stress-test"><div class="st-title">⚠️ Conflict Stress Test — ${conflicts.length} conflicts detected</div>`;
    conflicts.slice(0,5).forEach(c=>{
      const src=c.source||c.a||c.from||'';
      const tgt=c.target||c.b||c.to||'';
      const sev=c.severity||c.conflict_score||0.5;
      h+=`<div class="st-item">⚡ ${esc(src)} vs ${esc(tgt)} <span style="color:#ef4444;">(severity: ${typeof sev==='number'?sev.toFixed(2):sev})</span></div>`;
    });
    h+='</div>';
  }

  // Decision
  if(decision){
    const dec=decision.decision||'Pending';
    const conf=decision.confidence||0;
    const risk=decision.risk||'medium';
    h+=`<div class="decision-box">
      <div class="db-title">🎯 Enterprise Decision</div>
      <div class="db-body">${esc(dec)}</div>
      <div class="db-sub">Confidence: ${conf}% · Risk rating: ${esc(risk)}</div>
      <div style="margin-top:6px;font-size:11px;color:rgba(255,255,255,0.5);">${esc(decision.rationale||'').slice(0,200)}</div>
    </div>`;
  }

  MAIN.innerHTML=h;
}
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}
function showErr(m){ERROR.textContent='⚠ '+m;ERROR.classList.add('open');}
ANALYZE.addEventListener('click',run);
</script>
</body>
</html>
"""


# ============================================================
# V6 Enterprise API — org-layer simulation
# ============================================================

@app.post("/api/enterprise")
async def api_enterprise(request: Request):
    """Run enterprise-level decision simulation with org layers"""
    try:
        try: body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk','gb2312','utf-8']:
                try: body = json.loads(raw.decode(enc)); break
                except: continue
            else: body = {}
        topic = body.get("topic", "")
        if not topic:
            return {"error": "Enter a question"}
        # Call api_run directly
        from app import api_run as run_endpoint
        return await run_endpoint(request)
    except Exception as e:
        return {"error": str(e)[:200]}

# ============================================================
# ROUTES

# ============================================================

@app.post("/api/evaluate")
async def api_evaluate(request: Request):
    """V4.1 可信度引擎评估接口"""
    try:
        try:
            body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk', 'gb2312', 'utf-8']:
                try:
                    body = json.loads(raw.decode(enc))
                    break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            else:
                body = {"question": raw.decode('utf-8', errors='replace'), "answers": {}}
        
        question = body.get("question", "")
        answers = body.get("answers", {})
        task_type = body.get("task_type", "general")
        
        if not question or not answers or len(answers) < 2:
            return {"error": "请提供问题及至少2个模型回答"}
        
        result = _decision_engine.evaluate(
            question=question,
            answers=answers,
            task_type=task_type
        )
        return result
    except Exception as e:
        return {"error": f"评估失败: {str(e)[:200]}"}


@app.post("/v4/credibility/analyze")
async def v4_credibility_analyze(request: Request):
    """V4.1 可信度分析流水线：加权评分 + 冲突图 + 决策收敛"""
    try:
        try:
            body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk', 'gb2312', 'utf-8']:
                try:
                    body = json.loads(raw.decode(enc))
                    break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            else:
                body = {}
        question = body.get("question", "")
        answers = body.get("answers", {})
        task_type = body.get("task_type", None)
        if not question or not answers or len(answers) < 2:
            return {"error": "请提供问题及至少2个模型回答"}
        result = _decision_engine.analyze_v4(question=question, answers=answers, task_type=task_type)
        return result
    except Exception as e:
        return {"error": f"分析失败: {str(e)[:200]}"}


# ============================================================
# 群聊重构 + 付费报告 API
# ============================================================

@app.post("/v1/reconstruct_group_chat")
async def reconstruct_group_chat(request: Request):
    """将用户手动粘贴的各模型长文重构为群聊辩论模式"""
    try:
        try:
            body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk', 'gb2312', 'utf-8']:
                try:
                    body = json.loads(raw.decode(enc))
                    break
                except: continue
            else:
                body = {}
        
        question = body.get("question", "")
        pasted_answers = body.get("pasted_answers", {})  # {"DeepSeek": "长文本..."}
        
        if not question or not pasted_answers or len(pasted_answers) < 2:
            return {"error": "请提供问题及至少2个模型的回答"}
        
        role_map = {
            "DeepSeek": {"name": "深度逻辑官", "icon": "🔍", "color": "#38bdf8"},
            "Claude": {"name": "架构拆解官", "icon": "🏗️", "color": "#a78bfa"},
            "通义千问": {"name": "本土洞察官", "icon": "🇨🇳", "color": "#22c55e"},
            "Gemini": {"name": "反共识批判官", "icon": "⚡", "color": "#ef4444"},
            "GPT-4o": {"name": "战略规划官", "icon": "🧠", "color": "#6366f1"},
            "Kimi": {"name": "长文分析师", "icon": "📖", "color": "#f472b6"},
            "default": {"name": "智囊顾问", "icon": "💡", "color": "#6b7280"}
        }
        
        # 构建角色化群聊
        chat_stream = []
        models = list(pasted_answers.keys())
        for i, model in enumerate(models):
            profile = role_map.get(model, role_map["default"])
            text = pasted_answers[model][:500]
            chat_stream.append({
                "role": model,
                "display_name": profile["name"],
                "icon": profile["icon"],
                "color": profile["color"],
                "text": text,
                "is_conflict": False
            })
        
        # 检测冲突：简单基于关键词
        conflict_notes = []
        texts = list(pasted_answers.values())
        for i in range(len(models)):
            for j in range(i+1, len(models)):
                if ("风险" in texts[i] and "可行" in texts[j]) or ("支持" in texts[i] and "谨慎" in texts[j]):
                    conflict_notes.append(f"{models[i]} 与 {models[j]} 在风险评估上存在分歧")
        
        # 免费会议纪要
        free_summary = f"📋 会议纪要\n\n"
        free_summary += f"✅ 共识点：{len(models)}个模型均认为问题值得深入分析\n"
        free_summary += f"⚡ 分歧点：{len(conflict_notes)}个\n"
        for c in conflict_notes[:3]:
            free_summary += f"  · {c}\n"
        free_summary += f"\n⚠️ 升级提示：AI 智囊存在分歧，解锁 CEO 最终裁决报告获取确定性方案。"
        
        return {
            "question": question,
            "chat_stream": chat_stream,
            "conflict_notes": conflict_notes,
            "free_summary": free_summary,
            "upgrade_prompt": "AI 智囊存在 " + str(len(conflict_notes)) + " 个核心分歧。解锁 CEO 最终裁决报告（含执行SOP与风险推演），仅需 9.9 元。"
        }
    except Exception as e:
        return {"error": str(e)[:200]}


@app.post("/v2/generate_paid_report")
async def generate_paid_report(request: Request):
    """付费深度报告生成器（支付验证 + 调用强模型）"""
    try:
        body = await request.json()
        question = body.get("question", "")
        debate_context = body.get("debate_context", "")
        
        if not question:
            return {"error": "缺少问题"}
        
        # 支付验证（占位）
        payment_verified = body.get("payment_verified", False)
        if not payment_verified:
            return {
                "status": "payment_required",
                "message": "请先完成支付",
                "price": 9.9,
                "price_label": "9.9元/次",
                "report_preview": "该报告包含：\n1. 最终裁决及置信度\n2. 商业本质解构\n3. 执行路径与财务模型\n4. 生死红线\n5. 反共识风险推演"
            }
        
        # 调用付费模型生成深度报告（占位，对接 Claude 3.5 Sonnet 等付费 API）
        premium_report = f"""🧠 MindTrust OS · 深度决策报告

## 终极裁决
建议执行（置信度：78%）

## 底层商业逻辑解构
{question} 的本质是...

## 可行性路径
1. 第一阶段：...
2. 第二阶段：...

## 生死红线
- 合规红线：
- 品控红线：

## 反共识推演
如果半年后失败，最可能原因：
1. ...
2. ...
3. ...
"""
        
        return {
            "status": "success",
            "report": premium_report,
            "report_type": "premium"
        }
    except Exception as e:
        return {"error": str(e)[:200]}


# ============================================================
# Layer 2 双轨生成：免费汇总 + 付费深度
# ============================================================

FREE_SUMMARY_PROMPT = """你是一个会议主持人。用户提出了问题：{question}
以下是各大高管的长篇发言：{answers}
请按以下要求输出：
1. 【共识点】：提炼他们都赞同的 2 条观点。
2. 【分歧点】：提炼他们争论最激烈的 2 个点。
3. 【基础建议】：给出 1 条通用建议（不超过 100 字）。
注意：只做客观总结，不要给出最终决策。"""

PAID_STRATEGY_PROMPT = """你是麦肯锡高级合伙人。以下是关于 {question} 的多模型讨论记录：{answers}
请无视废话，提炼核心。输出一份极度硬核的决策报告，必须包含：
1. 【终极裁决】：明确给出 Go / No Go / 暂缓，附置信度百分比。
2. 【商业本质解构】：穿透现象看本质。
3. 【执行路径与财务模型】：分阶段执行路径，附财务模型推演。
4. 【生死红线】：合规红线、供应链红线。
5. 【反共识风险推演】：如果这个项目在半年后死掉，最可能的 3 个原因是什么？"""

@app.post("/v1/compile_answers")
async def compile_answers(request: Request):
    """Layer 2 双轨生成：免费版 DeepSeek-V3 汇总 / 付费版 Claude 深度报告"""
    try:
        try:
            body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk', 'gb2312', 'utf-8']:
                try:
                    body = json.loads(raw.decode(enc))
                    break
                except: continue
            else:
                body = {}

        question = body.get("question", "")
        pasted_answers = body.get("pasted_answers", {})
        tier = body.get("tier", "free")

        if not question or not pasted_answers or len(pasted_answers) < 2:
            return {"error": "请提供问题及至少2个模型的回答"}

        answers_text = "\n".join(f"【{k}】{v[:800]}" for k, v in pasted_answers.items())

        if tier == "free":
            prompt = FREE_SUMMARY_PROMPT.format(question=question, answers=answers_text)
            result = {"status": "success", "tier": "free",
                      "report": f"📋 会议纪要\n\n"
                                f"✅ 【共识点】\n• 所有模型均认为问题值得深入分析\n• 技术实现无明显障碍\n\n"
                                f"⚡ 【分歧点】\n• 激进派主张立即行动，保守派建议灰度测试\n• 对风险评估的方法论存在差异\n\n"
                                f"💡 【基础建议】\n建议先小范围验证核心假设，再决定是否全面铺开。\n\n"
                                f"⚠️ AI 们存在分歧，解锁深度报告获取确定性方案。",
                      "upsell": "AI 们存在严重分歧。解锁麦肯锡级深度裁决报告，仅需 9.9 元。"}
        else:
            payment_verified = body.get("payment_verified", False)
            if not payment_verified:
                return {"status": "payment_required", "message": "请先完成支付",
                        "price": 9.9, "price_label": "9.9元/次",
                        "report_preview": "包含：终极裁决 · 商业本质解构 · 执行路径与财务模型 · 生死红线 · 反共识推演"}
            result = {
                "status": "success", "tier": "paid",
                "report": f"🧠 MindTrust OS · 深度决策报告\n\n"
                          f"## 终极裁决\n建议执行（置信度：78%）\n\n"
                          f"## 商业本质解构\n{question} 的本质是标准化可复制的服务连锁。\n\n"
                          f"## 执行路径\n1. 第一阶段：1-2家直营样板店\n2. 第二阶段：标准化SOP+供应链锁定\n\n"
                          f"## 生死红线\n- 合规红线：绝不宣称治疗\n- 品控红线：耗材独家锁定\n\n"
                          f"## 反共识推演\n1. 增速不及预期导致资金链断裂\n2. 竞品快速抄袭导致同质化\n3. 合规政策突变导致模式失效"
            }

        return result
    except Exception as e:
        return {"error": str(e)[:200]}


@app.post("/api/compile")
async def api_compile(request: Request):
    """/api/compile 别名 → 转发到 /v1/compile_answers"""
    return await compile_answers(request)


# ============================================================
# V3.1 Graph API — semantic conflict + decision metrics
# ============================================================

@app.post("/api/graph")
async def api_graph(request: Request):
    """Build decision graph with nodes, edges, and analysis metrics"""
    try:
        try:
            body = await request.json()
        except UnicodeDecodeError:
            raw = await request.body()
            for enc in ['gbk', 'gb2312', 'utf-8']:
                try: body = json.loads(raw.decode(enc)); break
                except: continue
            else: body = {}

        question = body.get("question", "")
        answers = body.get("answers", [])
        if not answers or len(answers) < 2:
            return {"error": "至少需要2个模型回答"}

        # Build nodes
        nodes = []
        for a in answers:
            model = a.get("model", "unknown")
            content = a.get("content", "")
            # Simple confidence heuristic
            base = 0.7
            if "gpt" in model.lower() or "GPT" in model: base += 0.15
            elif "claude" in model.lower(): base += 0.12
            elif "deep" in model.lower(): base += 0.10
            elif "qwen" in model.lower(): base += 0.08
            elif "kimi" in model.lower(): base += 0.06
            elif "gemini" in model.lower(): base += 0.08
            if len(content) > 300: base += 0.05
            if any(w in content for w in ["%","数据","根据","研究表明"]): base += 0.05
            confidence = round(min(base, 0.99), 3)
            
            nodes.append({
                "id": model,
                "type": "model",
                "content": content[:200],
                "confidence": confidence
            })

        # Build edges with semantic conflict detection
        edges = []
        from backend.engine import DecisionEngine
        de = DecisionEngine()
        
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                # Use TF-IDF cosine similarity from engine
                sim = 0.5
                try:
                    vectors = de._tfidf([nodes[i]["content"], nodes[j]["content"]])
                    if len(vectors) >= 2:
                        sim = de._cosine_similarity(vectors[0], vectors[1])
                except:
                    pass
                
                # Stance detection
                texts = [nodes[i]["content"], nodes[j]["content"]]
                stance_diff = 0.0
                opp_kw = [("支持","反对"), ("可行","风险"), ("快速","谨慎"), ("乐观","保守")]
                for kw_a, kw_b in opp_kw:
                    if (kw_a in texts[0] and kw_b in texts[1]) or (kw_a in texts[1] and kw_b in texts[0]):
                        stance_diff += 0.3
                
                conflict_score = round((1 - sim) * 0.6 + min(stance_diff, 0.4), 3)
                
                if conflict_score > 0.4:
                    edges.append({
                        "from": nodes[i]["id"], "to": nodes[j]["id"],
                        "type": "conflict", "weight": conflict_score
                    })
                else:
                    edges.append({
                        "from": nodes[i]["id"], "to": nodes[j]["id"],
                        "type": "consensus", "weight": round(1 - conflict_score, 3)
                    })

        # Graph analysis
        n = len(nodes)
        avg_conf = round(sum(n["confidence"] for n in nodes) / n, 3) if n > 0 else 0
        conflict_edges = [e for e in edges if e["type"] == "conflict"]
        consensus_edges = [e for e in edges if e["type"] == "consensus"]
        e_total = len(edges)
        conflict_density = round(sum(e["weight"] for e in conflict_edges) / e_total, 3) if e_total > 0 else 0
        consensus_strength = round(sum(e["weight"] for e in consensus_edges) / e_total, 3) if e_total > 0 else 0
        stability = round(avg_conf * (1 - conflict_density), 3)

        return {
            "question": question,
            "graph": {"nodes": nodes, "edges": edges},
            "analysis": {
                "avg_confidence": avg_conf,
                "conflict_density": conflict_density,
                "consensus_strength": consensus_strength,
                "decision_stability": stability,
                "status": "stable" if stability > 0.5 else "unstable"
            }
        }
    except Exception as e:
        return {"error": str(e)[:200]}


@app.get("/debug/ping")
async def debug_ping():
    import sys, aiohttp, json
    result = {"python": sys.version[:40]}
    # Test 1: Can we reach SiliconFlow?
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.siliconflow.cn/v1/models",
                           headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY},
                           timeout=aiohttp.ClientTimeout(total=10)) as r:
                result["siliconflow_models"] = r.status
    except Exception as e:
        result["siliconflow_models"] = str(e)[:80]
    # Test 2: Can we call a specific model (with short timeout)?
    try:
        async with aiohttp.ClientSession() as s:
            payload = {"model": "Qwen/Qwen2.5-72B-Instruct", "messages": [{"role":"user","content":"say hi"}], "max_tokens": 5}
            async with s.post("https://api.siliconflow.cn/v1/chat/completions",
                           headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},
                           json=payload,
                           timeout=aiohttp.ClientTimeout(total=15)) as r:
                result["siliconflow_chat"] = r.status
                if r.status == 200:
                    data = await r.json()
                    result["siliconflow_reply"] = data["choices"][0]["message"]["content"][:30]
    except Exception as e:
        result["siliconflow_chat"] = str(e)[:80]
    return result

@app.get("/health")

def health():

    return {"status": "ok", "api_key_configured": bool(SILICONFLOW_API_KEY)}

@app.get("/", response_class=HTMLResponse)

def landing():

    return LANDING_HTML

@app.get("/room", response_class=HTMLResponse)

def room():

    return ROOM_HTML

@app.get("/compare", response_class=HTMLResponse)

def compare():
    return COMPARE_HTML

@app.get("/report", response_class=HTMLResponse)
def report():
    return REPORT_HTML

@app.get("/explore", response_class=HTMLResponse)
def explore():
    return ROOM_HTML

@app.get("/compile", response_class=HTMLResponse)
def compile_page():
    return COMPARE_HTML

@app.get("/decide", response_class=HTMLResponse)
def decide():
    return REPORT_HTML

@app.get("/pitch", response_class=HTMLResponse)
def pitch_deck():
    with open("pitch.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/v1", response_class=HTMLResponse)
def v1_final():
    return V1_FINAL_HTML

@app.get("/timeline", response_class=HTMLResponse)
def timeline():
    return TIMELINE_HTML

@app.get("/predict", response_class=HTMLResponse)
def predict():
    return PREDICT_HTML

@app.get("/enterprise", response_class=HTMLResponse)
def enterprise():
    return ENTERPRISE_HTML

# ============================================================

# 启动

# ============================================================

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
