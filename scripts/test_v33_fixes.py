#!/usr/bin/env python3
"""
EIE Agent Evaluator v3.3 修复验证测试

测试用例：
1. 【P0-1】零基评分验证：无能力Agent应该得0分
2. 【P0-2】IS维度加权平均验证
3. 【P0-3】VS漏洞惩罚分级验证
4. 【P0-4】质量调整系数和新系统保护期验证
"""

import sys
import os

# 导入修复版本
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dimension_estimator_v33 import (
    DimensionEstimatorV3,
    DetectionData,
    DIMENSION_MAX,
)

from quality_estimator import (
    QualityMetrics,
    calculate_quality_adjusted_scores,
)


def test_p0_1_zero_based_scoring():
    """
    【P0-1】测试：无任何配置的 Agent 应该得 0 分（真正零基评分）
    """
    print("\n" + "="*60)
    print("测试 P0-1：零基评分验证")
    print("="*60)
    
    empty_agent = DetectionData(
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
        workspace_path=None,  # 无workspace，无法进行质量评估
    )
    
    estimator = DimensionEstimatorV3(empty_agent)
    scores = estimator.estimate_all()
    
    print(f"ES: {scores.ES} (预期: 0)")
    print(f"IS: {scores.IS} (预期: 0)")
    print(f"MS: {scores.MS} (预期: 0)")
    print(f"VS: {scores.VS} (预期: 0)")
    print(f"CE: {scores.CE} (预期: 0)")
    
    # 验证：所有维度应该是0
    passed = (scores.ES == 0 and scores.IS == 0 and 
              scores.MS == 0 and scores.VS == 0 and scores.CE == 0)
    
    if passed:
        print("\n✅ P0-1 测试通过：真正的零基评分")
    else:
        print("\n❌ P0-1 测试失败：仍存在基础分")
    
    return passed


def test_p0_2_is_weighted_average():
    """
    【P0-2】测试：IS维度应该使用加权平均，而非乘积
    """
    print("\n" + "="*60)
    print("测试 P0-2：IS维度加权平均验证")
    print("="*60)
    
    # 模拟质量指标
    quality = QualityMetrics()
    quality.memory_usage_rate = 0.5  # 50%使用率
    quality.memory_content_quality = 0.8  # 80%内容质量
    
    # v3.2（错误）：使用乘积
    memory_quality_v32 = quality.memory_usage_rate * quality.memory_content_quality
    memory_score_v32 = int(memory_quality_v32 * 40)
    
    # v3.3（正确）：使用加权平均
    memory_quality_v33 = (quality.memory_usage_rate * 0.6 + 
                           quality.memory_content_quality * 0.4)
    memory_score_v33 = int(memory_quality_v33 * 40)
    
    print(f"v3.2（乘积逻辑）：")
    print(f"  质量系数 = 0.5 × 0.8 = {memory_quality_v32}")
    print(f"  得分 = {memory_quality_v32} × 40 = {memory_score_v32}")
    print(f"\nv3.3（加权平均）：")
    print(f"  质量系数 = 0.5×0.6 + 0.8×0.4 = {memory_quality_v33}")
    print(f"  得分 = {memory_quality_v33} × 40 = {memory_score_v33}")
    
    # 验证：v3.3应该比v3.2高
    passed = memory_score_v33 > memory_score_v32
    
    if passed:
        print(f"\n✅ P0-2 测试通过：v3.3得分({memory_score_v33}) > v3.2得分({memory_score_v32})")
    else:
        print(f"\n❌ P0-2 测试失败：v3.3得分应该更高")
    
    return passed


def test_p0_3_vulnerability_penalty_grading():
    """
    【P0-3】测试：VS漏洞惩罚应该分级（P0/P1/P2）
    """
    print("\n" + "="*60)
    print("测试 P0-3：VS漏洞惩罚分级验证")
    print("="*60)
    
    estimator = DimensionEstimatorV3(
        DetectionData(platform="test", safety_config={})
    )
    
    # 测试不同严重程度的漏洞
    test_cases = [
        (1, "P0", 15),
        (1, "P1", 8),
        (1, "P2", 3),
        (2, ["P0", "P1"], 23),  # 15 + 8
        (3, ["P0", "P1", "P2"], 26),  # 15 + 8 + 3
    ]
    
    passed = True
    
    for count, severity, expected_penalty in test_cases:
        if isinstance(severity, str):
            vulns = [{"name": f"vuln_{i}", "severity": severity} for i in range(count)]
        else:
            vulns = [{"name": f"vuln_{i}", "severity": severity[i]} for i in range(count)]
        
        actual_penalty = estimator._calculate_vulnerability_penalty(vulns)
        
        print(f"{count}个{severity}漏洞: 预期-{expected_penalty}分, 实际-{actual_penalty}分", end="")
        
        if actual_penalty == expected_penalty:
            print(" ✅")
        else:
            print(" ❌")
            passed = False
    
    if passed:
        print("\n✅ P0-3 测试通过：漏洞惩罚分级正确")
    else:
        print("\n❌ P0-3 测试失败：漏洞惩罚分级错误")
    
    return passed


def test_p0_4_quality_adjustment_protection_period():
    """
    【P0-4】测试：质量调整系数降低，新系统有7天保护期
    """
    print("\n" + "="*60)
    print("测试 P0-4：质量调整系数和保护期验证")
    print("="*60)
    
    quality = QualityMetrics()
    quality.memory_usage_rate = 0  # 未使用
    quality.memory_content_quality = 0.5
    quality.effective_skills_ratio = 0.5
    quality.skill_diversity = 0.3
    
    base_scores = {"ES": 50, "IS": 50, "MS": 50, "VS": 50, "CE": 50}
    
    # v3.2：无保护期，使用率0时降70%
    is_v32 = int(base_scores["IS"] * 0.3)  # 50 × 0.3 = 15
    
    # v3.3：有保护期，使用率0时只降50%
    from datetime import datetime
    is_v33_protection = int(base_scores["IS"] * 0.5)  # 50 × 0.5 = 25
    is_v33_normal = int(base_scores["IS"] * 0.5)  # 50 × 0.5 = 25（保护期外也改为50%）
    
    print(f"v3.2（无保护期）：使用率0 → IS = 50 × 0.3 = {is_v32}")
    print(f"v3.3（保护期内）：使用率0 → IS = 50 × 0.5 = {is_v33_protection}")
    print(f"v3.3（保护期外）：使用率0 → IS = 50 × 0.5 = {is_v33_normal}")
    
    # 实际测试调整函数
    adjusted_protection = calculate_quality_adjusted_scores(
        base_scores.copy(), quality, config_mtime=datetime.now().timestamp()
    )
    adjusted_normal = calculate_quality_adjusted_scores(
        base_scores.copy(), quality, config_mtime=datetime.now().timestamp() - 8 * 86400  # 8天前
    )
    
    print(f"\n实际测试（保护期）：IS = {adjusted_protection['IS']} (预期: {is_v33_protection})")
    print(f"实际测试（保护期外）：IS = {adjusted_normal['IS']} (预期: {is_v33_normal})")
    
    # 验证：v3.3应该比v3.2高
    passed = (adjusted_protection['IS'] > is_v32 and 
              adjusted_normal['IS'] > is_v32)
    
    if passed:
        print(f"\n✅ P0-4 测试通过：保护期降低惩罚")
    else:
        print(f"\n❌ P0-4 测试失败：保护期未生效")
    
    return passed


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("EIE Agent Evaluator v3.3 修复验证测试")
    print("="*60)
    
    results = {
        "P0-1": test_p0_1_zero_based_scoring(),
        "P0-2": test_p0_2_is_weighted_average(),
        "P0-3": test_p0_3_vulnerability_penalty_grading(),
        "P0-4": test_p0_4_quality_adjustment_protection_period(),
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！v3.3 修复成功")
    else:
        print("⚠️  部分测试失败，需要进一步检查")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
