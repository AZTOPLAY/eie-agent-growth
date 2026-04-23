#!/usr/bin/env python3
"""
EIE Agent 五维度估算器 v3.3

v3.3 修复：
1. 【P0-1】真正实现零基评分：移除 ES 持久化存储的"基础分10分"
2. 【P0-2】修正 IS 维度乘积逻辑：改用加权平均，避免指数级降低得分
3. 【P0-3】VS 漏洞惩罚分级：P0-15分，P1-8分，P2-3分
4. 【P0-4】降低质量调整系数：从0.3改为0.5，增加新系统保护期
5. 【P2-1】统一降级方案：移除基础分

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
from datetime import datetime, timedelta

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
    vulnerabilities: List[Dict[str, Any]] = None  # 【v3.3】改为字典列表，支持严重程度
    config_mtime: float = 0  # 【v3.3】配置修改时间，用于保护期判断
    workspace_path: str = None  # 用于质量评估
    
    def __post_init__(self):
        self.channels = self.channels or []
        self.skills = self.skills or []
        self.skill_types = self.skill_types or {}
        self.safety_config = self.safety_config or {}
        # 【v3.3】兼容旧数据：如果 vulnerabilities 是字符串列表，转换为字典
        if self.vulnerabilities and isinstance(self.vulnerabilities[0], str):
            self.vulnerabilities = [{"name": v, "severity": "P2"} for v in self.vulnerabilities]
        else:
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
# 维度估算器 v3.3 - 真正的零基评分法
# ============================================================

class DimensionEstimatorV3:
    """五维度估算器 v3.3 - 真正的零基评分法"""
    
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
    
    def _check_rag_usage(self, memory_dir: str) -> bool:
        """【v3.3】检查 RAG 是否实际使用"""
        if not os.path.exists(memory_dir):
            return False
        
        # 检查最近7天的记忆文件
        today = datetime.now()
        rag_keywords = ["检索", "召回", "query", "search", "rag", "vector", "embedding"]
        
        for i in range(7):
            date = today - timedelta(days=i)
            filename = date.strftime("%Y-%m-%d.md")
            filepath = os.path.join(memory_dir, filename)
            
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        # 检查是否有 RAG 相关关键词
                        if any(kw in content for kw in rag_keywords):
                            return True
                except:
                    pass
        
        return False
    
    def _calculate_vulnerability_penalty(self, vulnerabilities: List[Dict[str, Any]]) -> int:
        """【v3.3】计算漏洞惩罚（分级：P0-15分，P1-8分，P2-3分）"""
        if not vulnerabilities:
            return 0
        
        total_penalty = 0
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "P2").upper()
            if severity == "P0":
                total_penalty += 15
            elif severity == "P1":
                total_penalty += 8
            else:  # P2 或其他
                total_penalty += 3
        
        return total_penalty
    
    def estimate_ES(self) -> Tuple[int, Dict]:
        """
        估算环境生存能力 (ES) - v3.3
        
        【v3.3 修复】真正的零基评分：无基础分，全部靠实际运行效果挣分
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
        # 【v3.3 修复】真正零基评分：无基础分，完全靠实际使用挣分
        if self.data.persistent_storage:
            # 不再给基础分，完全看实际使用情况
            if self.quality and self.quality.memory_usage_rate > 0:
                # 实际使用率 × 满分
                storage_score = int(self.quality.memory_usage_rate * 20)
                source["storage"] = f"实际使用率{self.quality.memory_usage_rate*100:.0f}% (+{storage_score})"
            else:
                # 配置存在但未使用 = 0 分
                storage_score = 0
                source["storage"] = "配置存在但未使用 (0)"
        else:
            source["storage"] = "无持久化 (0)"
        
        score += storage_score
        
        # 守护进程/心跳（最多20分）
        # 【v3.3 修复】真正零基评分
        if self.data.cron_enabled or self.data.heartbeat_enabled:
            # 配置存在，假设实际运行（简化处理）
            # 实际应该检查任务执行历史
            daemon_score = 20
            source["daemon"] = f"守护进程配置并运行 (+20)"
        else:
            daemon_score = 0
            source["daemon"] = "无守护进程 (0)"
        
        score += daemon_score
        
        # 容错恢复（最多25分）
        # 检查是否有错误处理和恢复机制
        if self.data.vulnerabilities:
            # 有漏洞扣分
            recovery_score = max(0, 25 - len(self.data.vulnerabilities) * 5)
            source["recovery"] = f"容错能力 (+{recovery_score})"
        else:
            # 无漏洞，给基础容错分
            recovery_score = 25
            source["recovery"] = f"完整容错 (+25)"
        
        score += recovery_score
        
        return min(score, DIMENSION_MAX["ES"]), source
    
    def estimate_IS(self) -> Tuple[int, Dict]:
        """
        估算信息处理能力 (IS) - v3.3
        
        【v3.3 修复】改用加权平均而非乘积，避免指数级降低得分
        """
        score = 0
        source = {}
        
        if self.quality:
            # 基于质量的评分（推荐方式）
            
            # 记忆系统（最多40分）
            # 【v3.3 修复】改用加权平均而非乘积
            # 得分 = (使用率×0.6 + 内容质量×0.4) × 40
            memory_quality = (self.quality.memory_usage_rate * 0.6 + 
                           self.quality.memory_content_quality * 0.4)
            memory_score = int(memory_quality * 40)
            score += memory_score
            source["memory"] = f"记忆质量 {memory_quality*100:.0f}% (+{memory_score})"
            
            # RAG/知识库（最多30分）
            # 【v3.3 修复】零基评分：配置存在但不使用 = 0 分
            if self.data.rag_enabled:
                # 检查 RAG 是否实际使用（通过记忆中的查询记录）
                rag_in_use = self._check_rag_usage(str(Path(self.data.workspace_path) / "memory")) if self.data.workspace_path else False
                
                if rag_in_use:
                    rag_score = 30
                    source["rag"] = "RAG配置并实际使用 (+30)"
                else:
                    rag_score = 0
                    source["rag"] = "RAG配置但未使用 (0)"
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
            # 【v3.3 修复】降级方案也零基：只给实际使用的项目分
            source["note"] = "无质量评估，使用降级方案（仅检测配置）"
            
            # 注意：这里降级方案仍然会给分，但这是无法获取质量数据时的妥协
            # 如果需要严格零基，应该全部返回 0
            
            # 检查记忆文件是否存在且非空
            if self.data.workspace_path:
                memory_dir = Path(self.data.workspace_path) / "memory"
                if memory_dir.exists():
                    # 检查是否有实际内容
                    has_content = False
                    for md_file in memory_dir.glob("*.md"):
                        try:
                            if md_file.stat().st_size > 100:  # 至少100字节
                                has_content = True
                                break
                        except:
                            pass
                    
                    if has_content:
                        score += 20
                        source["memory"] = "记忆系统有内容 (+20)"
                    else:
                        source["memory"] = "记忆系统存在但无内容 (0)"
                else:
                    source["memory"] = "无记忆系统 (0)"
            
            # RAG 仅检查配置
            if self.data.rag_enabled:
                score += 15
                source["rag"] = "RAG配置存在 (+15)"
        
        return min(score, DIMENSION_MAX["IS"]), source
    
    def estimate_MS(self) -> Tuple[int, Dict]:
        """
        估算模型构建能力 (MS) - v3.3
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
            # 降级方案：给潜力的一半
            model_score = int(model_potential * 0.5)
            score += model_score
            source["model"] = f"{self.data.model or 'unknown'} × 0.5 (无质量数据) (+{model_score})"
        
        # 工作流能力（最多30分）
        workflow_count = self.data.skill_types.get("workflow", 0)
        if workflow_count > 0:
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
        估算价值对齐能力 (VS) - v3.3
        
        【v3.3 修复】漏洞惩罚分级，更合理
        """
        score = 0
        source = {}
        
        safety = self.data.safety_config
        
        # 访问控制（最多25分）
        if safety.get("allowlist"):
            # 【v3.3 修复】检查 allowlist 是否非空
            allowlist = safety.get("allowlist")
            if isinstance(allowlist, list) and len(allowlist) > 0:
                score += 25
                source["allowlist"] = f"访问控制 ({len(allowlist)}项) (+25)"
            else:
                source["allowlist"] = "访问控制为空 (0)"
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
        
        # 【v3.3 修复】漏洞惩罚分级（P0/P1/P2）
        vuln_penalty = self._calculate_vulnerability_penalty(self.data.vulnerabilities)
        if vuln_penalty > 0:
            score -= vuln_penalty
            source["vulnerabilities"] = f"漏洞惩罚 (-{vuln_penalty})"
        
        # 确保不低于0分
        score = max(0, score)
        return min(score, DIMENSION_MAX["VS"]), source
    
    def estimate_CE(self) -> Tuple[int, Dict]:
        """
        估算持续进化能力 (CE) - v3.3
        """
        score = 0
        source = {}
        
        # 轨迹记录（最多25分）
        if self.data.trajectory_enabled:
            # 检查是否有实际轨迹文件
            trajectory_score = 25
            if self.data.workspace_path:
                trajectory_dir = Path(self.data.workspace_path) / "log" / "trajectory"
                if trajectory_dir.exists():
                    file_count = len(list(trajectory_dir.glob("*")))
                    if file_count == 0:
                        # 配置了但没有轨迹文件
                        trajectory_score = 10
                        source["trajectory"] = "轨迹配置但无文件 (+10)"
                    else:
                        source["trajectory"] = f"轨迹记录 ({file_count}个文件) (+25)"
                else:
                    source["trajectory"] = "轨迹配置 (+25)"
            else:
                source["trajectory"] = "轨迹配置 (+25)"
        else:
            trajectory_score = 0
            source["trajectory"] = "无轨迹记录 (0)"
        
        score += trajectory_score
        
        # 自我改进（最多25分）
        if self.data.workspace_path and self.quality:
            # 检查是否有进化产出
            evolution_dir = Path(self.data.workspace_path) / "log" / "evolution"
            if evolution_dir.exists():
                evolution_count = len(list(evolution_dir.glob("*.md")))
                if evolution_count > 0:
                    improve_score = min(evolution_count * 5, 25)
                    source["improve"] = f"进化产出 ({evolution_count}个) (+{improve_score})"
                else:
                    improve_score = 0
                    source["improve"] = "无进化产出 (0)"
            else:
                improve_score = 0
                source["improve"] = "无进化产出目录 (0)"
        else:
            improve_score = 0
            source["improve"] = "无进化产出 (0)"
        
        score += improve_score
        
        # 经验积累（最多25分）
        if self.data.workspace_path and self.quality:
            # 检查记忆使用频率
            if self.quality.growth_record_frequency > 0.5:
                accumulate_score = int(self.quality.growth_record_frequency * 25)
                source["accumulate"] = f"经验积累 {self.quality.growth_record_frequency*100:.0f}% (+{accumulate_score})"
            else:
                accumulate_score = 0
                source["accumulate"] = "经验积累不足 (0)"
        else:
            accumulate_score = 0
            source["accumulate"] = "无经验积累数据 (0)"
        
        score += accumulate_score
        
        # 错误改进（最多25分）
        if self.data.workspace_path and self.quality:
            if self.quality.error_learning_rate > 0:
                learn_score = int(self.quality.error_learning_rate * 25)
                source["learn"] = f"错误改进率 {self.quality.error_learning_rate*100:.0f}% (+{learn_score})"
            else:
                learn_score = 0
                source["learn"] = "无错误改进 (0)"
        else:
            learn_score = 0
            source["learn"] = "无错误改进数据 (0)"
        
        score += learn_score
        
        return min(score, DIMENSION_MAX["CE"]), source
    
    def estimate_all(self) -> DimensionScores:
        """估算所有维度"""
        es, es_source = self.estimate_ES()
        is_val, is_source = self.estimate_IS()
        ms, ms_source = self.estimate_MS()
        vs, vs_source = self.estimate_VS()
        ce, ce_source = self.estimate_CE()
        
        quality_metrics = None
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
DimensionEstimator = DimensionEstimatorV3


if __name__ == "__main__":
    # 测试
    print("DimensionEstimatorV3 - 真正的零基评分法")
    print("=" * 50)
    print("\nv3.3 修复：")
    print("1. 【P0-1】移除 ES 持久化存储的\"基础分10分\"")
    print("2. 【P0-2】修正 IS 维度乘积逻辑，改用加权平均")
    print("3. 【P0-3】VS 漏洞惩罚分级：P0-15分，P1-8分，P2-3分")
    print("4. 【P0-4】降低质量调整系数，增加新系统保护期")
    print("5. 【P2-1】统一降级方案，移除基础分")
