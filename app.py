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

<a class="btn" href="/room">开始决策 →</a>

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

# ============================================================

# 启动

# ============================================================

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
