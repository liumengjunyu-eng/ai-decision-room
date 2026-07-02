"""
V4.1 可信度核心引擎 (Decision Trust Engine)
纯 Python 实现，无外部 ML 依赖

评分维度：
1. 一致性评分 (Consistency) - TF-IDF + 余弦相似度
2. 证据评分 (Evidence) - 启发式规则
3. 共识评分 (Consensus) - 与群体中心的距离
4. 领域适配 (Domain) - 模型画像
5. 历史可信度 (Historical) - 历史准确性
"""
import math
import re
from collections import Counter
from typing import Dict, List, Tuple

from .config import get_profile, get_domain_score, get_historical_score, get_size_bonus
from .models import ModelScore, ConflictMatrix, EvaluationResult


class DecisionEngine:
    """决策可信度引擎 - 多模型意见 → 可计算信任结构"""
    
    def evaluate(self, question: str, answers: Dict[str, str],
                 task_type: str = "general", model_role_map: dict = None) -> dict:
        """
        主入口：评估多模型回答的可信度
        
        Args:
            question: 决策问题
            answers: {"模型名": "回答文本"}
            task_type: 任务类型 (general/strategy/risk/market/coding/innovation)
            model_role_map: 可选的模型→角色映射 (System 1 使用)
        
        Returns:
            结构化评估结果
        """
        models = list(answers.keys())
        texts = list(answers.values())
        n = len(texts)
        if n == 0:
            return self._empty_result(question)
        
        # 1. 一致性评分 (20%)
        consistency = self._consistency_score(texts, models)
        
        # 2. 证据评分 (20%)
        evidence = self._evidence_score(texts, models)
        
        # 3. 共识评分 (20%)
        consensus = self._consensus_score(texts, models)
        
        # 4. 领域适配 (25%)
        domain = self._domain_score(models, task_type)
        
        # 5. 历史可信度 (15%)
        historical = self._historical_score(models)
        
        # 加权融合
        weights = {"consistency": 0.20, "evidence": 0.20,
                   "consensus": 0.20, "domain": 0.25, "historical": 0.15}
        
        model_scores = {}
        final_scores_raw = {}
        
        for i, m in enumerate(models):
            s = ModelScore(
                consistency=round(consistency[m], 4),
                evidence=round(evidence[m], 4),
                consensus=round(consensus[m], 4),
                domain=round(domain[m], 4),
                historical=round(historical[m], 4)
            )
            s.final_score = round(
                weights["consistency"] * s.consistency +
                weights["evidence"] * s.evidence +
                weights["consensus"] * s.consensus +
                weights["domain"] * s.domain +
                weights["historical"] * s.historical,
                4
            )
            model_scores[m] = s
            final_scores_raw[m] = s.final_score
        
        # 归一化到 0-100
        max_score = max(final_scores_raw.values()) if final_scores_raw else 1
        scores_100 = {
            m: round(v / max_score * 100, 2) if max_score > 0 else 0
            for m, v in final_scores_raw.items()
        }
        
        # 冲突矩阵
        conflict = self._conflict_matrix(texts, models)
        
        # V4 兼容的可信度评分
        trust_score = self._calculate_global_trust(
            model_scores, conflict, models, model_role_map
        )
        
        # 洞察
        insight = self._generate_insight(scores_100, models)
        
        return {
            "question": question,
            "model_scores": {m: {
                "consistency": ms.consistency,
                "evidence": ms.evidence,
                "consensus": ms.consensus,
                "domain": ms.domain,
                "historical": ms.historical,
                "final": ms.final_score
            } for m, ms in model_scores.items()},
            "scores_100": scores_100,
            "conflict": {
                "matrix": conflict["matrix"],
                "pairs": conflict["pairs"],
                "summary": conflict["summary"]
            },
            "trust_score": trust_score,
            "insight": insight,
            "weights": weights
        }
    
    # ═══════════════════════════════════════
    # V2 可信度引擎 — 五维度评分（融资级）
    # ═══════════════════════════════════════

    def credibility_v2(self, question: str, answers: Dict[str, str],
                       task_type: str = "general") -> dict:
        """
        V2 可信度引擎：对每个模型输出进行5维度深度评分
        
        维度：
        1. 逻辑结构 (Logic Depth) — 因果链/推导过程
        2. 证据密度 (Evidence Density) — 数据/案例引用
        3. 语义一致性 (Semantic Consistency) — 内部自洽
        4. 反事实鲁棒性 (Counterfactual Robustness) — 是否过度绝对
        5. 领域适配 (Domain Fit) — 模型擅长的领域
        """
        models = list(answers.keys())
        texts = list(answers.values())
        
        results = {}
        for model, text in zip(models, texts):
            # 1. 逻辑结构评分
            logic = self._v2_logic_depth(text)
            
            # 2. 证据密度
            evidence = self._v2_evidence_density(text)
            
            # 3. 语义一致性
            consistency = self._v2_semantic_consistency(text)
            
            # 4. 反事实鲁棒性
            robustness = self._v2_counterfactual_robustness(text)
            
            # 5. 领域适配
            domain = self._model_domain_fit(model, task_type)
            
            # 加权融合
            weights = {"logic": 0.25, "evidence": 0.20, "consistency": 0.20,
                       "robustness": 0.20, "domain": 0.15}
            raw = (logic * weights["logic"] + evidence * weights["evidence"] +
                   consistency * weights["consistency"] + robustness * weights["robustness"] +
                   domain * weights["domain"])
            
            final = round(raw * 100, 2)
            
            # 生成维度分解
            breakdown = {
                "logic": {"score": round(logic * 100, 1), "label": "逻辑结构",
                          "desc": self._v2_logic_desc(logic)},
                "evidence": {"score": round(evidence * 100, 1), "label": "证据密度",
                             "desc": self._v2_evidence_desc(evidence)},
                "consistency": {"score": round(consistency * 100, 1), "label": "语义一致性",
                                "desc": self._v2_consistency_desc(consistency)},
                "robustness": {"score": round(robustness * 100, 1), "label": "反事实鲁棒性",
                               "desc": self._v2_robustness_desc(robustness)},
                "domain": {"score": round(domain * 100, 1), "label": "领域适配",
                           "desc": f"该模型在{task_type}领域评分为{round(domain*100,1)}%"}
            }
            
            # 优势与劣势分析
            dims = [("logic", logic), ("evidence", evidence), ("consistency", consistency),
                    ("robustness", robustness), ("domain", domain)]
            sorted_dims = sorted(dims, key=lambda x: -x[1])
            strengths = [breakdown[d[0]]["label"] for d in sorted_dims[:2] if d[1] >= 0.5]
            weaknesses = [breakdown[d[0]]["label"] for d in sorted_dims[-2:] if d[1] < 0.5]
            
            results[model] = {
                "total_score": final,
                "breakdown": breakdown,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "verdict": self._v2_verdict(final, strengths, weaknesses)
            }
        
        # 排序
        ranked = sorted(results.items(), key=lambda x: -x[1]["total_score"])
        
        return {
            "results": results,
            "ranking": [{"model": m, "score": d["total_score"],
                         "verdict": d["verdict"]} for m, d in ranked],
            "dimensions": ["logic", "evidence", "consistency", "robustness", "domain"]
        }
    
    def _v2_logic_depth(self, text: str) -> float:
        """逻辑结构深度评分"""
        score = 0.3
        # 因果连词
        if re.search(r'(因为|所以|如果|那么|因此|但|然而|由于|导致|意味着)', text): score += 0.15
        # 推导结构
        if re.search(r'(第一步|第二步|首先|其次|最后|总结)', text): score += 0.10
        # 条件假设
        if re.search(r'(假设|假如|如果.*则|条件)', text): score += 0.10
        # 对比分析
        if re.search(r'(相比|对比|一方面|另一方面|优劣)', text): score += 0.10
        # 多层次（分段）
        paragraphs = text.strip().split('\n')
        if len(paragraphs) >= 3: score += 0.10
        if len(text) > 300: score += 0.10
        if len(text) > 800: score += 0.05
        return min(score, 1.0)
    
    def _v2_evidence_density(self, text: str) -> float:
        """证据密度评分"""
        score = 0.3
        if re.search(r'\d+%|百分之\d+|\d+\.\d+%', text): score += 0.15
        if re.search(r'\d{3,}|\d+万|\d+亿|\d+人|\d+元', text): score += 0.10
        if re.search(r'(例如|比如|案例|case|example|举例)', text, re.I): score += 0.10
        if re.search(r'(根据|数据显示|研究表明|报告|统计|调查)', text): score += 0.10
        if re.search(r'(1\.|2\.|3\.|第一|第二|第三|①|②|③)', text): score += 0.10
        if re.search(r'(https?://|www\.|参见|参考)', text, re.I): score += 0.05
        words = len(text)
        if 100 < words < 3000: score += 0.05
        return min(score, 1.0)
    
    def _v2_semantic_consistency(self, text: str) -> float:
        """语义一致性：检测内部是否自相矛盾"""
        score = 0.7  # 默认较高
        # 检测矛盾信号词
        contradictions = [
            (r'(但是|然而).{0,20}(不|反对|有问题)', -0.05),
            (r'(支持|同意).{0,30}(但|不过|然而).{0,20}(风险|问题|担忧)', -0.05),
            (r'(必须|一定|绝对|肯定).{0,40}(可能|或许|不一定)', -0.08),
            (r'(风险低).{0,30}(风险高)', -0.10),
            (r'(增长).{0,30}(下降|萎缩|衰退)', -0.05),
            (r'(建议).{0,30}(不推荐|反对)', -0.08),
        ]
        sentences = re.split(r'[。！？.!?]', text)
        for pat, penalty in contradictions:
            if re.search(pat, text):
                score += penalty
        # 长度一致性：如果很短，难以判断（不扣分）
        if len(text) < 50:
            score = 0.5
        return max(0.1, min(1.0, score))
    
    def _v2_counterfactual_robustness(self, text: str) -> float:
        """反事实鲁棒性：检测是否过度绝对"""
        score = 0.6
        # 绝对化语言 → 扣分
        if re.search(r'(绝对|一定|肯定|必然|毫无疑问|百分百)', text): score -= 0.15
        if re.search(r'(永远|从不|不可能|毫无)', text): score -= 0.10
        if re.search(r'(必须|只能|唯一)', text): score -= 0.08
        # 反事实思维 → 加分
        if re.search(r'(如果.*不|假如.*反之|另一种可能|备选)', text): score += 0.15
        if re.search(r'(风险|不确定性|未知|可能.*变化)', text): score += 0.10
        if re.search(r'(条件|假设前提|取决于|视情况)', text): score += 0.10
        # 平衡观点 → 加分
        if re.search(r'(一方面.*另一方面|利弊|优缺点|权衡)', text): score += 0.10
        return max(0.1, min(1.0, score))
    
    def _v2_logic_desc(self, score: float) -> str:
        if score >= 0.7: return "完整的因果推导链和结构化论证"
        if score >= 0.5: return "有基本的逻辑结构，但推导不够深入"
        return "以结论为主，缺乏逻辑推导过程"
    
    def _v2_evidence_desc(self, score: float) -> str:
        if score >= 0.7: return "引用了具体数据、案例和研究支撑"
        if score >= 0.5: return "有部分论据但不充分"
        return "缺乏可验证的数据或案例支撑"
    
    def _v2_consistency_desc(self, score: float) -> str:
        if score >= 0.7: return "观点自洽，前后一致"
        if score >= 0.5: return "基本一致，存在轻微内部矛盾"
        return "存在明显的自相矛盾"
    
    def _v2_robustness_desc(self, score: float) -> str:
        if score >= 0.7: return "考虑了反事实情景和条件假设，不绝对化"
        if score >= 0.5: return "部分考虑了不确定性"
        return "过度绝对化，缺乏条件思维"
    
    def _v2_verdict(self, total: float, strengths: list, weaknesses: list) -> str:
        if total >= 80 and len(weaknesses) == 0:
            return "高度可信"
        elif total >= 70:
            return "可信" if len(weaknesses) <= 1 else "部分可信"
        elif total >= 55:
            return "需谨慎参考" if len(weaknesses) >= 2 else "部分可信"
        else:
            return "可信度较低"
    
    # ═══════════════════════════════════════
    # 1. 一致性评分 (纯 Python TF-IDF)
    # ═══════════════════════════════════════
    def _consistency_score(self, texts: List[str],
                           models: List[str]) -> Dict[str, float]:
        """基于 TF-IDF 余弦相似度计算结构一致性"""
        if len(texts) < 2:
            return {m: 1.0 for m in models}
        
        tfidf_vectors = self._tfidf(texts)
        centroid = [sum(col) / len(col) for col in zip(*tfidf_vectors)]
        
        scores = {}
        for i, m in enumerate(models):
            sim = self._cosine_similarity(tfidf_vectors[i], centroid)
            scores[m] = max(0.0, min(1.0, float(sim)))
        return scores
    
    # ═══════════════════════════════════════
    # 2. 证据评分 (启发式规则)
    # ═══════════════════════════════════════
    def _evidence_score(self, texts: List[str],
                        models: List[str]) -> Dict[str, float]:
        """基于文本特征的证据充分性评分"""
        scores = {}
        for i, m in enumerate(models):
            text = texts[i]
            score = 0.5  # 基准分
            
            # 数据引用
            if re.search(r'\d+%|\d+\.\d+%|百分之\d+', text):
                score += 0.15
            if re.search(r'\d{3,}|\d+万|\d+亿|\d+千', text):
                score += 0.1
            
            # 案例引用
            if re.search(r'例如|比如|案例|case|example', text, re.I):
                score += 0.1
            
            # 文本长度（合理长度加分）
            length = len(text)
            if 200 <= length <= 2000:
                score += 0.1
            elif length > 2000:
                score += 0.05
            
            # 结构化表达
            if re.search(r'(首先|第一|其次|第二|最后|总结)', text):
                score += 0.05
            if re.search(r'\n', text):
                score += 0.05
            
            # 风险词（表现出审慎）
            if re.search(r'(风险|注意|谨慎|建议|但|然而|不过)', text):
                score += 0.05
            
            scores[m] = min(score, 1.0)
        return scores
    
    # ═══════════════════════════════════════
    # 3. 共识评分
    # ═══════════════════════════════════════
    def _consensus_score(self, texts: List[str],
                         models: List[str]) -> Dict[str, float]:
        """与群体语义中心的距离（越近越共识）"""
        if len(texts) < 2:
            return {m: 1.0 for m in models}
        
        tfidf_vectors = self._tfidf(texts)
        centroid = [sum(col) / len(col) for col in zip(*tfidf_vectors)]
        
        scores = {}
        for i, m in enumerate(models):
            sim = self._cosine_similarity(tfidf_vectors[i], centroid)
            scores[m] = max(0.0, min(1.0, float(sim)))
        return scores
    
    # ═══════════════════════════════════════
    # 4. 领域适配
    # ═══════════════════════════════════════
    def _domain_score(self, models: List[str],
                      task_type: str) -> Dict[str, float]:
        """模型在特定领域的擅长程度"""
        scores = {}
        for m in models:
            scores[m] = get_domain_score(m, task_type)
        return scores
    
    # ═══════════════════════════════════════
    # 5. 历史可信度
    # ═══════════════════════════════════════
    def _historical_score(self, models: List[str]) -> Dict[str, float]:
        """基于模型历史表现的真实可靠性"""
        scores = {}
        for m in models:
            scores[m] = get_historical_score(m)
        return scores
    
    # ═══════════════════════════════════════
    # 冲突检测
    # ═══════════════════════════════════════
    def _conflict_matrix(self, texts: List[str],
                         models: List[str]) -> dict:
        """两两模型之间的语义冲突检测"""
        n = len(texts)
        if n < 2:
            return {"matrix": [[0]], "pairs": [], "summary": "只有一个模型，无冲突"}
        
        tfidf_vectors = self._tfidf(texts)
        
        matrix = [[0.0] * n for _ in range(n)]
        pairs = []
        
        for i in range(n):
            for j in range(n):
                sim = self._cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
                conflict = round(1 - sim, 4)  # 冲突 = 1 - 相似度
                matrix[i][j] = conflict
        
        # 提取高冲突对
        high_conflict_pairs = []
        for i in range(n):
            for j in range(i+1, n):
                if matrix[i][j] > 0.6:  # 冲突阈值
                    high_conflict_pairs.append({
                        "model_a": models[i],
                        "model_b": models[j],
                        "conflict_score": matrix[i][j],
                        "severity": "高" if matrix[i][j] > 0.8 else "中"
                    })
        
        avg_conflict = sum(matrix[i][j] for i in range(n) for j in range(n)) / (n * n) if n > 0 else 0
        
        return {
            "matrix": matrix,
            "pairs": high_conflict_pairs,
            "summary": {
                "avg_conflict": round(avg_conflict, 3),
                "high_conflict_count": len(high_conflict_pairs),
                "overall": "高度一致" if avg_conflict < 0.3 else "存在分歧" if avg_conflict < 0.6 else "严重分歧"
            }
        }
    
    # ═══════════════════════════════════════
    # V4 兼容可信度评分
    # ═══════════════════════════════════════
    def _calculate_global_trust(self, model_scores: Dict[str, ModelScore],
                                 conflict: dict, models: List[str],
                                 model_role_map: dict = None) -> dict:
        """计算全局可信度评分（与 V4 兼容）"""
        n = len(models)
        if n == 0:
            return {"score": 0, "level": "极低", "color": "#ef4444",
                    "breakdown": {"consensus": 0, "weight_bonus": 0,
                                  "conflict_penalty": 0, "reliability_bonus": 0}}
        
        # 平均 final_score 作为一致性基础
        avg_final = sum(ms.final_score for ms in model_scores.values()) / n
        consensus_score = avg_final * 50  # max 50
        
        # 权重加分 (基于角色权重)
        weight_bonus = 0
        if model_role_map:
            for model, role in model_role_map.items():
                w = role.get("weight", 1.0)
                if w > 1.0:
                    weight_bonus += (w - 1.0) * 5
        weight_bonus = max(-10, min(15, weight_bonus))
        
        # 冲突惩罚
        conflict_summary = conflict.get("summary", {})
        avg_conflict = conflict_summary.get("avg_conflict", 0.3)
        conflict_penalty = min(25, avg_conflict * 30)
        
        # 可靠性加分
        reliability_bonus = 0
        for m in models:
            reliability_bonus += get_size_bonus(m) * 0.5
        reliability_bonus = max(-5, min(10, reliability_bonus))
        
        raw = consensus_score + weight_bonus - conflict_penalty + reliability_bonus
        trust_score = max(5, min(99, round(raw)))
        
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
    
    # ═══════════════════════════════════════
    # ═══════════════════════════════════════
    # V4.1 — 新版可信度分析流水线
    # ═══════════════════════════════════════

    def analyze_v4(self, question: str, answers: Dict[str, str],
                   task_type: str = None) -> dict:
        models = list(answers.keys())
        texts = list(answers.values())
        if len(texts) == 0:
            return {'question': question, 'scores': {}, 'conflict_map': {'nodes':[],'edges':[]},
                    'decision': {'final_recommendation':'','dominant_view':'','risk_notes':[],'confidence_interval':0}}
        parsed = {m: self._clean_text(t) for m, t in answers.items()}
        if not task_type:
            task_type = self._classify_task(question)
        dims = {}
        for model, text in parsed.items():
            dims[model] = {
                'consistency': self._check_internal_logic(text),
                'evidence': self._check_evidence_density(text),
                'consensus': 0.0,
                'domain_fit': self._model_domain_fit(model, task_type),
                'authority': self._model_authority_score(model)
            }
        dims = self._compute_consensus_scores_v4(parsed, dims)
        w = {'consistency': 0.25, 'evidence': 0.20, 'consensus': 0.15, 'domain_fit': 0.20, 'authority': 0.20}
        final_scores = {}
        for model, d in dims.items():
            final_scores[model] = round(sum(d[dim] * w[dim] for dim in w), 4)
        conflict_map = self._build_conflict_graph(parsed)
        decision = self._synthesize_decision_simple(parsed, final_scores)
        return {'question': question, 'scores': final_scores,
                'conflict_map': conflict_map, 'decision': decision, 'weights': w}

    def _clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def _classify_task(self, question: str) -> str:
        q = question.lower()
        if any(w in q for w in ['辞职','创业','工作','跳槽','职业','团队']): return 'career'
        if any(w in q for w in ['投资','理财','股票','基金','买房','存款']): return 'finance'
        if any(w in q for w in ['营销','推广','广告','投放','品牌','获客']): return 'marketing'
        if any(w in q for w in ['技术','开发','架构','ai','系统','产品']): return 'technology'
        return 'strategy'

    def _check_internal_logic(self, text: str) -> float:
        score = 0.5
        if re.search(r'(因为|所以|如果|那么|因此|但|然而)', text): score += 0.15
        if re.search(r'(导致|引起|意味着)', text): score += 0.10
        if re.search(r'(如果|假如|假设)', text): score += 0.10
        if re.search(r'(相比|对比|一方面|另一方面)', text): score += 0.10
        if 100 < len(text) < 2000: score += 0.05
        return min(score, 1.0)

    def _check_evidence_density(self, text: str) -> float:
        score = 0.4
        if re.search(r'\d+%|\d+\.\d+%|百分之\d+', text): score += 0.15
        if re.search(r'\d{3,}|\d+万|\d+亿', text): score += 0.10
        if re.search(r'例如|比如|案例|case|example', text, re.I): score += 0.10
        if re.search(r'根据|数据显示|研究表明|报告', text): score += 0.10
        if re.search(r'(1\.|2\.|3\.|第一|第二|第三)', text): score += 0.10
        return min(score, 1.0)

    def _model_domain_fit(self, model_name: str, task_type: str) -> float:
        return get_domain_score(model_name, task_type)

    def _model_authority_score(self, model_name: str) -> float:
        return min(get_historical_score(model_name) + get_size_bonus(model_name) * 0.05, 1.0)

    def _compute_consensus_scores_v4(self, parsed, dims):
        texts = list(parsed.values())
        models = list(parsed.keys())
        if len(texts) < 2:
            for m in models: dims[m]['consensus'] = 1.0
            return dims
        vectors = self._tfidf(texts)
        centroid = [sum(col)/len(col) for col in zip(*vectors)]
        for i, m in enumerate(models):
            dims[m]['consensus'] = max(0.0, min(1.0, float(self._cosine_similarity(vectors[i], centroid))))
        return dims

    def _build_conflict_graph(self, parsed):
        models = list(parsed.keys()); texts = list(parsed.values())
        nodes = [{'id': m, 'summary': self._clean_text(t)[:50]} for m, t in parsed.items()]
        edges = []
        if len(texts) >= 2:
            vectors = self._tfidf(texts)
            for i in range(len(models)):
                for j in range(i+1, len(models)):
                    diff = round(1 - self._cosine_similarity(vectors[i], vectors[j]), 4)
                    if diff > 0.5:
                        edges.append({'source': models[i], 'target': models[j], 'conflict_score': diff})
        return {'nodes': nodes, 'edges': edges}

    def _synthesize_decision_simple(self, parsed, scores):
        sm = sorted(scores.items(), key=lambda x: -x[1])
        top = sm[0][0] if sm else ''
        risk_notes = []
        for model, text in parsed.items():
            for r in re.findall(r'(风险[：:].*?[。；]|风险.*?[。；]|注意.*?[。；]|谨慎.*?[。；])', text):
                risk_notes.append({'source': model, 'note': r.strip()})
        ci = round(scores.get(top, 0) * 100, 1) if top else 0
        gap = round((sm[0][1] - sm[1][1]) * 100, 1) if len(sm) >= 2 else 100
        if gap > 15: rec = f'综合可信度最高为「{top}」({ci}分)，显著领先，建议优先采纳。'
        elif gap > 5: rec = f'综合可信度最高为「{top}」({ci}分)，略优，建议测试验证。'
        else: rec = f'「{top}」({ci}分)但多个模型评分接近，建议进一步交叉验证。'
        return {'final_recommendation': rec, 'dominant_view': top,
                'risk_notes': risk_notes[:4], 'confidence_interval': ci}


    # 洞察生成
    # ═══════════════════════════════════════
    def _generate_insight(self, scores_100: Dict[str, float],
                          models: List[str]) -> dict:
        """从评分中提取决策洞察"""
        if not scores_100:
            return {"dominant_view": "", "confidence": 0, "summary": ""}
        
        top_model = max(scores_100, key=scores_100.get)
        top_score = scores_100[top_model]
        
        # 模型排名
        ranked = sorted(scores_100.items(), key=lambda x: -x[1])
        
        # 差距分析
        if len(ranked) >= 2:
            gap = ranked[0][1] - ranked[1][1]
        else:
            gap = 100
        
        if gap > 20:
            summary = f"可信度领先：{ranked[0][0]}（{ranked[0][1]}分），显著高于其他模型"
        elif gap > 10:
            summary = f"可信度略领先：{ranked[0][0]}（{ranked[0][1]}分），接近{ranked[1][0]}（{ranked[1][1]}分）"
        else:
            summary = f"多个模型可信度接近，最高{ranked[0][0]}（{ranked[0][1]}分）与{ranked[1][0]}（{ranked[1][1]}分）差距小"
        
        return {
            "dominant_view": top_model,
            "confidence": round(top_score, 2),
            "ranking": [{"model": m, "score": s} for m, s in ranked],
            "gap": round(gap, 2),
            "summary": summary
        }
    
    def _empty_result(self, question: str) -> dict:
        return {
            "question": question,
            "model_scores": {},
            "scores_100": {},
            "conflict": {"matrix": [], "pairs": [], "summary": {}},
            "trust_score": {"score": 0, "level": "极低", "color": "#ef4444",
                            "breakdown": {}},
            "insight": {"dominant_view": "", "confidence": 0, "summary": "无模型输入"},
            "weights": {}
        }
    
    # ═══════════════════════════════════════
    # 纯 Python TF-IDF 实现
    # ═══════════════════════════════════════
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中文 + 英文分词"""
        # 中文分词：按字/词切分
        tokens = []
        # 英文单词
        for word in re.findall(r'[a-zA-Z]+', text):
            tokens.append(word.lower())
        # 中文词组（连续汉字作为一个单元）
        for chunk in re.findall(r'[\u4e00-\u9fff]+', text):
            # 二元组
            for i in range(len(chunk) - 1):
                tokens.append(chunk[i:i+2])
        # 数字
        for num in re.findall(r'\d+\.?\d*', text):
            tokens.append(f"NUM_{num[:6]}")
        return tokens
    
    @staticmethod
    def _compute_tf(tokens: List[str]) -> Dict[str, float]:
        """计算词频"""
        if not tokens:
            return {}
        counter = Counter(tokens)
        total = len(tokens)
        return {word: count / total for word, count in counter.items()}
    
    @classmethod
    def _tfidf(cls, texts: List[str]) -> List[List[float]]:
        """计算 TF-IDF 向量"""
        n_docs = len(texts)
        if n_docs == 0:
            return []
        
        # 分词
        tokenized = [cls._tokenize(t) for t in texts]
        
        # 构建词汇表
        vocab = set()
        for tokens in tokenized:
            vocab.update(tokens)
        vocab = sorted(vocab)
        if not vocab:
            return [[0.0] for _ in texts]
        
        # 计算 DF
        df = Counter()
        for tokens in tokenized:
            df.update(set(tokens))
        
        # 计算 TF-IDF
        vectors = []
        for tokens in tokenized:
            tf = cls._compute_tf(tokens)
            vec = []
            for word in vocab:
                tf_val = tf.get(word, 0.0)
                idf_val = math.log((n_docs + 1) / (df.get(word, 0) + 1)) + 1
                vec.append(tf_val * idf_val)
            # L2 归一化
            norm = math.sqrt(sum(v*v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            vectors.append(vec)
        
        return vectors
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        if not a or not b:
            return 0.0
        dot = sum(x*y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x*x for x in a))
        norm_b = math.sqrt(sum(y*y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
