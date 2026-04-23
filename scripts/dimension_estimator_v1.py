#!/usr/bin/env python3
"""
EIE Agent 五维度估算器

基于真实数据自动估算五维度分数

维度估算规则：
- ES（环境生存能力）：Channels数量、持久化存储、自动重启
- IS（信息处理能力）：Memory系统、RAG/知识库、多模态Skills
- MS（模型构建能力）：模型能力基准、Tools/Skills数量、工作流Skills
- VS（价值对齐能力）：安全配置、内容过滤、用户反馈机制
- CE（持续进化能力）：Skills数量、Cron/Heartbeat、自我改进Skills、轨迹记录
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# ============================================================
# 维度分数上限
# ============================================================

DIMENSION_MAX = {
    "ES": 90,
    "IS": 90,
    "MS": 90,
    "VS": 95,
    "CE": 90,
}

# ============================================================
# 模型能力基准表
# ============================================================

MODEL_BASELINE = {
    # GPT系列
    "gpt-4o": 75, "gpt-4-turbo": 72, "gpt-4": 70, "gpt-4o-mini": 65,
    "gpt-3.5-turbo": 55,
    # Claude系列
    "claude-3-5-sonnet": 78, "claude-3-opus": 76, "claude-3-sonnet": 72,
    "claude-3-haiku": 60,
    # 开源模型
    "llama-3-70b": 68, "llama-3-8b": 58, "llama-2-70b": 62, "llama-2-7b": 52,
    "qwen-72b": 65, "qwen-14b": 58, "qwen-7b": 52,
    "deepseek-67b": 66, "deepseek-33b": 60, "deepseek-7b": 55,
    "mixtral-8x7b": 63, "mistral-7b": 55,
    # 国内模型
    "yi-large": 68, "yi-medium": 60, "yi-6b": 52,
    "baichuan-4": 65, "baichuan3": 62,
    "glm-4": 68, "glm-4v": 70, "glm-3": 58,
    # 本地/私有模型
    "local": 40, "ollama": 42, "vllm": 45, "private": 50,
}


def get_model_baseline(model_name: str) -> int:
    """获取模型能力基准分数"""
    if not model_name:
        return 45  # 默认值
    
    model_lower = model_name.lower()
    
    # 精确匹配
    if model_lower in MODEL_BASELINE:
        return MODEL_BASELINE[model_lower]
    
    # 前缀匹配
    for key, value in MODEL_BASELINE.items():
        if model_lower.startswith(key) or key in model_lower:
            return value
    
    # 未知模型，根据上下文推断
    if "gpt" in model_lower:
        return 60
    if "claude" in model_lower:
        return 65
    if "local" in model_lower or "ollama" in model_lower:
        return 40
    
    return 50  # 默认基准


# ============================================================
# Skill类型检测关键词
# ============================================================

SKILL_TYPES = {
    "multimodal": ["vision", "image", "视觉", "多模态", "ocr", "visual", "generate_image", "generate_image"],
    "rag": ["rag", "knowledge", "知识库", "检索", "retrieval", "vector", "embedding", "文档", "search"],
    "tool": ["tool", "api", "function", "工具", "调用", "browser", "web", "http"],
    "memory": ["memory", "记忆", "state", "状态", "persist", "storage", "db", "database"],
    "safety": ["safety", "安全", "filter", "filter", "audit", "审计", "permission", "权限"],
    "self_improve": ["self_improve", "self-improve", "自我", "learn", "学习", "evolution", "进化", "improve"],
    "workflow": ["workflow", "工作流", "pipeline", "chain", "agent", "orchestrat"],
    "analysis": ["analysis", "分析", "log", "日志", "analytics", "统计", "monitor", "监控"],
}


def detect_skill_type(skill_name: str, skill_content: str = "") -> List[str]:
    """检测Skill类型"""
    content = (skill_name + " " + skill_content).lower()
    detected = []
    
    for skill_type, keywords in SKILL_TYPES.items():
        for keyword in keywords:
            if keyword in content:
                detected.append(skill_type)
                break
    
    return detected


# ============================================================
# 数据类：检测结果
# ============================================================

@dataclass
class DetectionData:
    """检测到的原始数据"""
    platform: str  # "openclaw" | "hermes" | "unknown"
    channels: List[str] = None  # 可用渠道
    skills: List[str] = None  # Skills列表
    skill_types: Dict[str, int] = None  # Skill类型统计
    model: str = ""  # 模型名称
    memory_system: bool = False  # 是否有记忆系统
    rag_enabled: bool = False  # 是否启用RAG
    persistent_storage: bool = False  # 是否有持久化存储
    safety_config: Dict[str, Any] = None  # 安全配置
    cron_enabled: bool = False  # 是否有定时任务
    heartbeat_enabled: bool = False  # 是否有心跳
    trajectory_enabled: bool = False  # 是否记录轨迹
    user_feedback_enabled: bool = False  # 是否有用户反馈机制
    vulnerabilities: List[str] = None  # 发现的安全漏洞
    workspace_path: str = None  # workspace路径，用于质量评估
    
    def __post_init__(self):
        self.channels = self.channels or []
        self.skills = self.skills or []
        self.skill_types = self.skill_types or {}
        self.safety_config = self.safety_config or {}
        self.vulnerabilities = self.vulnerabilities or []


@dataclass
class DimensionScores:
    """五维度分数"""
    ES: int
    IS: int
    MS: int
    VS: int
    CE: int
    data_source: Dict[str, str] = None  # 各维度数据来源
    
    def __post_init__(self):
        self.data_source = self.data_source or {}
        # 限制上限
        self.ES = min(self.ES, DIMENSION_MAX["ES"])
        self.IS = min(self.IS, DIMENSION_MAX["IS"])
        self.MS = min(self.MS, DIMENSION_MAX["MS"])
        self.VS = min(self.VS, DIMENSION_MAX["VS"])
        self.CE = min(self.CE, DIMENSION_MAX["CE"])


# ============================================================
# 维度估算器
# ============================================================

class DimensionEstimator:
    """五维度估算器"""
    
    def __init__(self, data: DetectionData):
        self.data = data
    
    def estimate_ES(self) -> Tuple[int, str]:
        """
        估算环境生存能力 (ES)
        
        规则：
        - 基础分：30（能运行）
        - Channels数量 × 5（每增加一个渠道+5）
        - 持久化存储：+10
        - 自动重启/守护进程：+10
        - 上限：90
        """
        base_score = 30
        source = {}
        
        # Channels贡献
        channel_count = len(self.data.channels)
        channel_score = min(channel_count * 5, 25)  # 最多5个渠道=25分
        source["channels"] = f"{channel_count}个渠道 (+{channel_score})"
        
        # 持久化存储
        storage_score = 10 if self.data.persistent_storage else 0
        source["storage"] = f"持久化存储 (+{storage_score})" if storage_score else "无持久化"
        
        # 守护进程/自动重启
        daemon_score = 10 if (self.data.cron_enabled or self.data.heartbeat_enabled) else 0
        source["daemon"] = f"守护进程 (+{daemon_score})" if daemon_score else "无守护进程"
        
        total = base_score + channel_score + storage_score + daemon_score
        return min(total, DIMENSION_MAX["ES"]), source
    
    def estimate_IS(self) -> Tuple[int, str]:
        """
        估算信息处理能力 (IS)
        
        规则：
        - 基础分：20
        - Memory系统：+15
        - RAG/知识库：+15
        - 多模态Skills数量 × 3
        - 日志分析能力：+10
        - 上限：90
        """
        base_score = 20
        source = {}
        
        # Memory系统
        memory_score = 15 if self.data.memory_system else 0
        source["memory"] = f"记忆系统 (+{memory_score})" if memory_score else "无记忆系统"
        
        # RAG/知识库
        rag_score = 15 if self.data.rag_enabled else 0
        source["rag"] = f"RAG/知识库 (+{rag_score})" if rag_score else "无RAG"
        
        # 多模态Skills
        multimodal_count = self.data.skill_types.get("multimodal", 0)
        multimodal_score = min(multimodal_count * 3, 15)
        source["multimodal"] = f"{multimodal_count}个多模态Skill (+{multimodal_score})"
        
        # 日志分析
        analysis_count = self.data.skill_types.get("analysis", 0)
        analysis_score = 10 if analysis_count > 0 else 0
        source["analysis"] = f"日志分析 (+{analysis_score})" if analysis_score else "无日志分析"
        
        total = base_score + memory_score + rag_score + multimodal_score + analysis_score
        return min(total, DIMENSION_MAX["IS"]), source
    
    def estimate_MS(self) -> Tuple[int, str]:
        """
        估算模型构建能力 (MS)
        
        规则：
        - 基础分：模型能力基准（GPT-4: 60, Claude: 65, 本地模型: 40）
        - Tools/Skills数量 × 2（工具多=模型调度能力强）
        - 工作流/复杂Skills：+10
        - 上限：90
        """
        # 模型基准
        model_baseline = get_model_baseline(self.data.model)
        source = {"model": f"{self.data.model or 'unknown'} (基准+{model_baseline})"}
        
        # Skills数量贡献
        skill_count = len(self.data.skills)
        skill_score = min(skill_count * 2, 20)
        source["skills"] = f"{skill_count}个Skills (+{skill_score})"
        
        # 工作流Skills
        workflow_count = self.data.skill_types.get("workflow", 0)
        workflow_score = 10 if workflow_count > 0 else 0
        source["workflow"] = f"工作流Skills (+{workflow_score})" if workflow_score else "无工作流"
        
        total = model_baseline + skill_score + workflow_score
        return min(total, DIMENSION_MAX["MS"]), source
    
    def estimate_VS(self) -> Tuple[int, str]:
        """
        估算价值对齐能力 (VS)
        
        规则：
        - 基础分：40
        - 安全配置（allowlist, 审计）：+15
        - 内容过滤：+10
        - 用户反馈机制：+10
        - 发现漏洞：-10
        - 上限：95
        """
        base_score = 40
        source = {}
        
        # 安全配置
        safety = self.data.safety_config
        safety_score = 0
        if safety.get("allowlist"):
            safety_score += 8
        if safety.get("audit") or safety.get("logging"):
            safety_score += 7
        source["safety"] = f"安全配置 (+{safety_score})"
        
        # 内容过滤
        filter_score = 10 if safety.get("content_filter") else 0
        source["filter"] = f"内容过滤 (+{filter_score})" if filter_score else "无内容过滤"
        
        # 用户反馈机制
        feedback_score = 10 if self.data.user_feedback_enabled else 0
        source["feedback"] = f"用户反馈 (+{feedback_score})" if feedback_score else "无用户反馈"
        
        # 漏洞惩罚
        vuln_penalty = len(self.data.vulnerabilities) * 10
        source["vulnerabilities"] = f"{len(self.data.vulnerabilities)}个漏洞 (-{vuln_penalty})"
        
        total = base_score + safety_score + filter_score + feedback_score - vuln_penalty
        return max(0, min(total, DIMENSION_MAX["VS"])), source
    
    def estimate_CE(self) -> Tuple[int, str]:
        """
        估算持续进化能力 (CE)
        
        规则：
        - 基础分：20
        - Skills数量 × 2（技能多=进化能力强）
        - Cron/Heartbeat：+15
        - 自我改进Skills：+20
        - 轨迹记录：+10
        - 上限：90
        """
        base_score = 20
        source = {}
        
        # Skills数量
        skill_count = len(self.data.skills)
        skill_score = min(skill_count * 2, 20)
        source["skills"] = f"{skill_count}个Skills (+{skill_score})"
        
        # Cron/Heartbeat
        cron_score = 15 if (self.data.cron_enabled or self.data.heartbeat_enabled) else 0
        source["cron"] = f"定时任务/心跳 (+{cron_score})" if cron_score else "无定时任务"
        
        # 自我改进Skills
        self_improve_count = self.data.skill_types.get("self_improve", 0)
        self_improve_score = min(self_improve_count * 10, 20)
        source["self_improve"] = f"{self_improve_count}个自我改进Skill (+{self_improve_score})"
        
        # 轨迹记录
        trajectory_score = 10 if self.data.trajectory_enabled else 0
        source["trajectory"] = f"轨迹记录 (+{trajectory_score})" if trajectory_score else "无轨迹记录"
        
        total = base_score + skill_score + cron_score + self_improve_score + trajectory_score
        return min(total, DIMENSION_MAX["CE"]), source
    
    def estimate_all(self) -> DimensionScores:
        """估算所有维度"""
        es, es_source = self.estimate_ES()
        is_val, is_source = self.estimate_IS()
        ms, ms_source = self.estimate_MS()
        vs, vs_source = self.estimate_VS()
        ce, ce_source = self.estimate_CE()
        
        return DimensionScores(
            ES=es,
            IS=is_val,
            MS=ms,
            VS=vs,
            CE=ce,
            data_source={
                "ES": str(es_source),
                "IS": str(is_source),
                "MS": str(ms_source),
                "VS": str(vs_source),
                "CE": str(ce_source),
            }
        )


# ============================================================
# 辅助函数
# ============================================================

def scan_directory(path: str, extensions: List[str] = None) -> List[str]:
    """
    扫描目录下的文件
    
    Args:
        path: 目录路径
        extensions: 筛选的文件扩展名，如 [".py", ".json"]
    
    Returns:
        文件路径列表
    """
    if not os.path.exists(path):
        return []
    
    files = []
    for root, _, filenames in os.walk(os.path.expanduser(path)):
        for filename in filenames:
            if extensions is None or any(filename.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, filename))
    
    return files


def read_json_safe(path: str) -> Dict:
    """安全读取JSON文件"""
    try:
        with open(os.path.expanduser(path), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def extract_skill_types(skills_dir: str) -> Dict[str, int]:
    """从Skills目录提取Skill类型统计"""
    skill_types_count = {}
    
    files = scan_directory(skills_dir)
    for filepath in files:
        skill_name = os.path.basename(os.path.dirname(filepath)) or os.path.basename(filepath)
        
        # 尝试读取Skill内容进行分类
        content = ""
        try:
            if filepath.endswith('.json'):
                data = read_json_safe(filepath)
                content = json.dumps(data)
            elif filepath.endswith(('.py', '.md', '.txt')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
        except Exception:
            pass
        
        detected = detect_skill_type(skill_name, content)
        for st in detected:
            skill_types_count[st] = skill_types_count.get(st, 0) + 1
    
    return skill_types_count


# ============================================================
# 单元测试
# ============================================================

if __name__ == "__main__":
    # 测试模拟数据
    mock_data = DetectionData(
        platform="openclaw",
        channels=["web", "api", "slack"],
        skills=["rag_skill", "vision_skill", "web_tool", "self_improve"],
        skill_types={"multimodal": 1, "rag": 1, "tool": 1, "self_improve": 1},
        model="gpt-4",
        memory_system=True,
        rag_enabled=True,
        persistent_storage=True,
        safety_config={"allowlist": True, "audit": True, "content_filter": True},
        cron_enabled=True,
        heartbeat_enabled=True,
        trajectory_enabled=True,
        user_feedback_enabled=True,
    )
    
    estimator = DimensionEstimator(mock_data)
    scores = estimator.estimate_all()
    
    print("五维度估算结果：")
    print(f"ES (环境生存): {scores.ES}")
    print(f"IS (信息处理): {scores.IS}")
    print(f"MS (模型构建): {scores.MS}")
    print(f"VS (价值对齐): {scores.VS}")
    print(f"CE (持续进化): {scores.CE}")
    print("\n数据来源：")
    for dim, source in scores.data_source.items():
        print(f"  {dim}: {source}")
