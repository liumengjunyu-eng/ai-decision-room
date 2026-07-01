# AI Decision Room - 辩论可视化功能集成

**时间**: 2026-07-01 11:58  
**目标**: 将「AI董事会辩论可视化」集成到 ai-decision-room 项目

## 核心改动

### 前端 HTML/CSS/JS（app.py）

1. **新增辩论区 DOM** — 「💬 AI 董事会辩论」区块
2. **辩论可视化 CSS** — debate-container, debate-card(active/done), debate-header(icon/name/status+specific colors), debate-content(cursor+typing), debate-stance标签
3. **JS 函数**:
   - `renderDebate(data)` — 构建辩论卡片 HTML + 启动流式
   - `startDebateStream(agents)` — 依次打字+状态切换(发言中闪烁→已发言✓)
   - `afterDebateComplete(agents)` — 辩论结束后渲染AI意见+冲突+决策
   - 通过 `window._pendingAPIData` 串联 API 数据和辩论播放
4. **runFreeDecision 改造** — 清空旧数据→API请求→保存数据到 `_pendingAPIData`→启动 `renderDebate`
5. **renderMockData 改造** — 同样通过 `_pendingAPIData + renderDebate` 走辩论流程
6. **修复**：增加免费次数至20，加载提示信息，agentGrid 命名冲突

### 用户可见效果

点击"生成分析"后:
1. 4个AI依次逐字打字发言（30ms/字，800ms间隔）
2. 每个卡片有状态: 等待发言 → 发言中(闪烁) → 已发言✓
3. 自动滚动到最新发言
4. 全部发言结束 → 自动展示冲突+决策

### 提交
- Commit: `e0c6129` feat: AI董事会辩论可视化
- 已推送到 GitHub
