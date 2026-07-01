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

<html><head><meta charset="utf-8"><title>MindTrust OS · AI 智囊局</title>

<style>

*{margin:0;padding:0;box-sizing:border-box;}

body{background:#0B0F1A;color:#E6E8FF;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;}

.container{text-align:center;max-width:640px;padding:40px;}

h1{font-size:48px;font-weight:700;margin-bottom:6px;}

h1 span{background:linear-gradient(135deg,#7C5CFF,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}

.tagline{font-size:14px;color:#4a5268;margin-bottom:24px;letter-spacing:2px;text-transform:uppercase;}

p{color:#8A8FA6;font-size:18px;line-height:1.6;margin-bottom:16px;}

.glow-input{width:100%;background:#111827;border:1px solid #1f2937;border-radius:16px;padding:20px 24px;color:#fff;font-size:18px;font-family:inherit;outline:none;margin-bottom:20px;transition:all .2s;}

.glow-input:focus{border-color:#7C5CFF;box-shadow:0 0 0 4px rgba(124,92,255,0.1);}

.glow-input::placeholder{color:#4a5268;}

.actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;}

.btn{display:inline-block;padding:16px 40px;background:#7C5CFF;color:#fff;font-size:16px;font-weight:600;border:none;border-radius:12px;cursor:pointer;text-decoration:none;transition:background .2s;}

.btn:hover{background:#6B4DE0;}

.btn-green{background:#22c55e;color:#000;}

.btn-green:hover{background:#16a34a;}

.btn-outline{background:transparent;border:1px solid #1f2937;color:#9ca3af;}

.btn-outline:hover{background:#1f2937;color:#e5e7eb;}

.links{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:28px;padding-top:20px;border-top:1px solid #1f2937;}

.links a{font-size:12px;color:#4a5268;text-decoration:none;padding:4px 10px;border-radius:6px;border:1px solid #1f2937;transition:all .1s;}

.links a:hover{color:#9ca3af;border-color:#374151;}

.pricing-note{font-size:12px;color:#4a5268;margin-top:20px;}

</style>

</head><body>

<div class="container">

<div style="margin-bottom:8px;"><span style="font-size:14px;color:#7C5CFF;font-weight:600;">🧠 MindTrust OS</span><span style="font-size:12px;color:#4a5268;margin-left:8px;">v5 · AI 智囊局</span></div>

<h1>不要一个人<br>做艰难的<span>决定</span></h1>

<div class="tagline">汇聚全球顶尖大模型 · 为你提供确定性决策</div>

<p style="font-size:15px;color:#6b7280;">输入你的困境，让最聪明的 AI 大脑为你开会。</p>

<textarea class="glow-input" id="landingQuestion" rows="2" placeholder="你正在纠结什么决策？&#10;例如：是否该离职做自媒体？五官灸加盟能不能做？"></textarea>

<div class="actions">

<a class="btn" href="/room" id="landingGoBtn">开始智囊会议 →</a>

<a class="btn btn-outline" href="/compare">手动粘贴 · 多模型对比</a>

</div>

<div class="links">

<a href="https://claude.ai" target="_blank">Claude</a>

<a href="https://chat.deepseek.com" target="_blank">DeepSeek</a>

<a href="https://kimi.moonshot.cn" target="_blank">Kimi</a>

<a href="https://chatgpt.com" target="_blank">ChatGPT</a>

<a href="https://gemini.google.com" target="_blank">Gemini</a>

<a href="https://tongyi.aliyun.com" target="_blank">通义千问</a>

<a href="https://chatglm.cn" target="_blank">智谱GLM</a>

<a href="https://www.doubao.com" target="_blank">豆包</a>

</div>

<div class="pricing-note">免费版 · 每日3次智囊会议 · <span style="color:#22c55e;">高级版 9.9元解锁深度决策报告</span></div>

</div>

<script>

document.getElementById('landingQuestion').addEventListener('keydown', function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();var v=this.value.trim();if(v){sessionStorage.setItem('mindtrust_question',v);window.location.href='/room';}}});

document.getElementById('landingGoBtn').addEventListener('click',function(e){var v=document.getElementById('landingQuestion').value.trim();if(v){e.preventDefault();sessionStorage.setItem('mindtrust_question',v);window.location.href='/room';}});

</script>

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
  timelineContainer.innerHTML = '';
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
<title>Decision Compiler Pro · V4</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:#0b0f17;color:#e6e6e6;
  display:flex;height:100vh;overflow:hidden;
}

/* ─── 左侧 22% ─── */
.left{
  width:22%;min-width:220px;
  border-right:1px solid #1f2937;
  padding:20px;display:flex;flex-direction:column;
  background:#0d111c;
}
.left .brand{
  font-size:14px;font-weight:700;color:#e5e7eb;margin-bottom:4px;
}
.left .brand span{color:#22c55e;}
.left .sub{font-size:11px;color:#6b7280;margin-bottom:20px;}

.left label{font-size:11px;color:#9ca3af;font-weight:600;margin-bottom:6px;display:block;}
.left textarea{
  width:100%;height:140px;padding:12px;
  background:#111827;border:1px solid #1f2937;border-radius:8px;
  color:#e5e7eb;font-size:13px;font-family:inherit;
  resize:none;outline:none;line-height:1.6;
}
.left textarea:focus{border-color:#22c55e;}
.left textarea::placeholder{color:#4a5268;}

.left .actions{flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:8px;margin-top:16px;}
.left .btn{
  width:100%;padding:10px;border:none;border-radius:8px;
  font-weight:600;font-size:12px;cursor:pointer;transition:all .15s;
}
.btn-primary{background:#22c55e;color:#000;}
.btn-primary:hover{background:#16a34a;}
.btn-primary:disabled{opacity:0.3;cursor:not-allowed;}
.btn-secondary{background:#1f2937;color:#e5e7eb;}
.btn-secondary:hover{background:#374151;}
.btn-danger{background:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.2)!important;}
.btn-danger:hover{background:rgba(239,68,68,0.2);}
.btn-outline{background:transparent;color:#9ca3af;border:1px solid #1f2937;}
.btn-outline:hover{background:#1f2937;color:#e5e7eb;}
.left .mode-indicator{
  font-size:10px;color:#4a5268;padding:6px 8px;
  background:#0f172a;border-radius:6px;text-align:center;
}

/* ─── 中间 38% ─── */
.center{
  width:38%;min-width:320px;
  border-right:1px solid #1f2937;
  padding:20px;overflow-y:auto;background:#0b0f17;
}
.center .section-title{
  font-size:11px;color:#9ca3af;font-weight:600;
  margin-bottom:12px;display:flex;align-items:center;gap:6px;
}
.model-card{
  background:#111827;border:1px solid #1f2937;
  border-radius:10px;padding:12px;margin-bottom:10px;
  transition:border-color .15s;
}
.model-card.filled{border-color:rgba(34,197,94,0.2);}
.model-card .mc-header{
  display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;
}
.model-card .mc-header .mc-label{
  font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px;
}
.mc-label-a{background:rgba(59,130,246,0.12);color:#3b82f6;}
.mc-label-b{background:rgba(249,115,22,0.12);color:#f97316;}
.mc-label-c{background:rgba(139,92,246,0.12);color:#8b5cf6;}
.mc-label-d{background:rgba(236,72,153,0.12);color:#ec4899;}
.mc-label-e{background:rgba(14,165,233,0.12);color:#0ea5e9;}
.mc-label-f{background:rgba(34,197,94,0.12);color:#22c55e;}

.model-card .mc-header .mc-actions{display:flex;gap:4px;}
.model-card .mc-header .mc-actions button{
  background:none;border:none;color:#4a5268;cursor:pointer;
  font-size:12px;padding:2px 6px;border-radius:4px;
}
.model-card .mc-header .mc-actions button:hover{color:#ef4444;background:rgba(239,68,68,0.1);}
.model-card .mc-header .mc-actions .cred-badge{
  font-size:10px;padding:1px 6px;border-radius:4px;
  background:rgba(34,197,94,0.08);color:#22c55e;
}
.model-card select{
  width:100%;padding:6px 8px;margin-bottom:6px;
  background:#0f172a;border:1px solid #1f2937;border-radius:6px;
  color:#e5e7eb;font-size:11px;outline:none;cursor:pointer;
}
.model-card select:focus{border-color:#22c55e;}
.model-card textarea{
  width:100%;min-height:80px;padding:8px 10px;
  background:#0f172a;border:1px solid #1f2937;border-radius:6px;
  color:#e5e7eb;font-size:12px;font-family:inherit;
  resize:vertical;outline:none;line-height:1.6;
}
.model-card textarea:focus{border-color:#22c55e;}
.model-card textarea::placeholder{color:#4a5268;}

.center .add-row-btn{
  width:100%;padding:10px;border:1px dashed #1f2937;border-radius:8px;
  background:transparent;color:#6b7280;font-size:12px;cursor:pointer;transition:all .15s;
}
.center .add-row-btn:hover{border-color:#374151;color:#9ca3af;background:#0f172a;}

/* ─── 右侧 ─── */
.right{
  flex:1;padding:20px;overflow-y:auto;min-width:300px;
  background:#0b0f17;
}
.right .section-title{
  font-size:11px;color:#9ca3af;font-weight:600;
  margin-bottom:12px;display:flex;align-items:center;gap:6px;
}
.report-card{
  background:#111827;border:1px solid #1f2937;
  border-radius:10px;padding:14px;margin-bottom:10px;
}
.report-card .rc-title{
  font-size:11px;font-weight:600;color:#6b7280;margin-bottom:8px;
  display:flex;align-items:center;justify-content:space-between;
}
.report-card .rc-title .rc-badge{
  font-size:10px;padding:1px 6px;border-radius:4px;
}
.rc-badge-green{background:rgba(34,197,94,0.1);color:#22c55e;}
.rc-badge-yellow{background:rgba(251,191,36,0.1);color:#fbbf24;}
.rc-badge-red{background:rgba(239,68,68,0.1);color:#ef4444;}

.consensus-item{
  display:flex;gap:8px;align-items:flex-start;padding:6px 0;
  border-bottom:1px solid rgba(31,41,55,0.5);
}
.consensus-item:last-child{border-bottom:none;}
.consensus-item .dot{
  width:6px;height:6px;border-radius:50%;background:#22c55e;
  margin-top:4px;flex-shrink:0;
}
.consensus-item .text{font-size:12px;color:#d1d5db;line-height:1.5;}
.consensus-item .conf-bar{
  height:3px;border-radius:2px;margin-top:4px;
  background:#1f2937;position:relative;
}
.consensus-item .conf-bar .fill{
  height:100%;border-radius:2px;position:absolute;left:0;top:0;
}
.fill-high{background:#22c55e;width:90%;}
.fill-medium{background:#fbbf24;width:60%;}
.fill-low{background:#ef4444;width:30%;}

.dissent-item{
  padding:8px 0;border-bottom:1px solid rgba(31,41,55,0.5);
}
.dissent-item:last-child{border-bottom:none;}
.dissent-item .d-topic{
  font-size:12px;font-weight:600;color:#fbbf24;margin-bottom:4px;
}
.dissent-item .d-pos{
  display:flex;gap:6px;align-items:center;padding:3px 0;
  font-size:11px;
}
.dissent-item .d-pos .d-model{
  padding:1px 6px;border-radius:3px;font-weight:600;flex-shrink:0;
}
.dissent-item .d-pos .d-stance{color:#9ca3af;flex-shrink:0;}
.dissent-item .d-pos .d-summary{color:#6b7280;}

/* 反共识卡 */
.anti-card{
  background:linear-gradient(135deg,#1a0a0a,#0f172a);
  border:1px solid rgba(239,68,68,0.2);border-radius:10px;
  padding:14px;margin-bottom:10px;
  display:none;
}
.anti-card.open{display:block;}
.anti-card .ac-title{
  font-size:11px;font-weight:700;color:#ef4444;margin-bottom:6px;
  display:flex;align-items:center;gap:6px;
}
.anti-card .ac-challenge{font-size:13px;color:#fca5a5;line-height:1.5;margin-bottom:8px;}
.anti-card .ac-blindspot{
  padding:4px 0;font-size:12px;color:#d1d5db;list-style:none;
}
.anti-card .ac-blindspot li{padding:2px 0;padding-left:12px;position:relative;}
.anti-card .ac-blindspot li::before{content:"⚠";position:absolute;left:0;color:#ef4444;}
.anti-card .ac-warning{font-size:11px;color:#6b7280;margin-top:6px;padding:6px;background:rgba(239,68,68,0.04);border-radius:6px;}

/* 收敛建议 */
.rec-card{
  background:linear-gradient(135deg,#064e3b,#0f172a);
  border:1px solid #22c55e;border-radius:10px;
  padding:14px;margin-bottom:10px;
}
.rec-card .rc-title{
  font-size:11px;font-weight:700;color:#22c55e;margin-bottom:6px;
}
.rec-card .rc-body{font-size:13px;color:#d1d5db;line-height:1.6;}
.rec-card .rc-meta{
  font-size:10px;color:#4a5268;margin-top:8px;
  display:flex;gap:12px;
}

/* 加载 */
.loading-overlay{
  display:none;position:absolute;inset:0;z-index:10;
  background:rgba(11,15,23,0.7);backdrop-filter:blur(4px);
  align-items:center;justify-content:center;flex-direction:column;
}
.loading-overlay.open{display:flex;}
.loading-spinner{
  width:28px;height:28px;border:2px solid #1f2937;
  border-top-color:#22c55e;border-radius:50%;
  animation:spin 0.7s linear infinite;
}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-overlay .lm{font-size:12px;color:#9ca3af;margin-top:10px;}

/* 错误 */
.error-bar{
  display:none;padding:8px 12px;margin-bottom:8px;
  background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.12);
  border-radius:6px;font-size:11px;color:#ef4444;
}
.error-bar.open{display:block;}

/* 空状态 */
.empty-prompt{font-size:12px;color:#4a5268;text-align:center;padding:20px 0;line-height:1.6;}

/* 导航头 */
.nav-bar{
  display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap;
}
.nav-bar a{
  font-size:10px;padding:4px 10px;border-radius:6px;
  color:#6b7280;text-decoration:none;border:1px solid #1f2937;transition:all .1s;
}
.nav-bar a:hover{color:#9ca3af;border-color:#374151;}
.nav-bar a.active{color:#22c55e;border-color:#22c55e;background:rgba(34,197,94,0.06);}

/* 滚动条 */
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-thumb{background:#1f2937;border-radius:2px;}

@media(max-width:1024px){
  body{flex-direction:column;height:auto;overflow:auto;}
  .left,.center,.right{width:100%;min-width:0;border-right:none;border-bottom:1px solid #1f2937;}
  .left textarea{height:100px;}
}
</style>
</head>
<body>

<!-- ◀ LEFT: 问题区 -->
<div class="left">
  <div>
    <div class="brand">Decision <span>Compiler</span></div>
    <div class="sub">System 2 · 多模型认知编译器 V4</div>
  </div>

  <label>📌 决策问题</label>
  <textarea id="topicInput" placeholder="输入你要决策的问题…"></textarea>

  <div class="mode-indicator">Multi-Model Decision Compiler</div>

  <div class="actions">
    <button class="btn btn-primary" id="analyzeBtn" disabled>▶ 生成决策报告</button>
    <button class="btn btn-secondary" id="exportBtn" disabled>📄 导出 MD 报告</button>
    <button class="btn btn-danger" id="challengeBtn" style="display:none;">⚡ 挑战共识</button>
    <button class="btn btn-outline" id="resetBtn">↺ 清空重新开始</button>
  </div>
</div>

<!-- ◀ CENTER: 模型输入区 -->
<div class="center">
  <div class="nav-bar">
    <a href="/room">System 1 · 董事会</a>
    <a href="/compare" class="active">System 2 · 编译器</a>
  </div>

  <div class="section-title">🤖 多模型输入（粘贴各模型回答）</div>
  <div id="modelEntries"></div>
  <button class="add-row-btn" id="addRowBtn">+ 添加一个模型回答</button>
</div>

<!-- ◀ RIGHT: 决策报告区 -->
<div class="right" id="rightPanel">
  <div class="section-title">📊 决策报告</div>
  <div id="reportContent">
    <div class="empty-prompt">
      粘贴 2 个以上模型的回答<br>
      点击「生成决策报告」
    </div>
  </div>
</div>

<!-- 加载遮罩 -->
<div class="loading-overlay" id="loadingOverlay">
  <div class="loading-spinner"></div>
  <div class="lm" id="loadingMsg">正在分析多模型认知结构…</div>
</div>

<script>
// ─── 标签颜色 ───
const LABEL_COLORS = ['mc-label-a','mc-label-b','mc-label-c','mc-label-d','mc-label-e','mc-label-f'];
const MODEL_LIST = ['GPT-4o','Claude','Gemini','DeepSeek','Qwen','Perplexity','Grok','Mistral','Kimi','豆包','文心一言','通义千问','其他'];
const STANCE_COLORS = {a:'#3b82f6',b:'#f97316',c:'#8b5cf6',d:'#ec4899',e:'#0ea5e9',f:'#22c55e'};

let entries = [];
let lastAnalysis = null;
let challengeResult = null;

function getLabelColor(i){return LABEL_COLORS[i % LABEL_COLORS.length];}

// ─── 渲染模型输入行 ───
function renderEntries(){
  const container = document.getElementById('modelEntries');
  container.innerHTML = '';
  entries.forEach((e, i) => {
    const card = document.createElement('div');
    card.className = 'model-card' + (e.content.trim() ? ' filled' : '');
    const colorClass = getLabelColor(i);
    
    let credHtml = '';
    // credibility data from window credStore
    if(window.credStore && window.credStore[e.label]){
      const c = window.credStore[e.label];
      credHtml = `<span class="cred-badge">${c.percent}%</span>`;
    }
    
    card.innerHTML = `
      <div class="mc-header">
        <span class="mc-label ${colorClass}">${e.label}</span>
        <div class="mc-actions">
          ${credHtml}
          <button onclick="removeEntry(${i})" title="移除">✕</button>
        </div>
      </div>
      <select onchange="updateLabel(${i}, this.value)">
        ${MODEL_LIST.map(m => `<option value="${m}" ${m===e.label?'selected':''}>${m}</option>`).join('')}
      </select>
      <textarea placeholder="粘贴 ${e.label} 的回答…" oninput="updateContent(${i}, this.value)">${e.content}</textarea>
    `;
    container.appendChild(card);
  });
  updateUI();
}

function addEntry(label){
  entries.push({label: label || 'GPT-4o', content: ''});
  renderEntries();
  const cards = document.querySelectorAll('.model-card');
  if(cards.length) cards[cards.length-1].scrollIntoView({behavior:'smooth',block:'center'});
}
function removeEntry(i){entries.splice(i,1);renderEntries();}
function updateLabel(i,v){entries[i].label=v;renderEntries();}
function updateContent(i,v){
  entries[i].content=v;
  const cards = document.querySelectorAll('.model-card');
  if(cards[i]) cards[i].className='model-card'+(v.trim()?' filled':'');
  updateUI();
}

function updateUI(){
  const valid = entries.filter(e=>e.content.trim()).length;
  document.getElementById('analyzeBtn').disabled = valid < 2;
  document.getElementById('exportBtn').disabled = !lastAnalysis;
}

// ─── 加载动画 ───
function showLoading(msg){
  document.getElementById('loadingMsg').textContent = msg || '正在分析…';
  document.getElementById('loadingOverlay').classList.add('open');
}
function hideLoading(){document.getElementById('loadingOverlay').classList.remove('open');}

function showError(msg){
  const bar = document.createElement('div');
  bar.className = 'error-bar open';
  bar.textContent = '⚠ ' + msg;
  document.getElementById('reportContent').prepend(bar);
  setTimeout(()=>bar.remove(), 5000);
}

// ─── 生成决策报告 ───
async function runAnalysis(){
  const valid = entries.filter(e=>e.content.trim());
  const topic = document.getElementById('topicInput').value.trim();
  if(valid.length < 2){showError('请至少填写2个模型回答');return;}
  
  showLoading('正在分析多模型认知结构…');
  document.getElementById('challengeBtn').style.display = 'none';
  
  try{
    const resp = await fetch('/api/compare', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({entries: valid.map(e=>({label:e.label,content:e.content})), topic: topic})
    });
    const data = await resp.json();
    hideLoading();
    
    if(data.error){showError(data.error);return;}
    const analysis = data.analysis;
    if(!analysis || analysis.error){showError(analysis?.error||'分析失败');return;}
    
    lastAnalysis = analysis;
    renderReport(analysis, valid);
    document.getElementById('exportBtn').disabled = false;
    
    // 如果有共识，显示挑战按钮
    if(analysis.consensus && analysis.consensus.length >= 2){
      document.getElementById('challengeBtn').style.display = 'block';
    }
    
  }catch(err){hideLoading();showError(err.message||'请求失败');}
}

// ─── V4 可信度评分（System 2 版） ───
function calculateSystem2TrustScore(analysis, modelCount) {
  if (!analysis || modelCount < 2) return null;
  const consensus = analysis.consensus || [];
  const dissent = analysis.dissent || [];
  const hasRec = !!analysis.recommendation;
  
  // 一致性分数 (max 40)
  const consensusRatio = consensus.length / Math.max(consensus.length + dissent.length, 1);
  const consensusScore = consensusRatio * 40;
  
  // 模型覆盖面 (max 20)
  const coverageScore = Math.min(modelCount / 5, 1) * 20;
  
  // 分歧惩罚 (max 25)
  let dissentPenalty = 0;
  dissent.forEach(d => {
    if (d.severity === 'high') dissentPenalty += 8;
    else if (d.severity === 'medium') dissentPenalty += 5;
    else dissentPenalty += 2;
  });
  dissentPenalty = Math.min(dissentPenalty, 25);
  
  // 推荐加分 (max 15)
  const recScore = hasRec ? 15 : 0;
  
  const raw = consensusScore + coverageScore - dissentPenalty + recScore;
  const score = Math.max(5, Math.min(99, Math.round(raw)));
  
  let level, color;
  if (score >= 85) { level = '很高'; color = '#22c55e'; }
  else if (score >= 70) { level = '高'; color = '#4ade80'; }
  else if (score >= 55) { level = '中等'; color = '#fbbf24'; }
  else if (score >= 40) { level = '低'; color = '#f97316'; }
  else { level = '极低'; color = '#ef4444'; }
  
  return {
    score, level, color,
    breakdown: {
      consensus: consensusScore.toFixed(1),
      coverage: coverageScore.toFixed(1),
      dissent_penalty: dissentPenalty.toFixed(1),
      recommendation: recScore.toFixed(1)
    }
  };
}

// ─── 渲染报告 ───
function renderReport(analysis, validEntries){
  const rc = document.getElementById('reportContent');
  
  const consensus = analysis.consensus || [];
  const dissent = analysis.dissent || [];
  const sources = analysis.conflict_sources || [];
  const recommendation = analysis.recommendation || '';
  const uncertainty = analysis.uncertainty || '';
  const xvalid = document.getElementById('crossValidBox');
  
  let html = '';
  
  // 交叉验证
  if(analysis._xvalid){
    html += `<div class="report-card"><div class="rc-title" style="color:#6366f1;">✓ 双模型交叉验证 <span class="rc-badge rc-badge-green">已验证</span></div>
    <div style="font-size:11px;color:#6b7280;">主模型与验证模型分析结论一致</div></div>`;
  }
  
  // 共识
  html += `<div class="report-card"><div class="rc-title">✅ 一致观点 <span class="rc-badge rc-badge-green">${consensus.length}</span></div>`;
  if(consensus.length===0){
    html += '<div style="font-size:11px;color:#4a5268;padding:4px 0;">未识别到明显一致观点</div>';
  }else{
    consensus.forEach(c=>{
      const fillClass = c.confidence==='high'?'fill-high':c.confidence==='medium'?'fill-medium':'fill-low';
      html += `<div class="consensus-item"><div class="dot"></div><div style="flex:1;">
        <div class="text">${c.point||''}</div>
        <div class="conf-bar"><div class="fill ${fillClass}"></div></div></div></div>`;
    });
  }
  html += '</div>';
  
  // 分歧
  html += `<div class="report-card"><div class="rc-title">⚡ 分歧观点 <span class="rc-badge rc-badge-yellow">${dissent.length}</span></div>`;
  if(dissent.length===0){
    html += '<div style="font-size:11px;color:#4a5268;padding:4px 0;">所有模型观点高度一致</div>';
  }else{
    dissent.forEach(d=>{
      const severity = d.severity||'medium';
      const sevLabel = severity==='high'?'严重':severity==='medium'?'中等':'轻微';
      html += `<div class="dissent-item"><div class="d-topic">${d.topic||''} <span style="font-weight:400;font-size:10px;color:#6b7280;">[${sevLabel}]</span></div>`;
      (d.positions||[]).forEach((p,pi)=>{
        const sc = STANCE_COLORS[String.fromCharCode(97+(pi%6))]||'#3b82f6';
        html += `<div class="d-pos">
          <span class="d-model" style="color:${sc}">${p.model||'模型'}</span>
          <span class="d-stance">${p.stance||''}</span>
          <span class="d-summary">${p.summary||''}</span>
        </div>`;
      });
      html += '</div>';
    });
  }
  html += '</div>';
  
  // 冲突来源
  if(sources && sources.length > 0){
    html += `<div class="report-card"><div class="rc-title">🔍 冲突来源分析</div>`;
    sources.forEach(s=>{
      html += `<div style="padding:6px 0;font-size:12px;color:#d1d5db;border-bottom:1px solid rgba(31,41,55,0.3);">
        <div style="font-weight:500;">${s.source||''}</div>
        <div style="color:#6b7280;margin-top:2px;">${s.detail||''}</div></div>`;
    });
    html += '</div>';
  }
  
  // 不确定性
  if(uncertainty){
    html += `<div class="report-card"><div class="rc-title" style="color:#fbbf24;">⚠️ 仍有不确定性</div>
    <div style="font-size:12px;color:#6b7280;line-height:1.6;">${uncertainty}</div></div>`;
  }
  
  // 反共识区（占位）
  html += `<div class="anti-card" id="antiCard"></div>`;
  
  // 收敛建议
  html += `<div class="rec-card"><div class="rc-title">🎯 收敛建议</div>
    <div class="rc-body">${recommendation||'暂无建议'}</div>
    <div class="rc-meta">
      <span>基于 ${validEntries.length} 个模型</span>
      <span>${validEntries.map(e=>e.label).join(' · ')}</span>
    </div></div>`;
  
  // V4 Trust Score card (client-side calculated for System 2)
  const ts = calculateSystem2TrustScore(analysis, validEntries.length);
  if (ts) {
    html = html.replace('<div class="rec-card">',
      `<div class="report-card" style="border-color:${ts.color}40;"><div class="rc-title" style="color:${ts.color};">
        🧠 可信度评分 <span style="font-size:18px;font-weight:700;">${ts.score}/100</span>
        <span class="rc-badge" style="background:${ts.color}20;color:${ts.color};">${ts.level}</span>
      </div>
      <div style="height:5px;background:#1f2937;border-radius:3px;margin-bottom:8px;overflow:hidden;">
        <div style="height:100%;border-radius:3px;width:${ts.score}%;background:${ts.color};transition:width 0.6s;"></div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;font-size:10px;color:#6b7280;">
        <span>一致性 +${ts.breakdown.consensus}</span>
        <span>覆盖面 +${ts.breakdown.coverage}</span>
        <span>分歧 -${ts.breakdown.dissent_penalty}</span>
        <span>推荐 +${ts.breakdown.recommendation}</span>
      </div></div>`
    );
  }
  
  rc.innerHTML = html;
  rc.scrollIntoView({behavior:'smooth',block:'start'});
}

// ─── 挑战共识 ───
async function challengeConsensus(){
  if(!lastAnalysis || !lastAnalysis.consensus || lastAnalysis.consensus.length < 2) return;
  const topic = document.getElementById('topicInput').value.trim();
  
  showLoading('正在生成反共识分析…');
  try{
    const resp = await fetch('/api/challenge', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        consensus_points: lastAnalysis.consensus,
        topic: topic
      })
    });
    const data = await resp.json();
    hideLoading();
    
    if(data.error){showError(data.error);return;}
    challengeResult = data;
    
    const card = document.getElementById('antiCard');
    if(!card) return;
    card.className = 'anti-card open';
    card.innerHTML = `
      <div class="ac-title">⚡ 反共识挑战</div>
      <div class="ac-challenge">${data.challenge||'挑战未被识别'}</div>
      <ul class="ac-blindspot">
        ${(data.blindspots||[]).map(b=>`<li>${b}</li>`).join('')}
      </ul>
      <div style="font-size:12px;color:#d1d5db;margin:6px 0;padding:6px;background:rgba(239,68,68,0.04);border-radius:6px;">
        <div style="font-weight:500;color:#fca5a5;">替代假设：</div>
        <div style="color:#6b7280;margin-top:2px;">${data.alternative||''}</div>
      </div>
      <div class="ac-warning">⚠ ${data.warning||''}</div>
    `;
    card.scrollIntoView({behavior:'smooth',block:'center'});
    
  }catch(err){hideLoading();showError(err.message);}
}

// ─── 导出 ───
async function exportReport(){
  if(!lastAnalysis) return;
  const valid = entries.filter(e=>e.content.trim());
  const topic = document.getElementById('topicInput').value.trim();
  
  try{
    const resp = await fetch('/api/export', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        analysis: lastAnalysis,
        topic: topic,
        entries: valid.map(e=>({label:e.label}))
      })
    });
    const data = await resp.json();
    if(data.markdown){
      const blob = new Blob([data.markdown], {type:'text/markdown'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `decision-report-${Date.now()}.md`;
      a.click();
      URL.revokeObjectURL(url);
    }else{showError('导出失败');}
  }catch(err){showError(err.message);}
}

// ─── 重置 ───
function resetAll(){
  entries = [];
  lastAnalysis = null;
  challengeResult = null;
  document.getElementById('topicInput').value = '';
  document.getElementById('reportContent').innerHTML = `
    <div class="empty-prompt">
      粘贴 2 个以上模型的回答<br>
      点击「生成决策报告」
    </div>`;
  renderEntries();
  document.getElementById('challengeBtn').style.display = 'none';
  document.getElementById('exportBtn').disabled = true;
}

// ─── 初始化 ───
function init(){
  addEntry('GPT-4o');
  addEntry('Claude');
  addEntry('DeepSeek');
  
  document.getElementById('addRowBtn').addEventListener('click',()=>addEntry('GPT-4o'));
  document.getElementById('analyzeBtn').addEventListener('click',runAnalysis);
  document.getElementById('exportBtn').addEventListener('click',exportReport);
  document.getElementById('challengeBtn').addEventListener('click',challengeConsensus);
  document.getElementById('resetBtn').addEventListener('click',resetAll);
  
  // 加载可靠性数据
  fetch('/api/credibility').then(r=>r.json()).then(d=>{window.credStore=d;}).catch(()=>{});
}

init();
</script>

</body>
</html>
"""


# ============================================================
# V4.1 Credibility Engine Instance
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

# ============================================================

# 启动

# ============================================================

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
