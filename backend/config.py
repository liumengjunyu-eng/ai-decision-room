"""
V4.1 模型画像系统
每个模型在不同领域的可信度权重 + 历史准确性
"""
MODEL_PROFILES = {
    "gpt-4o": {
        "coding": 0.9,
        "strategy": 0.85,
        "risk": 0.80,
        "market": 0.82,
        "innovation": 0.88,
        "general": 0.85,
        "historical_accuracy": 0.88,
        "size_bonus": 1.5
    },
    "deepseek-v3": {
        "coding": 0.88,
        "strategy": 0.92,
        "risk": 0.90,
        "market": 0.85,
        "innovation": 0.86,
        "general": 0.88,
        "historical_accuracy": 0.86,
        "size_bonus": 2.0
    },
    "deepseek-v2.5": {
        "coding": 0.82,
        "strategy": 0.85,
        "risk": 0.83,
        "market": 0.80,
        "innovation": 0.82,
        "general": 0.83,
        "historical_accuracy": 0.82,
        "size_bonus": 2.0
    },
    "qwen2.5-72b": {
        "coding": 0.85,
        "strategy": 0.88,
        "risk": 0.82,
        "market": 0.84,
        "innovation": 0.85,
        "general": 0.86,
        "historical_accuracy": 0.84,
        "size_bonus": 1.5
    },
    "qwen2-7b": {
        "coding": 0.75,
        "strategy": 0.78,
        "risk": 0.76,
        "market": 0.74,
        "innovation": 0.76,
        "general": 0.76,
        "historical_accuracy": 0.76,
        "size_bonus": 0.5
    },
    "glm-4": {
        "coding": 0.75,
        "strategy": 0.80,
        "risk": 0.92,
        "market": 0.78,
        "innovation": 0.74,
        "general": 0.80,
        "historical_accuracy": 0.84,
        "size_bonus": 0.5
    },
    "default": {
        "coding": 0.7,
        "strategy": 0.7,
        "risk": 0.7,
        "market": 0.7,
        "innovation": 0.7,
        "general": 0.7,
        "historical_accuracy": 0.75,
        "size_bonus": 1.0
    }
}

def get_profile(model_name: str) -> dict:
    """根据模型名匹配画像，支持模糊匹配"""
    model_lower = model_name.lower().replace("-", "").replace(" ", "")
    for key, profile in MODEL_PROFILES.items():
        key_clean = key.lower().replace("-", "").replace(" ", "")
        if key_clean in model_lower or model_lower in key_clean:
            return profile
    return MODEL_PROFILES["default"]

def get_domain_score(model_name: str, task_type: str = "general") -> float:
    """获取模型在特定领域的能力分数"""
    profile = get_profile(model_name)
    return profile.get(task_type, profile.get("general", 0.7))

def get_historical_score(model_name: str) -> float:
    """获取模型历史准确性"""
    profile = get_profile(model_name)
    return profile.get("historical_accuracy", 0.75)

def get_size_bonus(model_name: str) -> float:
    """获取模型规模加分"""
    profile = get_profile(model_name)
    return profile.get("size_bonus", 1.0)
