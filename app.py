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
ROOM_HTML = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Decision Graph</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0B0F19;
  --border: rgba(255,255,255,0.06);
  --text: #E6E6E6;
  --text-sec: #8A92A8;
  --text-muted: #4A5268;
  --purple: #7C5CFF;
  --purple-dim: rgba(124,92,255,0.12);
  --red: #FF6B6B;
  --green: #4ADE80;
  --radius: 10px;
  --radius-lg: 14px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:var(--font); overflow:hidden; height:100vh; }
.topbar { height:56px; display:flex; align-items:center; padding:0 24px; border-bottom:1px solid var(--border); background:rgba(255,255,255,0.02); justify-content:space-between; }
.logo { font-weight:600; font-size:15px; letter-spacing:0.3px; }
.logo span { color:var(--purple); }
.header-actions { display:flex; align-items:center; gap:16px; }
.badge { font-size:13px; color:var(--text-sec); background:rgba(255,255,255,0.04); border:1px solid var(--border); padding:4px 14px; border-radius:20px; display:flex; align-items:center; gap:8px; }
.badge strong { color:var(--text); }
.view-toggle { display:flex; gap:2px; background:rgba(255,255,255,0.04); border-radius:8px; padding:3px; border:1px solid var(--border); }
.view-btn { padding:6px 14px; border:none; border-radius:6px; background:transparent; color:var(--text-muted); font-family:var(--font); font-size:12px; font-weight:500; cursor:pointer; }
.view-btn.active { background:var(--purple-dim); color:var(--purple); }
.app { display:flex; height:calc(100vh - 56px); width:100%; }
.panel { width:320px; min-width:320px; border-right:1px solid var(--border); padding:24px 20px; display:flex; flex-direction:column; gap:16px; background:rgba(255,255,255,0.01); overflow-y:auto; }
.panel .hint { font-size:13px; color:var(--text-muted); line-height:1.6; }
.panel .divider { border:none; border-top:1px solid var(--border); margin:4px 0; }
.input-group label { display:block; font-size:12px; font-weight:500; color:var(--text-sec); margin-bottom:6px; letter-spacing:0.3px; }
.input-group textarea { width:100%; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:var(--radius); padding:12px 14px; color:var(--text); font-size:14px; line-height:1.5; resize:vertical; min-height:80px; outline:none; font-family:inherit; }
.input-group textarea:focus { border-color:var(--purple); }
.btn { padding:12px 20px; border-radius:var(--radius); background:var(--purple); border:none; color:white; font-weight:600; font-size:14px; cursor:pointer; width:100%; }
.btn:hover { background:#6B4DE0; }
.btn:disabled { opacity:0.35; cursor:not-allowed; }
.ad-banner { display:none; align-items:center; justify-content:space-between; padding:10px 14px; background:rgba(255,107,107,0.08); border:1px solid rgba(255,107,107,0.12); border-radius:var(--radius); flex-wrap:wrap; gap:8px; }
.ad-banner.active { display:flex; }
.ad-banner .ad-btn { padding:6px 16px; background:var(--red); border:none; border-radius:6px; color:#fff; font-weight:600; font-size:12px; cursor:pointer; }
.graph { flex:1; position:relative; overflow:hidden; background:radial-gradient(ellipse at 70% 50%,rgba(124,92,255,0.04),transparent 60%),radial-gradient(ellipse at 30% 80%,rgba(124,92,255,0.02),transparent 40%); }
.stream-view { flex:1; overflow-y:auto; padding:32px 48px; display:none; }
.stream-view.active { display:block; }
.node { position:absolute; padding:14px 18px; border-radius:var(--radius-lg); background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); min-width:120px; max-width:200px; box-shadow:0 4px 20px rgba(0,0,0,0.2); backdrop-filter:blur(4px); }
.node.ceo { background:var(--purple-dim); border-color:rgba(124,92,255,0.4); }
.node .role { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; opacity:0.6; margin-bottom:4px; }
.node .content { font-size:13px; line-height:1.5; }
.edge { position:absolute; height:1px; background:rgba(255,255,255,0.08); transform-origin:0 0; pointer-events:none; }
.edge.active { background:rgba(124,92,255,0.25); }
.empty-state { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; color:var(--text-muted); font-size:14px; pointer-events:none; }
.flow-item { display:flex; gap:16px; padding:16px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.flow-item .avatar { width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px; background:rgba(255,255,255,0.04); border:1px solid var(--border); flex-shrink:0; }
.flow-item .content { flex:1; min-width:0; }
.flow-item .content .meta { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:4px; }
.flow-item .content .meta .name { font-weight:600; font-size:15px; }
.flow-item .content .meta .title { font-size:12px; color:var(--text-muted); }
.flow-item .content .text { font-size:14px; color:var(--text-sec); line-height:1.7; min-height:22px; }
.stance-tag { font-size:11px; font-weight:600; padding:2px 12px; border-radius:12px; }
.stance-tag.support { background:rgba(74,222,128,0.12); color:var(--green); }
.stance-tag.oppose { background:rgba(255,107,107,0.12); color:var(--red); }
.stance-tag.neutral { background:rgba(255,255,255,0.04); color:var(--text-muted); }
.status-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:16px; }
.status-dot.waiting { background:var(--text-muted); }
.status-dot.speaking { background:var(--purple); animation:pulse-dot 1s ease-in-out infinite; }
.status-dot.done { background:var(--green); }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }
.sec-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted); margin-bottom:16px; }
.conflict-bar-group { display:flex; flex-direction:column; gap:12px; background:rgba(255,255,255,0.02); border-radius:var(--radius-lg); padding:20px; border:1px solid var(--border); margin-bottom:24px; }
.conflict-item { display:flex; flex-direction:column; gap:4px; }
.conflict-label { display:flex; justify-content:space-between; font-size:13px; color:var(--text-sec); }
.conflict-label .l { color:var(--purple); }
.conflict-label .r { color:var(--red); }
.conflict-track { height:4px; background:rgba(255,255,255,0.06); border-radius:4px; overflow:hidden; display:flex; }
.conflict-track .fill { height:100%; }
.conflict-track .fill.l { background:var(--purple); }
.conflict-track .fill.r { background:var(--red); }
.conflict-meta { display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted); margin-top:2px; }
.ceo-card { background:var(--purple-dim); border:1px solid rgba(124,92,255,0.15); border-radius:var(--radius-lg); padding:20px 24px; }
.ceo-card .lab { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:var(--purple); margin-bottom:6px; }
.ceo-card .dec { font-size:24px; font-weight:700; letter-spacing:-0.02em; }
.ceo-card .conf { font-size:14px; color:var(--text-sec); margin-top:4px; }
.ceo-card .div { height:1px; background:var(--border); margin:12px 0; }
.ceo-card .rea { font-size:14px; color:var(--text-sec); line-height:1.7; }
.ceo-card .steps { margin-top:12px; }
.ceo-card .steps .slab { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; color:var(--text-muted); margin-bottom:6px; }
.ceo-card .steps ul { list-style:none; padding:0; }
.ceo-card .steps ul li { font-size:14px; color:var(--text-sec); padding:4px 0 4px 20px; position:relative; }
.ceo-card .steps ul li::before { content:'\\25B9'; position:absolute; left:0; color:var(--purple); }
.ceo-card .risk { margin-top:12px; display:inline-flex; align-items:center; gap:8px; font-size:13px; color:var(--red); padding:4px 14px; border-radius:20px; }
@media (max-width:768px){ .app{flex-direction:column;height:auto} .panel{width:100%;min-width:unset;border-right:none;padding:16px} .graph{height:500px;min-height:300px;flex:none} .stream-view{padding:24px} }
@media (max-width:480px){ .topbar{padding:0 16px;height:48px} .panel{padding:12px} .graph{height:400px;min-height:250px} }
</style>
</head>
<body>
<header class="topbar">
  <div class="logo">🧠 AI <span>Decision Graph</span></div>
  <div class="header-actions">
    <div class="view-toggle" id="viewToggle">
      <button class="view-btn active" data-view="graph">📊 图谱</button>
      <button class="view-btn" data-view="stream">💬 辩论</button>
    </div>
    <div class="badge"><span>今日剩余</span> <strong id="remainingCount">10</strong> <span>次</span></div>
  </div>
</header>
<div class="app">
  <aside class="panel">
    <div class="input-group">
      <label for="problemInput">决策议题</label>
      <textarea id="problemInput" placeholder="例如：蕲艾五官灸是否要做小红书投放？"></textarea>
    </div>
    <button class="btn" id="runBtn">🚀 启动 AI 董事会</button>
    <div class="ad-banner" id="adBanner">
      <span class="ad-text">📺 今日已用完，看 15s广告 解锁 5次</span>
      <button class="ad-btn" id="adBtn">▶ 观看广告</button>
    </div>
    <hr class="divider" />
    <div class="hint"><strong>⚡ 决策图谱</strong><br>各 AI 角色独立分析 → 冲突收敛 → CEO 裁决<br><br><span style="font-size:12px;color:var(--text-muted);">节点位置反映观点空间关系</span></div>
  </aside>
  <main class="graph" id="graphContainer">
    <div class="empty-state" id="emptyState"><div class="icon">🧠</div><div class="text">输入决策问题<br>点击启动 AI 董事会</div></div>
  </main>
  <div class="stream-view" id="streamView">
    <div class="sec-label">💬 董事会辩论</div>
    <div id="agentGrid"></div>
    <div class="sec-label" style="margin-top:32px;">⚔️ 核心冲突</div>
    <div id="conflictContainer" class="conflict-bar-group"><div style="color:var(--text-muted);padding:20px;text-align:center;">⏳ 运行分析后显示</div></div>
    <div style="margin-top:24px;"><div class="sec-label">👑 CEO 裁决</div><div id="decisionContainer" class="ceo-card"><div class="lab">最终决策</div><div style="color:var(--text-muted);font-size:14px;">等待辩论结束...</div></div></div>
  </div>
</div>
<script>
(function(){
var S = function(id){ return document.getElementById(id); };
var B = [
  {id:'strategy',role:'\u6218\u7565\u5b98',icon:'\uD83E\uDDD9',color:'#7C5CFF',x:0.20,y:0.20,stance:'support',title:'CSO'},
  {id:'critic',role:'\u6279\u5224\u5b98',icon:'\u2694\uFE0F',color:'#FF6B6B',x:0.20,y:0.45,stance:'oppose',title:'CRO'},
  {id:'risk',role:'\u98ce\u63a7\u5b98',icon:'\uD83D\uDEE1\uFE0F',color:'#F59E0B',x:0.20,y:0.65,stance:'neutral',title:'COO'},
  {id:'growth',role:'\u589e\u957f\u5b98',icon:'\uD83D\uDCC8',color:'#4ADE80',x:0.20,y:0.85,stance:'support',title:'CGO'},
  {id:'insight',role:'\u6d1e\u5bdf\u5b98',icon:'\uD83D\uDD0D',color:'#38BDF8',x:0.20,y:0.05,stance:'support',title:'CCO'},
  {id:'innovation',role:'\u521b\u65b0\u5b98',icon:'\uD83D\uDE80',color:'#A78BFA',x:0.72,y:0.08,stance:'support',title:'CIO'},
  {id:'ceo',role:'CEO\u88c1\u51b3\u5b98',icon:'\uD83D\uDC51',color:'#7C5CFF',x:0.65,y:0.50,stance:'support',title:'CEO'},
];
var ST = {remaining:10,isAdPlaying:false,userId:function(){try{return localStorage.getItem('duid')||'d'}catch(e){return 'd'}}()};
var G=S('graphContainer'),ES=S('emptyState'),RB=S('runBtn'),PI=S('problemInput'),RE=S('remainingCount'),AB=S('adBanner'),AD=S('adBtn'),SV=S('streamView'),AG=S('agentGrid'),CC=S('conflictContainer'),DC=S('decisionContainer');
var pn=[],ca=null;
function ls(){try{var d=JSON.parse(localStorage.getItem('dr_'+ST.userId));if(d&&d.date===(new Date()).toDateString())ST.remaining=d.remaining;else{ST.remaining=10;sv()}}catch(e){ST.remaining=10;sv()}up();}
function sv(){try{localStorage.setItem('dr_'+ST.userId,JSON.stringify({date:(new Date()).toDateString(),remaining:ST.remaining}))}catch(e){}}
function u1(){if(ST.remaining<=0)return false;ST.remaining--;sv();up();return true;}
function up(){RE.textContent=ST.remaining;RB.disabled=ST.remaining<=0;AB.classList.toggle('active',ST.remaining<=0);}
function ua(){if(ST.isAdPlaying)return;ST.isAdPlaying=true;AD.disabled=true;AD.textContent='\\u23f3 '+'15s';var s=15;var iv=setInterval(function(){s--;AD.textContent='\\u23f3 '+s+'s';if(s<=0){clearInterval(iv);ST.remaining=Math.min(10,ST.remaining+5);ST.isAdPlaying=false;sv();up();AD.disabled=false;AD.textContent='\\u25b6 '+'\\u89c2\\u770b\\u5e7f\\u544a';}},1000);}
function cg(){var e=G.querySelectorAll('.node,.edge');for(var i=0;i<e.length;i++)e[i].remove();pn=[];ES.style.display='block';}
function cn(m,t,c){var sz=G.getBoundingClientRect(),pad=60,x=(m.x||0.5)*(sz.width-pad*2)+pad,y=(m.y||0.5)*(sz.height-pad*2)+pad;var el=document.createElement('div');el.className='node'+(c?' ceo':'');el.style.cssText='left:'+x+'px;top:'+y+'px;';var sm={support:'\\u2705 '+'\\u652f\\u6301',oppose:'\\u274c '+'\\u53cd\\u5bf9',neutral:'\\u2696\\ufe0f'+'\\u4e2d\\u7acb'};var sd=sm[m.stance]||m.stance;if(c)el.innerHTML='<div class="role">\\ud83d\\udc51'+m.role+'</div><div class="content">'+t+'</div>';else el.innerHTML='<div class="role">'+m.icon+' '+m.role+' \\u00b7 '+sd+'</div><div class="content">'+t+'</div>';G.appendChild(el);pn.push({el:el,x:x,y:y});return el;}
function de(){var ce=null;for(var i=0;i<pn.length;i++){if(pn[i].el.classList.contains('ceo')){ce=pn[i];break}}if(!ce)return;var cr=ce.el.getBoundingClientRect(),gr=G.getBoundingClientRect(),cx=cr.left-gr.left+cr.width/2,cy=cr.top-gr.top+cr.height/2;for(var i=0;i<pn.length;i++){var n=pn[i];if(n.el===ce.el)continue;var r=n.el.getBoundingClientRect(),x1=r.left-gr.left+r.width,y1=r.top-gr.top+r.height/2,dx=cx-x1,dy=cy-y1,len=Math.sqrt(dx*dx+dy*dy),ang=Math.atan2(dy,dx)*180/Math.PI;var l=document.createElement('div');l.className='edge active';l.style.cssText='width:'+len+'px;left:'+x1+'px;top:'+y1+'px;transform:rotate('+ang+'deg);';G.appendChild(l);}}
function rg(a){cg();ES.style.display='none';var ni=[];for(var i=0;i<Math.min(B.length-1,a.length);i++){var m=JSON.parse(JSON.stringify(B[i])),v=a[i]||{};m.stance=v.stance||'neutral';cn(m,v.reason||v.output||'...',false);ni.push(pn[pn.length-1]);}
setTimeout(function(){cn({role:'CEO \\u88c1\\u51b3',stance:'support',x:0.75,y:0.45},'\\u7efc\\u5408\\u5206\\u6790\\u4e2d...',true);setTimeout(de,200);},500);}
function pb(a,od){if(!a||a.length===0){if(od)od();return}var h='';for(var i=0;i<a.length;i++){var v=a[i],m=B[i]||{},st=v.stance||'neutral',lb=st==='support'?'\\u652f\\u6301':st==='oppose'?'\\u53cd\\u5bf9':'\\u4e2d\\u7acb';h+='<div class="flow-item" id="f-'+i+'"><div class="avatar">'+(m.icon||'\\ud83e\\udde0')+'</div><div class="content"><div class="meta"><span class="name">'+(m.role||v.role||'AI')+'</span><span class="title">'+(m.title||'')+'</span><span class="stance-tag '+st+'">'+lb+'</span></div><div class="text" id="t-'+i+'"></div></div><span class="status-dot waiting" id="d-'+i+'"></span></div>';}
AG.innerHTML=h;var idx=0;function nx(){if(idx>=a.length){if(od)od();return}var it=S('f-'+idx),te=S('t-'+idx),dt=S('d-'+idx);it.style.opacity='1';dt.className='status-dot speaking';var tx=a[idx].reason||a[idx].output||'\\u2014',ci=0;te.textContent='';var ti=setInterval(function(){if(ci<tx.length){te.textContent+=tx[ci];ci++}else{clearInterval(ti);dt.className='status-dot done';idx++;setTimeout(nx,300)}},20);}
setTimeout(nx,200);}
function rc(c){if(!c||c.length===0){CC.innerHTML='<div style="color:var(--text-muted);text-align:center;padding:20px;">\\u2705 '+'\\u672a\\u68c0\\u6d4b\\u5230\\u660e\\u663e\\u51b2\\u7a81</div>';return}var h='';for(var i=0;i<c.length;i++){var f=c[i],s=f.severity_pct||50;h+='<div class="conflict-item"><div class="conflict-label"><span class="l">'+(f.left||'')+'</span><span class="r">'+(f.right||'')+'</span></div><div class="conflict-track"><div class="fill l" style="width:'+s+'%;"></div><div class="fill r" style="width:'+(100-s)+'%;"></div></div><div class="conflict-meta"><span>'+(f.title||'')+'</span><span>\\u5f3a\\u5ea6 '+s+'%</span></div></div>';}
CC.innerHTML=h;}
function rd(d){if(!d||!d.decision){DC.innerHTML='<div class="lab">\\u6700\\u7ec8\\u51b3\\u7b56</div><div style="color:var(--text-muted);font-size:14px;">\\u7b49\\u5f85\\u8fa9\\u8bba\\u7ed3\\u675f...</div>';return}var st=d.steps||[''];DC.innerHTML='<div class="lab">\\u6700\\u7ec8\\u51b3\\u7b56</div><div class="dec">'+d.decision+'</div><div class="conf">\\u7f6e\\u4fe1\\u5ea6 '+(d.confidence||78)+'%</div><div class="div"></div><div class="rea">'+(d.rationale||'')+'</div><div class="steps"><div class="slab">\\u6267\\u884c\\u8def\\u5f84</div><ul>'+st.map(function(s){return '<li>'+s+'</li>'}).join('')+'</ul></div><div class="risk">\\u26a0 '+(d.risk||'')+'</div>';}
var mA=[{stance:'support',reason:'\\u4e09\\u4f0f\\u5929\\u662f\\u517b\\u751f\\u5fc3\\u667a\\u6700\\u5f3a\\u65f6\\u671f\\uff0c\\u7ade\\u54c1\\u5df2\\u9a8c\\u8bc1\\u8def\\u5f84\\uff0c\\u5efa\\u8bae\\u5c0f\\u6b65\\u5feb\\u8dd1\\u62a2\\u5360\\u5148\\u673a\\u3002'},{stance:'oppose',reason:'3\\u4e07\\u9884\\u7b97\\u5728\\u5c0f\\u7ea2\\u4e66\\u6d4b\\u8bd5\\u95e8\\u69db\\u4e0d\\u8db3\\uff0c\\u7ade\\u54c1\\u5df2\\u5360\\u636e\\u5fc3\\u667a\\uff0c\\u6b64\\u65f6\\u8fdb\\u5165\\u6210\\u672c\\u8fc7\\u9ad8\\u3002'},{stance:'neutral',reason:'\\u98ce\\u9669\\u53ef\\u63a7\\u4f46\\u9700\\u8c28\\u614e\\u3002\\u5efa\\u8bae\\u8bbe5000\\u5143\\u6b62\\u635f\\u7ebf\\uff0c48h\\u5185\\u5b8c\\u6210\\u9a8c\\u8bc1\\u3002'},{stance:'support',reason:'\\u8d5b\\u9053\\u7684\\u83b7\\u5ba2\\u6210\\u672c\\u6b63\\u4e0a\\u5347\\uff0c\\u73b0\\u5728\\u662f\\u5361\\u4f4d\\u6700\\u540e\\u7a97\\u53e3\\u3002\\u5efa\\u8bae\\u75285000\\u5143\\u505aAB\\u6d4b\\u8bd5\\u3002'},{stance:'support',reason:'\\u5c0f\\u7ea2\\u4e66\\u517b\\u751f\\u4eba\\u7fa4\\u589e\\u957f43%\\uff0c\\u5185\\u5bb9\\u6d4b\\u8bd5\\u6210\\u672c\\u4f4e\\u4e8e3\\u5343\\u5143\\u5373\\u53ef\\u9a8c\\u8bc1\\uff0c\\u503c\\u5f97\\u5c1d\\u8bd5\\u3002'},{stance:'support',reason:'\\u53ef\\u7ed3\\u5408AI\\u751f\\u6210\\u6d4b\\u8bc4\\u5185\\u5bb9+UGC\\u88c2\\u53d8\\uff0c\\u4ee5\\u6781\\u4f4e\\u6210\\u672c\\u5b8c\\u6210\\u51b7\\u542f\\u52a8\\uff0c\\u5efa\\u8bae\\u6267\\u884c\\u3002'},{stance:'support',reason:'\\u7efc\\u5408\\u610f\\u89c1\\u2014\\u20144\\u7968\\u652f\\u6301\\u30011\\u7968\\u53cd\\u5bf9\\u30011\\u7968\\u4e2d\\u7acb\\uff0c\\u5efa\\u8bae\\u6295\\u51658000\\u5143\\u505a2\\u5468\\u5185\\u5bb9\\u6d4b\\u8bd5\\u3002'}];
var mC=[{title:'\\u9884\\u7b97\\u5224\\u65ad\\u5206\\u6b67',left:'\\u6218\\u7565\\u5b98 3\\u4e07\\u8db3\\u591f',right:'\\u6279\\u5224\\u5b98 3\\u4e07\\u4e0d\\u8db3',severity_pct:82},{title:'\\u65f6\\u95f4\\u7a97\\u53e3',left:'\\u589e\\u957f\\u5b98 \\u5fc5\\u987b7\\u6708\\u524d',right:'\\u98ce\\u63a7\\u5b98 \\u53ef\\u5ef6\\u540e',severity_pct:65},{title:'\\u6e20\\u9053\\u7b56\\u7565\\u5206\\u6b67',left:'\\u6d1e\\u5bdf\\u5b98 \\u5c0f\\u7ea2\\u4e66\\u4f4e\\u6210\\u672c',right:'\\u6279\\u5224\\u5b98 ROI\\u4e0d\\u786e\\u5b9a',severity_pct:48}];
var mD={decision:'\\u5c0f\\u89c4\\u6a21\\u6d4b\\u8bd5\\uff08\\u5efa\\u8bae8000\\u5143\\u9884\\u7b97\\uff09',confidence:82,rationale:'6\\u4f4d\\u8463\\u4e8b\\u6295\\u7968\\uff1a4\\u7968\\u652f\\u6301\\u30011\\u7968\\u53cd\\u5bf9\\u30011\\u7968\\u4e2d\\u7acb\\u3002\\u5e02\\u573a\\u5b58\\u5728\\u771f\\u5b9e\\u9700\\u6c42\\u4fe1\\u53f7\\uff0c\\u98ce\\u9669\\u53ef\\u63a7\\u3002',steps:['\\u7b5b\\u90093\\u4e2aKOC\\u8d26\\u53f7\\u8be2\\u4ef7','\\u5236\\u4f5c2\\u6761AI+\\u771f\\u4eba\\u5185\\u5bb9','\\u6295\\u51658000\\u5143\\u8d912\\u5468','\\u7b2c7\\u5929\\u590d\\u76d8\\uff0cROI>1.0\\u5219\\u8ffd\\u52a0'],risk:'\\u521d\\u671f\\u8f6c\\u5316\\u6ce2\\u52a8\\u8f83\\u5927\\uff0c\\u5185\\u5bb9\\u8d28\\u91cf\\u51b3\\u5b9aROI\\u4e0a\\u9650\\u3002\\u9700\\u9884\\u75592\\u4e07\\u5143\\u6b62\\u635f\\u7ebf\\u3002'};

async function rd2(){if(!u1())return;RB.disabled=true;RB.textContent='\\u23f3'+'\\u5206\\u6790\\u4e2d...';DC.innerHTML='<div class="lab">\\u6700\\u7ec8\\u51b3\\u7b56</div><div style="color:var(--text-muted);font-size:14px;">\\u23f3'+'AI\\u8463\\u4e8b\\u4f1a\\u6b63\\u5728\\u5206\\u6790...</div>';try{var pl={topic:PI.value.trim()||'\\u8548\\u827e\\u4e94\\u5b98\\u7092\\u662f\\u5426\\u505a\\u5c0f\\u7ea2\\u4e66\\u6295\\u653e',background:''};var r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pl)});var d=await r.json();var a=d.agents||mA,cf=d.conflicts||mC,dc=d.decision||mD;ca=a;rg(a);pb(a,function(){rc(cf);rd(dc);})}catch(e){rg(mA);pb(mA,function(){rc(mC);rd(mD);})}RB.disabled=false;RB.textContent='\\ud83d\\ude80'+'\\u542f\\u52a8 AI \\u8463\\u4e8b\\u4f1a';}

var btns=document.querySelectorAll('.view-btn');for(var i=0;i<btns.length;i++){btns[i].addEventListener('click',function(){for(var j=0;j<btns.length;j++)btns[j].classList.remove('active');this.classList.add('active');var v=this.dataset.view;G.style.display=v==='graph'?'block':'none';SV.classList.toggle('active',v==='stream');});}
ls();RB.addEventListener('click',rd2);AD.addEventListener('click',ua);PI.addEventListener('keydown',function(e){if(e.key==='Enter')rd2();});
setTimeout(function(){rg(mA);pb(mA,function(){rc(mC);rd(mD);})},300);
var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(function(){if(ca)rg(ca)},400);});
})();
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
