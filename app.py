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
# ROOM PAGE — V3 Single-Thread Meeting Room
# ============================================================
ROOM_HTML = r"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Decision Meeting Room</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    background: #0B0F1A;
    color: #E6EAF2;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* ─── 顶部 ─── */
.header {
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    border-bottom: 1px solid #1F2430;
    background: rgba(11,15,26,0.95);
    flex-shrink: 0;
}
.header .logo { font-weight: 600; font-size: 14px; color: #A8B3CF; }
.header .logo span { color: #7C5CFF; }
.header .status { font-size: 12px; color: #6B7280; display: flex; align-items: center; gap: 8px; }
.header .status .dot {
    width: 7px; height: 7px; border-radius: 50%; background: #4A5268;
}
.header .status .dot.active { background: #4ADE80; animation: pulse-dot 1.2s ease-in-out infinite; }
.header .status .dot.speaking { background: #F59E0B; animation: pulse-dot 0.8s ease-in-out infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(0.7)} }

/* ─── 主区域 ─── */
.main {
    flex: 1;
    overflow-y: auto;
    padding: 0;
}
.main::-webkit-scrollbar { width: 4px; }
.main::-webkit-scrollbar-track { background: transparent; }
.main::-webkit-scrollbar-thumb { background: #2A3142; border-radius: 4px; }

/* ─── 容器 ─── */
.container {
    max-width: 720px;
    margin: 0 auto;
    padding: 24px 20px 100px;
}

/* ─── 议题卡 ─── */
.topic-card {
    background: #111625;
    border: 1px solid #232838;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
}
.topic-card .tlabel {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #7AA2FF; margin-bottom: 8px;
}
.topic-card .tinput {
    display: flex; gap: 10px;
}
.topic-card input {
    flex: 1; padding: 12px 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #2A3142; border-radius: 10px;
    color: #E6EAF2; font-size: 14px; outline: none;
    font-family: inherit;
}
.topic-card input:focus { border-color: #7C5CFF; }
.topic-card input::placeholder { color: #4A5268; }
.topic-card button {
    padding: 12px 24px; background: #6D5EF7; border: none;
    border-radius: 10px; color: #fff; font-weight: 600;
    font-size: 13px; cursor: pointer; white-space: nowrap;
}
.topic-card button:hover { background: #5C4EE0; }
.topic-card button:disabled { opacity: 0.35; cursor: not-allowed; }

/* ─── 会议阶段标签 ─── */
.stage-label {
    font-size: 12px; color: #8B93A7;
    padding: 6px 0; margin-bottom: 4px;
    display: flex; align-items: center; gap: 8px;
}
.stage-label .stage-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #7C5CFF;
}

/* ─── 发言消息 ─── */
.msg {
    padding: 14px 16px;
    border-radius: 12px;
    border: 1px solid #222838;
    background: #0F1422;
    line-height: 1.7;
    margin-bottom: 8px;
    opacity: 0;
    transform: translateY(6px);
    animation: msgIn 0.35s ease forwards;
}
@keyframes msgIn { to { opacity:1; transform:translateY(0); } }
.msg .role {
    font-size: 13px; color: #7AA2FF; margin-bottom: 4px;
    display: flex; align-items: center; gap: 8px;
}
.msg .role .tag {
    font-size: 10px; font-weight: 600; padding: 1px 8px;
    border-radius: 8px;
}
.msg .role .tag.support { background: rgba(34,197,94,0.12); color: #22C55E; }
.msg .role .tag.oppose { background: rgba(239,68,68,0.12); color: #EF4444; }
.msg .role .tag.neutral { background: rgba(251,191,36,0.12); color: #FBBF24; }

/* 发起人 */
.msg.user { background: #1A1F33; border-left: 3px solid #7C5CFF; }
.msg.user .role { color: #A8B3CF; }

/* AI发言 */
.msg.ai { border-left: 3px solid #2DD4BF; }
.msg.ai.oppose { border-left: 3px solid #EF4444; }
.msg.ai.neutral { border-left: 3px solid #FBBF24; }

/* CEO */
.msg.ceo {
    background: #15122A;
    border: 1px solid rgba(109,94,247,0.3);
    border-left: 3px solid #7C5CFF;
    margin-top: 16px;
}
.msg.ceo .role { color: #7C5CFF; }
.msg.ceo .verdict { font-size: 18px; font-weight: 700; margin: 4px 0; }
.msg.ceo .conf { font-size: 12px; color: #8B93A7; margin-bottom: 8px; }
.msg.ceo .steps { margin-top: 8px; }
.msg.ceo .steps .step {
    font-size: 13px; color: #B0C0D8; padding: 2px 0 2px 14px; position: relative;
}
.msg.ceo .steps .step::before {
    content: ""; position: absolute; left: 0; top: 8px;
    width: 5px; height: 5px; border-radius: 50%; background: #7C5CFF;
}

/* 当前发言人高亮 */
.msg.speaking {
    border-color: #7C5CFF;
    box-shadow: 0 0 0 1px rgba(124,92,255,0.15);
}

/* 打字光标 */
.msg .content .cursor {
    display: inline-block; width: 2px; height: 15px;
    background: #7C5CFF; animation: blink 0.8s step-end infinite;
    vertical-align: text-bottom; margin-left: 1px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* 错误 */
.msg.error { border-left: 3px solid #F59E0B; }
.msg.error .role { color: #F59E0B; }
.msg .err-text { font-size: 13px; color: #F59E0B; font-style: italic; }

/* ─── 输入栏 ─── */
.input-bar {
    flex-shrink: 0;
    border-top: 1px solid #1F2430;
    padding: 12px 20px;
    background: #0B0F1A;
    display: flex;
    justify-content: center;
}
.input-inner {
    max-width: 720px;
    width: 100%;
    display: flex;
    gap: 10px;
}
.input-inner input {
    flex: 1; padding: 12px 16px;
    border-radius: 10px; border: 1px solid #2A3142;
    background: #111625; color: white; font-size: 14px;
    outline: none; font-family: inherit;
}
.input-inner input:focus { border-color: #7C5CFF; }
.input-inner input::placeholder { color: #4A5268; }
.input-inner button {
    padding: 12px 20px; background: #6D5EF7; border: none;
    border-radius: 10px; color: white; font-weight: 600;
    font-size: 13px; cursor: pointer;
}
.input-inner button:hover { background: #5C4EE0; }
.input-inner button:disabled { opacity: 0.35; cursor: not-allowed; }

/* ─── 空状态 ─── */
.empty-state {
    text-align: center; color: #4A5268; padding: 60px 0;
}
.empty-state .icon { font-size: 36px; margin-bottom: 10px; opacity: 0.4; }
.empty-state .hint { font-size: 13px; margin-top: 6px; color: #3A4268; }
</style>
</head>
<body>

<div class="header">
    <div class="logo">🧠 AI <span>Decision Meeting Room</span></div>
    <div class="status">
        <span class="dot" id="statusDot"></span>
        <span id="statusText">就绪</span>
    </div>
</div>

<div class="main" id="mainArea">
    <div class="container">

        <!-- 议题 -->
        <div class="topic-card">
            <div class="tlabel">📋 当前议题</div>
            <div class="tinput">
                <input id="topicInput" placeholder="例如：是否要进入五官灸健康赛道？" />
                <button id="runBtn">发起会议</button>
            </div>
        </div>

        <!-- 发言区 -->
        <div id="threadContainer">
            <div class="empty-state" id="emptyState">
                <div class="icon">🏛️</div>
                <div>输入议题，AI 董事会将依次发言</div>
                <div class="hint">发起人 → 6位董事 → CEO 裁决</div>
            </div>
        </div>

    </div>
</div>

<!-- 输入栏 -->
<div class="input-bar">
    <div class="input-inner">
        <input id="bottomInput" placeholder="输入新的议题..." />
        <button id="bottomBtn">发起会议</button>
    </div>
</div>

<script>
const BOARD = [
    { id: 'strategy',  name: '战略官', icon: '🧙', title: '战略部' },
    { id: 'critic',    name: '批判官', icon: '⚔️', title: '风控部' },
    { id: 'risk',      name: '风控官', icon: '🛡️', title: '风控部' },
    { id: 'growth',    name: '增长官', icon: '📈', title: '增长部' },
    { id: 'insight',   name: '洞察官', icon: '🔍', title: '洞察部' },
    { id: 'innovation',name: '创新官', icon: '💡', title: '创新部' }
];
const CEO = { name: 'CEO 裁决官', icon: '👑', title: '最终裁决' };

const container = document.getElementById('threadContainer');
const emptyState = document.getElementById('emptyState');
const topicInput = document.getElementById('topicInput');
const bottomInput = document.getElementById('bottomInput');
const runBtn = document.getElementById('runBtn');
const bottomBtn = document.getElementById('bottomBtn');
const mainArea = document.getElementById('mainArea');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

let isRunning = false;
let meetingPhase = 'idle';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// 添加阶段标签
function addStage(text) {
    emptyState.style.display = 'none';
    const div = document.createElement('div');
    div.className = 'stage-label';
    div.innerHTML = '<span class="stage-dot"></span> ' + text;
    container.appendChild(div);
}

// 添加消息
function addMessage(type, icon, name, roleHtml, content, extraClass) {
    emptyState.style.display = 'none';
    const div = document.createElement('div');
    div.className = 'msg ' + type + (extraClass ? ' ' + extraClass : '');
    div.innerHTML = `
        <div class="role">${icon} ${name}${roleHtml}</div>
        <div class="content">${content}</div>
    `;
    container.appendChild(div);
    div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return div.querySelector('.content');
}

// 获取立场标签
function stanceTag(stance) {
    if (stance === '支持') return '<span class="tag support">支持</span>';
    if (stance === '反对') return '<span class="tag oppose">反对</span>';
    if (stance === '中立') return '<span class="tag neutral">中立</span>';
    return '';
}

// 打字效果
async function typeText(el, text, speed = 16) {
    el.textContent = '';
    for (let i = 0; i < text.length; i++) {
        el.textContent += text[i];
        await sleep(speed);
    }
}

async function runMeeting() {
    if (isRunning) return;
    const topic = topicInput.value.trim() || bottomInput.value.trim();
    if (!topic) {
        statusText.textContent = '⚠️ 请输入议题';
        return;
    }

    isRunning = true;
    meetingPhase = 'running';
    runBtn.disabled = bottomBtn.disabled = true;
    runBtn.textContent = bottomBtn.textContent = '⏳ 会议中…';
    statusDot.className = 'dot speaking';
    statusText.textContent = '会议进行中';

    // 清空并重置
    document.querySelectorAll('.msg, .stage-label').forEach(el => el.remove());
    emptyState.style.display = 'none';

    // 阶段1: 主持人提出议题
    addStage('📌 主持人提出议题');
    const userEl = addMessage('user', '👤', '发起人', '', topic);
    userEl.innerHTML = topic;
    await sleep(400);

    // 阶段2: 董事依次发言
    addStage('💬 董事发言');
    await sleep(200);

    try {
        const resp = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });
        if (!resp.ok) throw new Error('API 请求失败');
        const data = await resp.json();
        const agents = data.agents || [];
        const decision = data.decision || null;

        // 依次发言
        for (let i = 0; i < Math.min(agents.length, BOARD.length); i++) {
            const agent = agents[i];
            const member = BOARD[i];
            const isError = !agent.stance || agent.stance === '—' ||
                (agent.reason && (agent.reason.startsWith('API 错误') || agent.reason.startsWith('请求失败')));
            const text = agent.reason || '分析中…';
            
            const roleHtml = ' <span style="font-size:11px;color:#6B7280;">' + member.title + '</span> ' + stanceTag(agent.stance || '');
            const msgCls = isError ? 'error' : (agent.stance === '反对' ? 'oppose' : agent.stance === '中立' ? 'neutral' : '');
            const displayText = isError ? (text.includes('403') ? '模型暂不可用，正在切换…' : text) : text;
            
            const contentEl = addMessage('ai ' + msgCls, member.icon, member.name, roleHtml, '', msgCls);
            statusText.textContent = member.name + ' 发言中…';
            
            if (!isError) {
                await typeText(contentEl, text, 14);
            } else {
                contentEl.innerHTML = '<span class="err-text">' + displayText + '</span>';
            }
            await sleep(150);
        }

        // 阶段3: CEO裁决
        if (decision) {
            addStage('👑 CEO 裁决');
            statusText.textContent = 'CEO 正在裁决…';
            await sleep(300);

            const stepsHtml = (decision.steps || []).map(s => '<div class="step">' + s + '</div>').join('');
            const div = document.createElement('div');
            div.className = 'msg ceo';
            div.innerHTML = `
                <div class="role">${CEO.icon} ${CEO.name} <span style="font-size:11px;color:#6B7280;">${CEO.title}</span></div>
                <div class="verdict">${decision.decision || '—'}</div>
                <div class="conf">置信度 ${decision.confidence || 0}%</div>
                <div style="font-size:13px;color:#9AA8C0;line-height:1.6;">${decision.rationale || decision.reasoning || ''}</div>
                <div class="steps">${stepsHtml}</div>
            `;
            container.appendChild(div);
            div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        meetingPhase = 'done';
        statusText.textContent = '✅ 会议结束';
        statusDot.className = 'dot active';

    } catch (err) {
        meetingPhase = 'error';
        statusText.textContent = '❌ 会议出错';
        const contentEl = addMessage('error', '⚠️', '系统', '', '');
        contentEl.innerHTML = '<span class="err-text">' + (err.message || '请求失败') + '</span>';
    }

    statusDot.className = 'dot';
    runBtn.disabled = bottomBtn.disabled = false;
    runBtn.textContent = bottomBtn.textContent = '发起会议';
    isRunning = false;
}

function triggerRun() {
    bottomInput.value = topicInput.value;
    topicInput.value = bottomInput.value;
    runMeeting();
}

runBtn.addEventListener('click', triggerRun);
bottomBtn.addEventListener('click', triggerRun);
topicInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') triggerRun(); });
bottomInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') triggerRun(); });

console.log('🏛️ AI Decision Meeting Room V3 加载完成');
console.log('单线程会议流 · 6董事 → 冲突 → CEO裁决');
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
