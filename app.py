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
# ROOM PAGE — 冲突剧场 UI
# ============================================================
ROOM_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>AI Decision Room</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#0B0F1A;color:#E6E8FF;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:40px 24px;min-height:100vh;}
.container{max-width:960px;margin:0 auto;}
.header{margin-bottom:48px;}
.header h1{font-size:28px;font-weight:700;letter-spacing:-.5px;}
.header h1 span{color:#7C5CFF;}
.header .sub{color:#5A5F7A;font-size:14px;margin-top:4px;}
.input-section{margin-bottom:48px;}
.input-section input{width:100%;padding:16px 18px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;color:#E6E8FF;font-size:16px;outline:none;transition:border-color .2s;font-family:inherit;}
.input-section input:focus{border-color:#7C5CFF;}
.input-section input::placeholder{color:#3A3F5A;}
.btn-run{margin-top:12px;padding:14px 32px;background:#7C5CFF;border:none;border-radius:10px;color:#fff;font-weight:600;font-size:15px;cursor:pointer;transition:background .2s;}
.btn-run:hover{background:#6B4DE0;}
.btn-run:disabled{opacity:.5;cursor:not-allowed;}
.section-title{font-size:14px;font-weight:600;color:#5A5F7A;text-transform:uppercase;letter-spacing:.5px;margin-bottom:16px;}
.agent-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:48px;}
.agent-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px 18px;}
.agent-icon{font-size:20px;}
.agent-name{font-size:14px;font-weight:600;margin-top:4px;}
.agent-model{font-size:12px;color:#4A4F6A;}
.agent-stance{margin-top:10px;font-size:14px;font-weight:500;padding:6px 0 2px;border-top:1px solid rgba(255,255,255,.04);}
.agent-stance.support{color:#4ADE80;}
.agent-stance.oppose{color:#FF6B6B;}
.agent-stance.neutral{color:#FBBF24;}
.agent-reason{font-size:13px;color:#6A6F8A;margin-top:4px;}
.conflict-section{margin-bottom:48px;}
.conflict-card{background:rgba(255,77,79,.04);border-left:3px solid #FF4D4F;border-radius:0 12px 12px 0;padding:18px 22px;margin-bottom:12px;}
.conflict-card:last-child{margin-bottom:0;}
.conflict-title{font-size:15px;font-weight:600;margin-bottom:8px;}
.conflict-rows{display:flex;justify-content:space-between;font-size:14px;color:#B0B5CC;}
.conflict-rows .left{color:#7CC4FF;}
.conflict-rows .right{color:#FF7C7C;}
.conflict-bar{margin-top:10px;height:3px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden;}
.conflict-bar .fill{height:100%;border-radius:4px;background:#FF4D4F;transition:width .6s ease;}
.conflict-level{font-size:12px;color:#5A5F7A;margin-top:4px;text-align:right;}
.ceo-section{margin-bottom:48px;}
.ceo-box{background:rgba(124,92,255,.05);border:1px solid rgba(124,92,255,.12);border-radius:12px;padding:24px 28px;}
.ceo-box .verdict{font-size:24px;font-weight:700;color:#7C5CFF;}
.ceo-box .confidence{font-size:14px;color:#5A5F7A;margin-top:2px;}
.ceo-box .divider{height:1px;background:rgba(255,255,255,.06);margin:16px 0;}
.ceo-box .label{font-size:12px;font-weight:600;color:#5A5F7A;text-transform:uppercase;letter-spacing:.3px;margin-bottom:6px;}
.ceo-box .reason{font-size:14px;color:#B0B5CC;line-height:1.6;}
.ceo-box .steps{list-style:none;padding:0;margin:0;}
.ceo-box .steps li{font-size:14px;color:#B0B5CC;padding:4px 0 4px 20px;position:relative;}
.ceo-box .steps li::before{content:"▹";position:absolute;left:0;color:#7C5CFF;}
.risk-tag{display:inline-block;background:rgba(255,77,79,.1);color:#FF7C7C;font-size:13px;padding:4px 14px;border-radius:20px;margin-top:12px;}
.loading-text{color:#4A4F6A;font-size:14px;}
.hidden{display:none;}
@media(max-width:640px){body{padding:20px 16px;}.agent-grid{grid-template-columns:1fr 1fr;gap:8px;}.conflict-rows{flex-direction:column;gap:4px;}.ceo-box{padding:18px 20px;}}
</style>
</head><body>
<div class="container">
<header class="header"><h1>🧠 AI <span>Decision Room</span></h1><div class="sub">输入决策 → AI 辩论 → 冲突分析 → 可执行结论</div></header>
<div class="input-section">
<input id="topicInput" placeholder="输入你正在纠结的决策，例如：是否要做小红书投放？" />
<button class="btn-run" id="runBtn">召开 AI 董事会</button>
</div>
<div class="section-title">AI 董事会</div>
<div class="agent-grid" id="agentGrid">
<div class="agent-card"><div class="agent-icon">🧙</div><div class="agent-name">东方战略官</div><div class="agent-model">Qwen</div><div class="agent-stance neutral">—</div></div>
<div class="agent-card"><div class="agent-icon">⚔️</div><div class="agent-name">批判分析官</div><div class="agent-model">DeepSeek</div><div class="agent-stance neutral">—</div></div>
<div class="agent-card"><div class="agent-icon">🛡️</div><div class="agent-name">风险控制官</div><div class="agent-model">GLM</div><div class="agent-stance neutral">—</div></div>
<div class="agent-card"><div class="agent-icon">📈</div><div class="agent-name">增长策略官</div><div class="agent-model">GPT-4o</div><div class="agent-stance neutral">—</div></div>
</div>
<div class="conflict-section">
<div class="section-title">⚔️ 核心冲突</div>
<div id="conflictContainer"><div class="loading-text">运行分析后显示冲突结构</div></div>
</div>
<div class="ceo-section">
<div class="section-title">👑 CEO 决策</div>
<div id="decisionContainer"><div class="loading-text">等待决策生成…</div></div>
</div>
</div>
<script>
const topicInput=document.getElementById('topicInput');const runBtn=document.getElementById('runBtn');const agentGrid=document.getElementById('agentGrid');const conflictContainer=document.getElementById('conflictContainer');const decisionContainer=document.getElementById('decisionContainer');
const AGENTS=[{icon:'🧙',name:'东方战略官',model:'Qwen'},{icon:'⚔️',name:'批判分析官',model:'DeepSeek'},{icon:'🛡️',name:'风险控制官',model:'GLM'},{icon:'📈',name:'增长策略官',model:'GPT-4o'}];
function renderAgents(data){if(!data||data.length===0)return;let html='';data.forEach((a,i)=>{const meta=AGENTS[i]||AGENTS[0];const cls=a.stance==='支持'?'support':a.stance==='反对'?'oppose':'neutral';html+=`<div class="agent-card"><div class="agent-icon">${meta.icon}</div><div class="agent-name">${a.role||meta.name}</div><div class="agent-model">${a.model||meta.model}</div><div class="agent-stance ${cls}">${a.stance||'—'}</div>${a.reason?`<div class="agent-reason">${a.reason}</div>`:''}</div>`;});agentGrid.innerHTML=html;}
function renderConflicts(c){if(!c||c.length===0){conflictContainer.innerHTML='<div class="loading-text">✅ 未检测到明显冲突</div>';return;}const lm={'高':'80%','中':'50%','低':'25%'};let html='';c.forEach(x=>{const w=lm[x.level]||'50%';html+=`<div class="conflict-card"><div class="conflict-title">⚔️ ${x.title||'冲突'}</div><div class="conflict-rows"><span class="left">${x.left||'—'}</span><span class="right">${x.right||'—'}</span></div><div class="conflict-bar"><div class="fill" style="width:${w};"></div></div><div class="conflict-level">强度：${x.level||'中'}</div></div>`;});conflictContainer.innerHTML=html;}
function renderDecision(d){if(!d||!d.decision){decisionContainer.innerHTML='<div class="loading-text">等待决策生成…</div>';return;}const steps=d.steps||['规划执行路径'];const html=`<div class="ceo-box"><div class="verdict">${d.decision}</div><div class="confidence">置信度 ${d.confidence||78}%</div><div class="divider"></div><div class="label">为什么</div><div class="reason">${d.rationale||'基于多模型冲突分析，综合决策。'}</div><div style="margin-top:14px;"><div class="label">执行路径</div><ul class="steps">${steps.map(s=>`<li>${s}</li>`).join('')}</ul></div><div class="risk-tag">⚠️ ${d.risk||'请关注执行风险'}</div></div>`;decisionContainer.innerHTML=html;}
async function callAPI(){const payload={topic:topicInput.value.trim()||'蕲艾五官灸是否做小红书投放'};runBtn.disabled=true;runBtn.textContent='分析中...';try{const res=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();if(data.agents)renderAgents(data.agents);if(data.conflicts)renderConflicts(data.conflicts);if(data.decision)renderDecision(data.decision);}catch(e){renderMockData();}finally{runBtn.disabled=false;runBtn.textContent='召开 AI 董事会';}}
function renderMockData(){renderAgents([{role:'东方战略官',model:'Qwen',stance:'支持',reason:'三伏天是养生心智最强时期'},{role:'批判分析官',model:'DeepSeek',stance:'反对',reason:'3万预算测试门槛不足'},{role:'风险控制官',model:'GLM',stance:'中立',reason:'风险可控，需设止损线'},{role:'增长策略官',model:'GPT-4o',stance:'支持',reason:'市场窗口期正在打开'}]);renderConflicts([{title:'预算判断分歧',left:'东方战略官 → 3万足够测试',right:'批判分析官 → 3万远远不足',level:'高'},{title:'时间窗口判断',left:'增长策略官 → 7月15日前必须决策',right:'风险控制官 → 养生心智全年可打',level:'中'}]);renderDecision({decision:'小规模测试',confidence:78,rationale:'市场存在真实需求信号，风险可控，ROI不确定但可验证。',steps:['筛选3个KOC账号询价','投入5000元测试2条内容','48小时后复盘决定是否追加'],risk:'初期转化波动较大，内容质量决定ROI上限'});}
document.addEventListener('DOMContentLoaded',()=>{renderMockData();runBtn.addEventListener('click',callAPI);topicInput.addEventListener('keydown',(e)=>{if(e.key==='Enter')callAPI();});});
</script>
</body></html>
"""

# ============================================================
# API — 调用多模型
# ============================================================
async def call_siliconflow(model_id: str, prompt: str, role_name: str) -> dict:
    """调用硅基流动 API"""
    if not SILICONFLOW_API_KEY:
        return {"role": role_name, "model": model_id, "stance": "—", "reason": "API Key 未配置"}

    system_prompt = f"你是一个决策顾问。你的角色是【{role_name}】。请针对用户的问题，给出你的判断（支持/反对/中立），并说明理由。只输出两行：第一行是判断（支持/反对/中立），第二行是理由。"
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
                headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    return {"role": role_name, "model": model_id, "stance": "—", "reason": f"API 错误: {resp.status}"}
                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip().split("\n")
                stance = content[0].replace("判断：", "").replace("判断:", "").strip() if len(content) > 0 else "—"
                reason = content[1] if len(content) > 1 else ""
                return {"role": role_name, "model": model_id, "stance": stance, "reason": reason}
    except Exception as e:
        return {"role": role_name, "model": model_id, "stance": "—", "reason": f"请求失败: {str(e)}"}

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

    # 模拟冲突检测（基于 stance 对立）
    conflicts = []
    stances = {r["role"]: r["stance"] for r in results}
    roles = list(stances.keys())

    for i in range(len(roles)):
        for j in range(i + 1, len(roles)):
            if stances[roles[i]] == "支持" and stances[roles[j]] == "反对":
                conflicts.append({
                    "title": f"{roles[i]} vs {roles[j]} 立场冲突",
                    "left": f"{roles[i]} → 支持",
                    "right": f"{roles[j]} → 反对",
                    "level": "高"
                })
            elif stances[roles[i]] == "反对" and stances[roles[j]] == "支持":
                conflicts.append({
                    "title": f"{roles[j]} vs {roles[i]} 立场冲突",
                    "left": f"{roles[j]} → 支持",
                    "right": f"{roles[i]} → 反对",
                    "level": "高"
                })

    # 简单决策（基于支持/反对计数）
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
        "rationale": f"在 {len(results)} 个模型中，{support_count} 个支持，{oppose_count} 个反对，存在 {len(conflicts)} 个核心冲突。",
        "steps": ["明确核心目标", "识别关键风险点", "制定验证方案", "设定成败标准"],
        "risk": "建议进一步分析关键冲突点"
    }

    return {"agents": agents, "conflicts": conflicts, "decision": decision}

# ============================================================
# ROUTES
# ============================================================
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
