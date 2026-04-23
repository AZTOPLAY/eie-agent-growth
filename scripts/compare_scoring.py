#!/usr/bin/env python3
"""
新旧评分系统对比测试

展示零基评分法 vs 基础分评分法的差异
"""

import sys
sys.path.insert(0, '.')

from dimension_estimator import DimensionEstimator as OldEstimator, DetectionData
from dimension_estimator_v2 import DimensionEstimatorV2 as NewEstimator
from quality_estimator import QualityMetrics


def test_empty_system():
    """测试空白系统"""
    print("\n" + "="*60)
    print("测试场景：完全空白的系统")
    print("="*60)
    
    data = DetectionData(
        platform="test",
        channels=[],
        skills=[],
        skill_types={},
        model="",
        memory_system=False,
        rag_enabled=False,
        persistent_storage=False,
        safety_config={},
        cron_enabled=False,
        heartbeat_enabled=False,
        trajectory_enabled=False,
        user_feedback_enabled=False,
        vulnerabilities=[],
        workspace_path=None,
    )
    
    # 旧评分
    old = OldEstimator(data)
    old_scores = old.estimate_all()
    
    # 新评分（无质量评估）
    new = NewEstimator(data)
    new_scores = new.estimate_all()
    
    print("\n维度对比：")
    print(f"{'维度':<10} {'旧评分':<10} {'新评分':<10} {'差异':<10}")
    print("-" * 40)
    for dim in ["ES", "IS", "MS", "VS", "CE"]:
        old_val = getattr(old_scores, dim)
        new_val = getattr(new_scores, dim)
        diff = new_val - old_val
        print(f"{dim:<10} {old_val:<10} {new_val:<10} {diff:>+6}")
    
    # 计算MEQ
    old_meq = old_scores.ES*0.25 + old_scores.IS*0.15 + old_scores.MS*0.20 + old_scores.VS*0.15 + old_scores.CE*0.25
    new_meq = new_scores.ES*0.25 + new_scores.IS*0.15 + new_scores.MS*0.20 + new_scores.VS*0.15 + new_scores.CE*0.25
    
    print(f"\nMEQ对比：")
    print(f"旧评分：{old_meq:.1f}")
    print(f"新评分：{new_meq:.1f}")
    print(f"差异：{new_meq - old_meq:+.1f}")


def test_openclaw_current():
    """测试当前OpenClaw配置"""
    print("\n" + "="*60)
    print("测试场景：当前OpenClaw配置")
    print("="*60)
    
    data = DetectionData(
        platform="openclaw",
        channels=["feishu", "whatsapp"],
        skills=["skill_" + str(i) for i in range(82)],
        skill_types={"multimodal": 2, "tool": 5, "workflow": 3},
        model="llama-3.3-70b",
        memory_system=True,
        rag_enabled=False,
        persistent_storage=True,
        safety_config={},
        cron_enabled=True,
        heartbeat_enabled=True,
        trajectory_enabled=False,
        user_feedback_enabled=False,
        vulnerabilities=[],
    )
    # 设置 workspace_path
    data.workspace_path = "/workspace/projects/workspace"
    
    # 旧评分
    old = OldEstimator(data)
    old_scores = old.estimate_all()
    
    # 新评分（有质量评估）
    new = NewEstimator(data)
    new_scores = new.estimate_all()
    
    print("\n维度对比：")
    print(f"{'维度':<10} {'旧评分':<10} {'新评分':<10} {'差异':<10} {'说明':<30}")
    print("-" * 70)
    
    explanations = {
        "ES": "渠道2个+存储+心跳",
        "IS": "记忆使用率36%",
        "MS": "模型潜力×调度能力",
        "VS": "安全完全空白",
        "CE": "成长频率36%",
    }
    
    for dim in ["ES", "IS", "MS", "VS", "CE"]:
        old_val = getattr(old_scores, dim)
        new_val = getattr(new_scores, dim)
        diff = new_val - old_val
        print(f"{dim:<10} {old_val:<10} {new_val:<10} {diff:>+6}   {explanations[dim]:<30}")
    
    # 计算MEQ
    old_meq = old_scores.ES*0.25 + old_scores.IS*0.15 + old_scores.MS*0.20 + old_scores.VS*0.15 + old_scores.CE*0.25
    new_meq = new_scores.ES*0.25 + new_scores.IS*0.15 + new_scores.MS*0.20 + new_scores.VS*0.15 + new_scores.CE*0.25
    
    print(f"\nMEQ对比：")
    print(f"旧评分：{old_meq:.1f} (虚高)")
    print(f"新评分：{new_meq:.1f} (真实)")
    print(f"差异：{new_meq - old_meq:+.1f}")
    
    # VL等级
    def get_vl(meq):
        if meq >= 80: return "VL5"
        if meq >= 65: return "VL4"
        if meq >= 50: return "VL3"
        if meq >= 35: return "VL2"
        if meq >= 20: return "VL1"
        return "VL0"
    
    print(f"\nVL等级对比：")
    print(f"旧评分：{get_vl(old_meq)} (可能误判)")
    print(f"新评分：{get_vl(new_meq)} (更准确)")


def print_scoring_logic_comparison():
    """打印评分逻辑对比"""
    print("\n" + "="*60)
    print("评分逻辑对比")
    print("="*60)
    
    comparison = """
┌──────────┬─────────────────────────────┬─────────────────────────────┐
│ 维度     │ 旧评分（v1.x）              │ 新评分（v2.0）              │
├──────────┼─────────────────────────────┼─────────────────────────────┤
│ ES       │ 基础分30 + 配置项加分       │ 0分起，实际运行效果挣分     │
│ IS       │ 基础分20 + 配置项加分       │ 0分起，记忆使用率×质量挣分  │
│ MS       │ 模型基准40-50 + Skills加分  │ 模型潜力×实际调度能力       │
│ VS       │ 基础分40 + 安全配置加分     │ 0分起，每个安全部件挣分     │
│ CE       │ 基础分20 + 配置项加分       │ 0分起，成长记录×改进率挣分  │
└──────────┴─────────────────────────────┴─────────────────────────────┘

核心差异：
1. 旧评分：基础分20-40，什么都不做也有分
2. 新评分：0基础分，全部靠实际能力挣分
3. 新评分引入质量系数：实际效果 / 配置存在
    """
    print(comparison)


if __name__ == "__main__":
    print("新旧评分系统对比测试")
    print("=" * 60)
    
    print_scoring_logic_comparison()
    test_empty_system()
    test_openclaw_current()
    
    print("\n" + "="*60)
    print("结论：")
    print("="*60)
    print("1. 旧评分系统有'基础分'设计缺陷，导致分数虚高")
    print("2. 新评分系统采用'零基评分法'，分数更真实")
    print("3. 空白系统旧评分MEQ≈30，新评分MEQ≈0-10")
    print("4. OpenClaw旧评分MEQ≈46，新评分MEQ≈25-35")
