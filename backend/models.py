"""
V4.1 可信度引擎数据结构
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ModelScore:
    """单个模型的可信度评分"""
    consistency: float = 0.0      # 结构一致性 0-1
    evidence: float = 0.0         # 证据充分性 0-1
    consensus: float = 0.0        # 共识程度 0-1
    domain: float = 0.0           # 领域适配度 0-1
    historical: float = 0.0       # 历史可信度 0-1
    final_score: float = 0.0      # 加权融合分 0-1


@dataclass
class ConflictMatrix:
    """冲突矩阵：模型之间的分歧程度"""
    matrix: List[List[float]] = field(default_factory=list)
    model_names: List[str] = field(default_factory=list)
    conflict_pairs: List[dict] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """完整评估结果"""
    question: str
    model_scores: Dict[str, ModelScore]
    scores_100: Dict[str, float]    # 归一化到 0-100
    conflict: ConflictMatrix
    trust_score: dict               # V4 兼容的可信度评分
    insight: dict
