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
