#!/usr/bin/env python3
"""
EIE Agent 质量评估器

基于"实际效果"而非"配置存在"评估五维度

核心改进：
1. IS：从"Memory存在"改为"Memory使用率"
2. MS：从"Skills数量"改为"有效Skills"
3. CE：从"配置存在"改为"成长记录"
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class QualityMetrics:
    """质量指标"""
    # 记忆系统质量
    memory_usage_rate: float = 0.0  # 0-1，记忆文件活跃度
    memory_content_quality: float = 0.0  # 0-1，内容质量（非空比例）
    
    # Skills质量
    effective_skills_ratio: float = 0.5  # 0-1，有效Skills比例
    skill_diversity: float = 0.0  # 0-1，类型多样性
    
    # 成长质量
    growth_record_frequency: float = 0.0  # 0-1，记录更新频率
    error_learning_rate: float = 0.0  # 0-1，错误改进率
    evolution_output_count: int = 0  # 进化产出数量
    
    # 安全质量
    safety_active: bool = False  # 安全部件是否真正启用
    feedback_loop_active: bool = False  # 反馈闭环是否真正工作


def analyze_memory_quality(memory_dir: str, days: int = 14) -> Tuple[float, float]:
    """
    分析记忆系统质量
    
    Returns:
        (usage_rate, content_quality)
        - usage_rate: 最近N天有内容的天数占比
        - content_quality: 非空文件的内容质量（行数/阈值）
    """
    if not os.path.exists(memory_dir):
        return 0.0, 0.0
    
    today = datetime.now()
    active_days = 0
    total_quality = 0.0
    checked_days = 0
    
    for i in range(days):
        date = today - timedelta(days=i)
        filename = date.strftime("%Y-%m-%d.md")
        filepath = os.path.join(memory_dir, filename)
        
        checked_days += 1
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.strip().split('\n'))
                    
                    if lines > 5:  # 有实质内容
                        active_days += 1
                        # 内容质量：50行以上为满分
                        quality = min(lines / 50.0, 1.0)
                        total_quality += quality
            except:
                pass
    
    usage_rate = active_days / checked_days if checked_days > 0 else 0.0
    content_quality = total_quality / active_days if active_days > 0 else 0.0
    
    return usage_rate, content_quality


def analyze_skills_effectiveness(skills_dir: str, config_path: str = None) -> Tuple[float, float]:
    """
    分析Skills有效性
    
    Returns:
        (effective_ratio, diversity)
        - effective_ratio: 有效Skills比例（有SKILL.md且有实质内容）
        - diversity: 类型多样性（不同类型Skills占比）
    """
    if not os.path.exists(skills_dir):
        return 0.0, 0.0
    
    skill_dirs = [d for d in os.listdir(skills_dir) 
                  if os.path.isdir(os.path.join(skills_dir, d))]
    
    if not skill_dirs:
        return 0.0, 0.0
    
    effective_count = 0
    type_keywords = set()
    
    for skill_name in skill_dirs:
        skill_path = os.path.join(skills_dir, skill_name)
        skill_md = os.path.join(skill_path, "SKILL.md")
        
        # 检查是否有SKILL.md且有实质内容
        if os.path.exists(skill_md):
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 有YAML头部且内容超过500字符
                    if '---' in content and len(content) > 500:
                        effective_count += 1
                        
                        # 提取类型关键词
                        content_lower = content.lower()
                        for kw in ['rag', 'vision', 'tool', 'memory', 'safety', 'workflow', 
                                   'analysis', 'search', 'calendar', 'task', 'file', 'web']:
                            if kw in content_lower:
                                type_keywords.add(kw)
            except:
                pass
    
    effective_ratio = effective_count / len(skill_dirs) if skill_dirs else 0.0
    # 多样性：不同类型数量/最大可能类型数
    diversity = len(type_keywords) / 12.0 if type_keywords else 0.0
    
    return effective_ratio, diversity


def analyze_growth_quality(workspace_dir: str) -> Tuple[float, float, int]:
    """
    分析成长质量
    
    Returns:
        (record_frequency, error_learning_rate, evolution_count)
        - record_frequency: 记忆文件更新频率
        - error_learning_rate: 错误记录改进率
        - evolution_count: 进化产出数量
    """
    memory_dir = os.path.join(workspace_dir, "memory")
    log_dir = os.path.join(workspace_dir, "log")
    
    # 记录更新频率
    usage_rate, _ = analyze_memory_quality(memory_dir, days=14)
    record_frequency = usage_rate
    
    # 错误改进率
    error_dir = os.path.join(log_dir, "error") if log_dir else None
    error_learning_rate = 0.0
    
    if error_dir and os.path.exists(error_dir):
        error_files = [f for f in os.listdir(error_dir) if f.endswith('.md')]
        if error_files:
            # 检查错误记录是否包含"教训"或"预防"
            learned_count = 0
            for ef in error_files:
                try:
                    with open(os.path.join(error_dir, ef), 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        if '教训' in content or '预防' in content or 'lesson' in content:
                            learned_count += 1
                except:
                    pass
            error_learning_rate = learned_count / len(error_files) if error_files else 0.0
    
    # 进化产出数量
    evolution_dir = os.path.join(log_dir, "evolution") if log_dir else None
    evolution_count = 0
    
    if evolution_dir and os.path.exists(evolution_dir):
        evolution_count = len([f for f in os.listdir(evolution_dir) 
                               if f.endswith('.md') or f.endswith('.json')])
    
    return record_frequency, error_learning_rate, evolution_count


def analyze_safety_quality(config: dict, workspace_dir: str) -> Tuple[bool, bool]:
    """
    分析安全质量
    
    Returns:
        (safety_active, feedback_loop_active)
    """
    safety_active = False
    feedback_loop_active = False
    
    # 检查安全配置是否真正启用
    safety_config = config.get("safety", {})
    if safety_config:
        # 有allowlist且非空
        allowlist = safety_config.get("allowlist", [])
        if allowlist and len(allowlist) > 0:
            safety_active = True
        
        # 有content_filter且启用
        if safety_config.get("content_filter", {}).get("enabled", False):
            safety_active = True
    
    # 检查反馈闭环
    # 1. 有错误记录目录
    error_dir = os.path.join(workspace_dir, "log", "error")
    has_error_records = os.path.exists(error_dir) and len(os.listdir(error_dir)) > 0 if os.path.exists(error_dir) else False
    
    # 2. 有MEMORY.md在更新
    memory_file = os.path.join(workspace_dir, "MEMORY.md")
    has_active_memory = False
    if os.path.exists(memory_file):
        try:
            mtime = os.path.getmtime(memory_file)
            days_since_update = (datetime.now().timestamp() - mtime) / 86400
            has_active_memory = days_since_update < 7  # 7天内更新过
        except:
            pass
    
    feedback_loop_active = has_error_records and has_active_memory
    
    return safety_active, feedback_loop_active


def calculate_quality_adjusted_scores(
    base_scores: Dict[str, int],
    quality: QualityMetrics,
    config_mtime: float = 0  # 【v3.3】新增：配置修改时间，用于保护期判断
) -> Dict[str, int]:
    """
    根据质量指标调整维度分数
    
    【v3.3 修复】
    - 降低调整系数：从0.3改为0.5，避免过度惩罚新系统
    - 增加7天保护期：新系统未使用时只降50%而非70%
    
    Args:
        base_scores: 基础分数 {"ES": x, "IS": y, ...}
        quality: 质量指标
        config_mtime: 配置修改时间戳（用于保护期判断）
    
    Returns:
        调整后的分数
    """
    adjusted = base_scores.copy()
    
    # 【v3.3】判断是否在保护期内（7天）
    days_since_config = 0
    if config_mtime > 0:
        days_since_config = (datetime.now().timestamp() - config_mtime) / 86400
    in_protection_period = days_since_config < 7
    
    # IS调整：基于记忆使用率和内容质量
    is_quality_factor = (quality.memory_usage_rate * 0.6 + quality.memory_content_quality * 0.4)
    if quality.memory_usage_rate > 0:
        adjusted["IS"] = int(base_scores["IS"] * (0.5 + 0.5 * is_quality_factor))
    else:
        # 【v3.3 修复】保护期内只降50%，保护期外降50%（原70%）
        if in_protection_period:
            adjusted["IS"] = int(base_scores["IS"] * 0.5)  # 保护期：降50%
        else:
            adjusted["IS"] = int(base_scores["IS"] * 0.5)  # 非保护期：降50%（原70%）
    
    # MS调整：基于Skills有效性
    ms_quality_factor = (quality.effective_skills_ratio * 0.7 + quality.skill_diversity * 0.3)
    adjusted["MS"] = int(base_scores["MS"] * (0.6 + 0.4 * ms_quality_factor))
    
    # CE调整：基于成长记录
    ce_quality_factor = (
        quality.growth_record_frequency * 0.4 + 
        quality.error_learning_rate * 0.3 + 
        min(quality.evolution_output_count / 10.0, 1.0) * 0.3
    )
    adjusted["CE"] = int(base_scores["CE"] * (0.4 + 0.6 * ce_quality_factor))
    
    # VS调整：基于安全活跃度
    if quality.safety_active:
        adjusted["VS"] = min(adjusted["VS"] + 10, 95)
    if quality.feedback_loop_active:
        adjusted["VS"] = min(adjusted["VS"] + 10, 95)
    
    # 确保分数在合理范围
    for dim in adjusted:
        adjusted[dim] = max(10, min(adjusted[dim], 90))
    
    return adjusted


def generate_quality_report(quality: QualityMetrics) -> str:
    """生成质量报告"""
    
    report = []
    report.append("📊 质量指标分析：")
    report.append(f"  • 记忆使用率: {quality.memory_usage_rate*100:.0f}%")
    report.append(f"  • 记忆内容质量: {quality.memory_content_quality*100:.0f}%")
    report.append(f"  • Skills有效性: {quality.effective_skills_ratio*100:.0f}%")
    report.append(f"  • Skills多样性: {quality.skill_diversity*100:.0f}%")
    report.append(f"  • 成长记录频率: {quality.growth_record_frequency*100:.0f}%")
    report.append(f"  • 错误改进率: {quality.error_learning_rate*100:.0f}%")
    report.append(f"  • 进化产出: {quality.evolution_output_count}个")
    report.append(f"  • 安全部件: {'✅ 启用' if quality.safety_active else '❌ 未启用'}")
    report.append(f"  • 反馈闭环: {'✅ 工作' if quality.feedback_loop_active else '❌ 未建立'}")
    
    return "\n".join(report)


# ============================================================
# 单元测试
# ============================================================

if __name__ == "__main__":
    # 测试当前workspace
    workspace = os.getcwd()
    
    print("=== 质量评估测试 ===\n")
    
    # 记忆质量
    memory_dir = os.path.join(workspace, "memory")
    usage, quality = analyze_memory_quality(memory_dir)
    print(f"记忆系统：使用率 {usage*100:.0f}%, 质量 {quality*100:.0f}%")
    
    # Skills有效性
    skills_dir = os.path.join(workspace, "skills")
    eff_ratio, diversity = analyze_skills_effectiveness(skills_dir)
    print(f"Skills：有效性 {eff_ratio*100:.0f}%, 多样性 {diversity*100:.0f}%")
    
    # 成长质量
    rec_freq, err_rate, evo_count = analyze_growth_quality(workspace)
    print(f"成长：记录频率 {rec_freq*100:.0f}%, 错误改进 {err_rate*100:.0f}%, 进化产出 {evo_count}个")
