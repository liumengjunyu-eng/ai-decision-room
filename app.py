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
# ROOM PAGE — V3.5 Decision Trace OS
# ============================================================
ROOM_HTML = r"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Decision Trace</title>
<style>
/* ─── 全局 ─── */
* { margin:0; padding:0; box-sizing:border-box; }
body {
    background: #0B0F1A;
    color: #E6EAF2;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* ─── 顶部 ─── */
.header {
    padding: 16px 24px;
    border-bottom: 1px solid #1F2430;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(11,15,26,0.95);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 10;
}
.header .logo { font-size: 14px; font-weight: 600; color: #E6EAF2; }
.header .logo span { color: #7C5CFF; }
.header .tagline { font-size: 12px; color: #6B7280; }

/* ─── 容器 ─── */
.container {
    max-width: 860px;
    margin: 0 auto;
    padding: 24px 20px;
}

/* ─── 状态栏 ─── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding: 10px 14px;
    background: rgba(124,92,255,0.04);
    border: 1px solid rgba(124,92,255,0.08);
    border-radius: 10px;
    font-size: 13px;
    color: #8B93A7;
}
.status-bar .dot {
    width: 8px; height: 8px; border-radius: 50%; background: #4A5268;
    flex-shrink: 0;
}
.status-bar .dot.active { background: #4ADE80; animation: pulse-dot 1.2s ease-in-out infinite; }
.status-bar .dot.running { background: #F59E0B; animation: pulse-dot 1.2s ease-in-out infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(0.7)} }
.status-bar .stext { flex: 1; }
.status-bar .saction { font-size: 12px; color: #7C5CFF; cursor: pointer; }

/* ─── 问题 ─── */
.question {
    background: #121827;
    border: 1px solid #232A3B;
    padding: 14px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.question .qlabel {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #7AA2FF; margin-bottom: 6px;
}
.question .qinput {
    display: flex; gap: 10px;
}
.question input {
    flex: 1; padding: 12px 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #232A3B; border-radius: 10px;
    color: #E6EAF2; font-size: 14px; outline: none;
    font-family: inherit;
}
.question input:focus { border-color: #7C5CFF; }
.question input::placeholder { color: #4A5268; }
.question button {
    padding: 12px 24px; background: #7C5CFF; border: none;
    border-radius: 10px; color: #fff; font-weight: 600;
    font-size: 13px; cursor: pointer; white-space: nowrap;
}
.question button:hover { background: #6B4DE0; }
.question button:disabled { opacity: 0.35; cursor: not-allowed; }

/* ─── 冲突矩阵 ─── */
.matrix {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 8px;
    margin-bottom: 20px;
}
.cell {
    background: #0E1320;
    border: 1px solid #222838;
    padding: 12px 8px;
    border-radius: 10px;
    font-size: 12px;
    text-align: center;
    line-height: 1.5;
}
.cell .num { font-size: 20px; font-weight: 700; display: block; margin-bottom: 2px; }
.cell.support .num { color: #22C55E; }
.cell.oppose .num { color: #EF4444; }
.cell.neutral .num { color: #FBBF24; }
.cell.verdict .num { color: #7C5CFF; }
.cell .label { color: #8B93A7; font-size: 11px; }

/* ─── 模块（推理块） ─── */
.block {
    margin-bottom: 12px;
    border-radius: 12px;
    background: #0F1422;
    border: 1px solid #222838;
    padding: 14px;
    opacity: 0;
    transform: translateY(8px);
    animation: fadeUp 0.4s ease forwards;
}
@keyframes fadeUp { to { opacity:1; transform:translateY(0); } }
.block.support { border-left: 3px solid #22C55E; }
.block.oppose { border-left: 3px solid #EF4444; }
.block.neutral { border-left: 3px solid #FBBF24; }

.block .role {
    font-size: 12px; color: #7AA2FF; margin-bottom: 6px;
    display: flex; align-items: center; gap: 8px;
}
.block .role .tag {
    font-size: 10px; font-weight: 600; padding: 1px 8px;
    border-radius: 8px;
}
.block .role .tag.support { background: rgba(34,197,94,0.12); color: #22C55E; }
.block .role .tag.oppose { background: rgba(239,68,68,0.12); color: #EF4444; }
.block .role .tag.neutral { background: rgba(251,191,36,0.12); color: #FBBF24; }
.block .role .weight-badge { color: #8B93A7; font-size: 11px; }

.block .summary {
    font-size: 14px; color: #C8D0E0; line-height: 1.6;
    margin-bottom: 8px;
}
.block .summary .type-cursor {
    display: inline-block; width: 2px; height: 15px;
    background: #7C5CFF; animation: blink 0.8s step-end infinite;
    vertical-align: text-bottom; margin-left: 1px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.block .expand-hint {
    font-size: 12px; color: #6B7280; cursor: pointer;
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 0;
}
.block .expand-hint:hover { color: #7C5CFF; }

/* 推理链 */
.block .trace {
    margin-top: 10px;
    padding: 12px 14px;
    background: rgba(124,92,255,0.04);
    border: 1px solid rgba(124,92,255,0.08);
    border-radius: 10px;
    font-size: 13px;
    color: #9AA8C0;
    line-height: 1.7;
    display: none;
}
.block .trace.open { display: block; }
.block .trace .chain-step {
    padding: 2px 0; display: flex; align-items: flex-start; gap: 8px;
}
.block .trace .chain-step::before {
    content: "→"; color: #7C5CFF; flex-shrink: 0;
}

/* 错误状态 */
.block.error { border-left: 3px solid #F59E0B; }
.block.error .role { color: #F59E0B; }
.block .error-msg { font-size: 13px; color: #F59E0B; font-style: italic; }

/* ─── 决策结果 ─── */
.result {
    margin-top: 20px;
    padding: 18px;
    border-radius: 14px;
    background: #11162A;
    border: 1px solid rgba(124,92,255,0.25);
    display: none;
}
.result.open { display: block; }
.result .rlabel {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: #7C5CFF; margin-bottom: 4px;
}
.result .rverdict { font-size: 22px; font-weight: 700; color: #E8EDF5; margin-bottom: 2px; }
.result .rconfidence {
    font-size: 13px; color: #8B93A7; margin-bottom: 10px;
}
.result .bar-track {
    height: 6px; background: #1F2430; border-radius: 6px;
    overflow: hidden; margin-bottom: 12px;
}
.result .bar-track .bar-fill {
    height: 100%; border-radius: 6px;
    transition: width 0.8s ease;
}
.result .bar-track .bar-fill.support { background: #22C55E; }
.result .bar-track .bar-fill.oppose { background: #EF4444; }
.result .bar-track .bar-fill.neutral { background: #FBBF24; }
.result .rlogic {
    background: rgba(124,92,255,0.04);
    border: 1px solid rgba(124,92,255,0.08);
    border-radius: 10px; padding: 12px 14px;
    font-size: 13px; color: #9AA8C0; line-height: 1.7;
}
.result .rsteps { margin-top: 10px; }
.result .rsteps .step {
    font-size: 13px; color: #B0C0D8; padding: 3px 0 3px 16px; position: relative;
}
.result .rsteps .step::before {
    content: ""; position: absolute; left: 0; top: 9px;
    width: 6px; height: 6px; border-radius: 50%; background: #7C5CFF;
}

/* ─── 空状态 ─── */
.empty {
    text-align: center; color: #4A5268; padding: 60px 0; font-size: 14px;
}
.empty .icon { font-size: 40px; margin-bottom: 12px; opacity: 0.4; }

/* ─── 响应式 ─── */
@media (max-width: 640px) {
    .container { padding: 16px 12px; }
    .matrix { grid-template-columns: 1fr 1fr; }
    .question .qinput { flex-direction: column; }
}
</style>
</head>
<body>

<div class="header">
    <div class="logo">🧠 AI <span>Decision Trace</span></div>
    <div class="tagline">Explainable Decision Engine</div>
</div>

<div class="container">

    <!-- 状态 -->
    <div class="status-bar" id="statusBar">
        <span class="dot" id="statusDot"></span>
        <span class="stext" id="statusText">就绪 — 输入决策问题启动分析</span>
        <span class="saction" id="statusAction"></span>
    </div>

    <!-- 问题 -->
    <div class="question">
        <div class="qlabel">🔍 决策问题</div>
        <div class="qinput">
            <input id="topicInput" placeholder="例如：是否要进入五官灸健康赛道？" />
            <button id="runBtn">分析决策</button>
        </div>
    </div>

    <!-- 冲突矩阵 -->
    <div class="matrix" id="matrixContainer">
        <div class="cell support">
            <span class="num" id="mSupport">0</span>
            <span class="label">✅ 支持</span>
        </div>
        <div class="cell oppose">
            <span class="num" id="mOppose">0</span>
            <span class="label">❌ 反对</span>
        </div>
        <div class="cell neutral">
            <span class="num" id="mNeutral">0</span>
            <span class="label">⚖️ 中立</span>
        </div>
        <div class="cell verdict">
            <span class="num" id="mVerdict">—</span>
            <span class="label">🏁 结论</span>
        </div>
    </div>

    <!-- 推理链列表 -->
    <div id="traceContainer">
        <div class="empty" id="emptyState">
            <div class="icon">🧠</div>
            <div>输入决策问题，启动 AI 分析</div>
            <div style="font-size:12px;color:#4A5268;margin-top:8px;">7位董事 → 冲突分析 → 加权决策</div>
        </div>
    </div>

    <!-- 决策结果 -->
    <div class="result" id="resultContainer">
        <div class="rlabel">👑 最终裁决</div>
        <div class="rverdict" id="rVerdict">—</div>
        <div class="rconfidence" id="rConfidence">置信度 —</div>
        <div class="bar-track"><div class="bar-fill" id="rBar" style="width:0%"></div></div>
        <div class="rlogic" id="rLogic"></div>
        <div class="rsteps" id="rSteps"></div>
    </div>

</div>

<script>
// 董事会配置
const BOARD = [
    { id: 0, name: '战略官',   icon: '🧙', title: 'CSO', tagClass: 'support' },
    { id: 1, name: '批判官',   icon: '⚔️', title: 'CRO', tagClass: 'oppose' },
    { id: 2, name: '风控官',   icon: '🛡️', title: 'CTO', tagClass: 'oppose' },
    { id: 3, name: '增长官',   icon: '📈', title: 'CGO', tagClass: 'support' },
    { id: 4, name: '洞察官',   icon: '🔍', title: 'CIO', tagClass: 'neutral' },
    { id: 5, name: '创新官',   icon: '💡', title: 'CIO', tagClass: 'support' }
];

const container = document.getElementById('traceContainer');
const emptyState = document.getElementById('emptyState');
const topicInput = document.getElementById('topicInput');
const runBtn = document.getElementById('runBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const matrix = {
    support: document.getElementById('mSupport'),
    oppose: document.getElementById('mOppose'),
    neutral: document.getElementById('mNeutral'),
    verdict: document.getElementById('mVerdict')
};
const resultContainer = document.getElementById('resultContainer');
const rVerdict = document.getElementById('rVerdict');
const rConfidence = document.getElementById('rConfidence');
const rBar = document.getElementById('rBar');
const rLogic = document.getElementById('rLogic');
const rSteps = document.getElementById('rSteps');

let isRunning = false;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// 清空
function clearAll() {
    document.querySelectorAll('.block').forEach(el => el.remove());
    emptyState.style.display = 'block';
    resultContainer.classList.remove('open');
    // Reset matrix
    matrix.support.textContent = '0';
    matrix.oppose.textContent = '0';
    matrix.neutral.textContent = '0';
    matrix.verdict.textContent = '—';
}

// 展开/折叠推理链
function toggleTrace(el) {
    const trace = el.nextElementSibling;
    if (trace && trace.classList.contains('trace')) {
        const isOpen = trace.classList.contains('open');
        trace.classList.toggle('open');
        el.textContent = isOpen ? '展开推理链 →' : '收起推理链 ↓';
    }
}

// 推断推理链（从角色文本中提取关键短语）
function extractReasoningChain(text) {
    if (!text || text.length < 20) return [];
    // 尝试按 。！？分割成有意义的短句
    const sentences = text.split(/[。！？\n]/).filter(s => s.trim().length > 5);
    if (sentences.length <= 2) {
        // 太短就用原始文本中的关键词
        const parts = text.split(/[,，、]/).filter(s => s.trim().length > 3);
        return parts.slice(0, 5).map(s => s.trim());
    }
    return sentences.slice(0, 5).map(s => s.trim());
}

// 创建推理块
function addTraceBlock(member, text, stance, isError, index) {
    emptyState.style.display = 'none';
    
    const div = document.createElement('div');
    div.className = 'block ' + (isError ? 'error' : (stance === '支持' ? 'support' : stance === '反对' ? 'oppose' : 'neutral'));
    div.style.animationDelay = (index * 0.15) + 's';

    const chain = extractReasoningChain(text);
    let traceHTML = '';
    if (chain.length > 0 && !isError) {
        traceHTML = '<div class="trace" id="trace-' + index + '">' +
            chain.map(s => '<div class="chain-step">' + s + '</div>').join('') +
            '</div>';
    }

    // 默认不展开推理链
    div.innerHTML = `
        <div class="role">
            ${member.icon} ${member.name}
            <span class="tag ${isError ? 'neutral' : stance}">${isError ? '暂不可用' : (stance || '中立')}</span>
            <span class="weight-badge">${isError ? '' : member.title}</span>
        </div>
        <div class="summary" id="sum-${index}">${isError ? '<span class="error-msg">' + text + '</span>' : ''}</div>
        ${chain.length > 0 && !isError ? '<div class="expand-hint" onclick="toggleTrace(this)">展开推理链 →</div>' : ''}
        ${traceHTML}
    `;
    container.appendChild(div);
    return div.querySelector('.summary');
}

// 打字效果
async function typeText(el, text, speed = 15) {
    el.textContent = '';
    for (let i = 0; i < text.length; i++) {
        el.textContent += text[i];
        await sleep(speed);
    }
}

// 更新冲突矩阵
function updateMatrix(agents) {
    const sup = agents.filter(a => a.stance === '支持').length;
    const opp = agents.filter(a => a.stance === '反对').length;
    const neu = agents.filter(a => a.stance === '中立' || a.stance === '—').length;
    matrix.support.textContent = sup;
    matrix.oppose.textContent = opp;
    matrix.neutral.textContent = neu;
    // 初步结论
    if (sup > opp) matrix.verdict.textContent = '支持领先';
    else if (opp > sup) matrix.verdict.textContent = '反对领先';
    else matrix.verdict.textContent = '胶着';
}

// 显示决策结果
function showResult(decision, agents) {
    if (!decision) return;
    rVerdict.textContent = decision.decision || '—';
    const conf = decision.confidence || 0;
    rConfidence.textContent = '置信度：' + conf + '%（基于风险权重主导）';
    const rational = decision.rationale || decision.reasoning || '';
    rLogic.textContent = '计算逻辑：' + rational;

    // 条形图颜色
    const sup = agents.filter(a => a.stance === '支持').length;
    const opp = agents.filter(a => a.stance === '反对').length;
    if (conf >= 50) {
        const dominating = sup > opp ? '支持' : '反对';
        rBar.className = 'bar-fill ' + (dominating === '支持' ? 'support' : 'oppose');
    } else {
        rBar.className = 'bar-fill neutral';
    }
    rBar.style.width = conf + '%';

    // 步骤
    rSteps.innerHTML = '';
    const steps = decision.steps || [];
    steps.forEach(s => {
        const el = document.createElement('div');
        el.className = 'step';
        el.textContent = s;
        rSteps.appendChild(el);
    });

    resultContainer.classList.add('open');
    setTimeout(() => resultContainer.scrollIntoView({ behavior: 'smooth', block: 'center' }), 200);
}

// 运行分析
async function runAnalysis() {
    if (isRunning) return;
    const topic = topicInput.value.trim();
    if (!topic) {
        statusText.textContent = '⚠️ 请先输入决策问题';
        return;
    }

    isRunning = true;
    runBtn.disabled = true;
    runBtn.textContent = '⏳ 分析中…';
    statusDot.className = 'dot running';
    statusText.textContent = '正在调用 AI 董事会分析…';

    clearAll();

    try {
        const resp = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });

        if (!resp.ok) {
            const errText = await resp.text().catch(() => '');
            throw new Error(errText || 'API 请求失败 (' + resp.status + ')');
        }

        const data = await resp.json();
        const agents = data.agents || [];
        const decision = data.decision || null;

        if (!agents || agents.length === 0) {
            throw new Error('未收到 AI 董事会回应');
        }

        statusText.textContent = '分析进行中…';

        // 依次显示每个推理块
        for (let i = 0; i < Math.min(agents.length, BOARD.length); i++) {
            const agent = agents[i];
            const member = BOARD[i];
            
            // 检查是否CEO（CEO单独在最后）
            if (i === agents.length - 1 && agent.role === 'CEO裁决官') continue;

            const isError = !agent.stance || agent.stance === '—' || 
                (agent.reason && (agent.reason.startsWith('API 错误') || agent.reason.startsWith('请求失败')));
            const text = agent.reason || agent.output || '分析中…';

            const el = addTraceBlock(member, text, agent.stance, isError, i);
            updateMatrix(agents.slice(0, i + 1));

            if (!isError) {
                await typeText(el, text, 15);
            } else {
                el.innerHTML = '<span class="error-msg">' + (text.includes('403') ? '模型暂不可用，正在切换…' : text) + '</span>';
            }
            await sleep(200);
        }

        // 显示决策结果
        if (decision) {
            await sleep(300);
            statusText.textContent = '正在生成最终裁决…';
            await sleep(500);
            showResult(decision, agents);
            matrix.verdict.textContent = decision.decision || '—';
        }

        statusDot.className = 'dot';
        statusText.textContent = '✅ 分析完成 — ' + (decision?.decision || '已结束');

    } catch (err) {
        statusDot.className = 'dot';
        statusText.textContent = '❌ 出错了: ' + (err.message || '未知错误');
        // 显示错误在页面上
        const errDiv = document.createElement('div');
        errDiv.className = 'block error';
        errDiv.innerHTML = '<div class="role">⚠️ 系统</div><div class="summary"><span class="error-msg">请求失败: ' + (err.message || '') + '</span></div>';
        container.appendChild(errDiv);
    }

    runBtn.disabled = false;
    runBtn.textContent = '分析决策';
    isRunning = false;
}

// 绑定
runBtn.addEventListener('click', runAnalysis);
topicInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') runAnalysis(); });

console.log('🧠 AI Decision Trace V3.5 已加载');
console.log('核心模式：冲突矩阵 → 推理链 → 加权决策');
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
