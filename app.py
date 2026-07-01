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

/* ───── 辩论可视化 ───── */
.debate-container {
 display: flex;
 flex-direction: column;
 gap: 12px;
 margin-bottom: 28px;
 max-height: 600px;
 overflow-y: auto;
 padding-right: 6px;
}
.debate-container::-webkit-scrollbar { width: 4px; }
.debate-container::-webkit-scrollbar-track { background: rgba(255,255,255,0.04); border-radius: 4px; }
.debate-container::-webkit-scrollbar-thumb { background: #2A2F45; border-radius: 4px; }

.debate-card {
 background: rgba(255,255,255,0.03);
 border: 1px solid rgba(255,255,255,0.06);
 border-radius: 12px;
 padding: 14px 18px;
 transition: all 0.3s ease;
 opacity: 0.3;
}
.debate-card.active {
 opacity: 1;
 border-color: rgba(124,92,255,0.3);
 background: rgba(124,92,255,0.06);
 box-shadow: 0 0 30px rgba(124,92,255,0.05);
}
.debate-card.done {
 opacity: 1;
 border-color: rgba(255,255,255,0.06);
}

.debate-header {
 display: flex;
 align-items: center;
 gap: 10px;
 margin-bottom: 6px;
}
.debate-header .icon { font-size: 20px; }
.debate-header .name { font-size: 14px; font-weight: 600; }
.debate-header .model { font-size: 11px; color: #4A4F6A; margin-left: 4px; }
.debate-header .status {
 font-size: 11px;
 padding: 2px 10px;
 border-radius: 12px;
 margin-left: auto;
 font-weight: 500;
 white-space: nowrap;
}
.debate-header .status.speaking {
 background: rgba(124,92,255,0.15);
 color: #7C5CFF;
 animation: pulse 1.2s ease-in-out infinite;
}
.debate-header .status.done {
 background: rgba(74,222,128,0.12);
 color: #4ADE80;
}
.debate-header .status.waiting {
 background: rgba(255,255,255,0.04);
 color: #4A4F6A;
}

@keyframes pulse {
 0%, 100% { opacity: 1; }
 50% { opacity: 0.4; }
}

.debate-content {
 font-size: 14px;
 color: #B0B5CC;
 line-height: 1.6;
 min-height: 24px;
}

.debate-content .cursor {
 display: inline-block;
 width: 2px;
 height: 16px;
 background: #7C5CFF;
 animation: blink 0.8s step-end infinite;
 vertical-align: text-bottom;
 margin-left: 2px;
}
@keyframes blink {
 0%, 100% { opacity: 1; }
 50% { opacity: 0; }
}

.debate-stance {
 display: inline-block;
 font-size: 12px;
 font-weight: 600;
 padding: 2px 10px;
 border-radius: 12px;
 margin-top: 8px;
}
.debate-stance.support { background: rgba(74,222,128,0.12); color: #4ADE80; }
.debate-stance.oppose { background: rgba(255,77,79,0.12); color: #FF6B6B; }
.debate-stance.neutral { background: rgba(251,191,36,0.12); color: #FBBF24; }

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

 <!-- 💬 AI 董事会辩论 -->
 <div class="section-title">💬 AI 董事会辩论</div>
 <div class="debate-container" id="debateContainer">
 <div style="color:#4A4F6A;font-size:14px;padding:20px 0;text-align:center;">输入决策问题后点击「生成分析」，AI 将依次发言辩论</div>
 </div>

 <!-- AI 意见 -->
 <div class="section-title">AI 意见</div>
 <div class="ai-stream" id="agentGrid">
 <div class="ai-card"><div class="icon">🧙</div><div class="name">首席战略官</div><div class="model">Qwen 72B</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">⚔️</div><div class="name">批判分析官</div><div class="model">DeepSeek V3</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">🛡️</div><div class="name">风险控制官</div><div class="model">GLM-4 9B</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">📈</div><div class="name">增长策略官</div><div class="model">Qwen 72B</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">🔍</div><div class="name">洞察官</div><div class="model">InternLM2 7B</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">💡</div><div class="name">创新官</div><div class="model">Mistral 7B</div><div class="stance neutral">等待分析…</div></div>
 <div class="ai-card"><div class="icon">👑</div><div class="name">CEO裁决官</div><div class="model">Qwen 7B</div><div class="stance neutral">等待分析…</div></div>
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
 remaining: 20,
 maxFree: 20,
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
var debateContainer = document.getElementById('debateContainer');
var agentGrid = document.getElementById('agentGrid');
var conflictContainer = document.getElementById('conflictContainer');
var decisionContainer = document.getElementById('decisionContainer');
var remainingEl = document.getElementById('remainingCount');
var adBanner = document.getElementById('adBanner');
var adBtn = document.getElementById('adBtn');

var DEBATE_AGENTS = [
 { icon: '🧙', name: '首席战略官', model: 'Qwen 72B', role: '首席战略官' },
 { icon: '⚔️', name: '批判分析官', model: 'DeepSeek V3', role: '批判分析官' },
 { icon: '🛡️', name: '风险控制官', model: 'GLM-4 9B', role: '风险控制官' },
 { icon: '📈', name: '增长策略官', model: 'Qwen 72B', role: '增长策略官' },
 { icon: '🔍', name: '洞察官', model: 'InternLM2 7B', role: '洞察官' },
 { icon: '💡', name: '创新官', model: 'Mistral 7B', role: '创新官' },
 { icon: '👑', name: 'CEO裁决官', model: 'Qwen 7B', role: 'CEO裁决官' }
];

var AGENTS = [
 { icon: '🧙', name: '首席战略官', model: 'Qwen 72B' },
 { icon: '⚔️', name: '批判分析官', model: 'DeepSeek V3' },
 { icon: '🛡️', name: '风险控制官', model: 'GLM-4 9B' },
 { icon: '📈', name: '增长策略官', model: 'Qwen 72B' },
 { icon: '🔍', name: '洞察官', model: 'InternLM2 7B' },
 { icon: '💡', name: '创新官', model: 'Mistral 7B' },
 { icon: '👑', name: 'CEO裁决官', model: 'Qwen 7B' }
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
function renderDebate(data) {
 if (!data || data.length === 0) { debateContainer.innerHTML = '<div style="color:#4A4F6A;font-size:14px;padding:20px 0;text-align:center;">暂无辩论数据</div>'; return; }
 var html = '';
 for (var i = 0; i < data.length; i++) {
 var a = data[i];
 var meta = DEBATE_AGENTS[i] || DEBATE_AGENTS[0];
 var statusClass = i === 0 ? 'active' : 'waiting';
 var statusText = i === 0 ? '发言中...' : '等待发言';
 var stanceClass = a.stance === '支持' ? 'support' : a.stance === '反对' ? 'oppose' : 'neutral';
 html += '<div class="debate-card ' + statusClass + '" id="debate_' + i + '">' +
 '<div class="debate-header">' +
 '<span class="icon">' + meta.icon + '</span>' +
 '<span class="name">' + (a.role || meta.name) + '</span>' +
 '<span class="model">' + (a.model || meta.model) + '</span>' +
 '<span class="status ' + (i === 0 ? 'speaking' : 'waiting') + '">' + statusText + '</span>' +
 '</div>' +
 '<div class="debate-content" id="debateContent_' + i + '">' +
 (i === 0 ? '<span class="cursor"></span>' : '') +
 '</div>' +
 (a.stance ? '<span class="debate-stance ' + stanceClass + '" id="debateStance_' + i + '" style="display:none;">' + a.stance + '</span>' : '') +
 '</div>';
 }
 debateContainer.innerHTML = html;

 // 开始流式辩论
 startDebateStream(data);
}

function startDebateStream(agents) {
 var currentIndex = 0;

 function playNext(index) {
 if (index >= agents.length) {
 // 所有发言完成 — 触发冲突+决策渲染
 afterDebateComplete(agents);
 return;
 }

 var card = document.getElementById('debate_' + index);
 var contentEl = document.getElementById('debateContent_' + index);
 if (!card || !contentEl) { playNext(index + 1); return; }

 // 标记发言中
 card.className = 'debate-card active';
 card.querySelector('.status').textContent = '发言中...';
 card.querySelector('.status').className = 'status speaking';

 // 打字效果
 var text = agents[index].reason || '';
 var charIndex = 0;
 contentEl.innerHTML = '';

 var typeInterval = setInterval(function() {
 if (charIndex < text.length) {
 contentEl.textContent += text[charIndex];
 charIndex++;
 debateContainer.scrollTop = debateContainer.scrollHeight;
 } else {
 clearInterval(typeInterval);
 // 完成发言
 card.className = 'debate-card done';
 card.querySelector('.status').textContent = '已发言 ✓';
 card.querySelector('.status').className = 'status done';
 contentEl.innerHTML = text;
 var stanceEl = document.getElementById('debateStance_' + index);
 if (stanceEl) stanceEl.style.display = 'inline-block';

 // 下一个（等待800ms）
 setTimeout(function() {
 playNext(index + 1);
 }, 800);
 }
 }, 30);
 }

 // 延迟500ms后开始
 setTimeout(function() { playNext(0); }, 500);
}

function afterDebateComplete(agents) {
 // 渲染AI意见卡片
 renderAgents(agents);
 // 分析冲突
 if (window._pendingAPIData) {
 var data = window._pendingAPIData;
 if (data.conflicts) renderConflicts(data.conflicts);
 if (data.decision) renderDecision(data.decision);
 }
}

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
 var width = c.severity_pct ? c.severity_pct + '%' : (levelMap[c.level] || '50%');
 html += '<div class="conflict-item">' +
 '<div class="title">' + (c.title || '冲突') + '</div>' +
 '<div class="sides"><span class="left">' + (c.left || '—') + '</span><span class="right">' + (c.right || '—') + '</span></div>' +
 '<div class="bar-wrap"><div class="bar-bg"><div class="bar-fill" style="width:' + width + ';"></div></div><span class="level">强度 ' + (c.severity_pct || c.level || '中') + '%</span></div>' +
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
 runBtn.textContent = '⏳ 分析中…';

 // 清空旧数据
debateContainer.innerHTML = '<div style="color:#4A4F6A;font-size:14px;padding:20px 0;text-align:center;">🧠 AI正在辩论中，请稍候…</div>';
agentGrid.innerHTML = '';
conflictContainer.innerHTML = '<div class="empty-state">等待辩论完成</div>';
decisionContainer.innerHTML = '<div style="color:#4A4F6A;font-size:14px;">等待辩论完成…</div>';

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
 // 保存API数据，辩论完成后使用
 window._pendingAPIData = data;
 // 开始辩论可视化
 if (data.agents && data.agents.length > 0) {
 renderDebate(data.agents);
 } else {
 throw new Error('未获取到AI回复');
 }
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
 var mockAgents = [
 { role: '首席战略官', model: 'Qwen 72B', stance: '支持', reason: '三伏天是养生心智最强时期，建议小步快跑抢占窗口。' },
 { role: '批判分析官', model: 'DeepSeek V3', stance: '反对', reason: '3万预算在小红书测试门槛不足，建议暂缓投入。' },
 { role: '风险控制官', model: 'GLM-4 9B', stance: '中立', reason: '风险可控，但需设置明确止损线，建议小规模测试。' },
 { role: '增长策略官', model: 'Qwen 72B', stance: '支持', reason: '市场窗口期正在打开，竞品已验证路径，建议快速跟进。' },
 { role: '洞察官', model: 'InternLM2 7B', stance: '支持', reason: '小红书养生人群增长43%，内容测试成本低于3千元即可验证。' },
 { role: '创新官', model: 'Mistral 7B', stance: '支持', reason: '可结合AI生成测评内容+UGC裂变，以极低成本完成冷启动。' },
 { role: 'CEO裁决官', model: 'Qwen 7B', stance: '支持', reason: '综合6位董事意见，多数支持。建议投入8000元做2周内容测试，ROI>1.5则追加。' }
 ];
 window._pendingAPIData = {
 agents: mockAgents,
 conflicts: [
 { topic: '预算', title: '预算判断分歧', left: '首席战略官：3万足够测试', right: '批判分析官：3万远远不足', level: '高', severity_pct: 82 },
 { topic: '时间窗口', title: '时间窗口判断分歧', left: '增长策略官：7月15日前必须决策', right: '风险控制官：养生心智全年可打', level: '中', severity_pct: 65 },
 { topic: '渠道策略', title: '渠道策略分歧', left: '洞察官：小红书内容测试成本低', right: '批判分析官：竞争激烈ROI不确定', level: '中', severity_pct: 48 }
 ],
 decision: {
 decision: '小规模测试（建议8000元预算）',
 confidence: 82,
 rationale: '6位董事投票：4位支持、1位反对、1位中立。市场存在真实需求信号，风险可控，创新官提出了低成本冷启动方案。',
 steps: ['筛选3个KOC账号报价', '制作2条AI测评+真人体验内容', '投入8000元跑2周小红书投放', '第7天复盘，ROI>1.0则追加至2万', '第14天终审决定是否正式推广'],
 risk: '风险等级中。初期转化波动较大，内容质量决定ROI上限。需预留2万元止损线。'
 }
 };
 renderDebate(mockAgents);
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
