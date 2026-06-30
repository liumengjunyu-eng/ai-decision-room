from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# ============================================================
# LANDING PAGE（/）
# ============================================================
LANDING_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AI Decision Room</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0B0F1A;color:#E6E8FF;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.container{text-align:center;max-width:560px;padding:40px}
h1{font-size:42px;font-weight:700;margin-bottom:12px}
h1 span{color:#7C5CFF}
p{color:#8A8FA6;font-size:18px;line-height:1.6;margin-bottom:32px}
.btn{display:inline-block;padding:16px 40px;background:#7C5CFF;color:#fff;font-size:18px;font-weight:600;border:none;border-radius:12px;cursor:pointer;text-decoration:none;transition:background .2s}
.btn:hover{background:#6B4DE0}
</style>
</head>
<body>
<div class="container">
<h1>🧠 AI <span>Decision Room</span></h1>
<p>输入你正在纠结的真实决策<br>让多个 AI 帮你拆解冲突，得到可执行结论</p>
<a class="btn" href="/room">开始决策 →</a>
</div>
</body>
</html>"""

# ============================================================
# DECISION ROOM PAGE（/room）
# ============================================================
ROOM_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AI Decision Room</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0B0F1A;color:#E6E8FF;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:24px;min-height:100vh}
.container{max-width:1000px;margin:0 auto}
.header{margin-bottom:28px}
.header h1{font-size:26px;font-weight:700}
.header h1 span{color:#7C5CFF}
.header .sub{color:#8A8FA6;font-size:14px;margin-top:4px}
.card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:20px 24px;margin-bottom:24px}
.card-title{font-size:16px;font-weight:600;margin-bottom:14px}
.input-group input,.input-group textarea{width:100%;padding:12px 14px;margin-bottom:10px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.08);border-radius:10px;color:#E6E8FF;font-size:14px;outline:none;font-family:inherit}
.input-group input:focus,.input-group textarea:focus{border-color:#7C5CFF}
.input-group textarea{min-height:70px;resize:vertical}
.btn-primary{padding:12px 24px;background:#7C5CFF;border:none;border-radius:10px;color:#fff;font-weight:600;font-size:15px;cursor:pointer;transition:background .2s}
.btn-primary:hover{background:#6B4DE0}
.btn-primary:disabled{opacity:.5;cursor:not-allowed}
.agent-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.agent-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:14px 16px}
.agent-icon{font-size:20px}
.agent-role{font-size:14px;font-weight:600;margin-top:2px}
.agent-model{font-size:12px;color:#8A8FA6}
.agent-stance{margin-top:8px;font-size:14px;font-weight:500}
.agent-reason{font-size:13px;color:#B0B5CC;margin-top:4px}
.conflict-card{background:rgba(255,77,79,.05);border:1px solid rgba(255,77,79,.15);border-radius:12px;padding:16px 18px;margin-bottom:12px}
.conflict-card:last-child{margin-bottom:0}
.conflict-title{font-size:15px;font-weight:600;margin-bottom:10px}
.conflict-rows{font-size:14px}
.conflict-rows .left{color:#7CC4FF}
.conflict-rows .right{color:#FF7C7C}
.conflict-bar-wrap{margin-top:10px;display:flex;align-items:center;gap:12px}
.conflict-bar-bg{flex:1;height:4px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden}
.conflict-bar-fill{height:100%;border-radius:4px;background:#FF4D4F;transition:width .6s ease}
.conflict-level{font-size:13px;font-weight:500;color:#FF7C7C}
.ceo-box{background:rgba(124,92,255,.06);border:1px solid rgba(124,92,255,.15);border-radius:12px;padding:18px 22px}
.ceo-box .verdict{font-size:22px;font-weight:700;color:#7C5CFF}
.ceo-box .confidence{font-size:14px;color:#8A8FA6;margin:4px 0 12px}
.ceo-box .section-label{font-weight:600;color:#B0B5CC;margin-top:12px;margin-bottom:6px;font-size:13px}
.ceo-box ul{list-style:none;padding:0}
.ceo-box ul li{padding:4px 0 4px 20px;position:relative;font-size:14px;color:#D0D4E8}
.ceo-box ul li::before{content:"\25B9";position:absolute;left:0;color:#7C5CFF}
.risk-tag{display:inline-block;background:rgba(255,77,79,.15);color:#FF7C7C;font-size:13px;padding:4px 12px;border-radius:20px;margin-top:10px}
.loading-text{color:#8A8FA6;font-size:14px}
@media(max-width:640px){body{padding:16px}.agent-grid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="container">

<header class="header">
<h1>🧠 AI <span>Decision Room</span></h1>
<div class="sub">输入真实决策 → AI 辩论 → 冲突结构 → 可执行结论</div>
</header>

<!-- 输入区 -->
<section class="card">
<div class="card-title">📌 决策议题</div>
<div class="input-group">
<input id="topicInput" placeholder="你要决定什么？例如：蕲艾五官灸是否要做小红书投放？" />
<textarea id="bgInput" placeholder="背景信息（可选）"></textarea>
<button class="btn-primary" id="runBtn">🧠 召开 AI 董事会</button>
</div>
</section>

<!-- AI 辩论区 -->
<section class="card" id="boardroomSection">
<div class="card-title">💬 AI 董事会辩论</div>
<div id="agentGrid" class="agent-grid">
<div class="agent-card"><div class="agent-icon">🧙</div><div class="agent-role">东方战略官</div><div class="agent-model">Qwen</div><div class="agent-stance" style="color:#8A8FA6;">等待分析…</div></div>
<div class="agent-card"><div class="agent-icon">⚔️</div><div class="agent-role">批判分析官</div><div class="agent-model">DeepSeek</div><div class="agent-stance" style="color:#8A8FA6;">等待分析…</div></div>
<div class="agent-card"><div class="agent-icon">🛡️</div><div class="agent-role">风险控制官</div><div class="agent-model">GLM</div><div class="agent-stance" style="color:#8A8FA6;">等待分析…</div></div>
<div class="agent-card"><div class="agent-icon">📈</div><div class="agent-role">增长策略官</div><div class="agent-model">GPT-4o</div><div class="agent-stance" style="color:#8A8FA6;">等待分析…</div></div>
</div>
</section>

<!-- 冲突区 -->
<section class="card" id="conflictSection">
<div class="card-title">⚔️ 核心冲突</div>
<div id="conflictContainer"><div class="loading-text">运行分析后冲突将在此显示</div></div>
</section>

<!-- CEO 决策区 -->
<section class="card" id="decisionSection">
<div class="card-title">👑 CEO 决策</div>
<div id="decisionContainer"><div class="loading-text">等待决策生成…</div></div>
</section>

</div>

<script>
const topicInput = document.getElementById('topicInput');
const bgInput = document.getElementById('bgInput');
const runBtn = document.getElementById('runBtn');
const agentGrid = document.getElementById('agentGrid');
const conflictContainer = document.getElementById('conflictContainer');
const decisionContainer = document.getElementById('decisionContainer');

const AGENTS = [
  { icon: '🧙', role: '东方战略官', model: 'Qwen' },
  { icon: '⚔️', role: '批判分析官', model: 'DeepSeek' },
  { icon: '🛡️', role: '风险控制官', model: 'GLM' },
  { icon: '📈', role: '增长策略官', model: 'GPT-4o' }
];

function renderAgents(data) {
  if (!data || data.length === 0) return;
  let html = '';
  data.forEach((a, i) => {
    const meta = AGENTS[i] || AGENTS[0];
    const color = a.stance === '支持' ? '#7CFFB0' : a.stance === '反对' ? '#FF7C7C' : '#8A8FA6';
    html += '<div class="agent-card"><div class="agent-icon">' + meta.icon + '</div><div class="agent-role">' + (a.role || meta.role) + '</div><div class="agent-model">' + (a.model || meta.model) + '</div><div class="agent-stance" style="color:' + color + '">' + (a.stance || '—') + '</div>' + (a.reason ? '<div class="agent-reason">' + a.reason + '</div>' : '') + '</div>';
  });
  agentGrid.innerHTML = html;
}

function renderConflicts(conflicts) {
  if (!conflicts || conflicts.length === 0) {
    conflictContainer.innerHTML = '<div class="loading-text">✅ 未检测到明显冲突</div>';
    return;
  }
  const levelMap = { '高': '80%', '中': '50%', '低': '25%' };
  let html = '';
  conflicts.forEach(c => {
    const width = levelMap[c.level] || '50%';
    html += '<div class="conflict-card"><div class="conflict-title">⚔️ ' + (c.title || '冲突') + '</div><div class="conflict-rows"><div class="left">🧠 ' + (c.left || '—') + '</div><div class="right">⚔️ ' + (c.right || '—') + '</div></div><div class="conflict-bar-wrap"><span style="font-size:13px;color:#8A8FA6;">冲突强度</span><div class="conflict-bar-bg"><div class="conflict-bar-fill" style="width:' + width + ';"></div></div><span class="conflict-level">' + (c.level || '中') + '</span></div></div>';
  });
  conflictContainer.innerHTML = html;
}

function renderDecision(data) {
  if (!data || !data.decision) {
    decisionContainer.innerHTML = '<div class="loading-text">等待决策生成…</div>';
    return;
  }
  const steps = data.steps || ['规划执行路径'];
  const html = '<div class="ceo-box"><div class="verdict">' + data.decision + '</div><div class="confidence">置信度：' + (data.confidence || 78) + '%</div><div class="section-label">📌 为什么</div><div style="font-size:14px;color:#D0D4E8;margin-bottom:6px;">' + (data.rationale || '基于多模型冲突分析，综合决策。') + '</div><div class="section-label">🚀 执行路径</div><ul>' + steps.map(s => '<li>' + s + '</li>').join('') + '</ul><div class="risk-tag">⚠️ ' + (data.risk || '请关注执行过程中的关键风险') + '</div></div>';
  decisionContainer.innerHTML = html;
}

async function runDecision() {
  const payload = { topic: topicInput.value.trim() || '蕲艾五官灸是否做小红书投放', background: bgInput.value.trim() || '' };
  runBtn.disabled = true;
  runBtn.textContent = '⏳ 分析中...';
  try {
    const res = await fetch('/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (data.agents) renderAgents(data.agents);
    if (data.conflicts) renderConflicts(data.conflicts);
    if (data.decision) renderDecision(data.decision);
  } catch (err) {
    renderMockData();
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = '🧠 召开 AI 董事会';
  }
}

function renderMockData() {
  renderAgents([{ role: '东方战略官', model: 'Qwen', stance: '支持', reason: '三伏天是养生心智最强时期' }, { role: '批判分析官', model: 'DeepSeek', stance: '反对', reason: '3万预算测试门槛不足' }, { role: '风险控制官', model: 'GLM', stance: '中立', reason: '风险可控，需设止损线' }, { role: '增长策略官', model: 'GPT-4o', stance: '支持', reason: '市场窗口期正在打开' }]);
  renderConflicts([{ title: '预算判断分歧', left: '东方战略官 → 3万足够测试', right: '批判分析官 → 3万远远不足', level: '高' }, { title: '时间窗口判断', left: '增长策略官 → 7月15日前必须决策', right: '风险控制官 → 养生心智全年可打', level: '中' }]);
  renderDecision({ decision: '小规模测试', confidence: 78, rationale: '市场存在真实需求信号，风险可控，ROI不确定但可验证。', steps: ['筛选3个KOC账号询价', '投入5000元测试2条内容', '48小时后复盘决定是否追加'], risk: '初期转化波动较大，内容质量决定ROI上限' });
}

document.addEventListener('DOMContentLoaded', () => {
  renderMockData();
  runBtn.addEventListener('click', runDecision);
  topicInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') runDecision(); });
});
</script>
</body>
</html>"""

# ============================================================
# FASTAPI ROUTES
# ============================================================

@app.get("/", response_class=HTMLResponse)
def landing():
    return LANDING_HTML

@app.get("/room", response_class=HTMLResponse)
def room():
    return ROOM_HTML

@app.post("/api/run")
async def api_run(request: Request):
    body = await request.json()
    return {
      "agents": [
        {"role": "东方战略官", "model": "Qwen", "stance": "支持", "reason": "三伏天是养生心智最强时期"},
        {"role": "批判分析官", "model": "DeepSeek", "stance": "反对", "reason": "3万预算测试门槛不足"},
        {"role": "风险控制官", "model": "GLM", "stance": "中立", "reason": "风险可控，需设止损线"},
        {"role": "增长策略官", "model": "GPT-4o", "stance": "支持", "reason": "市场窗口期正在打开"}
      ],
      "conflicts": [
        {"title": "预算判断分歧", "left": "东方战略官 → 3万足够测试", "right": "批判分析官 → 3万远远不足", "level": "高"},
        {"title": "时间窗口判断", "left": "增长策略官 → 7月15日前必须决策", "right": "风险控制官 → 养生心智全年可打", "level": "中"}
      ],
      "decision": {
        "decision": "小规模测试",
        "confidence": 78,
        "rationale": "市场存在真实需求信号，风险可控，ROI不确定但可验证。",
        "steps": ["筛选3个KOC账号询价", "投入5000元测试2条内容", "48小时后复盘决定是否追加"],
        "risk": "初期转化波动较大，内容质量决定ROI上限"
      }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
