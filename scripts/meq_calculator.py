#!/usr/bin/env python3
"""
EIE Agent MEQ 计算器

EIE = Energy-Information-Evolution（能量-信息-进化理论体系）

用法:
    python meq_calculator.py                    # 交互式输入
    python meq_calculator.py --es 60 --is 70 ... # 命令行参数
    python meq_calculator.py --system "RAG Agent"  # 系统类型自动估算
"""

import argparse
import sys
from typing import Optional, Dict, List, Tuple

# ============================================================
# 系统类型默认维度值
# ============================================================

SYSTEM_DEFAULTS: Dict[str, Dict[str, int]] = {
    "简单聊天机器人": {"ES": 25, "IS": 30, "MS": 15, "VS": 20, "CE": 10},
    "规则型客服": {"ES": 35, "IS": 40, "MS": 25, "VS": 30, "CE": 20},
    "LLM问答": {"ES": 45, "IS": 55, "MS": 50, "VS": 45, "CE": 35},
    "RAG系统": {"ES": 50, "IS": 60, "MS": 55, "VS": 50, "CE": 45},
    "RAG Agent": {"ES": 50, "IS": 60, "MS": 55, "VS": 50, "CE": 45},
    "工具型Agent": {"ES": 55, "IS": 60, "MS": 60, "VS": 55, "CE": 50},
    "多模态Agent": {"ES": 55, "IS": 70, "MS": 65, "VS": 60, "CE": 55},
    "自进化Agent": {"ES": 70, "IS": 75, "MS": 75, "VS": 80, "CE": 75},
    "Agent": {"ES": 55, "IS": 65, "MS": 60, "VS": 60, "CE": 55},
}

# ============================================================
# 权重配置
# ============================================================

WEIGHTS = {
    "ES": 0.25,
    "IS": 0.15,
    "MS": 0.20,
    "VS": 0.15,
    "CE": 0.25,
}

# ============================================================
# VL 等级定义
# ============================================================

VL_THRESHOLDS = [
    (0, 20, "VL0", "静态系统"),
    (20, 35, "VL1", "规则系统"),
    (35, 50, "VL2", "交互系统"),
    (50, 65, "VL3", "智能系统"),
    (65, 80, "VL4", "自主系统"),
    (80, 100, "VL5", "元演化体"),
]

# ============================================================
# 计算函数
# ============================================================

def calculate_meq(es: int, is_val: int, ms: int, vs: int, ce: int) -> float:
    """
    计算 MEQ 分数（线性公式）
    
    MEQ = ES×0.25 + IS×0.15 + MS×0.20 + VS×0.15 + CE×0.25
    """
    meq = (
        es * WEIGHTS["ES"] +
        is_val * WEIGHTS["IS"] +
        ms * WEIGHTS["MS"] +
        vs * WEIGHTS["VS"] +
        ce * WEIGHTS["CE"]
    )
    return round(meq, 1)


def calculate_meq_with_coupling(es: int, is_val: int, ms: int, vs: int, ce: int) -> float:
    """
    计算 MEQ 分数（含耦合项）
    
    MEQ_最终 = min(100, MEQ_线性 + 0.15 × [ (ES×MS)/10000 + (MS×CE)/10000 - 0.5 ])
    """
    meq_linear = calculate_meq(es, is_val, ms, vs, ce)
    coupling = 0.15 * ((es * ms) / 10000 + (ms * ce) / 10000 - 0.5)
    meq_final = min(100, meq_linear + coupling)
    return round(meq_final, 1)


def get_vl_level(meq: float) -> Tuple[str, str]:
    """
    根据 MEQ 获取 VL 等级和阶段名称
    """
    for low, high, vl, name in VL_THRESHOLDS:
        if low <= meq < high:
            return vl, name
    if meq >= 80:
        return "VL5", "元演化体"
    return "VL0", "静态系统"


def check_vl4_vl5_conditions(meq: float, ms: int, vs: int) -> Tuple[str, Optional[str]]:
    """
    检查 VL4/VL5 的特殊条件
    
    VL4: MEQ ≥ 65 且 MS ≥ 70 且 VS ≥ 80
    VL5: MEQ ≥ 80 且 MS ≥ 70 且 VS ≥ 80
    """
    if meq >= 80 and ms >= 70 and vs >= 80:
        return "VL5", "元演化体"
    elif meq >= 65 and ms >= 70 and vs >= 80:
        return "VL4", "自主系统"
    return get_vl_level(meq)


def get_dimension_warning(es: int, is_val: int, ms: int, vs: int, ce: int) -> List[str]:
    """
    获取需要关注的维度短板
    """
    warnings = []
    thresholds = {"ES": 40, "IS": 45, "MS": 50, "VS": 60, "CE": 45}
    names = {"ES": "环境适应", "IS": "感知深度", "MS": "决策质量", "VS": "对齐强度", "CE": "成长速度"}
    
    values = {"ES": es, "IS": is_val, "MS": ms, "VS": vs, "CE": ce}
    
    for dim, threshold in thresholds.items():
        if values[dim] < threshold:
            warnings.append(f"{dim}({names[dim]}): {values[dim]} ⚠️ 建议提升至{threshold}+")
    
    return warnings


def get_evolution_suggestion(meq: float, ms: int, vs: int) -> str:
    """
    根据当前状态给出进化建议
    """
    current_vl = check_vl4_vl5_conditions(meq, ms, vs)[0]
    
    suggestions = {
        "VL0": "建议引入状态管理和上下文处理能力",
        "VL1": "建议引入LLM能力替代纯规则引擎",
        "VL2": "建议增加外部知识库或RAG能力",
        "VL3": f"当前VL3，建议提升MS≥70、VS≥80以解锁VL4",
        "VL4": "已具备主动进化能力，建议保持CE投入",
        "VL5": "已达到元演化水平，建议探索新领域泛化"
    }
    
    return suggestions.get(current_vl, "持续优化各维度能力")


def get_percentile(meq: float) -> str:
    """
    估算超越多少百分位的系统
    """
    percentiles = [
        (85, "前 5%", "顶尖"),
        (75, "前 15%", "优秀"),
        (65, "前 25%", "较好"),
        (55, "前 40%", "中等偏上"),
        (45, "前 55%", "中等"),
        (35, "前 70%", "中等偏下"),
        (20, "后 30%", "基础"),
    ]
    
    for threshold, percentile, desc in percentiles:
        if meq >= threshold:
            return f"{percentile}的系统 ({desc})"
    return "后 50% 的基础系统"


# ============================================================
# 输出格式化
# ============================================================

def format_result(es: int, is_val: int, ms: int, vs: int, ce: int, 
                  meq: Optional[float] = None, with_coupling: bool = False) -> str:
    """
    格式化输出评估结果
    """
    if meq is None:
        if with_coupling:
            meq = calculate_meq_with_coupling(es, is_val, ms, vs, ce)
        else:
            meq = calculate_meq(es, is_val, ms, vs, ce)
    
    vl, stage_name = check_vl4_vl5_conditions(meq, ms, vs)
    warnings = get_dimension_warning(es, is_val, ms, vs, ce)
    suggestion = get_evolution_suggestion(meq, ms, vs)
    percentile = get_percentile(meq)
    
    # 生成维度条形图
    def bar(value: int, width: int = 10) -> str:
        filled = int(value / 10)
        return "█" * filled + "░" * (width - filled)
    
    output = f"""
╔══════════════════════════════════════════════════════════╗
║                    🎯 EIE 进化评估结果                      ║
╠══════════════════════════════════════════════════════════╣
║                                                            ║
║   ┌──────────────────────────────────────────────────┐     ║
║   │                                                   │     ║
║   │                   MEQ = {meq:>5.1f}                 │     ║
║   │                   {vl} · {stage_name:<12s}        │     ║
║   │                                                   │     ║
║   └──────────────────────────────────────────────────┘     ║
║                                                            ║
║   📊 五维度得分：                                          ║
║   ES(环境适应) {bar(es)} {es:>3d}                    ║
║   IS(感知深度) {bar(is_val)} {is_val:>3d}                    ║
║   MS(决策质量) {bar(ms)} {ms:>3d}                    ║
║   VS(对齐强度) {bar(vs)} {vs:>3d}                    ║
║   CE(成长速度) {bar(ce)} {ce:>3d}                    ║
║                                                            ║"""
    
    if warnings:
        output += "\n║   ⚠️  需要关注：                                       ║"
        for warning in warnings:
            output += f"\n║     • {warning:<47s} ║"
    
    output += f"""
║                                                            ║
║   💡 进化建议：                                             ║
║     {suggestion:<46s} ║
║                                                            ║
║   📈 水平定位：                                             ║
║     超越 {percentile}                       ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
"""
    return output


def get_system_defaults(system_desc: str) -> Dict[str, int]:
    """
    【v3.3 修复】根据系统描述获取默认维度值
    
    旧函数名：parse_system_type
    新函数名：get_system_defaults（语义更准确）
    
    Args:
        system_desc: 系统描述文本
        
    Returns:
        默认维度值字典
    """
    system_desc_lower = system_desc.lower()
    
    # 精确匹配
    for sys_type, defaults in SYSTEM_DEFAULTS.items():
        if sys_type.lower() in system_desc_lower or system_desc_lower in sys_type.lower():
            return defaults.copy()
    
    # 模糊匹配
    keywords = {
        "RAG": {"ES": 50, "IS": 60, "MS": 55, "VS": 50, "CE": 45},
        "agent": {"ES": 55, "IS": 65, "MS": 60, "VS": 60, "CE": 55},
        "多模态": {"ES": 55, "IS": 70, "MS": 65, "VS": 60, "CE": 55},
        "自进化": {"ES": 70, "IS": 75, "MS": 75, "VS": 80, "CE": 75},
        "客服": {"ES": 35, "IS": 40, "MS": 25, "VS": 30, "CE": 20},
        "聊天": {"ES": 25, "IS": 30, "MS": 15, "VS": 20, "CE": 10},
        "LLM": {"ES": 45, "IS": 55, "MS": 50, "VS": 45, "CE": 35},
    }
    
    for keyword, defaults in keywords.items():
        if keyword in system_desc_lower:
            return defaults.copy()
    
    # 默认返回中等水平Agent
    return {"ES": 50, "IS": 55, "MS": 50, "VS": 50, "CE": 45}


# 【v3.3】向后兼容：保留旧函数名作为别名
def parse_system_type(system_desc: str) -> Dict[str, int]:
    """
    【v3.3 向后兼容】旧函数名别名
    
    已弃用：请使用 get_system_defaults()
    保留原因：向后兼容
    """
    return get_system_defaults(system_desc)


# ============================================================
# 交互式输入
# ============================================================

def interactive_input() -> Dict[str, int]:
    """
    交互式输入五维度值
    """
    print("\n" + "="*50)
    print("EIE Agent MEQ 计算器 - 交互式输入")
    print("="*50)
    print("\n请输入五维度分数（0-100）：\n")
    
    dimensions = {}
    prompts = {
        "ES": "ES (环境生存能力 - '活下去的能力'): ",
        "IS": "IS (信息处理能力 - '看懂世界的能力'): ",
        "MS": "MS (模型构建能力 - '做决策的能力'): ",
        "VS": "VS (价值对齐能力 - '守原则的能力'): ",
        "CE": "CE (持续进化能力 - '变强的能力'): ",
    }
    
    for dim, prompt in prompts.items():
        while True:
            try:
                value = int(input(prompt))
                if 0 <= value <= 100:
                    dimensions[dim] = value
                    break
                else:
                    print("⚠️  请输入 0-100 之间的整数")
            except ValueError:
                print("⚠️  请输入有效的整数")
    
    return dimensions


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="EIE Agent MEQ 计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python meq_calculator.py                                    # 交互式输入
  python meq_calculator.py --system "RAG Agent"               # 自动估算
  python meq_calculator.py --es 60 --is 70 --ms 65 --vs 70 --ce 70  # 手动输入
        """
    )
    
    parser.add_argument("--system", "-s", type=str, help="系统类型描述")
    parser.add_argument("--es", type=int, help="环境生存能力 (0-100)")
    parser.add_argument("--is", "--IS", dest="is_val", type=int, help="信息处理能力 (0-100)")
    parser.add_argument("--ms", "--MS", dest="ms", type=int, help="模型构建能力 (0-100)")
    parser.add_argument("--vs", "--VS", dest="vs", type=int, help="价值对齐能力 (0-100)")
    parser.add_argument("--ce", "--CE", dest="ce", type=int, help="持续进化能力 (0-100)")
    parser.add_argument("--coupling", "-c", action="store_true", help="使用含耦合项的计算公式")
    
    args = parser.parse_args()
    
    # 根据参数决定输入方式
    if args.system:
        # 系统类型自动估算
        dimensions = get_system_defaults(args.system)
        print(f"\n📋 检测到系统类型，自动估算维度：")
        for dim, value in dimensions.items():
            print(f"   {dim}: {value}")
        es = dimensions["ES"]
        is_val = dimensions["IS"]
        ms = dimensions["MS"]
        vs = dimensions["VS"]
        ce = dimensions["CE"]
    elif all([args.es, args.is_val, args.ms, args.vs, args.ce]):
        # 命令行参数
        es = args.es
        is_val = args.is_val
        ms = args.ms
        vs = args.vs
        ce = args.ce
    else:
        # 交互式输入
        dimensions = interactive_input()
        es = dimensions["ES"]
        is_val = dimensions["IS"]
        ms = dimensions["MS"]
        vs = dimensions["VS"]
        ce = dimensions["CE"]
    
    # 计算并输出
    meq = calculate_meq_with_coupling(es, is_val, ms, vs, ce) if args.coupling else None
    print(format_result(es, is_val, ms, vs, ce, meq, args.coupling))
    
    # 显示公式信息
    formula = "含耦合项" if args.coupling else "线性公式"
    print(f"📐 计算公式: MEQ ({formula})")
    print(f"   MEQ = ES×0.25 + IS×0.15 + MS×0.20 + VS×0.15 + CE×0.25\n")


if __name__ == "__main__":
    main()
