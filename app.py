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

# 模型列表（按角色）
MODELS = {
    "东方战略官": "Qwen/Qwen2.5-72B-Instruct",
    "批判分析官": "deepseek-ai/DeepSeek-V3",
    "风险控制官": "THUDM/glm-4-9b-chat",
    "增长策略官": "Qwen/Qwen2.5-72B-Instruct"
}

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
<html>
<head>
 <meta charset="utf-8">
 <title>AI Decision Room</title>
 <style>
/* ───── 全局重置 ───── */
* { margin:0; padding:0; box-sizing:border-box; }
body {
 background: #0B0F1A;
 color: #E6E8FF;
 font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
 padding: 32px 24px;
 min-height: 100vh;
 display: flex;
 justify-content: center;
}
.container { max-width: 960px; width: 100%; }

/* ───── 品牌区 ───── */
.brand {
 display: flex;
 justify-content: space-between;
 align-items: flex-end;
 margin-bottom: 24px;
 border-bottom: 1px solid rgba(255,255,255,0.05);
 padding-bottom: 12px;
 flex-wrap: wrap;
 gap: 12px;
}
.brand-left h1 {
 font-size: 24px;
 font-weight: 700;
 letter-spacing: -0.3px;
}
.brand-left h1 span { color: #7C5CFF; }
.brand-left p {
 color: #5A5F7A;
 font-size: 14px;
 margin-top: 2px;
}
.brand-right {
 display: flex;
 align-items: center;
 gap: 16px;
 font-size: 14px;
 color: #8A8FA6;
}
.brand-right .count {
 background: rgba(124,92,255,0.12);
 padding: 6px 14px;
 border-radius: 20px;
 color: #7C5CFF;
 font-weight: 600;
 font-size: 13px;
}
.brand-right .count .num { font-size: 18px; }

/* ───── 模式切换器 ───── */
.mode-tabs {
 display: flex;
 gap: 4px;
 background: rgba(255,255,255,0.04);
 border-radius: 12px;
 padding: 4px;
 margin-bottom: 28px;
 border: 1px solid rgba(255,255,255,0.06);
}
.mode-tab {
 flex: 1;
 padding: 10px 16px;
 border: none;
 border-radius: 10px;
 background: transparent;
 color: #5A5F7A;
 font-size: 14px;
 font-weight: 500;
 cursor: pointer;
 transition: all 0.2s;
 font-family: inherit;
 text-align: center;
}
.mode-tab:hover { color: #B0B5CC; }
.mode-tab.active {
 background: rgba(124,92,255,0.15);
 color: #7C5CFF;
 box-shadow: 0 0 20px rgba(124,92,255,0.05);
}
.mode-tab .badge {
 font-size: 10px;
 background: rgba(255,77,79,0.15);
 color: #FF6B6B;
 padding: 2px 8px;
 border-radius: 10px;
 margin-left: 6px;
 font-weight: 600;
}
.mode-tab .badge.pro { background: rgba(124,92,255,0.15); color: #7C5CFF; }
.mode-tab .badge.free { background: rgba(74,222,128,0.12); color: #4ADE80; }

/* ───── 输入区 ───── */
.input-section {
 margin-bottom: 28px;
 display: none;
}
.input-section.active { display: block; }
.input-section .label {
 font-size: 14px;
 font-weight: 500;
 color: #8A8FA6;
 margin-bottom: 8px;
 display: block;
}
.input-section .input-row {
 display: flex;
 gap: 12px;
 flex-wrap: wrap;
}
.input-section input,
.input-section textarea {
 background: rgba(255,255,255,0.04);
 border: 1px solid rgba(255,255,255,0.07);
 border-radius: 10px;
 padding: 12px 16px;
 color: #E6E8FF;
 font-size: 14px;
 outline: none;
 font-family: inherit;
 flex: 1;
 min-width: 200px;
 transition: border-color 0.2s;
}
.input-section input:focus,
.input-section textarea:focus {
 border-color: #7C5CFF;
}
.input-section textarea {
 width: 100%;
 min-height: 50px;
 resize: vertical;
 flex: none;
}
.input-section .btn {
 padding: 12px 28px;
 background: #7C5CFF;
 border: none;
 border-radius: 10px;
 color: #fff;
 font-weight: 600;
 font-size: 15px;
 cursor: pointer;
 transition: background 0.2s;
 white-space: nowrap;
}
.input-section .btn:hover { background: #6B4DE0; }
.input-section .btn:disabled {
 opacity: 0.3;
 cursor: not-allowed;
 background: #3A3F5A;
}
.input-section .btn-secondary {
 background: rgba(255,255,255,0.06);
 border: 1px solid rgba(255,255,255,0.08);
 color: #B0B5CC;
}
.input-section .btn-secondary:hover { background: rgba(255,255,255,0.1); }

/* ───── 广告解锁横幅 ───── */
.ad-banner {
 background: rgba(255,77,79,0.06);
 border: 1px solid rgba(255,77,79,0.12);
 border-radius: 12px;
 padding: 16px 20px;
 margin-bottom: 20px;
 display: none;
 align-items: center;
 justify-content: space-between;
 flex-wrap: wrap;
 gap: 12px;
}
.ad-banner.active { display: flex; }
.ad-banner .ad-text { font-size: 14px; color: #B0B5CC; }
.ad-banner .ad-text strong { color: #FF6B6B; }
.ad-banner .ad-btn {
 padding: 8px 20px;
 background: #FF4D4F;
 border: none;
 border-radius: 8px;
 color: #fff;
 font-weight: 600;
 font-size: 13px;
 cursor: pointer;
 transition: background 0.2s;
}
.ad-banner .ad-btn:hover { background: #E04444; }
.ad-banner .ad-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ───── Section 标题 ───── */
.section-title {
 font-size: 13px;
 font-weight: 600;
 color: #5A5F7A;
 text-transform: uppercase;
 letter-spacing: 0.5px;
 margin-bottom: 14px;
 margin-top: 28px;
}

/* ───── AI 流 ───── */
.ai-stream {
 display: flex;
 gap: 12px;
 overflow-x: auto;
 padding-bottom: 8px;
 margin-bottom: 8px;
}
.ai-stream::-webkit-scrollbar { height: 4px; }
.ai-stream::-webkit-scrollbar-track { background: rgba(255,255,255,0.04); border-radius: 4px; }
.ai-stream::-webkit-scrollbar-thumb { background: #2A2F45; border-radius: 4px; }

.ai-card {
 min-width: 200px;
 flex: 0 0 auto;
 background: rgba(255,255,255,0.03);
 border: 1px solid rgba(255,255,255,0.06);
 border-radius: 12px;
 padding: 14px 18px;
}
.ai-card .icon { font-size: 20px; }
.ai-card .name { font-size: 14px; font-weight: 600; margin-top: 2px; }
.ai-card .model { font-size: 11px; color: #4A4F6A; }
.ai-card .stance {
 margin-top: 10px;
 font-size: 14px;
 font-weight: 500;
 padding-top: 8px;
 border-top: 1px solid rgba(255,255,255,0.05);
}
.ai-card .stance.support { color: #4ADE80; }
.ai-card .stance.oppose { color: #FF6B6B; }
.ai-card .stance.neutral { color: #FBBF24; }
.ai-card .reason {
 font-size: 13px;
 color: #6A6F8A;
 margin-top: 4px;
 line-height: 1.4;
}

/* ───── 冲突区 ───── */
.conflict-block {
 background: rgba(255,77,79,0.04);
 border-radius: 14px;
 padding: 20px 24px;
 margin-top: 8px;
}
.conflict-item {
 border-left: 3px solid #FF4D4F;
 padding: 12px 16px;
 margin-bottom: 10px;
 background: rgba(255,255,255,0.02);
 border-radius: 0 10px 10px 0;
}
.conflict-item:last-child { margin-bottom: 0; }
.conflict-item .title {
 font-size: 15px;
 font-weight: 600;
 margin-bottom: 6px;
}
.conflict-item .sides {
 display: flex;
 justify-content: space-between;
 font-size: 14px;
 color: #B0B5CC;
 flex-wrap: wrap;
 gap: 8px;
}
.conflict-item .sides .left { color: #7CC4FF; }
.conflict-item .sides .right { color: #FF7C7C; }
.conflict-item .bar-wrap {
 margin-top: 10px;
 display: flex;
 align-items: center;
 gap: 12px;
}
.conflict-item .bar-bg {
 flex: 1;
 height: 3px;
 background: rgba(255,255,255,0.06);
 border-radius: 4px;
 overflow: hidden;
}
.conflict-item .bar-fill {
 height: 100%;
 border-radius: 4px;
 background: #FF4D4F;
 transition: width 0.6s ease;
}
.conflict-item .level {
 font-size: 12px;
 color: #5A5F7A;
 white-space: nowrap;
}
.empty-state { color: #4A4F6A; font-size: 14px; padding: 8px 0; }

/* ───── 决策区 ───── */
.decision-block {
 background: rgba(124,92,255,0.05);
 border: 1px solid rgba(124,92,255,0.12);
 border-radius: 14px;
 padding: 24px 28px;
 margin-top: 28px;
}
.decision-block .verdict { font-size: 24px; font-weight: 700; color: #7C5CFF; }
.decision-block .confidence { font-size: 14px; color: #5A5F7A; margin-top: 2px; }
.decision-block .divider { height: 1px; background: rgba(255,255,255,0.06); margin: 16px 0; }
.decision-block .label { font-size: 12px; font-weight: 600; color: #5A5F7A; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 4px; }
.decision-block .reason { font-size: 14px; color: #B0B5CC; line-height: 1.6; }
.decision-block .steps { list-style: none; padding: 0; margin: 0; }
.decision-block .steps li {
 font-size: 14px;
 color: #B0B5CC;
 padding: 4px 0 4px 20px;
 position: relative;
}
.decision-block .steps li::before {
 content: "▹";
 position: absolute;
 left: 0;
 color: #7C5CFF;
}
.risk-tag {
 display: inline-block;
 background: rgba(255,77,79,0.1);
 color: #FF7C7C;
 font-size: 13px;
 padding: 4px 14px;
 border-radius: 20px;
 margin-top: 12px;
}

/* ───── 响应式 ───── */
@media (max-width: 640px) {
 body { padding: 20px 16px; }
 .brand { flex-direction: column; align-items: flex-start; }
 .brand-right { width: 100%; justify-content: space-between; }
 .mode-tabs { flex-direction: column; gap: 4px; }
 .mode-tab { text-align: center; }
 .input-section .input-row { flex-direction: column; }
 .ai-card { min-width: 160px; padding: 12px 14px; }
 .conflict-item .sides { flex-direction: column; gap: 2px; }
 .decision-block { padding: 18px 20px; }
 .ad-banner { flex-direction: column; text-align: center; }
}
 </style>
</head>
<body>
<div class="container">

 <!-- 品牌区 + 次数计数器 -->
 <div class="brand">
 <div class="brand-left">
 <h1>🧠 AI <span>Decision Room</span></h1>
 <p>输入真实决策 → AI 分歧 → 冲突总结 → 可执行结论</p>
 </div>
 <div class="brand-right">
 <span>今日剩余</span>
 <span class="count"><span class="num" id="remainingCount">10</span> 次</span>
 </div>
 </div>

 <!-- 模式切换器 -->
 <div class="mode-tabs" id="modeTabs">
 <button class="mode-tab active" data-mode="free">
 快速决策 <span class="badge free">免费</span>
 </button>
 <button class="mode-tab" data-mode="compare">
 深度对比 <span class="badge">手动</span>
 </button>
 <button class="mode-tab" data-mode="pro">
 全模型Pro <span class="badge pro">即将上线</span>
 </button>
 </div>

 <!-- 广告解锁横幅 -->
 <div class="ad-banner" id="adBanner">
 <span class="ad-text">今日免费次数已用完，看 <strong>15秒广告</strong> 解锁 <strong>5次</strong> 继续使用</span>
 <div style="display:flex;gap:10px;align-items:center;">
 <button class="ad-btn" id="adBtn">观看广告解锁</button>
 </div>
 </div>

 <!-- 输入区：快速决策 -->
 <div class="input-section active" id="inputFree">
 <span class="label">你的决策</span>
 <div class="input-row">
 <input id="topicInput" placeholder="例如：是否要做小红书投放？" />
 <button class="btn" id="runBtn">生成分析</button>
 </div>
 <textarea id="bgInput" placeholder="背景信息（可选）" style="margin-top:10px;"></textarea>
 </div>

 <!-- 输入区：深度对比 -->
 <div class="input-section" id="inputCompare">
 <span class="label">粘贴各模型输出（每行一个模型）</span>
 <textarea id="compareInput" placeholder="ChatGPT: 建议投放，理由...&#10;Claude: 建议暂缓，理由...&#10;DeepSeek: 建议测试，理由..." style="min-height:120px;"></textarea>
 <div style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;">
 <button class="btn" id="compareBtn">分析对比</button>
 </div>
 </div>

 <!-- 输入区：全模型Pro -->
 <div class="input-section" id="inputPro">
 <div style="text-align:center;padding:40px 20px;background:rgba(124,92,255,0.04);border-radius:12px;border:1px dashed rgba(124,92,255,0.15);">
 <div style="font-size:48px;margin-bottom:12px;">🧠</div>
 <h3 style="color:#7C5CFF;font-weight:600;">全模型Pro &#183; 即将上线</h3>
 <p style="color:#5A5F7A;font-size:14px;margin-top:6px;">调用 GPT-4o + Claude + Gemini 全模型集群</p>
 <p style="color:#5A5F7A;font-size:13px;margin-top:4px;">自动辩论 + 冲突收敛 + 高置信度决策</p>
 <button class="btn" style="margin-top:16px;background:rgba(255,255,255,0.06);color:#5A5F7A;cursor:default;" disabled>开发中</button>
 </div>
 </div>

 <!-- AI 意见 -->
 <div class="section-title">AI 意见</div>
 <div class="ai-stream" id="agentGrid">
 <div class="ai-card"><div class="icon">🧙</div><div class="name">东方战略官</div><div class="model">Qwen</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">⚔️</div><div class="name">批判分析官</div><div class="model">DeepSeek</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">🛡️</div><div class="name">风险控制官</div><div class="model">GLM</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">📈</div><div class="name">增长策略官</div><div class="model">GPT-4o</div><div class="stance neutral">等待分析…</div></div>
 </div>

 <!-- 核心冲突 -->
 <div class="section-title">核心冲突</div>
 <div class="conflict-block" id="conflictContainer">
 <div class="empty-state">运行分析后显示冲突结构</div>
 </div>

 <!-- CEO 决策 -->
 <div class="decision-block" id="decisionContainer">
 <div style="color:#4A4F6A; font-size:14px;">等待决策生成…</div>
 </div>

</div>

<script>
// ============================================================
// 状态管理
// ============================================================
var STATE = {
 mode: 'free',
 remaining: 10,
 maxFree: 10,
 isAdLocked: false,
 isAdPlaying: false,
 userId: localStorage.getItem('decision_room_user_id') || 'default'
};

// ============================================================
// DOM 引用
// ============================================================
var modeTabs = document.querySelectorAll('.mode-tab');
var inputFree = document.getElementById('inputFree');
var inputCompare = document.getElementById('inputCompare');
var inputPro = document.getElementById('inputPro');
var topicInput = document.getElementById('topicInput');
var bgInput = document.getElementById('bgInput');
var runBtn = document.getElementById('runBtn');
var compareInput = document.getElementById('compareInput');
var compareBtn = document.getElementById('compareBtn');
var agentGrid = document.getElementById('agentGrid');
var conflictContainer = document.getElementById('conflictContainer');
var decisionContainer = document.getElementById('decisionContainer');
var remainingEl = document.getElementById('remainingCount');
var adBanner = document.getElementById('adBanner');
var adBtn = document.getElementById('adBtn');

var AGENTS = [
 { icon: '🧙', name: '东方战略官', model: 'Qwen' },
 { icon: '⚔️', name: '批判分析官', model: 'DeepSeek' },
 { icon: '🛡️', name: '风险控制官', model: 'GLM' },
 { icon: '📈', name: '增长策略官', model: 'GPT-4o' }
];

// ============================================================
// 次数管理
// ============================================================
function loadState() {
 var key = 'decision_room_' + STATE.userId;
 var saved = localStorage.getItem(key);
 if (saved) {
 try {
 var data = JSON.parse(saved);
 var today = new Date().toDateString();
 if (data.date === today) {
 STATE.remaining = data.remaining;
 } else {
 STATE.remaining = STATE.maxFree;
 saveState();
 }
 } catch (e) {}
 } else {
 STATE.remaining = STATE.maxFree;
 saveState();
 }
 updateUI();
}

function saveState() {
 var key = 'decision_room_' + STATE.userId;
 localStorage.setItem(key, JSON.stringify({
 date: new Date().toDateString(),
 remaining: STATE.remaining
 }));
}

function useOne() {
 if (STATE.remaining <= 0) {
 STATE.isAdLocked = true;
 updateUI();
 return false;
 }
 STATE.remaining -= 1;
 STATE.isAdLocked = false;
 saveState();
 updateUI();
 return true;
}

function unlockByAd() {
 if (STATE.isAdPlaying) return;
 STATE.isAdPlaying = true;
 adBtn.disabled = true;
 adBtn.textContent = '播放中...';

 var seconds = 15;
 var interval = setInterval(function() {
 seconds -= 1;
 adBtn.textContent = seconds + 's';
 if (seconds <= 0) {
 clearInterval(interval);
 STATE.remaining = Math.min(STATE.maxFree, STATE.remaining + 5);
 STATE.isAdLocked = false;
 STATE.isAdPlaying = false;
 saveState();
 updateUI();
 adBtn.disabled = false;
 adBtn.textContent = '观看广告解锁';
 adBanner.classList.remove('active');
 }
 }, 1000);
}

function updateUI() {
 remainingEl.textContent = STATE.remaining;
 if (STATE.remaining <= 0) {
 adBanner.classList.add('active');
 runBtn.disabled = true;
 } else {
 adBanner.classList.remove('active');
 runBtn.disabled = false;
 }
}

// ============================================================
// 模式切换
// ============================================================
for (var t = 0; t < modeTabs.length; t++) {
 modeTabs[t].addEventListener('click', function() {
 for (var i = 0; i < modeTabs.length; i++) {
 modeTabs[i].classList.remove('active');
 }
 this.classList.add('active');
 STATE.mode = this.dataset.mode;

 inputFree.classList.remove('active');
 inputCompare.classList.remove('active');
 inputPro.classList.remove('active');

 if (STATE.mode === 'free') inputFree.classList.add('active');
 else if (STATE.mode === 'compare') inputCompare.classList.add('active');
 else if (STATE.mode === 'pro') inputPro.classList.add('active');
 });
}

// ============================================================
// 渲染函数
// ============================================================
function renderAgents(data) {
 if (!data || data.length === 0) return;
 var html = '';
 for (var i = 0; i < data.length; i++) {
 var a = data[i];
 var meta = AGENTS[i] || AGENTS[0];
 var stanceClass = a.stance === '支持' ? 'support' : a.stance === '反对' ? 'oppose' : 'neutral';
 html += '<div class="ai-card">' +
 '<div class="icon">' + meta.icon + '</div>' +
 '<div class="name">' + (a.role || meta.name) + '</div>' +
 '<div class="model">' + (a.model || meta.model) + '</div>' +
 '<div class="stance ' + stanceClass + '">' + (a.stance || '—') + '</div>' +
 (a.reason ? '<div class="reason">' + a.reason + '</div>' : '') +
 '</div>';
 }
 agentGrid.innerHTML = html;
}

function renderConflicts(conflicts) {
 if (!conflicts || conflicts.length === 0) {
 conflictContainer.innerHTML = '<div class="empty-state">未检测到明显冲突</div>';
 return;
 }
 var levelMap = { '高': '80%', '中': '50%', '低': '25%' };
 var html = '';
 for (var i = 0; i < conflicts.length; i++) {
 var c = conflicts[i];
 var width = levelMap[c.level] || '50%';
 html += '<div class="conflict-item">' +
 '<div class="title">' + (c.title || '冲突') + '</div>' +
 '<div class="sides"><span class="left">' + (c.left || '—') + '</span><span class="right">' + (c.right || '—') + '</span></div>' +
 '<div class="bar-wrap"><div class="bar-bg"><div class="bar-fill" style="width:' + width + ';"></div></div><span class="level">强度 ' + (c.level || '中') + '</span></div>' +
 '</div>';
 }
 conflictContainer.innerHTML = html;
}

function renderDecision(data) {
 if (!data || !data.decision) {
 decisionContainer.innerHTML = '<div style="color:#4A4F6A; font-size:14px;">等待决策生成…</div>';
 return;
 }
 var steps = data.steps || ['规划执行路径'];
 var stepsHtml = '';
 for (var i = 0; i < steps.length; i++) {
 stepsHtml += '<li>' + steps[i] + '</li>';
 }
 decisionContainer.innerHTML =
 '<div class="verdict">' + data.decision + '</div>' +
 '<div class="confidence">置信度 ' + (data.confidence || 78) + '%</div>' +
 '<div class="divider"></div>' +
 '<div class="label">为什么</div>' +
 '<div class="reason">' + (data.rationale || '基于多模型冲突分析，综合决策。') + '</div>' +
 '<div style="margin-top:14px;"><div class="label">执行路径</div><ul class="steps">' + stepsHtml + '</ul></div>' +
 '<div class="risk-tag"> ' + (data.risk || '请关注执行风险') + '</div>';
}

// ============================================================
// API 调用
// ============================================================
function runFreeDecision() {
 if (!useOne()) return;

 var payload = {
 topic: topicInput.value.trim() || '蕲艾五官灸是否做小红书投放',
 background: bgInput.value.trim() || ''
 };

 runBtn.disabled = true;
 runBtn.textContent = '分析中…';

 fetch('/api/run', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(payload)
 }).then(function(res) {
 if (!res.ok) {
 throw new Error('API 返回状态: ' + res.status);
 }
 return res.json();
 }).then(function(data) {
 if (data.detail) {
 throw new Error(data.detail);
 }
 if (data.agents) renderAgents(data.agents);
 if (data.conflicts) renderConflicts(data.conflicts);
 if (data.decision) renderDecision(data.decision);
 }).catch(function(err) {
 renderMockData();
 decisionContainer.innerHTML = '<div class="verdict">接口错误</div><div class="reason" style="color:#FF6B6B;margin-top:8px;">' + err.message + '</div>';
 }).finally(function() {
 runBtn.disabled = false;
 runBtn.textContent = '生成分析';
 updateUI();
 });
}

function runCompareDecision() {
 var text = compareInput.value.trim();
 if (!text) {
 alert('请粘贴各模型的输出');
 return;
 }
 var lines = text.split('\n').filter(function(l) { return l.trim(); });
 var parsed = lines.map(function(line) {
 var parts = line.split(':');
 if (parts.length >= 2) {
 return { model: parts[0].trim(), content: parts.slice(1).join(':').trim() };
 }
 return { model: '未知', content: line };
 });

 var agents = parsed.map(function(p) {
 var stance = '中立';
 if (p.content.indexOf('支持') !== -1 || p.content.indexOf('建议') !== -1) stance = '支持';
 else if (p.content.indexOf('反对') !== -1 || p.content.indexOf('不建议') !== -1) stance = '反对';
 return { role: p.model, model: p.model, stance: stance, reason: p.content.slice(0, 60) };
 });
 renderAgents(agents);

 var conflicts = [];
 for (var i = 0; i < agents.length; i++) {
 for (var j = i + 1; j < agents.length; j++) {
 if (agents[i].stance === '支持' && agents[j].stance === '反对') {
 conflicts.push({
 title: agents[i].role + ' vs ' + agents[j].role + ' 立场冲突',
 left: agents[i].role + ' 支持',
 right: agents[j].role + ' 反对',
 level: '高'
 });
 }
 }
 }
 renderConflicts(conflicts);

 renderDecision({
 decision: conflicts.length > 0 ? '建议综合各模型观点后决策' : '各模型意见趋于一致',
 confidence: 70,
 rationale: '分析了 ' + agents.length + ' 个模型观点，发现 ' + conflicts.length + ' 个核心冲突。',
 steps: ['明确核心目标', '重点关注冲突点', '制定验证方案'],
 risk: '建议进一步验证关键假设'
 });
}

// ============================================================
// Mock 数据
// ============================================================
function renderMockData() {
 renderAgents([
 { role: '东方战略官', model: 'Qwen', stance: '支持', reason: '三伏天是养生心智最强时期' },
 { role: '批判分析官', model: 'DeepSeek', stance: '反对', reason: '3万预算测试门槛不足' },
 { role: '风险控制官', model: 'GLM', stance: '中立', reason: '风险可控，需设止损线' },
 { role: '增长策略官', model: 'GPT-4o', stance: '支持', reason: '市场窗口期正在打开' }
 ]);
 renderConflicts([
 { title: '预算判断分歧', left: '东方战略官 3万足够测试', right: '批判分析官 3万远远不足', level: '高' },
 { title: '时间窗口判断', left: '增长策略官 7月15日前必须决策', right: '风险控制官 养生心智全年可打', level: '中' }
 ]);
 renderDecision({
 decision: '小规模测试',
 confidence: 78,
 rationale: '市场存在真实需求信号，风险可控，ROI不确定但可验证。',
 steps: ['筛选3个KOC账号询价', '投入5000元测试2条内容', '48小时后复盘决定是否追加'],
 risk: '初期转化波动较大，内容质量决定ROI上限'
 });
}

// ============================================================
// 初始化
// ============================================================
loadState();
renderMockData();

runBtn.addEventListener('click', runFreeDecision);
compareBtn.addEventListener('click', runCompareDecision);
adBtn.addEventListener('click', unlockByAd);

topicInput.addEventListener('keydown', function(e) {
 if (e.key === 'Enter' && STATE.mode === 'free') runFreeDecision();
});
</script>
</body>
</html>
"""

# ============================================================
# API 调用多模型
# ============================================================
async def call_siliconflow(model_id: str, prompt: str, role_name: str) -> dict:
    """调用硅基流动 API"""
    if not SILICONFLOW_API_KEY:
        return {"role": role_name, "model": model_id, "stance": "—", "reason": "API Key 未配置"}

    system_prompt = "你是一个决策顾问。你的角色是【" + role_name + "】。请针对用户的问题，给出你的判断（支持/反对/中立），并说明理由。只输出两行：第一行是判断（支持/反对/中立），第二行是理由。"
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SILICONFLOW_BASE,
                headers={"Authorization": "Bearer " + SILICONFLOW_API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    return {"role": role_name, "model": model_id, "stance": "—", "reason": "API 错误: " + str(resp.status)}
                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip().split("\n")
                stance = content[0].replace("判断：", "").replace("判断:", "").strip() if len(content) > 0 else "—"
                reason = content[1] if len(content) > 1 else ""
                return {"role": role_name, "model": model_id, "stance": stance, "reason": reason}
    except Exception as e:
        return {"role": role_name, "model": model_id, "stance": "—", "reason": "请求失败: " + str(e)}

@app.post("/api/run")
async def api_run(request: Request):
    body = await request.json()
    topic = body.get("topic", "")

    # 并行调用所有模型
    tasks = []
    for role_name, model_id in MODELS.items():
        tasks.append(call_siliconflow(model_id, topic, role_name))

    results = await asyncio.gather(*tasks)

    # 提取 agents
    agents = results

    # 冲突检测（基于 stance 对立）
    conflicts = []
    stances = {r["role"]: r["stance"] for r in results}
    roles = list(stances.keys())

    for i in range(len(roles)):
        for j in range(i + 1, len(roles)):
            if stances[roles[i]] == "支持" and stances[roles[j]] == "反对":
                conflicts.append({
                    "title": roles[i] + " vs " + roles[j] + " 立场冲突",
                    "left": roles[i] + " 支持",
                    "right": roles[j] + " 反对",
                    "level": "高"
                })
            elif stances[roles[i]] == "反对" and stances[roles[j]] == "支持":
                conflicts.append({
                    "title": roles[j] + " vs " + roles[i] + " 立场冲突",
                    "left": roles[j] + " 支持",
                    "right": roles[i] + " 反对",
                    "level": "高"
                })

    # 简单决策（基于投票）
    support_count = sum(1 for r in results if r["stance"] == "支持")
    oppose_count = sum(1 for r in results if r["stance"] == "反对")

    if support_count > oppose_count:
        decision_text = "建议执行"
        confidence = 60 + support_count * 8
    elif oppose_count > support_count:
        decision_text = "建议暂缓"
        confidence = 60 + oppose_count * 8
    else:
        decision_text = "建议小规模测试"
        confidence = 70

    decision = {
        "decision": decision_text,
        "confidence": min(confidence, 95),
        "rationale": "在 " + str(len(results)) + " 个模型中，" + str(support_count) + " 个支持，" + str(oppose_count) + " 个反对，存在 " + str(len(conflicts)) + " 个核心冲突。",
        "steps": ["明确核心目标", "识别关键风险点", "制定验证方案", "设定成败标准"],
        "risk": "建议进一步分析关键冲突点"
    }

    return {"agents": agents, "conflicts": conflicts, "decision": decision}

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
