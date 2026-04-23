#!/usr/bin/env python3
"""
EIE Agent 自动检测器

支持 OpenClaw 和 Hermes 平台的自动检测

功能：
1. 自动读取Agent配置
2. 扫描Skills/Memory目录
3. 进行行为测试（可选）
4. 基于真实数据计算MEQ
"""

import argparse
import json
import os
import sys
import yaml  # 添加YAML支持
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入同级模块
from dimension_estimator import (
    DetectionData,
    DimensionEstimator,
    DimensionScores,
    scan_directory,
    read_json_safe,
    extract_skill_types,
    get_model_baseline,
    DIMENSION_MAX,
)

# 导入质量评估器
try:
    from quality_estimator import (
        QualityMetrics,
        analyze_memory_quality,
        analyze_skills_effectiveness,
        analyze_growth_quality,
        analyze_safety_quality,
        calculate_quality_adjusted_scores,
        generate_quality_report,
    )
    QUALITY_ASSESSMENT_AVAILABLE = True
except ImportError:
    QUALITY_ASSESSMENT_AVAILABLE = False

# 导入MEQ计算器
try:
    from meq_calculator import (
        calculate_meq,
        calculate_meq_with_coupling,
        check_vl4_vl5_conditions,
        get_vl_level,
        get_dimension_warning,
        get_evolution_suggestion,
        format_result,
    )
except ImportError:
    # 如果meq_calculator不可用，定义基本函数
    def calculate_meq(es, is_val, ms, vs, ce):
        return round(es * 0.25 + is_val * 0.15 + ms * 0.20 + vs * 0.15 + ce * 0.25, 1)
    
    def calculate_meq_with_coupling(es, is_val, ms, vs, ce):
        meq_linear = calculate_meq(es, is_val, ms, vs, ce)
        coupling = 0.15 * ((es * ms) / 10000 + (ms * ce) / 10000 - 0.5)
        return round(min(100, meq_linear + coupling), 1)
    
    def get_vl_level(meq):
        if meq >= 80: return "VL5", "元演化体"
        if meq >= 65: return "VL4", "自主系统"
        if meq >= 50: return "VL3", "智能系统"
        if meq >= 35: return "VL2", "交互系统"
        if meq >= 20: return "VL1", "规则系统"
        return "VL0", "静态系统"
    
    def check_vl4_vl5_conditions(meq, ms, vs):
        if meq >= 80 and ms >= 70 and vs >= 80:
            return "VL5", "元演化体"
        if meq >= 65 and ms >= 70 and vs >= 80:
            return "VL4", "自主系统"
        return get_vl_level(meq)
    
    def get_dimension_warning(es, is_val, ms, vs, ce):
        warnings = []
        thresholds = {"ES": 40, "IS": 45, "MS": 50, "VS": 60, "CE": 45}
        for dim, threshold in thresholds.items():
            value = {"ES": es, "IS": is_val, "MS": ms, "VS": vs, "CE": ce}[dim]
            if value < threshold:
                warnings.append(f"{dim}: {value} ⚠️ 建议提升至{threshold}+")
        return warnings
    
    def get_evolution_suggestion(meq, ms, vs):
        vl, _ = check_vl4_vl5_conditions(meq, ms, vs)
        suggestions = {
            "VL0": "建议引入状态管理和上下文处理能力",
            "VL1": "建议引入LLM能力替代纯规则引擎",
            "VL2": "建议增加外部知识库或RAG能力",
            "VL3": "当前VL3，建议提升MS≥70、VS≥80以解锁VL4",
            "VL4": "已具备主动进化能力，建议保持CE投入",
            "VL5": "已达到元演化水平，建议探索新领域泛化"
        }
        return suggestions.get(vl, "持续优化各维度能力")
    
    def format_result(es, is_val, ms, vs, ce, meq=None, with_coupling=False):
        if meq is None:
            meq = calculate_meq(es, is_val, ms, vs, ce) if not with_coupling else calculate_meq_with_coupling(es, is_val, ms, vs, ce)
        vl, stage = check_vl4_vl5_conditions(meq, ms, vs)
        warnings = get_dimension_warning(es, is_val, ms, vs, ce)
        suggestion = get_evolution_suggestion(meq, ms, vs)
        
        bars = {k: "█" * (v // 10) + "░" * (10 - v // 10) for k, v in [("ES", es), ("IS", is_val), ("MS", ms), ("VS", vs), ("CE", ce)]}
        
        warning_str = "\n".join(f"│  💡 {w}" for w in warnings) if warnings else ""
        
        # 维度中文简称
        dim_names = {
            "ES": "环境适应",  # 系统能否稳定运行
            "IS": "感知深度",  # 系统能理解多少信息
            "MS": "决策质量",  # 系统能做出多好的判断
            "VS": "对齐强度",  # 系统行为是否符合预期
            "CE": "成长速度",  # 系统能否持续变强
        }
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║                    🎯 EIE 进化评估结果                      ║
╠══════════════════════════════════════════════════════════╣
║                                                            ║
║   ┌──────────────────────────────────────────────────┐     ║
║   │                                                   │     ║
║   │                   MEQ = {meq:<5}                       │     ║
║   │                   {vl} · {stage:<12}                       │     ║
║   │                                                   │     ║
║   └──────────────────────────────────────────────────┘     ║
║                                                            ║
║   📊 五维度得分：                                          ║
║   ES({dim_names["ES"]})   {bars["ES"]} {es:<3}                    ║
║   IS({dim_names["IS"]})   {bars["IS"]} {is_val:<3}                    ║
║   MS({dim_names["MS"]})   {bars["MS"]} {ms:<3}                    ║
║   VS({dim_names["VS"]})   {bars["VS"]} {vs:<3}                    ║
║   CE({dim_names["CE"]})   {bars["CE"]} {ce:<3}                    ║
║                                                            ║
{warning_str}
║                                                            ║
║   💡 进化建议：                                             ║
║     {suggestion[:45]:<45}     ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
"""

# ============================================================
# 权重配置（与meq_calculator保持一致）
# ============================================================

WEIGHTS = {
    "ES": 0.25,
    "IS": 0.15,
    "MS": 0.20,
    "VS": 0.15,
    "CE": 0.25,
}


# ============================================================
# 平台检测器基类
# ============================================================

class BaseDetector:
    """检测器基类"""
    
    name = "base"
    
    def detect(self) -> Optional[DetectionData]:
        """执行检测，返回检测数据"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """检查平台是否可用"""
        raise NotImplementedError


# ============================================================
# OpenClaw 检测器
# ============================================================

class OpenClawDetector(BaseDetector):
    """
    OpenClaw 检测器
    
    OpenClaw 配置文件：~/.openclaw/openclaw.json
    Skills目录：~/.openclaw/skills/
    """
    
    name = "openclaw"
    
    def __init__(self, config_path: str = None, skills_path: str = None, workspace_path: str = None):
        self.home_dir = os.path.expanduser("~/.openclaw")
        self.config_path = config_path or os.path.join(self.home_dir, "openclaw.json")
        self.skills_dir = skills_path or os.path.join(self.home_dir, "skills")
        self.workspace_path = workspace_path or os.path.expanduser("~/workspace")
        self.memory_dir = os.path.join(self.workspace_path, "memory") if self.workspace_path else None
    
    def is_available(self) -> bool:
        """检查OpenClaw是否安装"""
        return os.path.exists(self.config_path)
    
    def detect(self) -> Optional[DetectionData]:
        """执行OpenClaw检测"""
        if not self.is_available():
            return None
        
        # 1. 读取配置文件
        config = read_json_safe(self.config_path)
        
        # 2. 扫描Skills目录
        skills = self._scan_skills()
        skill_types = extract_skill_types(self.skills_dir) if os.path.exists(self.skills_dir) else {}
        
        # 3. 解析配置
        data = self._parse_config(config, skills, skill_types)
        
        return data
    
    def _scan_skills(self) -> List[str]:
        """扫描Skills目录"""
        if not os.path.exists(self.skills_dir):
            return []
        
        skills = []
        for item in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, item)
            if os.path.isdir(skill_path):
                skills.append(item)
            elif item.endswith(('.json', '.py')):
                skills.append(item)
        
        return skills
    
    def _parse_config(self, config: Dict, skills: List[str], skill_types: Dict) -> DetectionData:
        """解析配置文件"""
        
        # 提取Channels
        channels = []
        channels_config = config.get("channels", config.get("channel", {}))
        if isinstance(channels_config, dict):
            channels = list(channels_config.keys())
        elif isinstance(channels_config, list):
            channels = channels_config
        
        # 提取模型
        model = config.get("model", config.get("llm", {}).get("model", ""))
        
        # 持久化存储
        storage = config.get("storage", config.get("db", config.get("database", {})))
        persistent_storage = bool(storage)
        
        # 安全配置
        safety = config.get("safety", config.get("security", {}))
        safety_config = {
            "allowlist": bool(safety.get("allowlist", safety.get("whitelist"))),
            "audit": bool(safety.get("audit", safety.get("logging"))),
            "content_filter": bool(safety.get("filter", safety.get("content_filter"))),
        }
        
        # 定时任务
        cron = config.get("cron", config.get("scheduled_tasks", config.get("schedule", [])))
        cron_enabled = bool(cron)
        
        # 心跳
        heartbeat = config.get("heartbeat", config.get("health_check", {}))
        heartbeat_enabled = bool(heartbeat)
        
        # 记忆系统
        memory = config.get("memory", config.get("context", {}))
        memory_system = bool(memory)
        
        # RAG
        rag = config.get("rag", config.get("knowledge", config.get("vector_db", {})))
        rag_enabled = bool(rag)
        
        # 轨迹记录
        trajectory = config.get("trajectory", config.get("trajectories", {}))
        trajectory_enabled = bool(trajectory)
        
        # 用户反馈
        feedback = config.get("feedback", config.get("user_feedback", {}))
        user_feedback_enabled = bool(feedback)
        
        return DetectionData(
            platform=self.name,
            channels=channels,
            skills=skills,
            skill_types=skill_types,
            model=model,
            memory_system=memory_system,
            rag_enabled=rag_enabled,
            persistent_storage=persistent_storage,
            safety_config=safety_config,
            cron_enabled=cron_enabled,
            heartbeat_enabled=heartbeat_enabled,
            trajectory_enabled=trajectory_enabled,
            user_feedback_enabled=user_feedback_enabled,
        )


# ============================================================
# Hermes 检测器
# ============================================================

class HermesDetector(BaseDetector):
    """
    Hermes 检测器
    
    Hermes 使用 Python API + AIAgent 类
    Skills/Memory 本地目录
    save_trajectories=True 保存轨迹
    
    支持配置文件格式：
    - config.json
    - config.yaml (Hermes主要使用)
    - agent.json
    - hermes.json
    """
    
    name = "hermes"
    
    def __init__(self, agent_path: str = "~/.hermes"):
        self.agent_path = os.path.expanduser(agent_path)
        # 支持JSON和YAML格式
        self.config_paths = [
            os.path.join(self.agent_path, "config.yaml"),  # YAML优先(Hermes主要格式)
            os.path.join(self.agent_path, "config.json"),
            os.path.join(self.agent_path, "agent.json"),
            os.path.join(self.agent_path, "hermes.json"),
        ]
        self.skills_dir = os.path.join(self.agent_path, "skills")
        self.memory_dir = os.path.join(self.agent_path, "memory")
    
    def is_available(self) -> bool:
        """检查Hermes是否安装"""
        return any(os.path.exists(p) for p in self.config_paths)
    
    def detect(self) -> Optional[DetectionData]:
        """执行Hermes检测"""
        if not self.is_available():
            return None
        
        # 1. 查找配置文件
        config = self._find_config()
        if not config:
            return None
        
        # 2. 扫描Skills和Memory目录
        skills = self._scan_skills()
        skill_types = extract_skill_types(self.skills_dir) if os.path.exists(self.skills_dir) else {}
        
        # 3. 解析配置
        data = self._parse_config(config, skills, skill_types)
        
        return data
    
    def _find_config(self) -> Dict:
        """查找配置文件，支持JSON和YAML格式"""
        for path in self.config_paths:
            if os.path.exists(path):
                try:
                    if path.endswith('.yaml') or path.endswith('.yml'):
                        # 解析YAML文件
                        with open(path, 'r', encoding='utf-8') as f:
                            return yaml.safe_load(f) or {}
                    else:
                        # 解析JSON文件
                        return read_json_safe(path)
                except Exception as e:
                    print(f"警告: 读取配置文件 {path} 失败: {e}")
                    continue
        
        return {}
    
    def _scan_skills(self) -> List[str]:
        """扫描Skills目录"""
        if not os.path.exists(self.skills_dir):
            return []
        
        skills = []
        for item in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, item)
            if os.path.isdir(skill_path):
                skills.append(item)
            elif item.endswith(('.json', '.yaml', '.yml', '.py')):
                skills.append(item)
        
        return skills
    
    def _parse_config(self, config: Dict, skills: List[str], skill_types: Dict) -> DetectionData:
        """解析配置文件"""
        
        # 运行时配置
        runtime = config.get("runtime", config.get("agent", {}))
        
        # Channels（Hermes可能没有channels概念，使用skills作为渠道）
        channels = config.get("channels", config.get("endpoints", []))
        if not channels:
            channels = [s for s in skills if skill_types.get("tool", 0) > 0]  # 工具型skills作为渠道
        
        # 模型 - 处理YAML嵌套结构和JSON结构
        model_config = (runtime.get("model") or 
                        config.get("model") or 
                        config.get("llm", {}).get("model", ""))
        # 提取模型名称字符串
        if isinstance(model_config, dict):
            model = model_config.get("default") or model_config.get("model") or model_config.get("name") or ""
        elif isinstance(model_config, str):
            model = model_config
        else:
            model = str(model_config) if model_config else ""
        
        # 持久化存储
        storage = config.get("storage", config.get("db", {}))
        persistent_storage = bool(storage)
        
        # 安全配置
        safety = config.get("safety", config.get("security", runtime.get("safety", {})))
        safety_config = {
            "allowlist": bool(safety.get("allowlist", safety.get("permissions"))),
            "audit": bool(safety.get("audit", safety.get("logging"))),
            "content_filter": bool(safety.get("filter", safety.get("content_filter"))),
        }
        
        # 定时任务
        cron = config.get("cron", config.get("scheduled_tasks", []))
        cron_enabled = bool(cron)
        
        # 心跳
        heartbeat = config.get("heartbeat", config.get("health_check", {}))
        heartbeat_enabled = bool(heartbeat)
        
        # 记忆系统
        memory_system = os.path.exists(self.memory_dir) or bool(config.get("memory"))
        
        # RAG
        rag = config.get("rag", config.get("knowledge", config.get("vector_db", {})))
        rag_enabled = bool(rag)
        
        # 轨迹记录
        trajectory = config.get("trajectory", config.get("save_trajectories", False))
        trajectory_enabled = bool(trajectory)
        
        # 用户反馈
        feedback = config.get("feedback", config.get("user_feedback", {}))
        user_feedback_enabled = bool(feedback)
        
        return DetectionData(
            platform=self.name,
            channels=channels,
            skills=skills,
            skill_types=skill_types,
            model=model,
            memory_system=memory_system,
            rag_enabled=rag_enabled,
            persistent_storage=persistent_storage,
            safety_config=safety_config,
            cron_enabled=cron_enabled,
            heartbeat_enabled=heartbeat_enabled,
            trajectory_enabled=trajectory_enabled,
            user_feedback_enabled=user_feedback_enabled,
        )


# ============================================================
# 自动检测器管理器
# ============================================================

class AutoDetector:
    """自动检测器管理器"""
    
    def __init__(self):
        self.detectors: List[BaseDetector] = [
            OpenClawDetector(),
            HermesDetector(),
        ]
    
    def detect_all(self) -> Optional[Tuple[DetectionData, DimensionScores, Dict]]:
        """
        自动检测所有可用平台
        
        Returns:
            (检测数据, 维度分数, MEQ结果) 或 None
        """
        for detector in self.detectors:
            if detector.is_available():
                print(f"检测到平台: {detector.name}")
                data = detector.detect()
                if data:
                    return self._process_detection(data)
        
        print("未检测到支持的Agent平台")
        return None
    
    def detect_platform(self, platform: str) -> Optional[Tuple[DetectionData, DimensionScores, Dict]]:
        """检测指定平台"""
        for detector in self.detectors:
            if detector.name == platform and detector.is_available():
                data = detector.detect()
                if data:
                    return self._process_detection(data)
        
        print(f"平台 {platform} 不可用或未安装")
        return None
    
    def _process_detection(self, data: DetectionData, workspace_path: str = None) -> Tuple[DetectionData, DimensionScores, Dict]:
        """处理检测结果，集成质量评估"""
        # 估算维度
        estimator = DimensionEstimator(data)
        base_scores = estimator.estimate_all()
        
        # 质量评估（如果可用）
        if QUALITY_ASSESSMENT_AVAILABLE and workspace_path:
            quality = self._assess_quality(workspace_path, data)
            
            # 根据质量调整分数
            base_dict = {
                "ES": base_scores.ES,
                "IS": base_scores.IS,
                "MS": base_scores.MS,
                "VS": base_scores.VS,
                "CE": base_scores.CE,
            }
            adjusted = calculate_quality_adjusted_scores(base_dict, quality)
            
            # 更新分数
            base_scores.ES = adjusted["ES"]
            base_scores.IS = adjusted["IS"]
            base_scores.MS = adjusted["MS"]
            base_scores.VS = adjusted["VS"]
            base_scores.CE = adjusted["CE"]
            
            # 添加质量报告
            quality_report = generate_quality_report(quality)
        else:
            quality_report = "质量评估不可用"
        
        # 计算MEQ
        meq = calculate_meq(base_scores.ES, base_scores.IS, base_scores.MS, base_scores.VS, base_scores.CE)
        meq_with_coupling = calculate_meq_with_coupling(base_scores.ES, base_scores.IS, base_scores.MS, base_scores.VS, base_scores.CE)
        
        # 获取VL等级
        vl, stage = check_vl4_vl5_conditions(meq, base_scores.MS, base_scores.VS)
        
        # 维度警告
        warnings = get_dimension_warning(base_scores.ES, base_scores.IS, base_scores.MS, base_scores.VS, base_scores.CE)
        
        # 进化建议
        suggestion = get_evolution_suggestion(meq, base_scores.MS, base_scores.VS)
        
        result = {
            "meq": meq,
            "meq_with_coupling": meq_with_coupling,
            "vl": vl,
            "stage": stage,
            "warnings": warnings,
            "suggestion": suggestion,
            "quality_report": quality_report,
        }
        
        return data, base_scores, result
    
    def _assess_quality(self, workspace_path: str, data: DetectionData) -> 'QualityMetrics':
        """评估质量指标"""
        quality = QualityMetrics()
        
        # 记忆质量
        memory_dir = os.path.join(workspace_path, "memory")
        usage, content_q = analyze_memory_quality(memory_dir)
        quality.memory_usage_rate = usage
        quality.memory_content_quality = content_q
        
        # Skills有效性
        skills_dir = os.path.join(workspace_path, "skills")
        eff_ratio, diversity = analyze_skills_effectiveness(skills_dir)
        quality.effective_skills_ratio = eff_ratio
        quality.skill_diversity = diversity
        
        # 成长质量
        rec_freq, err_rate, evo_count = analyze_growth_quality(workspace_path)
        quality.growth_record_frequency = rec_freq
        quality.error_learning_rate = err_rate
        quality.evolution_output_count = evo_count
        
        # 安全质量
        safety_active, feedback_active = analyze_safety_quality({}, workspace_path)
        quality.safety_active = safety_active
        quality.feedback_loop_active = feedback_active
        
        return quality
    
    def format_full_report(self, data: DetectionData, scores: DimensionScores, result: Dict) -> str:
        """格式化完整报告"""
        
        # 维度条形图
        def bar(value: int) -> str:
            return "█" * (value // 10) + "░" * (10 - value // 10)
        
        # 数据来源说明
        data_sources = []
        if data.platform == "openclaw":
            data_sources.append(f"配置文件: ~/.openclaw/openclaw.json")
            data_sources.append(f"Skills目录: ~/.openclaw/skills/")
        elif data.platform == "hermes":
            data_sources.append(f"配置目录: {data.agent_path if hasattr(data, 'agent_path') else '~/.hermes'}")
            data_sources.append(f"Skills目录: skills/")
        
        if data.channels:
            data_sources.append(f"Channels: {', '.join(data.channels)}")
        if data.skills:
            data_sources.append(f"Skills: {len(data.skills)}个")
        if data.model:
            data_sources.append(f"模型: {data.model}")
        
        source_str = "\n│  ".join(data_sources)
        
        # 警告
        warning_str = ""
        if result["warnings"]:
            warning_str = "╠══════════════════════════════════════════════════════════╣\n"
            for w in result["warnings"]:
                warning_str += f"│  ⚠️  {w}\n"
        
        # 检测到的问题
        vuln_str = ""
        if data.vulnerabilities:
            vuln_str = "╠══════════════════════════════════════════════════════════╣\n"
            for v in data.vulnerabilities:
                vuln_str += f"│  🔴 安全漏洞: {v}\n"
        
        # 质量指标
        quality_str = ""
        if result.get("quality_report"):
            quality_str = "╠══════════════════════════════════════════════════════════╣\n"
            quality_str += "│  📊 质量指标                                              │\n"
            quality_str += "║  ─────────────────────────────────────────────────────── ║\n"
            for line in result["quality_report"].split("\n"):
                quality_str += f"│  {line:<55}│\n"
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║           🎯 EIE Agent 自动检测评估报告                    ║
╠══════════════════════════════════════════════════════════╣
║  检测平台: {data.platform.upper()}                                        ║
╠══════════════════════════════════════════════════════════╣
║  📊 综合评分                                              ║
║  ─────────────────────────────────────────────────────── ║
║  MEQ = {result["meq"]} | {result["vl"]} | {result["stage"]}                          ║
║  MEQ(含耦合) = {result["meq_with_coupling"]}                                      ║
╠══════════════════════════════════════════════════════════╣
║  📐 五维度得分                                            ║
║  ─────────────────────────────────────────────────────── ║
║  ES(环境适应) {bar(scores.ES)} {scores.ES}                            ║
║  IS(感知深度) {bar(scores.IS)} {scores.IS}                            ║
║  MS(决策质量) {bar(scores.MS)} {scores.MS}                            ║
║  VS(对齐强度) {bar(scores.VS)} {scores.VS}                            ║
║  CE(成长速度) {bar(scores.CE)} {scores.CE}                            ║
╠══════════════════════════════════════════════════════════╣
║  📋 数据来源                                              ║
║  ─────────────────────────────────────────────────────── ║
│  {source_str}
╠══════════════════════════════════════════════════════════╣
║  💡 进化建议                                              ║
║  ─────────────────────────────────────────────────────── ║
│  {result["suggestion"][:58]}
{warning_str}{vuln_str}{quality_str}╚══════════════════════════════════════════════════════════╝
"""


# ============================================================
# 手动检测模式（降级方案）
# ============================================================

def manual_estimate(system_type: str = None) -> Tuple[DimensionScores, Dict]:
    """
    手动评估（降级方案）
    
    当自动检测失败时使用，基于关键词智能估算
    """
    # 基础分数
    es, is_val, ms, vs, ce = 30, 20, 45, 40, 20
    
    if system_type:
        system_lower = system_type.lower()
        
        # ES维度关键词
        if any(k in system_lower for k in ["多渠道", "channel", "telegram", "discord", "微信", "whatsapp"]):
            es += 15
        if any(k in system_lower for k in ["持久化", "存储", "persist", "storage", "数据库"]):
            es += 10
        if any(k in system_lower for k in ["守护", "daemon", "后台", "cron", "定时"]):
            es += 10
        
        # IS维度关键词
        if any(k in system_lower for k in ["记忆", "memory", "状态", "state", "上下文"]):
            is_val += 15
        if any(k in system_lower for k in ["rag", "检索", "知识库", "knowledge", "向量", "文档"]):
            is_val += 15
        if any(k in system_lower for k in ["多模态", "图像", "语音", "视觉", "vision", "image", "audio"]):
            is_val += 12
        
        # MS维度关键词
        if any(k in system_lower for k in ["工具", "tool", "api", "调用", "function"]):
            ms += 10
        if any(k in system_lower for k in ["工作流", "workflow", "pipeline", "编排"]):
            ms += 10
        if any(k in system_lower for k in ["gpt-4", "claude", "opus", "大模型", "llm"]):
            ms += 15
        if any(k in system_lower for k in ["简单", "规则", "预设", "基础"]):
            ms -= 25
        
        # VS维度关键词
        if any(k in system_lower for k in ["安全", "safety", "审计", "audit", "权限"]):
            vs += 15
        if any(k in system_lower for k in ["过滤", "filter", "审核", "内容"]):
            vs += 10
        if any(k in system_lower for k in ["反馈", "feedback", "评价"]):
            vs += 10
        
        # CE维度关键词
        skill_count = len([k for k in ["工具", "tool", "skill", "能力", "插件"] if k in system_lower])
        ce += skill_count * 5
        if any(k in system_lower for k in ["进化", "evolution", "学习", "learn", "自我改进"]):
            ce += 20
        if any(k in system_lower for k in ["cron", "定时", "heartbeat", "心跳"]):
            ce += 15
        if any(k in system_lower for k in ["简单", "基础", "预设"]):
            ce -= 10
    
    # 限制范围
    es = min(max(es, 10), 90)
    is_val = min(max(is_val, 10), 90)
    ms = min(max(ms, 10), 90)
    vs = min(max(vs, 20), 95)
    ce = min(max(ce, 10), 90)
    
    scores = DimensionScores(
        ES=es,
        IS=is_val,
        MS=ms,
        VS=vs,
        CE=ce,
        data_source={"模式": "手动评估（描述型）"}
    )
    
    meq = calculate_meq(es, is_val, ms, vs, ce)
    vl, stage = check_vl4_vl5_conditions(meq, ms, vs)
    
    result = {
        "meq": meq,
        "meq_with_coupling": calculate_meq_with_coupling(es, is_val, ms, vs, ce),
        "vl": vl,
        "stage": stage,
        "warnings": get_dimension_warning(es, is_val, ms, vs, ce),
        "suggestion": get_evolution_suggestion(meq, ms, vs),
    }
    
    return scores, result


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="EIE Agent 自动检测器")
    parser.add_argument("--platform", "-p", choices=["openclaw", "hermes"], 
                        help="指定检测平台")
    parser.add_argument("--system", "-s", 
                        help="手动指定系统类型（降级模式）")
    parser.add_argument("--detailed", "-d", action="store_true",
                        help="显示详细数据来源")
    parser.add_argument("--coupling", "-c", action="store_true",
                        help="使用耦合增强公式")
    parser.add_argument("--config-path", help="配置文件路径")
    parser.add_argument("--skills-path", help="Skills目录路径")
    parser.add_argument("--workspace-path", help="Workspace目录路径")
    
    args = parser.parse_args()
    
    # 尝试自动检测
    detector = AutoDetector()
    
    # 如果指定了自定义路径，使用自定义检测器
    if args.config_path or args.workspace_path:
        workspace = args.workspace_path or os.getcwd()
        
        # 创建自定义OpenClaw检测器
        oc_detector = OpenClawDetector(
            config_path=args.config_path,
            skills_path=args.skills_path,
            workspace_path=workspace
        )
        
        if oc_detector.is_available():
            print(f"检测到平台: openclaw (自定义路径)")
            data = oc_detector.detect()
            if data:
                result = detector._process_detection(data, workspace_path=workspace)
                
                # 输出完整报告
                print(detector.format_full_report(data, result[1], result[2]))
                
                # 详细数据来源
                if args.detailed:
                    print("\n📊 维度详细估算来源：")
                    for dim, source in result[1].data_source.items():
                        print(f"  {dim}: {source}")
                return
    
    if args.platform:
        result = detector.detect_platform(args.platform)
    else:
        result = detector.detect_all()
    
    if result:
        data, scores, calc_result = result
        
        # 输出完整报告
        print(detector.format_full_report(data, scores, calc_result))
        
        # 详细数据来源
        if args.detailed:
            print("\n📊 维度详细估算来源：")
            for dim, source in scores.data_source.items():
                print(f"  {dim}: {source}")
    
    elif args.system:
        # 降级到手动模式
        print(f"\n⚠️  未检测到Agent平台，使用手动评估模式")
        print(f"系统类型: {args.system}\n")
        
        scores, calc_result = manual_estimate(args.system)
        
        meq = calc_result["meq_with_coupling"] if args.coupling else calc_result["meq"]
        print(format_result(scores.ES, scores.IS, scores.MS, scores.VS, scores.CE, 
                             meq=meq, with_coupling=args.coupling))
    
    else:
        print("""
╔══════════════════════════════════════════════════════════╗
║           ⚠️  未检测到支持的Agent平台                      ║
╠══════════════════════════════════════════════════════════╣
║  支持的平台：                                              ║
║  • OpenClaw: ~/.openclaw/openclaw.json                    ║
║  • Hermes: ~/.hermes/config.json                          ║
║                                                            ║
║  如需手动评估，请使用：                                     ║
║  python auto_detect.py --system "RAG Agent"               ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
