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

        "model": "Qwen/Qwen2-7B-Instruct",

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

        "model": "deepseek-ai/DeepSeek-V2.5",

        "emoji": "🔍",

        "color": "#38BDF8",

        "weight": 1.0,

        "prompt": "你是一位洞察官，擅长从非主流视角发现深层逻辑。请针对以下决策问题，给出明确判断（支持/反对/中立），并提出被主流视角忽略的关键洞察。"

    },

    "创新官": {

        "model": "Qwen/Qwen2.5-72B-Instruct",

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

<a class="btn" href="/room">AI 董事会 →</a>
<a class="btn" href="/compare" style="background:#22c55e;margin-left:12px;">手动编译器 →</a>

</div>

</body></html>

"""

# ============================================================

# ============================================================
# ============================================================
# ============================================================
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
    <span class="brand">Decision OS</span>
    <span class="sub" style="margin-left:8px;">董事会操作系统 v5</span>
  </div>
  <div class="status">
    <span class="dot" id="statusDot"></span>
    <span id="statusText">空闲</span>
  </div>
</div>

<div class="container">

  <!-- ═══ 1. 决策输入 ═══ -->
  <div class="section"><span>1</span> 决策输入 <span class="sec-line"></span></div>
  <div class="card input-card">
    <textarea id="topicInput" placeholder="在此输入你的决策问题，AI 董事会将为你分析…&#10;&#10;例如：&#10;• 是否要进入五官灸健康赛道？&#10;• 新产品应该先做小红书还是抖音？&#10;• 第三季度预算应该投品牌还是效果？"></textarea>
    <div class="actions">
      <button id="runBtn">▶ 执行分析</button>
    </div>
  </div>

  <!-- 错误 -->
  <div class="error-card" id="errorCard"></div>

  <!-- ═══ 2. 董事会执行 ═══ -->
  <div class="section"><span>2</span> 董事会执行 <span class="sec-line"></span></div>
  <div class="card" id="boardCard">
    <div class="board-grid" id="boardGrid"></div>
  </div>

  <!-- ═══ 3. 冲突时间线 ═══ -->
  <div class="section"><span>3</span> 冲突时间线 <span class="sec-line"></span></div>
  <div class="card">
    <div id="timelineContainer">
      <div class="empty-state" id="timelineEmpty">
        <div class="icon">🧠</div>
        <div>等待董事会分析完成后生成</div>
      </div>
    </div>
  </div>

  <!-- ═══ 4. 决策账本 ═══ -->
  <div class="section"><span>4</span> 决策账本 <span class="sec-line"></span></div>
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
    <div class="f-body" id="finalBody"></div>
    <div class="f-meta">
      <span id="finalConfidence">置信度 —</span>
      <span id="finalRisk">风险 —</span>
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
const timelineContainer = document.getElementById('timelineContainer');
const timelineEmpty = document.getElementById('timelineEmpty');
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
  boardGrid.innerHTML = '';
  BOARD.forEach((m, i) => {
    const div = document.createElement('div');
    div.className = 'member';
    div.id = 'member-' + m.id;
    div.innerHTML = `
      <div class="left">
        <span class="icon">${m.icon}</span>
        <span class="name">${m.name}</span>
        <span class="title">${m.title}</span>
      </div>
      <div class="right">
        <span class="status-text waiting" id="status-${m.id}">⏳ waiting</span>
      </div>
    `;
    boardGrid.appendChild(div);
  });
}

// 设置成员状态
function setMemberStatus(id, status, tagText, tagCls) {
  const el = document.getElementById('member-' + id);
  if (!el) return;
  el.className = 'member ' + (status === 'running' ? 'running' : status === 'done' ? 'done' : status === 'error' ? 'error' : '');
  const st = document.getElementById('status-' + id);
  if (!st) return;
  const statusMap = {
    waiting: '⏳ 等待中',
    thinking: '⏳ 思考中…',
    done: '✅ 完成',
    error: '❌ 出错'
  };
  st.textContent = statusMap[status] || status;
  st.className = 'status-text ' + status;
  if (tagText && tagCls) {
    st.innerHTML = '<span class="tag ' + tagCls + '">' + tagText + '</span>';
  }
}

// ─── 添加时间线事件 ───
function addTimelineEvent(icon, name, stance, reason, weight) {
  timelineEmpty.style.display = 'none';
  const div = document.createElement('div');
  div.className = 'event';
  const st = stance === '支持' ? 'support' : stance === '反对' ? 'oppose' : 'neutral';
  div.innerHTML = `
    <div class="ev-header">
      <span class="dot ${st}"></span>
      <b>${icon} ${name}</b>
      <span class="tag ${st}" style="font-size:10px;padding:1px 6px;border-radius:6px;display:inline-block;font-weight:600;">${stance || '中立'}</span>
      ${weight ? '<span style="font-size:11px;color:#6b7280;">weight ×' + weight + '</span>' : ''}
    </div>
    <div class="ev-reason">${reason}</div>
  `;
  timelineContainer.appendChild(div);
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
  timelineContainer.innerHTML = '';
  ledgerContainer.innerHTML = '';
  finalContainer.classList.remove('open');
  timelineEmpty.style.display = 'block';
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

    // 执行阶段动画
    for (let i = 0; i < Math.min(agents.length, BOARD.length); i++) {
      const agent = agents[i];
      const member = BOARD[i];
      const isError = !agent.stance || agent.stance === '—' ||
        (agent.reason && (agent.reason.startsWith('API 错误') || agent.reason.startsWith('请求失败')));

      setMemberStatus(member.id, 'thinking');
      setStatus(member.name + ' 分析中…', 'running');
      await sleep(800);

      if (isError) {
        setMemberStatus(member.id, 'error');
      } else {
        setMemberStatus(member.id, 'done', agent.stance, agent.stance === '支持' ? 'support' : agent.stance === '反对' ? 'oppose' : 'neutral');
      }
    }

    // 构建时间线
    setStatus('构建冲突时间线', 'running');
    await sleep(400);
    
    for (let i = 0; i < Math.min(agents.length, BOARD.length); i++) {
      const agent = agents[i];
      const member = BOARD[i];
      const isError = !agent.stance || agent.stance === '—' ||
        (agent.reason && (agent.reason.startsWith('API 错误') || agent.reason.startsWith('请求失败')));
      const text = agent.reason || '';
      const displayText = isError ? (text.includes('403') ? '模型暂不可用' : text) : text.slice(0, 200);
      addTimelineEvent(member.icon, member.name, agent.stance || '—', displayText, member.weight);
      await sleep(100);
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
      
      // 更新CEO状态
      const ceoMember = BOARD[BOARD.length - 1];
      if (ceoMember) {
        const ceoAgent = agents.length > BOARD.length - 1 ? agents[BOARD.length - 1] : null;
        const ceoStance = ceoAgent ? ceoAgent.stance : null;
        setMemberStatus(ceoMember.id, 'done', decision.decision || 'done', 'support');
      }
    }

    setStatus('✅ 分析完成', 'done');

  } catch (err) {
    showError(err.message || '请求失败');
    setStatus('❌ error', '');
    // 标记所有成员为错误
    BOARD.forEach(m => setMemberStatus(m.id, 'error'));
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

console.log('🧠 Decision OS V5 已加载');
console.log('5层架构：输入 → 执行 → 时间线 → 账本 → 裁决');
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

                data = await _parse_json_resp(resp)

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
            tasks.append(call_siliconflow(member["model"], topic, role_name, member["prompt"]))

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
# SYSTEM 2 PAGE HTML
# ============================================================
COMPARE_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Decision Compiler · System 2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:#0b0f19;
  color:#e5e7eb;
}
.header{
  padding:16px 28px;
  border-bottom:1px solid #1f2937;
  display:flex;justify-content:space-between;align-items:center;
  background:rgba(11,15,25,0.95);position:sticky;top:0;z-index:20;
}
.header .brand{
  font-size:17px;font-weight:700;
  background:linear-gradient(135deg,#34d399,#22c55e);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.header .sub{font-size:12px;color:#6b7280;margin-left:6px;}
.header .nav{display:flex;gap:12px;align-items:center;}
.header .nav a{color:#9ca3af;font-size:13px;text-decoration:none;padding:6px 14px;border-radius:8px;transition:all .15s;}
.header .nav a:hover{color:#e5e7eb;background:#1f2937;}
.header .nav a.active{color:#22c55e;background:rgba(34,197,94,0.08);}
.container{max-width:960px;margin:0 auto;padding:28px 28px 60px;}

/* ─── 页面标题 ─── */
.page-title{margin-bottom:24px;}
.page-title h1{font-size:22px;font-weight:600;color:#e5e7eb;}
.page-title p{font-size:13px;color:#6b7280;margin-top:4px;line-height:1.6;}

/* ─── 卡片 ─── */
.card{
  background:#111827;border:1px solid #1f2937;border-radius:14px;
  padding:24px;margin-bottom:16px;
}

/* ─── 粘贴区 ─── */
.paste-area{display:flex;flex-direction:column;gap:12px;}
.paste-row{
  display:flex;gap:12px;align-items:flex-start;
  opacity:1;transition:opacity .3s;
}
.paste-row .model-tag{
  flex-shrink:0;width:110px;
}
.paste-row .model-tag select{
  width:100%;padding:10px 10px;
  background:#0f172a;border:1px solid #1f2937;border-radius:8px;
  color:#e5e7eb;font-size:13px;outline:none;cursor:pointer;
}
.paste-row .model-tag select:focus{border-color:#22c55e;}
.paste-row textarea{
  flex:1;padding:12px 14px;
  background:#0f172a;border:1px solid #1f2937;border-radius:8px;
  color:#e5e7eb;font-size:13px;font-family:inherit;
  resize:vertical;min-height:80px;outline:none;line-height:1.7;
}
.paste-row textarea:focus{border-color:#22c55e;box-shadow:0 0 0 2px rgba(34,197,94,0.08);}
.paste-row textarea::placeholder{color:#4a5268;}
.paste-row .remove-btn{
  flex-shrink:0;width:32px;height:32px;margin-top:4px;
  border:none;border-radius:8px;background:#1f2937;color:#6b7280;
  font-size:16px;cursor:pointer;transition:all .15s;display:flex;align-items:center;justify-content:center;
}
.paste-row .remove-btn:hover{background:#374151;color:#ef4444;}

/* ─── 操作栏 ─── */
.actions-bar{
  display:flex;gap:12px;align-items:center;margin-top:8px;
}
.actions-bar .btn{
  padding:10px 24px;border:none;border-radius:10px;
  font-weight:600;font-size:13px;cursor:pointer;transition:all .15s;
}
.btn-primary{background:#22c55e;color:#000;}
.btn-primary:hover{background:#16a34a;}
.btn-primary:disabled{opacity:0.3;cursor:not-allowed;}
.btn-secondary{background:#1f2937;color:#e5e7eb;}
.btn-secondary:hover{background:#374151;}
.btn-ghost{background:transparent;color:#6b7280;border:1px dashed #374151;}
.btn-ghost:hover{background:#1f2937;color:#9ca3af;}
.actions-bar .hint{font-size:12px;color:#4a5268;margin-left:auto;}

/* ─── 加载动画 ─── */
.loading-section{display:none;text-align:center;padding:40px 0;}
.loading-section.open{display:block;}
.loading-spinner{
  width:36px;height:36px;border:3px solid #1f2937;
  border-top-color:#22c55e;border-radius:50%;
  animation:spin 0.8s linear infinite;margin:0 auto 16px;
}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-section .msg{font-size:14px;color:#9ca3af;}
.loading-section .sub-msg{font-size:12px;color:#4a5268;margin-top:4px;}

/* ─── 结果区 ─── */
.results-section{display:none;}
.results-section.open{display:block;}

.result-block{margin-bottom:20px;}
.result-block .block-title{
  font-size:13px;font-weight:600;color:#9ca3af;margin-bottom:10px;
  display:flex;align-items:center;gap:8px;
}
.result-block .block-title .badge{
  font-size:10px;padding:2px 8px;border-radius:6px;
}
.badge-green{background:rgba(34,197,94,0.12);color:#22c55e;}
.badge-yellow{background:rgba(251,191,36,0.12);color:#fbbf24;}
.badge-red{background:rgba(239,68,68,0.12);color:#ef4444;}
.badge-blue{background:rgba(59,130,246,0.12);color:#3b82f6;}

/* 共识点 */
.consensus-item{
  padding:12px 14px;background:rgba(34,197,94,0.04);
  border:1px solid rgba(34,197,94,0.1);border-radius:10px;
  margin-bottom:8px;display:flex;align-items:flex-start;gap:10px;
}
.consensus-item .dot{
  width:8px;height:8px;border-radius:50%;background:#22c55e;
  margin-top:4px;flex-shrink:0;
}
.consensus-item .text{font-size:13px;line-height:1.6;color:#d1d5db;}
.consensus-item .conf{
  font-size:11px;color:#6b7280;margin-top:2px;
}

/* 分歧点 */
.dissent-item{
  border:1px solid rgba(251,191,36,0.15);
  background:rgba(251,191,36,0.03);
  border-radius:10px;padding:14px;margin-bottom:10px;
}
.dissent-item .d-header{
  display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;
}
.dissent-item .d-header .topic{
  font-size:13px;font-weight:600;color:#e5e7eb;
}
.dissent-item .d-body{
  display:flex;flex-direction:column;gap:6px;
}
.dissent-item .position{
  display:flex;gap:8px;align-items:flex-start;
  padding:6px 8px;background:#0f172a;border-radius:6px;
}
.dissent-item .position .plabel{
  font-size:11px;font-weight:600;padding:2px 8px;
  border-radius:4px;flex-shrink:0;margin-top:1px;
}
.plabel-a{background:rgba(59,130,246,0.12);color:#3b82f6;}
.plabel-b{background:rgba(249,115,22,0.12);color:#f97316;}
.plabel-c{background:rgba(139,92,246,0.12);color:#8b5cf6;}
.plabel-d{background:rgba(236,72,153,0.12);color:#ec4899;}
.plabel-e{background:rgba(14,165,233,0.12);color:#0ea5e9;}
.dissent-item .position .pstance{font-size:12px;color:#9ca3af;flex-shrink:0;}
.dissent-item .position .psummary{font-size:12px;color:#6b7280;}

/* 冲突来源 */
.source-item{
  padding:10px 12px;background:#0f172a;
  border-left:3px solid #f59e0b;border-radius:0 8px 8px 0;
  margin-bottom:8px;
}
.source-item .s-title{font-size:13px;font-weight:500;color:#e5e7eb;}
.source-item .s-detail{font-size:12px;color:#6b7280;margin-top:3px;line-height:1.5;}

/* 最终建议 */
.recommendation-card{
  background:linear-gradient(135deg,#064e3b,#0f172a);
  border:1px solid #22c55e;border-radius:14px;
  padding:20px;margin-bottom:16px;
}
.recommendation-card .rc-title{
  font-size:13px;font-weight:700;color:#22c55e;margin-bottom:8px;
  display:flex;align-items:center;gap:8px;
}
.recommendation-card .rc-body{
  font-size:14px;color:#d1d5db;line-height:1.7;
}
.recommendation-card .rc-meta{
  font-size:12px;color:#6b7280;margin-top:12px;
  display:flex;gap:16px;
}

/* 交叉验证 */
.cross-validate{
  padding:12px 14px;background:rgba(99,102,241,0.04);
  border:1px solid rgba(99,102,241,0.1);border-radius:10px;margin-bottom:16px;
}
.cross-validate .cv-title{
  font-size:12px;font-weight:600;color:#6366f1;margin-bottom:6px;
}
.cross-validate .cv-body{font-size:12px;color:#6b7280;line-height:1.5;}

/* 空状态 */
.empty-state{
  text-align:center;color:#4a5268;padding:32px 0;
}
.empty-state .icon{font-size:28px;margin-bottom:6px;opacity:0.4;}
.empty-state .e-title{font-size:14px;color:#6b7280;margin-bottom:4px;}
.empty-state .e-sub{font-size:12px;}

/* 错误 */
.error-card{
  background:rgba(239,68,68,0.04);border:1px solid rgba(239,68,68,0.15);
  border-radius:10px;padding:12px;font-size:13px;color:#ef4444;
  display:none;margin-bottom:12px;
}
.error-card.open{display:block;}

/* 入口导航 */
.system-nav{
  display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap;
}
.system-nav .sn-item{
  padding:8px 16px;border-radius:10px;font-size:12px;font-weight:500;
  border:1px solid #1f2937;color:#6b7280;text-decoration:none;transition:all .15s;
}
.system-nav .sn-item:hover{border-color:#374151;color:#9ca3af;}
.system-nav .sn-item.active{border-color:#22c55e;color:#22c55e;background:rgba(34,197,94,0.06);}

/* 响应式 */
@media(max-width:640px){
  .container{padding:16px 14px;}
  .paste-row{flex-direction:column;}
  .paste-row .model-tag{width:100%;}
  .paste-row .remove-btn{align-self:flex-end;}
}
</style>
</head>
<body>

<div class="header">
  <div>
    <span class="brand">Decision Compiler</span>
    <span class="sub">System 2 · 多模型意见手动编译器</span>
  </div>
  <div class="nav">
    <a href="/room">Board</a>
    <a href="/compare" class="active">Compiler</a>
  </div>
</div>

<div class="container">

  <div class="page-title">
    <h1>🧠 多模型认知编译器</h1>
    <p>把不同 AI 的回答粘贴到这里。系统会自动找出共识、标出分歧、分析冲突来源，帮你从多个声音中收敛出可执行的结论。</p>
  </div>

  <!-- 系统选择 -->
  <div class="system-nav">
    <a href="/room" class="sn-item">⚡ System 1 · AI 董事会</a>
    <a href="/compare" class="sn-item active">🧩 System 2 · 手动编译器</a>
  </div>

  <!-- 粘贴区 -->
  <div class="card" id="pasteCard">
    <div class="paste-area" id="pasteArea"></div>
    <div class="actions-bar">
      <button class="btn btn-secondary" id="addEntryBtn">+ 添加一个模型回答</button>
      <button class="btn btn-primary" id="analyzeBtn">▶ 分析认知结构</button>
      <span class="hint" id="entryHint">至少需要 2 个模型回答</span>
    </div>
  </div>

  <!-- 错误 -->
  <div class="error-card" id="errorCard"></div>

  <!-- 加载 -->
  <div class="loading-section" id="loadingSection">
    <div class="loading-spinner"></div>
    <div class="msg" id="loadingMsg">正在分析多模型认知结构…</div>
    <div class="sub-msg">提取共识 · 检测分歧 · 溯源冲突</div>
  </div>

  <!-- 结果区 -->
  <div class="results-section" id="resultsSection">

    <!-- 交叉验证 -->
    <div class="cross-validate" id="crossValidBox" style="display:none;">
      <div class="cv-title">✓ 双模型交叉验证</div>
      <div class="cv-body" id="crossValidBody">主分析模型与验证模型结论一致，分析结果可靠。</div>
    </div>

    <!-- 共识 -->
    <div class="result-block" id="consensusBlock">
      <div class="block-title">✅ 一致观点 <span class="badge badge-green" id="consensusCount">0</span></div>
      <div id="consensusList"></div>
    </div>

    <!-- 分歧 -->
    <div class="result-block" id="dissentBlock">
      <div class="block-title">⚡ 分歧观点 <span class="badge badge-yellow" id="dissentCount">0</span></div>
      <div id="dissentList"></div>
    </div>

    <!-- 冲突来源 -->
    <div class="result-block" id="sourceBlock">
      <div class="block-title">🔍 冲突来源分析</div>
      <div id="sourceList"></div>
    </div>

    <!-- 不确定性 -->
    <div class="result-block" id="uncertaintyBlock" style="display:none;">
      <div class="block-title">⚠️ 仍有不确定性</div>
      <div id="uncertaintyBody" style="font-size:13px;color:#6b7280;line-height:1.6;"></div>
    </div>

    <!-- 最终收敛建议 -->
    <div class="recommendation-card" id="recCard">
      <div class="rc-title">🎯 收敛建议</div>
      <div class="rc-body" id="recBody"></div>
      <div class="rc-meta">
        <span id="recEntryCount">基于 — 个模型</span>
        <span id="recModels"></span>
      </div>
    </div>

    <!-- 新一轮 -->
    <div style="text-align:center;margin-top:8px;">
      <button class="btn btn-ghost" id="continueBtn" style="padding:10px 28px;">
        + 贴入新一轮回答继续迭代
      </button>
    </div>

  </div>

</div>

<script>
// ─── 默认模型列表 ───
const MODEL_OPTIONS = [
  'GPT-4o', 'Claude', 'Gemini', 'DeepSeek', 'Qwen',
  'Perplexity', 'Mistral', 'Grok', 'Kimi', '豆包', '文心一言', '通义千问', '其他'
];

// ─── 状态 ───
let entries = [];
let historyResult = null;

function getLabelColor(idx) {
  const colors = ['plabel-a','plabel-b','plabel-c','plabel-d','plabel-e'];
  return colors[idx % colors.length];
}

function getBadgeColor(severity) {
  if (severity === 'high') return 'badge-red';
  if (severity === 'medium') return 'badge-yellow';
  return 'badge-blue';
}

// ─── 渲染粘贴行 ───
function renderEntries() {
  const area = document.getElementById('pasteArea');
  area.innerHTML = '';
  entries.forEach((e, i) => {
    const row = document.createElement('div');
    row.className = 'paste-row';
    
    const select = document.createElement('select');
    select.className = 'model-select';
    select.dataset.index = i;
    MODEL_OPTIONS.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      if (m === e.label) opt.selected = true;
    });
    select.addEventListener('change', () => {
      entries[i].label = select.value;
    });
    
    const tagDiv = document.createElement('div');
    tagDiv.className = 'model-tag';
    tagDiv.appendChild(select);
    
    const textarea = document.createElement('textarea');
    textarea.placeholder = `粘贴 ${e.label || '模型'} 的回答…`;
    textarea.value = e.content;
    textarea.dataset.index = i;
    textarea.addEventListener('input', () => {
      entries[i].content = textarea.value;
    });
    
    const rmBtn = document.createElement('button');
    rmBtn.className = 'remove-btn';
    rmBtn.innerHTML = '×';
    rmBtn.addEventListener('click', () => {
      entries.splice(i, 1);
      renderEntries();
      updateUI();
    });
    
    row.appendChild(tagDiv);
    row.appendChild(textarea);
    row.appendChild(rmBtn);
    area.appendChild(row);
  });
  updateUI();
}

// ─── 更新界面状态 ───
function updateUI() {
  const count = entries.length;
  document.getElementById('entryHint').textContent = 
    count < 2 ? `已添加 ${count} 个，至少需要 2 个` : `已添加 ${count} 个模型回答`;
  document.getElementById('analyzeBtn').disabled = count < 2;
}

// ─── 添加条目 ───
function addEntry(label) {
  entries.push({ label: label || 'GPT-4o', content: '' });
  renderEntries();
  // scroll to new entry
  const rows = document.querySelectorAll('.paste-row');
  if (rows.length) rows[rows.length-1].scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ─── 显示错误 ───
function showError(msg) {
  const ec = document.getElementById('errorCard');
  ec.textContent = '⚠️ ' + msg;
  ec.classList.add('open');
}

// ─── 分析 ───
async function runAnalysis() {
  // 收集有效数据
  const validEntries = [];
  for (const e of entries) {
    const label = e.label.trim() || '未命名';
    const content = e.content.trim();
    if (content) validEntries.push({ label, content });
  }
  if (validEntries.length < 2) {
    showError('请至少填写 2 个模型的完整回答');
    return;
  }
  
  document.getElementById('errorCard').classList.remove('open');
  document.getElementById('loadingSection').classList.add('open');
  document.getElementById('resultsSection').classList.remove('open');
  document.getElementById('continueBtn').style.display = 'none';
  
  const msgEl = document.getElementById('loadingMsg');
  const msgs = ['正在分析多模型认知结构…', '提取共识观点…', '检测分歧点…', '溯源冲突…', '生成收敛建议…'];
  let msgIdx = 0;
  const msgTimer = setInterval(() => {
    msgIdx = (msgIdx + 1) % msgs.length;
    msgEl.textContent = msgs[msgIdx];
  }, 1800);
  
  try {
    const resp = await fetch('/api/compare', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ 
        entries: validEntries,
        history: historyResult
      })
    });
    const data = await resp.json();
    clearInterval(msgTimer);
    document.getElementById('loadingSection').classList.remove('open');
    
    if (data.error) { showError(data.error); return; }
    
    const analysis = data.analysis;
    if (!analysis || analysis.error) {
      showError(analysis?.error || '分析失败');
      return;
    }
    
    // 显示结果
    document.getElementById('resultsSection').classList.add('open');
    document.getElementById('continueBtn').style.display = 'inline-block';
    historyResult = analysis;
    
    // 共识
    renderConsensus(analysis.consensus || []);
    
    // 分歧
    renderDissent(analysis.dissent || []);
    
    // 冲突来源
    renderSources(analysis.conflict_sources || []);
    
    // 不确定性
    if (analysis.uncertainty) {
      document.getElementById('uncertaintyBlock').style.display = 'block';
      document.getElementById('uncertaintyBody').textContent = analysis.uncertainty;
    }
    
    // 收敛建议
    document.getElementById('recBody').textContent = analysis.recommendation || '暂无建议';
    document.getElementById('recEntryCount').textContent = `基于 ${data.entry_count || validEntries.length} 个模型`;
    document.getElementById('recModels').textContent = '来源: ' + (data.entries || []).join(' · ');
    
    // 交叉验证
    if (data.cross_validation) {
      document.getElementById('crossValidBox').style.display = 'block';
      const cv = data.cross_validation;
      const cvConsensus = (cv.consensus || []).length;
      const cvDissent = (cv.dissent || []).length;
      document.getElementById('crossValidBody').textContent = 
        `验证模型（DeepSeek-V3）独立分析结果：共识别 ${cvConsensus} 条共识、${cvDissent} 项分歧。` +
        (cvConsensus >= (analysis.consensus || []).length * 0.5 ? '与主模型结论基本一致，结果可信。' : '与主模型存在部分差异，建议对照查看。');
    }
    
    // 滚动到结果
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    
  } catch (err) {
    clearInterval(msgTimer);
    document.getElementById('loadingSection').classList.remove('open');
    showError(err.message || '分析请求失败');
  }
}

// ─── 渲染共识 ───
function renderConsensus(items) {
  const list = document.getElementById('consensusList');
  list.innerHTML = '';
  document.getElementById('consensusCount').textContent = items.length;
  if (items.length === 0) {
    list.innerHTML = '<div style="font-size:12px;color:#4a5268;padding:8px 0;">暂未识别到明显一致观点</div>';
    return;
  }
  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'consensus-item';
    div.innerHTML = `
      <div class="dot"></div>
      <div>
        <div class="text">${item.point || ''}</div>
        <div class="conf">置信度：${item.confidence === 'high' ? '高' : item.confidence === 'medium' ? '中' : '低'}</div>
      </div>`;
    list.appendChild(div);
  });
}

// ─── 渲染分歧 ───
function renderDissent(items) {
  const list = document.getElementById('dissentList');
  list.innerHTML = '';
  document.getElementById('dissentCount').textContent = items.length;
  if (items.length === 0) {
    list.innerHTML = '<div style="font-size:12px;color:#4a5268;padding:8px 0;">所有模型观点高度一致，无明显分歧</div>';
    return;
  }
  items.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'dissent-item';
    let positionsHtml = '';
    (item.positions || []).forEach((p, pi) => {
      positionsHtml += `<div class="position">
        <span class="plabel ${getLabelColor(pi)}">${p.model || '模型'}</span>
        <span class="pstance">${p.stance || ''}</span>
        <span class="psummary">${p.summary || ''}</span>
      </div>`;
    });
    div.innerHTML = `
      <div class="d-header">
        <span class="topic">${item.topic || '分歧#' + (idx+1)}</span>
        <span class="badge ${getBadgeColor(item.severity)}">${item.severity === 'high' ? '严重' : item.severity === 'medium' ? '中等' : '轻微'}</span>
      </div>
      <div class="d-body">${positionsHtml}</div>`;
    list.appendChild(div);
  });
}

// ─── 渲染冲突来源 ───
function renderSources(items) {
  const list = document.getElementById('sourceList');
  list.innerHTML = '';
  if (!items || items.length === 0) {
    list.innerHTML = '<div style="font-size:12px;color:#4a5268;padding:8px 0;">未识别到深层冲突来源</div>';
    return;
  }
  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'source-item';
    div.innerHTML = `<div class="s-title">${item.source || ''}</div>
      <div class="s-detail">${item.detail || ''}</div>`;
    list.appendChild(div);
  });
}

// ─── 新一轮 ───
function continueRound() {
  // 清空文本内容，保留标签
  entries.forEach(e => e.content = '');
  renderEntries();
  document.getElementById('resultsSection').classList.remove('open');
  document.getElementById('continueBtn').style.display = 'none';
  document.getElementById('analyzeBtn').disabled = true;
  // 聚焦第一个文本框
  const firstTextarea = document.querySelector('.paste-row textarea');
  if (firstTextarea) firstTextarea.focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─── 初始化 ───
function init() {
  // 默认 3 行
  addEntry('GPT-4o');
  addEntry('Claude');
  addEntry('DeepSeek');
  
  document.getElementById('addEntryBtn').addEventListener('click', () => addEntry('GPT-4o'));
  document.getElementById('analyzeBtn').addEventListener('click', runAnalysis);
  document.getElementById('continueBtn').addEventListener('click', continueRound);
}

init();
</script>

</body>
</html>
"""

# ============================================================

# ROUTES

# ============================================================

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

# ============================================================

# 启动

# ============================================================

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
