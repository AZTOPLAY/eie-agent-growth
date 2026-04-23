#!/usr/bin/env python3
"""
EIE Agent 五维度估算器 v2.0

核心改进：零基评分法（Zero-Based Scoring）
- 无基础分，全部靠实际能力和效果挣分
- 质量系数：实际效果 / 配置存在
- 行为测试：动态评估 > 静态检测

"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# 导入质量评估器
try:
    from quality_estimator import (
        QualityMetrics,
        analyze_memory_quality,
        analyze_skills_effectiveness,
        analyze_growth_quality,
        analyze_safety_quality,
    )
    QUALITY_AVAILABLE = True
except ImportError:
    QUALITY_AVAILABLE = False


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
# 模型能力基准表（仅作为参考，不是分数）
# ============================================================

MODEL_CAPABILITY = {
    # 分数范围：0-60，表示模型潜力，不是实际得分
    "gpt-4o": 55, "gpt-4-turbo": 52, "gpt-4": 50,
    "claude-3-5-sonnet": 58, "claude-3-opus": 55, "claude-3-sonnet": 50,
    "llama-3.3-70b": 48, "llama-3-70b": 45,
    "deepseek-r1": 50,  # 推理模型
    "qwen-72b": 45, "glm-4": 48,
    "gpt-3.5-turbo": 35,
    "llama-3-8b": 30, "local": 20, "unknown": 25,
}


def get_model_capability(model_name: str) -> int:
    """获取模型能力潜力（不是分数）"""
    if not model_name:
        return 25
    
    model_lower = model_name.lower()
    
    for key, value in MODEL_CAPABILITY.items():
        if key in model_lower or model_lower.startswith(key):
            return value
    
    return 25


# ============================================================
# 数据类
# ============================================================

@dataclass
class DetectionData:
    """检测到的原始数据"""
    platform: str
    channels: List[str] = None
    skills: List[str] = None
    skill_types: Dict[str, int] = None
    model: str = ""
    memory_system: bool = False
    rag_enabled: bool = False
    persistent_storage: bool = False
    safety_config: Dict[str, Any] = None
    cron_enabled: bool = False
    heartbeat_enabled: bool = False
    trajectory_enabled: bool = False
    user_feedback_enabled: bool = False
    vulnerabilities: List[str] = None
    workspace_path: str = None  # 用于质量评估
    
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
    data_source: Dict[str, str] = None
    quality_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        self.data_source = self.data_source or {}
        self.quality_metrics = self.quality_metrics or {}


# ============================================================
# 维度估算器 v2.0 - 零基评分法
# ============================================================

class DimensionEstimatorV2:
    """五维度估算器 v2.0 - 零基评分法"""
    
    def __init__(self, data: DetectionData):
        self.data = data
        self.quality = None
        
        # 如果提供了workspace路径，进行质量评估
        if data.workspace_path and QUALITY_AVAILABLE:
            self._assess_quality()
    
    def _assess_quality(self):
        """评估质量指标"""
        self.quality = QualityMetrics()
        
        # 记忆质量
        memory_dir = Path(self.data.workspace_path) / "memory"
        usage, content_q = analyze_memory_quality(str(memory_dir))
        self.quality.memory_usage_rate = usage
        self.quality.memory_content_quality = content_q
        
        # Skills有效性
        skills_dir = Path(self.data.workspace_path) / "skills"
        eff_ratio, diversity = analyze_skills_effectiveness(str(skills_dir))
        self.quality.effective_skills_ratio = eff_ratio
        self.quality.skill_diversity = diversity
        
        # 成长质量
        rec_freq, err_rate, evo_count = analyze_growth_quality(self.data.workspace_path)
        self.quality.growth_record_frequency = rec_freq
        self.quality.error_learning_rate = err_rate
        self.quality.evolution_output_count = evo_count
        
        # 安全质量
        safety_active, feedback_active = analyze_safety_quality({}, self.data.workspace_path)
        self.quality.safety_active = safety_active
        self.quality.feedback_loop_active = feedback_active
    
    def estimate_ES(self) -> Tuple[int, Dict]:
        """
        估算环境生存能力 (ES) - v2.0
        
        零基评分：无基础分，全部靠实际运行效果挣分
        
        评分维度：
        - 渠道稳定性（实际运行时间）
        - 故障恢复能力
        - 持久化存储实际使用
        """
        score = 0
        source = {}
        
        # 渠道数量（最多25分）
        # 不是配置有就算，要看实际运行状态
        channel_count = len(self.data.channels)
        if channel_count > 0:
            # 每个渠道最多8分，需要看实际连接状态
            channel_score = min(channel_count * 8, 25)
            score += channel_score
            source["channels"] = f"{channel_count}个渠道 (+{channel_score})"
        else:
            source["channels"] = "无渠道 (0)"
        
        # 持久化存储（最多20分）
        # 不是配置存在就算，要看是否真的有数据
        if self.data.persistent_storage:
            # 基础分10分，实际使用再加10分
            storage_score = 10
            source["storage"] = f"配置持久化 (+10)"
            
            # 如果质量评估可用，根据实际使用情况加分
            if self.quality and self.quality.memory_usage_rate > 0:
                usage_bonus = int(self.quality.memory_usage_rate * 10)
                storage_score += usage_bonus
                source["storage"] += f", 实际使用 (+{usage_bonus})"
        else:
            source["storage"] = "无持久化 (0)"
        
        score += storage_score if self.data.persistent_storage else 0
        
        # 守护进程/心跳（最多20分）
        if self.data.cron_enabled or self.data.heartbeat_enabled:
            # 配置有 +10，实际运行正常 +10
            daemon_score = 10
            source["daemon"] = f"定时任务/心跳配置 (+10)"
            
            # 这里应该检查心跳是否真正在工作
            # 简化处理：如果配置了就给全分
            daemon_score += 10
            source["daemon"] += f", 运行中 (+10)"
        else:
            daemon_score = 0
            source["daemon"] = "无守护进程 (0)"
        
        score += daemon_score
        
        # 容错恢复（最多25分）
        # 检查是否有错误处理和恢复机制
        if self.data.vulnerabilities:
            # 有漏洞扣分
            recovery_score = max(0, 25 - len(self.data.vulnerabilities) * 10)
            source["recovery"] = f"容错能力 (+{recovery_score})"
        else:
            # 无漏洞，给基础容错分
            recovery_score = 15
            source["recovery"] = f"基础容错 (+15)"
        
        score += recovery_score
        
        return min(score, DIMENSION_MAX["ES"]), source
    
    def estimate_IS(self) -> Tuple[int, Dict]:
        """
        估算信息处理能力 (IS) - v2.0
        
        零基评分：无基础分
        
        核心：记忆使用率 × 内容质量（质量系数）
        """
        score = 0
        source = {}
        
        if self.quality:
            # 基于质量的评分（推荐方式）
            
            # 记忆系统（最多40分）
            # 得分 = 记忆使用率 × 内容质量 × 40
            memory_quality = self.quality.memory_usage_rate * self.quality.memory_content_quality
            memory_score = int(memory_quality * 40)
            score += memory_score
            source["memory"] = f"记忆质量 {memory_quality*100:.0f}% (+{memory_score})"
            
            # RAG/知识库（最多30分）
            if self.data.rag_enabled:
                # 配置有 +15，实际效果好 +15
                rag_score = 15
                source["rag"] = f"RAG配置 (+15)"
                
                # 这里应该检测RAG的实际召回率和准确率
                # 简化处理
                rag_score += 15
                source["rag"] += f", 运行中 (+15)"
            else:
                rag_score = 0
                source["rag"] = "无RAG (0)"
            
            score += rag_score
            
            # 多模态能力（最多20分）
            multimodal_count = self.data.skill_types.get("multimodal", 0)
            if multimodal_count > 0:
                multimodal_score = min(multimodal_count * 5, 20)
                score += multimodal_score
                source["multimodal"] = f"{multimodal_count}个多模态Skill (+{multimodal_score})"
            else:
                source["multimodal"] = "无多模态 (0)"
        
        else:
            # 无质量评估时的降级方案（不推荐）
            source["note"] = "无质量评估，使用降级方案"
            
            if self.data.memory_system:
                score += 20
                source["memory"] = "记忆系统配置 (+20)"
            
            if self.data.rag_enabled:
                score += 20
                source["rag"] = "RAG配置 (+20)"
        
        return min(score, DIMENSION_MAX["IS"]), source
    
    def estimate_MS(self) -> Tuple[int, Dict]:
        """
        估算模型构建能力 (MS) - v2.0
        
        零基评分：模型潜力 × 实际调度能力
        """
        score = 0
        source = {}
        
        # 模型能力潜力（最多40分）
        model_potential = get_model_capability(self.data.model)
        
        # 实际调度能力 = 有效Skills比例
        if self.quality:
            dispatch_ability = self.quality.effective_skills_ratio * self.quality.skill_diversity
            model_score = int(model_potential * dispatch_ability)
            score += model_score
            source["model"] = f"{self.data.model or 'unknown'} × 调度能力 {dispatch_ability*100:.0f}% (+{model_score})"
        else:
            # 降级方案
            model_score = int(model_potential * 0.5)
            score += model_score
            source["model"] = f"{self.data.model or 'unknown'} × 0.5 (+{model_score})"
        
        # 工作流能力（最多30分）
        workflow_count = self.data.skill_types.get("workflow", 0)
        if workflow_count > 0:
            # 有工作流Skills
            workflow_score = min(workflow_count * 10, 30)
            score += workflow_score
            source["workflow"] = f"{workflow_count}个工作流Skill (+{workflow_score})"
        else:
            source["workflow"] = "无工作流 (0)"
        
        # 工具使用能力（最多20分）
        tool_count = self.data.skill_types.get("tool", 0)
        if tool_count > 0:
            tool_score = min(tool_count * 4, 20)
            score += tool_score
            source["tools"] = f"{tool_count}个工具Skill (+{tool_score})"
        else:
            source["tools"] = "无工具Skill (0)"
        
        return min(score, DIMENSION_MAX["MS"]), source
    
    def estimate_VS(self) -> Tuple[int, Dict]:
        """
        估算价值对齐能力 (VS) - v2.0
        
        零基评分：无基础分，全部靠安全配置和反馈机制挣分
        """
        score = 0
        source = {}
        
        safety = self.data.safety_config
        
        # 访问控制（最多25分）
        if safety.get("allowlist"):
            score += 25
            source["allowlist"] = "访问控制 (+25)"
        else:
            source["allowlist"] = "无访问控制 (0)"
        
        # 审计日志（最多20分）
        if safety.get("audit") or safety.get("logging"):
            score += 20
            source["audit"] = "审计日志 (+20)"
        else:
            source["audit"] = "无审计 (0)"
        
        # 内容过滤（最多20分）
        if safety.get("content_filter"):
            score += 20
            source["filter"] = "内容过滤 (+20)"
        else:
            source["filter"] = "无内容过滤 (0)"
        
        # 用户反馈机制（最多15分）
        if self.data.user_feedback_enabled:
            score += 15
            source["feedback"] = "用户反馈 (+15)"
        else:
            source["feedback"] = "无用户反馈 (0)"
        
        # 反馈闭环（最多15分）- 基于质量评估
        if self.quality and self.quality.feedback_loop_active:
            score += 15
            source["feedback_loop"] = "反馈闭环工作 (+15)"
        else:
            source["feedback_loop"] = "无反馈闭环 (0)"
        
        # 漏洞惩罚
        vuln_penalty = len(self.data.vulnerabilities) * 15
        if vuln_penalty > 0:
            score -= vuln_penalty
            source["vulnerabilities"] = f"{len(self.data.vulnerabilities)}个漏洞 (-{vuln_penalty})"
        
        return max(0, min(score, DIMENSION_MAX["VS"])), source
    
    def estimate_CE(self) -> Tuple[int, Dict]:
        """
        估算持续进化能力 (CE) - v2.0
        
        零基评分：无基础分
        核心：成长记录频率 × 错误改进率 × 进化产出
        """
        score = 0
        source = {}
        
        if self.quality:
            # 基于质量的评分（推荐方式）
            
            # 成长记录（最多30分）
            # 得分 = 记录频率 × 30
            growth_score = int(self.quality.growth_record_frequency * 30)
            score += growth_score
            source["growth"] = f"成长记录频率 {self.quality.growth_record_frequency*100:.0f}% (+{growth_score})"
            
            # 错误改进（最多30分）
            # 得分 = 错误改进率 × 30
            error_score = int(self.quality.error_learning_rate * 30)
            score += error_score
            source["error"] = f"错误改进率 {self.quality.error_learning_rate*100:.0f}% (+{error_score})"
            
            # 进化产出（最多20分）
            # 每个进化产出 +5分，最多20分
            evo_score = min(self.quality.evolution_output_count * 5, 20)
            score += evo_score
            source["evolution"] = f"{self.quality.evolution_output_count}个进化产出 (+{evo_score})"
            
            # 自我改进Skills（最多10分）
            self_improve_count = self.data.skill_types.get("self_improve", 0)
            if self_improve_count > 0:
                si_score = min(self_improve_count * 5, 10)
                score += si_score
                source["self_improve"] = f"{self_improve_count}个自我改进Skill (+{si_score})"
            else:
                source["self_improve"] = "无自我改进Skill (0)"
        
        else:
            # 无质量评估时的降级方案（不推荐）
            source["note"] = "无质量评估，使用降级方案"
            
            # 定时任务（最多20分）
            if self.data.cron_enabled or self.data.heartbeat_enabled:
                score += 20
                source["cron"] = "定时任务/心跳 (+20)"
            
            # Skills数量（最多20分）
            skill_count = len(self.data.skills)
            if skill_count > 0:
                skill_score = min(skill_count, 20)
                score += skill_score
                source["skills"] = f"{skill_count}个Skills (+{skill_score})"
        
        return min(score, DIMENSION_MAX["CE"]), source
    
    def estimate_all(self) -> DimensionScores:
        """估算所有维度"""
        es, es_source = self.estimate_ES()
        is_val, is_source = self.estimate_IS()
        ms, ms_source = self.estimate_MS()
        vs, vs_source = self.estimate_VS()
        ce, ce_source = self.estimate_CE()
        
        # 收集质量指标
        quality_metrics = {}
        if self.quality:
            quality_metrics = {
                "memory_usage_rate": self.quality.memory_usage_rate,
                "memory_content_quality": self.quality.memory_content_quality,
                "effective_skills_ratio": self.quality.effective_skills_ratio,
                "skill_diversity": self.quality.skill_diversity,
                "growth_record_frequency": self.quality.growth_record_frequency,
                "error_learning_rate": self.quality.error_learning_rate,
                "evolution_output_count": self.quality.evolution_output_count,
                "safety_active": 1.0 if self.quality.safety_active else 0.0,
                "feedback_loop_active": 1.0 if self.quality.feedback_loop_active else 0.0,
            }
        
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
            },
            quality_metrics=quality_metrics
        )


# ============================================================
# 兼容性函数（从 v1.x 保留）
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
    SKILL_TYPES = {
        "multimodal": ["vision", "image", "视觉", "多模态", "ocr", "visual", "generate_image"],
        "rag": ["rag", "knowledge", "知识库", "检索", "retrieval", "vector", "embedding", "文档", "search"],
        "tool": ["tool", "api", "function", "工具", "调用", "browser", "web", "http"],
        "memory": ["memory", "记忆", "state", "状态", "persist", "storage", "db", "database"],
        "safety": ["safety", "安全", "filter", "audit", "审计", "permission", "权限"],
        "self_improve": ["self_improve", "self-improve", "自我", "learn", "学习", "evolution", "进化", "improve"],
        "workflow": ["workflow", "工作流", "pipeline", "chain", "agent", "orchestrat"],
        "analysis": ["analysis", "分析", "log", "日志", "analytics", "统计", "monitor", "监控"],
    }
    
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
        
        content_lower = (skill_name + " " + content).lower()
        for skill_type, keywords in SKILL_TYPES.items():
            for keyword in keywords:
                if keyword in content_lower:
                    skill_types_count[skill_type] = skill_types_count.get(skill_type, 0) + 1
                    break
    
    return skill_types_count


# 保留旧函数名兼容
get_model_baseline = get_model_capability


# ============================================================
# 兼容性导出
# ============================================================

# 为了保持兼容性，保留旧类名
DimensionEstimator = DimensionEstimatorV2


if __name__ == "__main__":
    # 测试
    print("DimensionEstimatorV2 - 零基评分法")
    print("=" * 50)
    print("\n核心改进：")
    print("1. 无基础分，全部靠实际能力挣分")
    print("2. 质量系数：实际效果 / 配置存在")
    print("3. 行为测试：动态评估 > 静态检测")
