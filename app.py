"""
AI Decision Room — Monolith App
=================================
Deploys to Render in 3 files (app.py + requirements.txt + render.yaml)
Mock-first: guaranteed to work on first deploy.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn, json, os, re, sys

# ── Optional: real AI engines (silently fall back to mock) ──────────
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from model_router import call_models as _real_call_models
    from backend.conflict_engine import ConflictEngine
    from backend.ceo_arbiter import weighted_arbitration
    from backend.execution_engine import build_execution_pack
    _HAS_REAL_ENGINE = True
except Exception:
    _HAS_REAL_ENGINE = False

app = FastAPI(title="AI Decision Room")

# ──────────────────────────────────────────────────────────────
# LANDING PAGE  (/)
# ──────────────────────────────────────────────────────────────
LANDING_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
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

# ──────────────────────────────────────────────────────────────
# DECISION ROOM  (/room)
# ──────────────────────────────────────────────────────────────
ROOM_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
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
.ceo-box ul li::before{content:"\\25B9";position:absolute;left:0;color:#7C5CFF}
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

<section class="card">
<div class="card-title">📌 决策议题</div>
<div class="input-group">
<input id="topicInput" placeholder="你要决定什么？例如：蕲艾五官灸是否要做小红书投放？" />
<textarea id="bgInput" placeholder="背景信息（可选）"></textarea>
<button class="btn-primary" id="runBtn">🧠 召开 AI 董事会</button>
</div>
</section>

<section class="card">
<div class="card-title">💬 AI 董事会辩论</div>
<div id="agentGrid" class="agent-grid">
<div class="agent-card"><div class="agent-icon">🧙</div><div class="agent-role">东方战略官</div><div class="agent-model">Qwen</div><div class="agent-stance" style="color:#8A8FA6">等待分析…</div></div>
<div class="agent-card"><div class="agent-icon">⚔️</div><div class="agent-role">批判分析官</div><div class="agent-model">DeepSeek</div><div class="agent-stance" style="color:#8A8FA6">等待分析…</div></div>
<div class="agent-card"><div class="agent-icon">🛡️</div><div class="agent-role">风险控制官</div><div class="agent-model">GLM</div><div class="agent-stance" style="color:#8A8FA6">等待分析…</div></div>
<div class="agent-card"><div class="agent-icon">📈</div><div class="agent-role">增长策略官</div><div class="agent-model">GPT-4o</div><div class="agent-stance" style="color:#8A8FA6">等待分析…</div></div>
</div>
</section>

<section class="card">
<div class="card-title">⚔️ 核心冲突</div>
<div id="conflictContainer"><div class="loading-text">运行分析后冲突将在此显示</div></div>
</section>

<section class="card">
<div class="card-title">👑 CEO 决策</div>
<div id="decisionContainer"><div class="loading-text">等待决策生成…</div></div>
</section>

</div>

<script>
const AGENTS=[{icon:'🧙',role:'东方战略官',model:'Qwen'},{icon:'⚔️',role:'批判分析官',model:'DeepSeek'},{icon:'🛡️',role:'风险控制官',model:'GLM'},{icon:'📈',role:'增长策略官',model:'GPT-4o'}];
const ti=document.getElementById('topicInput'),bi=document.getElementById('bgInput'),rb=document.getElementById('runBtn');
const ag=document.getElementById('agentGrid'),cc=document.getElementById('conflictContainer'),dc=document.getElementById('decisionContainer');

function ra(d){if(!d||!d.length)return;let h='';d.forEach((a,i)=>{const m=AGENTS[i]||AGENTS[0],c=a.stance==='支持'?'#7CFFB0':a.stance==='反对'?'#FF7C7C':'#8A8FA6';h+='<div class="agent-card"><div class="agent-icon">'+m.icon+'</div><div class="agent-role">'+(a.role||m.role)+'</div><div class="agent-model">'+(a.model||m.model)+'</div><div class="agent-stance" style="color:'+c+'">'+(a.stance||'—')+'</div>'+(a.reason?'<div class="agent-reason">'+a.reason+'</div>':'')+'</div>'});ag.innerHTML=h}

function rc(d){if(!d||!d.length){cc.innerHTML='<div class="loading-text">✅ 未检测到明显冲突</div>';return}
const lm={'高':'80%','中':'50%','低':'25%'};let h='';d.forEach(c=>{const w=lm[c.level]||'50%';h+='<div class="conflict-card"><div class="conflict-title">⚔️ '+(c.title||'冲突')+'</div><div class="conflict-rows"><div class="left">🧠 '+(c.left||'—')+'</div><div class="right">⚔️ '+(c.right||'—')+'</div></div><div class="conflict-bar-wrap"><span style="font-size:13px;color:#8A8FA6">冲突强度</span><div class="conflict-bar-bg"><div class="conflict-bar-fill" style="width:'+w+';"></div></div><span class="conflict-level">'+c.level+'</span></div></div>'});cc.innerHTML=h}

function rd(d){if(!d||!d.decision){dc.innerHTML='<div class="loading-text">等待决策生成…</div>';return}
const st=d.steps||['规划执行路径'];dc.innerHTML='<div class="ceo-box"><div class="verdict">'+d.decision+'</div><div class="confidence">置信度：'+(d.confidence||78)+'%</div><div class="section-label">📌 为什么</div><div style="font-size:14px;color:#D0D4E8;margin-bottom:6px">'+(d.rationale||'基于多模型冲突分析，综合决策。')+'</div><div class="section-label">🚀 执行路径</div><ul>'+st.map(s=>'<li>'+s+'</li>').join('')+'</ul><div class="risk-tag">⚠️ '+(d.risk||'请关注执行过程中的关键风险')+'</div></div>'}

function rm(){ra([{role:'东方战略官',model:'Qwen',stance:'支持',reason:'三伏天是养生心智最强时期'},{role:'批判分析官',model:'DeepSeek',stance:'反对',reason:'3万预算测试门槛不足'},{role:'风险控制官',model:'GLM',stance:'中立',reason:'风险可控，需设止损线'},{role:'增长策略官',model:'GPT-4o',stance:'支持',reason:'市场窗口期正在打开'}]);rc([{title:'预算判断分歧',left:'东方战略官 → 3万足够测试',right:'批判分析官 → 3万远远不足',level:'高'},{title:'时间窗口判断',left:'增长策略官 → 7月15日前必须决策',right:'风险控制官 → 养生心智全年可打',level:'中'}]);rd({decision:'小规模测试',confidence:78,rationale:'市场存在真实需求信号，风险可控，ROI不确定但可验证。',steps:['筛选3个KOC账号询价','投入5000元测试2条内容','48小时后复盘决定是否追加'],risk:'初期转化波动较大，内容质量决定ROI上限'})}

async function run(){const p={topic:ti.value.trim()||'蕲艾五官灸是否做小红书投放',background:bi.value.trim()||''};rb.disabled=true;rb.textContent='⏳ 分析中...';try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});const d=await r.json();if(d.agents)ra(d.agents);if(d.conflicts)rc(d.conflicts);if(d.decision)rd(d.decision)}catch(e){rm()}finally{rb.disabled=false;rb.textContent='🧠 召开 AI 董事会'}}

document.addEventListener('DOMContentLoaded',()=>{rm();rb.addEventListener('click',run);ti.addEventListener('keydown',e=>{if(e.key==='Enter')run()})});
</script>
</body>
</html>"""

# ──────────────────────────────────────────────────────────────
# MOCK DATA  (always available fallback)
# ──────────────────────────────────────────────────────────────
MOCK_RESPONSE = {
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

# ──────────────────────────────────────────────────────────────
# FASTAPI ROUTES
# ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def landing():
    return LANDING_HTML

@app.get("/room", response_class=HTMLResponse)
def room():
    return ROOM_HTML

@app.post("/api/run")
async def api_run(request: Request):
    """AI 决策核心 —— 有真实引擎则调用，否则返回 Mock"""
    body = await request.json()
    topic = body.get("topic", "")
    background = body.get("background", "")

    if _HAS_REAL_ENGINE:
        try:
            return await _real_run(topic, background)
        except Exception:
            pass

    return MOCK_RESPONSE

# ──────────────────────────────────────────────────────────────
# REAL ENGINE (when modules are available)
# ──────────────────────────────────────────────────────────────
async def _real_run(topic: str, background: str):
    """调用真实 AI 模型 + 冲突引擎 + CEO 仲裁 + 执行引擎"""
    # 1. 调模型
    question = f"议题：{topic}\n背景：{background}\n请给出你的分析和建议。"
    outputs = _real_call_models(question, timeout=90)

    names = [o["model"] for o in outputs]
    texts = [o["content"] for o in outputs]

    # 2. 立场检测
    pos_words = ["推荐", "支持", "可行", "适合", "乐观", "机会", "应该", "赞成", "增长"]
    neg_words = ["不推荐", "反对", "不可行", "不适合", "悲观", "风险", "不应该", "下降", "饱和"]

    def detect_stance(t):
        s = sum(1 for w in pos_words if w in t) - sum(1 for w in neg_words if w in t)
        return "support" if s >= 2 else "oppose" if s <= -2 else "neutral"

    viewpoints = []
    for i, t in enumerate(texts):
        stance = detect_stance(t)
        sents = [s.strip() for s in re.split(r'[。\n]', t) if len(s.strip()) > 10]
        reasons = [s for s in sents if any(w in s for w in ["理由","原因","因为","优势","机会","增长","可行","成本","效益","流量"])]
        risks = [s for s in sents if any(w in s for w in ["风险","问题","挑战","不确定性","劣势","不足","谨慎"])]
        if not reasons: reasons = sents[:2]
        viewpoints.append({
            "model": names[i], "stance": stance,
            "summary": t[:80] + ("..." if len(t) > 80 else ""),
            "reasons": reasons[:3], "risks": risks[:2]
        })

    # 3. 冲突检测
    _conflict_engine = ConflictEngine(use_l1=True)
    model_claims = {}
    for v in viewpoints:
        claim = v["summary"] + " " + " ".join(v.get("reasons",[])) + " " + " ".join(v.get("risks",[]))
        model_claims[v["model"]] = [claim]

    raw_conflicts = _conflict_engine.extract_conflicts(model_claims, n_clusters=3, threshold=0.25, max_conflicts=10)
    conflicts = []
    for rc in raw_conflicts:
        mp = rc.get("model_positions", [])
        if len(mp) >= 2:
            conflicts.append({
                "title": rc.get("topic", "决策冲突"),
                "left": f"{mp[0]['model']} → {mp[0]['position'][:30]}",
                "right": f"{mp[1]['model']} → {mp[1]['position'][:30]}",
                "level": "高" if rc["severity"] >= 0.7 else "中" if rc["severity"] >= 0.4 else "低"
            })

    # Stance-based conflict
    stance_groups = {"support": [], "oppose": [], "neutral": []}
    for v in viewpoints:
        stance_groups[v["stance"]].append(v["model"])
    if stance_groups["support"] and stance_groups["oppose"]:
        conflicts.insert(0, {
            "title": "执行决策分歧",
            "left": f'{stance_groups["support"][0]} → 建议执行',
            "right": f'{stance_groups["oppose"][0]} → 建议观望',
            "level": "高"
        })

    # 4. CEO 裁决
    n_all = len(texts)
    pos_count = len(stance_groups["support"]) + 0.5 * len(stance_groups["neutral"])
    neg_count = len(stance_groups["oppose"]) + 0.5 * len(stance_groups["neutral"])
    if pos_count >= n_all * 0.75:
        decision_text = "建议执行"
        confidence = round(0.6 + (pos_count - neg_count) * 0.1, 2)
    elif neg_count >= n_all * 0.75:
        decision_text = "建议观望或小范围测试"
        confidence = round(0.6 + (neg_count - pos_count) * 0.1, 2)
    else:
        decision_text = "意见分歧较大"
        confidence = 0.5

    ceo_result = weighted_arbitration(viewpoints, raw_conflicts)

    # 5. 执行计划
    context = {"background": background, "budget": "", "timeframe": ""}
    try:
        execution = build_execution_pack(decision_text, confidence, raw_conflicts, context)
    except Exception:
        execution = {"goal": topic, "actions": ["参考CEO分析做决策"], "timeline": "", "risks": [], "kpis": []}

    # 6. 前端 format
    agents = []
    role_map = ["东方战略官", "批判分析官", "风险控制官", "增长策略官"]
    for i, v in enumerate(viewpoints):
        stance_label = "支持" if v["stance"] == "support" else "反对" if v["stance"] == "oppose" else "中立"
        agents.append({
            "role": role_map[i % len(role_map)],
            "model": v["model"],
            "stance": stance_label,
            "reason": (v["reasons"] or [""])[0]
        })

    steps = execution.get("actions", ["参考CEO分析做决策"])
    risks = execution.get("risks", [])
    risk_str = risks[0] if risks else "请关注执行过程中的关键风险"

    return {
        "agents": agents,
        "conflicts": conflicts,
        "decision": {
            "decision": ceo_result.get("decision", decision_text),
            "confidence": round((ceo_result.get("confidence", confidence) or confidence) * 100),
            "rationale": (ceo_result.get("summary", "") or ceo_result.get("rationale", "") or "基于多模型冲突分析，综合决策。")[:200],
            "steps": steps[:5],
            "risk": risk_str
        }
    }

# ──────────────────────────────────────────────────────────────
# HEALTH & STARTUP
# ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "engine": "real" if _HAS_REAL_ENGINE else "mock"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"[START] AI Decision Room on 0.0.0.0:{port} | Engine: {'REAL' if _HAS_REAL_ENGINE else 'MOCK'}")
    uvicorn.run(app, host="0.0.0.0", port=port)
