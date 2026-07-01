from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import json
import asyncio
import aiohttp
import os

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
        "emoji": "🧙",
        "color": "#7CC4FF",
        "weight": 1.3,
        "prompt": "你是一位资深的首席战略官，擅长从宏观视角判断商业机会和战略方向。请针对以下决策问题，给出明确判断（支持/反对/中立），并说明你的战略理由。"
    },
    "批判分析官": {
        "model": "deepseek-ai/DeepSeek-V3",
        "emoji": "⚔️",
        "color": "#FF7C7C",
        "weight": 1.2,
        "prompt": "你是一位严苛的批判分析官，你的职责是质疑一切、找出漏洞。请针对以下决策问题，给出明确判断（支持/反对/中立），并指出方案中的逻辑缺陷和风险。"
    },
    "风险控制官": {
        "model": "THUDM/glm-4-9b-chat",
        "emoji": "🛡️",
        "color": "#FBBF24",
        "weight": 1.1,
        "prompt": "你是一位风险控制官，擅长评估风险、计算代价。请针对以下决策问题，给出明确判断（支持/反对/中立），并评估主要风险点和可承受程度。"
    },
    "增长策略官": {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "emoji": "📈",
        "color": "#4ADE80",
        "weight": 1.2,
        "prompt": "你是一位增长策略官，擅长找到增长路径、设计实验。请针对以下决策问题，给出明确判断（支持/反对/中立），并设计增长验证路径和ROI判断。"
    },
    "洞察官": {
        "model": "internlm/internlm2_5-7b-chat",
        "emoji": "🔍",
        "color": "#38BDF8",
        "weight": 1.0,
        "prompt": "你是一位洞察官，擅长从非主流视角发现深层逻辑。请针对以下决策问题，给出明确判断（支持/反对/中立），并提出被主流视角忽略的关键洞察。"
    },
    "创新官": {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "emoji": "💡",
        "color": "#F472B6",
        "weight": 1.1,
        "prompt": "你是一位创新官，擅长破框思维、提出突破性方案。请针对以下决策问题，给出明确判断（支持/反对/中立），并提出超越常规的创新思路。"
    },
    "CEO裁决官": {
        "model": "Qwen/Qwen2-7B-Instruct",
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
<html><head><meta charset="utf-8"><title>AI Decision Room</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#0B0F1A;color:#E6E8FF;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;}
.container{text-align:center;max-width:560px;padding:40px;}
h1{font-size:42px;font-weight:700;margin-bottom:12px;}
h1 span{color:#7C5CFF;}
p{color:#8A8FA6;font-size:18px;line-height:1.6;margin-bottom:32px;}
.btn{display:inline-block;padding:16px 40px;background:#7C5CFF;color:#fff;font-size:18px;font-weight:600;border:none;border-radius:12px;cursor:pointer;text-decoration:none;transition:background .2s;}
.btn:hover{background:#6B4DE0;}
</style>
</head><body>
<div class="container">
<h1>🧠 AI <span>Decision Room</span></h1>
<p>输入你正在纠结的真实决策<br>让多个 AI 帮你拆解冲突，得到可执行结论</p>
<a class="btn" href="/room">开始决策 →</a>
</div>
</body></html>
"""

# ============================================================
# ROOM PAGE — 完整产品版（模式切换 + 次数 + 广告解锁）
# ============================================================
ROOM_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Decision Room</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0B0F1A;
  --bg-elevated: #111827;
  --border: rgba(255,255,255,0.06);
  --text: #EDF2F7;
  --text-secondary: #94A3B8;
  --text-muted: #475569;
  --purple: #6C5CE7;
  --purple-dim: rgba(108,92,231,0.12);
  --purple-glow: rgba(108,92,231,0.20);
  --red: #FF6B6B;
  --red-dim: rgba(255,107,107,0.08);
  --blue: #60A5FA;
  --green: #4ADE80;
  --radius: 12px;
  --radius-lg: 16px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background: var(--bg); color: var(--text); font-family: var(--font);
  font-size: 15px; line-height: 1.6; min-height: 100vh;
  padding: 24px; display: flex; justify-content: center; -webkit-font-smoothing: antialiased;
}
body::before {
  content:''; position:fixed; top:-30%;left:-10%; width:60%;height:60%;
  background:radial-gradient(circle at 30% 20%, rgba(108,92,231,0.06), transparent 70%);
  pointer-events:none; z-index:0;
}
.container { max-width:860px; width:100%; position:relative; z-index:1; }
.topbar {
  display:flex; justify-content:space-between; align-items:center;
  padding:8px 0 24px; border-bottom:1px solid var(--border); margin-bottom:32px;
}
.logo { display:flex; align-items:center; gap:10px; font-size:17px; font-weight:600; letter-spacing:-0.02em; color:var(--text); text-decoration:none; }
.logo-icon { width:32px; height:32px; background:var(--purple); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; }
.logo span { color:var(--text-secondary); font-weight:400; }
.badge {
  font-size:13px; color:var(--text-secondary); background:var(--bg-elevated);
  border:1px solid var(--border); padding:5px 16px; border-radius:20px;
  display:flex; align-items:center; gap:8px;
}
.badge strong { color:var(--text); font-weight:600; }
.input-area { margin-bottom:32px; }
.input-row { display:flex; gap:12px; }
.input-area input {
  flex:1; padding:14px 18px; background:var(--bg-elevated);
  border:1px solid var(--border); border-radius:var(--radius);
  color:var(--text); font-family:var(--font); font-size:15px;
  outline:none; transition:border-color 0.2s;
}
.input-area input:focus { border-color:var(--purple); box-shadow:0 0 0 3px var(--purple-dim); }
.input-area input::placeholder { color:var(--text-muted); }
.btn {
  padding:14px 28px; background:var(--purple); border:none; border-radius:var(--radius);
  color:#fff; font-weight:600; font-size:15px; cursor:pointer;
  transition:all 0.2s; white-space:nowrap;
}
.btn:hover { background:#5A4BD1; transform:translateY(-1px); box-shadow:0 8px 30px var(--purple-glow); }
.btn:disabled { opacity:0.35; cursor:not-allowed; transform:none; box-shadow:none; }
.ad-banner {
  display:none; align-items:center; justify-content:space-between;
  padding:14px 20px; background:var(--red-dim);
  border:1px solid rgba(255,107,107,0.12); border-radius:var(--radius);
  margin-bottom:24px; flex-wrap:wrap; gap:16px;
}
.ad-banner.active { display:flex; }
.ad-banner .ad-text { font-size:14px; color:var(--text-secondary); }
.ad-banner .ad-text strong { color:var(--red); }
.ad-banner .ad-btn {
  padding:8px 20px; background:var(--red); border:none; border-radius:8px;
  color:#fff; font-weight:600; font-size:13px; cursor:pointer;
}
.ad-banner .ad-btn:hover { background:#E05555; }
.section-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted); margin-bottom:16px; }
.debate-flow { margin-bottom:32px; }
.flow-item {
  display:flex; gap:16px; padding:16px 0;
  border-bottom:1px solid rgba(255,255,255,0.04);
  opacity:0; transform:translateX(-8px);
  transition:opacity 0.6s ease, transform 0.4s ease;
}
.flow-item.active { opacity:1; transform:translateX(0); }
.flow-item.done { opacity:0.85; transform:translateX(0); }
.flow-item .avatar {
  width:44px; height:44px; border-radius:50%;
  display:flex; align-items:center; justify-content:center; font-size:20px;
  flex-shrink:0; background:rgba(255,255,255,0.04); border:1px solid var(--border);
}
.flow-item .content { flex:1; min-width:0; }
.flow-item .content .meta {
  display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:4px;
}
.flow-item .content .meta .name { font-weight:600; font-size:15px; color:var(--text); }
.flow-item .content .meta .title { font-size:12px; color:var(--text-muted); }
.stance-tag {
  font-size:11px; font-weight:600; padding:2px 12px; border-radius:12px;
}
.stance-tag.support { background:rgba(74,222,128,0.12); color:var(--green); }
.stance-tag.oppose { background:rgba(255,107,107,0.12); color:var(--red); }
.stance-tag.neutral { background:rgba(255,255,255,0.04); color:var(--text-muted); }
.flow-item .content .text {
  font-size:15px; color:var(--text-secondary); line-height:1.7; min-height:24px;
}
.flow-item .content .text .cursor {
  display:inline-block; width:2px; height:18px; background:var(--purple);
  animation:blink 0.8s step-end infinite; vertical-align:text-bottom; margin-left:2px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.status-dot {
  width:10px; height:10px; border-radius:50%; flex-shrink:0; margin-top:17px;
  transition:all 0.3s;
}
.status-dot.waiting { background:#2A3347; }
.status-dot.speaking { background:var(--purple); animation:pulse-dot 1s ease-in-out infinite; }
.status-dot.done { background:var(--green); }
@keyframes pulse-dot {
  0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)}
}
.conflict-section { margin-bottom:32px; }
.conflict-bar-group {
  display:flex; flex-direction:column; gap:16px;
  background:var(--bg-elevated); border-radius:var(--radius-lg);
  padding:24px; border:1px solid var(--border);
}
.conflict-item { display:flex; flex-direction:column; gap:4px; }
.conflict-label { display:flex; justify-content:space-between; font-size:13px; color:var(--text-secondary); }
.conflict-label .left { color:var(--blue); }
.conflict-label .right { color:var(--red); }
.conflict-track { height:4px; background:rgba(255,255,255,0.06); border-radius:4px; overflow:hidden; display:flex; }
.conflict-track .fill { height:100%; transition:width 0.8s ease; }
.conflict-track .fill.left { background:var(--blue); }
.conflict-track .fill.right { background:var(--red); }
.conflict-meta { display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted); margin-top:2px; }
.ceo-section { margin-top:32px; padding-top:24px; border-top:1px solid var(--border); }
.ceo-card {
  background:rgba(108,92,231,0.04); border:1px solid rgba(108,92,231,0.12);
  border-radius:var(--radius-lg); padding:24px 28px;
}
.ceo-card .ceo-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:var(--purple); margin-bottom:6px; }
.ceo-card .ceo-decision { font-size:28px; font-weight:700; color:var(--text); letter-spacing:-0.02em; }
.ceo-card .ceo-confidence { font-size:14px; color:var(--text-secondary); margin-top:4px; }
.ceo-card .ceo-divider { height:1px; background:var(--border); margin:16px 0; }
.ceo-card .ceo-reason { font-size:14px; color:var(--text-secondary); line-height:1.7; }
.ceo-card .ceo-steps { margin-top:12px; }
.ceo-card .ceo-steps .step-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; color:var(--text-muted); margin-bottom:6px; }
.ceo-card .ceo-steps ul { list-style:none; padding:0; }
.ceo-card .ceo-steps ul li { font-size:14px; color:var(--text-secondary); padding:4px 0 4px 20px; position:relative; }
.ceo-card .ceo-steps ul li::before { content:'\u25B9'; position:absolute; left:0; color:var(--purple); }
.ceo-card .ceo-risk { margin-top:12px; display:inline-flex; align-items:center; gap:8px; font-size:13px; color:var(--red); background:var(--red-dim); padding:4px 14px; border-radius:20px; }
.empty-state { text-align:center; padding:48px 24px; color:var(--text-muted); font-size:14px; }
.empty-state .icon { font-size:32px; margin-bottom:16px; }
@media (max-width:640px) {
  body { padding:16px; }
  .topbar { flex-direction:column; align-items:flex-start; gap:16px; }
  .badge { align-self:flex-start; }
  .input-row { flex-direction:column; }
  .btn { width:100%; justify-content:center; }
  .ceo-card .ceo-decision { font-size:22px; }
  .ceo-card { padding:16px 18px; }
}
</style>
</head>
<body>
<div class="container">

<header class="topbar">
  <a class="logo" href="/"><span class="logo-icon">&#x1F9E0;</span> AI <span>Decision Room</span></a>
  <div class="badge"><span>今日剩余</span> <strong id="remainingCount">10</strong> <span>次</span></div>
</header>

<div class="ad-banner" id="adBanner">
  <span class="ad-text">&#x1F4FA; 今日免费次数已用完，看 <strong>15秒广告</strong> 解锁 <strong>5次</strong></span>
  <button class="ad-btn" id="adBtn">&#x25B6; 观看广告解锁</button>
</div>

<div class="input-area">
  <div class="input-row">
    <input id="topicInput" placeholder="输入决策议题，例如：蕲艾五官灸是否要做小红书投放？">
    <button class="btn" id="runBtn">&#x1F9E0; 召开董事会</button>
  </div>
</div>

<div class="debate-flow">
  <div class="section-label">&#x1F4AC; 董事会辩论</div>
  <div id="agentGrid"><div class="empty-state"><div class="icon">&#x1F4A1;</div><span>输入议题后，AI 董事会将依次发言</span></div></div>
</div>

<div class="conflict-section">
  <div class="section-label">&#x2694;&#xFE0F; 核心冲突</div>
  <div id="conflictContainer" class="conflict-bar-group">
    <div class="empty-state"><div class="icon">&#x23F3;</div><span>运行分析后显示冲突结构</span></div>
  </div>
</div>

<div class="ceo-section">
  <div class="section-label">&#x1F451; CEO 裁决</div>
  <div id="decisionContainer" class="ceo-card">
    <div class="ceo-label">最终决策</div>
    <div style="color:var(--text-muted);font-size:14px;">等待辩论结束&hellip;</div>
  </div>
</div>

</div>

<script>
// === 配置 ===
const BOARD = [
  {id:'strategy',  icon:'&#x1F9D9;', name:'战略官',   title:'CSO',  color:'#7CC4FF', stance:'support'},
  {id:'critic',   icon:'&#x2694;&#xFE0F;', name:'批判官', title:'CRO',  color:'#FF7C7C', stance:'oppose'},
  {id:'risk',     icon:'&#x1F6E1;&#xFE0F;', name:'风控官',  title:'COO',  color:'#FBBF24', stance:'neutral'},
  {id:'growth',   icon:'&#x1F4C8;',  name:'增长官',   title:'CGO',  color:'#4ADE80', stance:'support'},
  {id:'insight',  icon:'&#x1F50D;',  name:'洞察官',   title:'CCO',  color:'#60A5FA', stance:'support'},
  {id:'innovation', icon:'&#x1F680;', name:'创新官', title:'CIO',  color:'#A78BFA', stance:'support'},
  {id:'ceo',      icon:'&#x1F451;',  name:'CEO裁决官', title:'CEO',  color:'#7C5CFF', stance:'support'},
];

const STATE = {
  remaining: 10,
  isAdPlaying: false,
  userId: localStorage.getItem('decision_room_user_id') || 'default',
};

const $ = id => document.getElementById(id);
const topicInput = $('topicInput');
const runBtn = $('runBtn');
const agentGrid = $('agentGrid');
const conflictContainer = $('conflictContainer');
const decisionContainer = $('decisionContainer');
const remainingEl = $('remainingCount');
const adBanner = $('adBanner');
const adBtn = $('adBtn');

// === 次数管理 ===
function loadState(){
  try{
    const d = JSON.parse(localStorage.getItem('decision_room_'+STATE.userId));
    if(d && d.date === new Date().toDateString()) STATE.remaining = d.remaining;
    else { STATE.remaining = 10; saveState(); }
  } catch(e) { STATE.remaining = 10; saveState(); }
  updateUI();
}
function saveState(){
  localStorage.setItem('decision_room_'+STATE.userId, JSON.stringify({
    date: new Date().toDateString(), remaining: STATE.remaining,
  }));
}
function useOne(){
  if(STATE.remaining <= 0) return false;
  STATE.remaining -= 1; saveState(); updateUI(); return true;
}
function updateUI(){
  remainingEl.textContent = STATE.remaining;
  runBtn.disabled = STATE.remaining <= 0;
  runBtn.style.opacity = STATE.remaining <= 0 ? '0.35' : '1';
  adBanner.classList.toggle('active', STATE.remaining <= 0);
}
function unlockByAd(){
  if(STATE.isAdPlaying) return;
  STATE.isAdPlaying = true; adBtn.disabled = true; adBtn.textContent = '&#x23F3; 15s';
  let s = 15;
  const iv = setInterval(() => {
    s -= 1; adBtn.textContent = '&#x23F3; '+s+'s';
    if(s <= 0){
      clearInterval(iv);
      STATE.remaining = Math.min(10, STATE.remaining + 5);
      STATE.isAdPlaying = false; saveState(); updateUI();
      adBtn.disabled = false; adBtn.textContent = '&#x25B6; 观看广告解锁';
    }
  }, 1000);
}

// === 流式辩论 ===
function playDebateFlow(agents, onDone){
  if(!agents || agents.length === 0){ onDone(); return; }
  let html = '';
  agents.forEach((a, i) => {
    const m = BOARD[i] || {};
    const stance = a.stance || 'neutral';
    const label = stance === 'support' ? '支持' : stance === 'oppose' ? '反对' : '中立';
    html += '<div class="flow-item" id="flow-'+i+'">'
      + '<div class="avatar">'+(m.icon||'&#x1F9E0;')+'</div>'
      + '<div class="content">'
      + '<div class="meta">'
      + '<span class="name">'+(m.name||a.role||'AI')+'</span>'
      + '<span class="title">'+(m.title||'')+'</span>'
      + '<span class="stance-tag '+stance+'">'+label+'</span>'
      + '</div>'
      + '<div class="text" id="text-'+i+'"></div>'
      + '</div>'
      + '<span class="status-dot waiting" id="dot-'+i+'"></span>'
      + '</div>';
  });
  agentGrid.innerHTML = html;

  let idx = 0;
  function next(){
    if(idx >= agents.length){ onDone(); return; }
    const item = $('flow-'+idx);
    const textEl = $('text-'+idx);
    const dot = $('dot-'+idx);
    const agent = agents[idx];
    item.className = 'flow-item active';
    item.style.opacity = '1';
    dot.className = 'status-dot speaking';
    const text = agent.reason || agent.output || '—';
    let ci = 0;
    textEl.textContent = '';
    const ti = setInterval(() => {
      if(ci < text.length){ textEl.textContent += text[ci]; ci++; }
      else {
        clearInterval(ti);
        item.className = 'flow-item done';
        dot.className = 'status-dot done';
        idx++;
        setTimeout(next, 300);
      }
    }, 20);
  }
  setTimeout(next, 200);
}

function renderConflicts(conflicts){
  if(!conflicts || conflicts.length === 0){
    conflictContainer.innerHTML = '<div class="empty-state"><div class="icon">&#x2705;</div><span>未检测到明显冲突</span></div>';
    return;
  }
  let html = '';
  conflicts.forEach(c => {
    const sev = c.severity_pct || 50;
    html += '<div class="conflict-item">'
      + '<div class="conflict-label"><span class="left">'+(c.left||'支持方')+'</span><span class="right">'+(c.right||'反对方')+'</span></div>'
      + '<div class="conflict-track"><div class="fill left" style="width:'+sev+'%;"></div><div class="fill right" style="width:'+(100-sev)+'%;"></div></div>'
      + '<div class="conflict-meta"><span>'+(c.title||'冲突点')+'</span><span>强度 '+sev+'%</span></div>'
      + '</div>';
  });
  conflictContainer.innerHTML = html;
}

function renderDecision(data){
  if(!data || !data.decision){
    decisionContainer.innerHTML = '<div class="ceo-label">最终决策</div><div style="color:var(--text-muted);font-size:14px;">等待辩论结束&hellip;</div>';
    return;
  }
  const st = data.steps || ['规划执行路径'];
  decisionContainer.innerHTML = '<div class="ceo-label">最终决策</div>'
    + '<div class="ceo-decision">'+data.decision+'</div>'
    + '<div class="ceo-confidence">置信度 '+(data.confidence||78)+'%</div>'
    + '<div class="ceo-divider"></div>'
    + '<div class="ceo-reason">'+(data.rationale||'基于多模型冲突分析，综合决策。')+'</div>'
    + '<div class="ceo-steps"><div class="step-label">执行路径</div>'
    + '<ul>'+st.map(s => '<li>'+s+'</li>').join('')+'</ul></div>'
    + '<div class="ceo-risk">&#x26A0; '+(data.risk||'请关注执行风险')+'</div>';
}

// === Mock 数据（适配后端 7-agent 格式） ===
const MOCK_AGENTS = [
  {stance:'support', reason:'三伏天是养生心智最强时期，竞品已验证路径，建议小步快跑抢占先机。'},
  {stance:'oppose', reason:'3万预算在小红书测试门槛不足，竞品已占据心智，此时进入成本过高。'},
  {stance:'neutral', reason:'风险可控但需谨慎。建议设5000元止损线，48h内完成验证。'},
  {stance:'support', reason:'赛道的获客成本正上升，现在是卡位最后窗口。建议用5000元做AB测试。'},
  {stance:'support', reason:'小红书养生人群增长43%，内容测试成本低于3千元即可验证，值得尝试。'},
  {stance:'support', reason:'可结合AI生成测评内容+UGC裂变，以极低成本完成冷启动，建议执行。'},
  {stance:'support', reason:'综合6位董事意见——4票支持、1票反对、1票中立，建议投入8000元做2周内容测试。'},
];

const MOCK_CONFLICTS = [
  {title:'预算判断分歧', left:'战略官 3万足够', right:'批判官 3万不足', severity_pct:82},
  {title:'时间窗口判断', left:'增长官 必须7月前', right:'风控官 可延后', severity_pct:65},
  {title:'渠道策略分歧', left:'洞察官 小红书低成本', right:'批判官 ROI不确定', severity_pct:48},
];

const MOCK_DECISION = {
  decision: '小规模测试（建议8000元预算）',
  confidence: 82,
  rationale: '6位董事投票：4票支持、1票反对、1票中立。市场存在真实需求信号，风险可控。',
  steps: ['筛选3个KOC账号询价','制作2条AI+真人内容内容','投入8000元跑2周','第7天复盘，ROI>1.0则追加'],
  risk: '初期转化波动较大，内容质量决定ROI上限。需预留2万元止损线。',
};

async function runFreeDecision(){
  if(!useOne()) return;
  runBtn.disabled = true;
  runBtn.textContent = '&#x23F3; 辩论中…';
  decisionContainer.innerHTML = '<div class="ceo-label">最终决策</div><div style="color:var(--text-muted);font-size:14px;">&#x23F3; AI 董事会正在辩论&hellip;</div>';
  conflictContainer.innerHTML = '<div class="empty-state"><div class="icon">&#x23F3;</div><span>辩论中&hellip;</span></div>';

  try{
    const payload = {topic: topicInput.value.trim() || '蕲艾五官灸是否做小红书投放', background: ''};
    const res = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    if(data.agents){
      playDebateFlow(data.agents, () => {
        if(data.conflicts) renderConflicts(data.conflicts);
        if(data.decision) renderDecision(data.decision);
        else renderDecision(MOCK_DECISION);
      });
    } else { fallback(); }
  } catch(e){ fallback(); }

  function fallback(){
    playDebateFlow(MOCK_AGENTS, () => {
      renderConflicts(MOCK_CONFLICTS);
      renderDecision(MOCK_DECISION);
    });
  }

  runBtn.disabled = false;
  runBtn.textContent = '&#x1F9E0; 召开董事会';
  updateUI();
}

// === 初始化 ===
loadState();
runBtn.addEventListener('click', runFreeDecision);
adBtn.addEventListener('click', unlockByAd);
topicInput.addEventListener('keydown', e => { if(e.key === 'Enter') runFreeDecision(); });

// 初始展示
playDebateFlow(MOCK_AGENTS, () => {
  renderConflicts(MOCK_CONFLICTS);
  renderDecision(MOCK_DECISION);
});
</script>
</body>
</html>"""

# ════════════════════════════════════════════════════════════
# V1.2 冲突决策引擎
# ════════════════════════════════════════════════════════════

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
async def call_siliconflow(model_id: str, prompt: str, role_name: str, system_prompt: str) -> dict:
    """调用硅基流动 API"""
    if not SILICONFLOW_API_KEY:
        return {"role": role_name, "model": model_id, "stance": "—", "reason": "API Key 未配置"}

    payload = {
        "model": model_id,
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
                if resp.status != 200:
                    return {"role": role_name, "model": model_id, "stance": "—", "reason": "API 错误: " + str(resp.status)}
                data = await resp.json()
                raw = data["choices"][0]["message"]["content"].strip()
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
    except Exception as e:
        return {"role": role_name, "model": model_id, "stance": "—", "reason": "请求失败: " + str(e)}


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
                data = await resp.json()
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
    body = await request.json()
    topic = body.get("topic", "")

    # 并行调用所有非CEO角色
    tasks = []
    for role_name in DEBATE_ROLES:
        member = BOARD_MEMBERS[role_name]
        tasks.append(call_siliconflow(member["model"], topic, role_name, member["prompt"]))

    results = await asyncio.gather(*tasks)

    # 调用CEO裁决官（基于前6位结果）
    ceo_result = await call_ceo(results, topic)

    # 全部 agents = 6位董事 + CEO
    all_agents = results + [ceo_result]

    # ════════════════════════════════════════════════
    # V1.2 冲突决策引擎
    # ════════════════════════════════════════════════
    # Step 1: 语义级冲突聚类
    conflicts = _cluster_conflicts(results)

    # Step 2: 决策评分系统
    decision_score = _calculate_decision_score(results, conflicts)

    # Step 3: 结构化CEO裁决
    ceo_verdict = _ceo_structured_verdict(results, conflicts, decision_score)

    # Step 4: 整合返回
    support_count = sum(1 for r in results if r["stance"] == "支持")
    oppose_count = sum(1 for r in results if r["stance"] == "反对")

    decision = {
        "decision": ceo_verdict["decision"],
        "confidence": ceo_verdict["confidence"],
        "rationale": f"AI董事会7位董事辩论：{support_count}位支持（加权{decision_score['support_weight']}），{oppose_count}位反对（加权{decision_score['oppose_weight']}）。\n{ceo_verdict['reasoning']}",
        "steps": ceo_verdict["steps"],
        "risk": ceo_verdict["risk"]
    }

    return {
        "agents": all_agents,
        "conflicts": conflicts,
        "decision": decision
    }

# ============================================================
# ROUTES
# ============================================================
@app.get("/health")
def health():
    return {"status": "ok", "api_key_configured": bool(SILICONFLOW_API_KEY)}

@app.get("/", response_class=HTMLResponse)
def landing():
    return LANDING_HTML

@app.get("/room", response_class=HTMLResponse)
def room():
    return ROOM_HTML

# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
