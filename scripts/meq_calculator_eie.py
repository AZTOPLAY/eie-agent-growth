#!/usr/bin/env python3
"""
EIE Agent MEQ 计算器 v4.0 - EIE 理论版

核心改进：
1. E-I-E 链条效率作为核心评估维度
2. MS 是链条的结果，不是原因
3. 短板惩罚机制（低于平均70%惩罚）
4. E→I→E 正向反馈循环

EIE 理论核心：
- E（Energy/能量）：系统获取资源的能力
- I（Information/信息）：系统感知和处理信息的能力
- E（Evolution/进化）：系统自我改进的能力
- MS（Decision/决策）：以上三者的结果

公式：
MEQ = E基础 × 链条效率 + MS加成 × 链条效率 + VS贡献 × √链条效率
"""

from typing import Dict, Tuple, Optional, List


# ============================================================
# EIE 理论核心常量
# ============================================================

# EIE 链条权重
EIE_WEIGHTS = {
    "ES": 0.35,   # 能量获取（提升）
    "IS": 0.35,   # 信息处理（核心）
    "CE": 0.30,   # 进化能力（结果）
}

# VL 等级阈值（严格模式）
VL_THRESHOLDS_EIE = [
    (0, 15, "VL0", "静态系统"),
    (15, 30, "VL1", "规则系统"),
    (30, 45, "VL2", "交互系统"),
    (45, 60, "VL3", "智能系统"),
    (60, 75, "VL4", "自主系统"),
    (75, 100, "VL5", "元演化体"),
]

# 短板惩罚阈值
SHORTAGE_PENALTY_THRESHOLD = 0.70  # 低于平均的 70% 时惩罚
SHORTAGE_PENALTY_RATIO = 0.25      # 惩罚系数


# ============================================================
# EIE 理论核心计算
# ============================================================

def calculate_eie_chain_efficiency(es: int, is_val: int, ce: int) -> float:
    """
    计算 E-I-E 链条效率
    
    核心公式：使用几何平均，而非算术平均
    - 几何平均更能体现"短板效应"
    - 三者缺一不可
    
    Args:
        es: 环境适应度（能量获取）
        is_val: 感知深度（信息处理）
        ce: 成长速度（进化能力）
    
    Returns:
        链条效率（0-1）
    """
    # 几何平均
    geometric_mean = (es * is_val * ce) ** (1/3)
    
    # 归一化到 0-1
    efficiency = geometric_mean / 100
    
    return efficiency


def calculate_shortage_penalty(
    dimensions: List[int],
    weights: Dict[str, float]
) -> float:
    """
    计算短板惩罚
    
    如果最低维度远低于平均值，施加惩罚
    体现"木桶原理"：系统能力取决于最短板
    
    Args:
        dimensions: [ES, IS, MS, VS, CE]
        weights: 各维度权重
    
    Returns:
        惩罚分数（负数）
    """
    # 计算加权平均
    weighted_sum = sum(d * w for d, w in zip(dimensions, weights.values()))
    total_weight = sum(weights.values())
    weighted_avg = weighted_sum / total_weight
    
    min_dim = min(dimensions)
    
    # 检查是否需要惩罚
    if min_dim < weighted_avg * SHORTAGE_PENALTY_THRESHOLD:
        # 计算惩罚
        shortage_ratio = (weighted_avg - min_dim) / weighted_avg
        penalty = weighted_sum * shortage_ratio * SHORTAGE_PENALTY_RATIO
        return -penalty
    
    return 0


def calculate_meq_eie(
    es: int,
    is_val: int,
    ms: int,
    vs: int,
    ce: int
) -> Dict:
    """
    EIE 理论计算 MEQ
    
    核心洞察：
    1. MS 是 E-I-E 链条的结果，不是原因
    2. 只有链条健康时，MS 才有价值
    3. 短板会严重影响系统能力
    
    公式：
    MEQ = E基础 × 链条效率 + MS加成 × 链条效率 + VS贡献 × √链条效率
    
    Args:
        es: 环境适应度（能量获取）
        is_val: 感知深度（信息处理）
        ms: 决策质量（链条结果）
        vs: 对齐强度（安全保障）
        ce: 成长速度（进化能力）
    
    Returns:
        包含 MEQ、链条效率、惩罚等详细信息的字典
    """
    dimensions = [es, is_val, ms, vs, ce]
    eie_dims = [es, is_val, ce]  # E-I-E 链条维度
    
    # 1. 计算 E-I-E 链条效率
    chain_efficiency = calculate_eie_chain_efficiency(es, is_val, ce)
    
    # 2. 计算短板惩罚
    weights = {"ES": 0.25, "IS": 0.15, "MS": 0.20, "VS": 0.15, "CE": 0.25}
    shortage_penalty = calculate_shortage_penalty(dimensions, weights)
    
    # 3. 计算 E-I-E 基础分
    eie_base = (
        es * EIE_WEIGHTS["ES"] +
        is_val * EIE_WEIGHTS["IS"] +
        ce * EIE_WEIGHTS["CE"]
    )
    
    # 4. 计算 MS 加成（受链条效率影响）
    ms_contribution = ms * 0.20 * chain_efficiency
    
    # 5. 计算 VS 贡献（受链条效率平方根影响）
    vs_contribution = vs * 0.15 * (chain_efficiency ** 0.5)
    
    # 6. 计算 MEQ
    meq = eie_base + ms_contribution + vs_contribution + shortage_penalty
    
    # 7. 限制范围
    meq = max(0, min(100, meq))
    
    return {
        "meq": round(meq, 1),
        "chain_efficiency": round(chain_efficiency * 100, 1),
        "eie_base": round(eie_base, 1),
        "ms_contribution": round(ms_contribution, 1),
        "vs_contribution": round(vs_contribution, 1),
        "shortage_penalty": round(shortage_penalty, 1),
        "dimensions": {
            "ES": es,
            "IS": is_val,
            "MS": ms,
            "VS": vs,
            "CE": ce,
        },
        "warnings": _get_warnings(es, is_val, ms, vs, ce, chain_efficiency),
    }


def _get_warnings(
    es: int,
    is_val: int,
    ms: int,
    vs: int,
    ce: int,
    chain_efficiency: float
) -> List[str]:
    """获取警告信息"""
    warnings = []
    
    # 检查各维度是否低于阈值
    if es < 40:
        warnings.append(f"ES({es}) ⚠️ 环境适应不足，建议提升至40+")
    if is_val < 40:
        warnings.append(f"IS({is_val}) ⚠️ 信息处理薄弱，建议提升至40+")
    if vs < 50:
        warnings.append(f"VS({vs}) ⚠️ 价值对齐不足，建议提升至50+")
    
    # 检查链条效率
    if chain_efficiency < 0.4:
        warnings.append(f"E-I-E链条效率({chain_efficiency*100:.0f}%) ⚠️ 过低，MS难以发挥作用")
    
    # 检查高 MS 低链条
    if ms > 60 and chain_efficiency < 0.5:
        warnings.append("⚠️ MS高分但链条效率低，决策能力被严重削弱")
    
    return warnings


def get_vl_level(meq: float) -> Tuple[str, str]:
    """根据 MEQ 获取 VL 等级"""
    for low, high, vl, name in VL_THRESHOLDS_EIE:
        if low <= meq < high:
            return vl, name
    if meq >= 75:
        return "VL5", "元演化体"
    return "VL0", "静态系统"


def format_result_eie(result: Dict) -> str:
    """格式化 EIE 理论评估结果"""
    meq = result["meq"]
    vl, stage = get_vl_level(meq)
    
    dim = result["dimensions"]
    
    def bar(value: int, width: int = 10) -> str:
        filled = int(value / 10)
        return "█" * filled + "░" * (width - filled)
    
    output = f"""
╔══════════════════════════════════════════════════════════╗
║          🎯 EIE 进化评估结果（EIE 理论 v4.0）          ║
╠══════════════════════════════════════════════════════════╣
║                                                            ║
║   ┌──────────────────────────────────────────────────┐     ║
║   │                                                   │     ║
║   │                   MEQ = {meq:>5.1f}                 │     ║
║   │                   {vl} · {stage:<12s}            │     ║
║   │                                                   │     ║
║   └──────────────────────────────────────────────────┘     ║
║                                                            ║
║   🔗 E-I-E 链条效率：{result['chain_efficiency']:>5.1f}%                     ║
╠══════════════════════════════════════════════════════════╣
║                                                            ║
║   📊 五维度得分：                                          ║
║   ES(能量获取) {bar(dim['ES'])} {dim['ES']:>3d}                    ║
║   IS(信息处理) {bar(dim['IS'])} {dim['IS']:>3d}                    ║
║   MS(决策能力) {bar(dim['MS'])} {dim['MS']:>3d}                    ║
║   VS(价值对齐) {bar(dim['VS'])} {dim['VS']:>3d}                    ║
║   CE(进化能力) {bar(dim['CE'])} {dim['CE']:>3d}                    ║
║                                                            ║"""
    
    if result["shortage_penalty"] != 0:
        output += f"""
║   ⚠️ 短板惩罚：{result['shortage_penalty']:>5.1f}分                               ║"""
    
    if result["warnings"]:
        output += """
║                                                            ║
║   ⚠️ 警告：                                               ║"""
        for warning in result["warnings"]:
            output += f"""
║     • {warning:<47s} ║"""
    
    output += f"""
║                                                            ║
║   💡 EIE 理论建议：                                       ║
║     提升 E-I-E 链条效率，MS 才能真正发挥作用                ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
"""
    return output


# ============================================================
# 示例计算
# ============================================================

if __name__ == "__main__":
    # OpenClaw 真实评估
    print("="*60)
    print("OpenClaw EIE 理论评估")
    print("="*60)
    
    es = 46
    is_val = 30
    ms = 73
    vs = 42
    ce = 53
    
    result = calculate_meq_eie(es, is_val, ms, vs, ce)
    
    print(f"\n输入维度：ES={es}, IS={is_val}, MS={ms}, VS={vs}, CE={ce}")
    print(f"\nE-I-E 链条效率：{result['chain_efficiency']}%")
    print(f"E-I-E 基础分：{result['eie_base']}")
    print(f"MS 贡献（被打折）：{result['ms_contribution']}")
    print(f"VS 贡献：{result['vs_contribution']}")
    print(f"短板惩罚：{result['shortage_penalty']}")
    print(f"\n最终 MEQ：{result['meq']}")
    
    vl, stage = get_vl_level(result['meq'])
    print(f"VL 等级：{vl} · {stage}")
    
    print(format_result_eie(result))
