#!/usr/bin/env python3
"""
EIE Agent 评估器 v4.1 - 交互式评估入口 + 任务助手

支持三种评估模式：
1. 交互式输入：通过问答获取Agent特征
2. 命令行参数：直接指定维度分数
3. 系统类型估算：根据系统类型自动估算

【v4.1 新增】任务助手模式：
- 输出任务清单（而不只是 MEQ）
- 评估任务完成度
- 提供可执行的具体任务

用法:
    python evaluator.py --interactive              # 交互式输入
    python evaluator.py --es 60 --is 70 ...        # 直接指定
    python evaluator.py --system "RAG Agent"        # 按类型估算
    python evaluator.py --batch systems.json       # 批量评估
    
    【v4.1 新增】
    python evaluator.py --with-tasks               # 启用任务助手
    python evaluator.py --es 60 --is 70 --ms 65 --vs 55 --ce 45 --with-tasks
"""

import argparse
import json
import sys
from typing import Dict, List, Optional, Tuple

# 【v4.1】导入任务助手
try:
    from eie_task_assistant import EIETaskAssistant
    TASK_ASSISTANT_AVAILABLE = True
except ImportError:
    TASK_ASSISTANT_AVAILABLE = False

# 导入MEQ计算器
try:
    from meq_calculator import (
        calculate_meq,
        calculate_meq_with_coupling,
        check_vl4_vl5_conditions,
        format_result,
        get_vl_level,
        get_dimension_warning,
        get_evolution_suggestion,
        get_percentile,
        SYSTEM_DEFAULTS,
    )
except ImportError:
    from .meq_calculator import (
        calculate_meq,
        calculate_meq_with_coupling,
        check_vl4_vl5_conditions,
        format_result,
        get_vl_level,
        get_dimension_warning,
        get_evolution_suggestion,
        get_percentile,
        SYSTEM_DEFAULTS,
    )

# 导入维度估算器
try:
    from dimension_estimator import (
        estimate_from_description,
        DimensionEstimator,
    )
except ImportError:
    try:
        from .dimension_estimator import (
            estimate_from_description,
            DimensionEstimator,
        )
    except ImportError:
        dimension_estimator_available = False
    else:
        dimension_estimator_available = True
else:
    dimension_estimator_available = True


# ============================================================
# 系统类型默认值
# ============================================================

SYSTEM_DEFAULTS = {
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
# 关键词匹配规则
# ============================================================

KEYWORD_RULES = {
    # 知识库/检索相关 -> IS+, ES+
    "rag": {"IS": 15, "ES": 5},
    "知识库": {"IS": 15, "ES": 5},
    "检索": {"IS": 10, "ES": 3},
    "vector": {"IS": 12, "ES": 3},
    "embedding": {"IS": 12, "ES": 3},
    
    # 多模态相关 -> IS+, MS+
    "多模态": {"IS": 20, "MS": 5},
    "视觉": {"IS": 15, "MS": 5},
    "vision": {"IS": 15, "MS": 5},
    "image": {"IS": 15, "MS": 5},
    "ocr": {"IS": 10, "MS": 3},
    
    # 记忆/状态相关 -> ES+, IS+
    "记忆": {"ES": 10, "IS": 5},
    "memory": {"ES": 10, "IS": 5},
    "状态": {"ES": 8, "IS": 3},
    "context": {"ES": 5, "IS": 8},
    
    # 定时/心跳相关 -> CE+, ES+
    "定时": {"CE": 10, "ES": 5},
    "cron": {"CE": 10, "ES": 5},
    "心跳": {"CE": 8, "ES": 8},
    "heartbeat": {"CE": 8, "ES": 8},
    
    # 自我学习相关 -> CE++, MS+
    "学习": {"CE": 20, "MS": 10},
    "learn": {"CE": 20, "MS": 10},
    "进化": {"CE": 25, "MS": 10},
    "evolution": {"CE": 25, "MS": 10},
    "自我改进": {"CE": 30, "MS": 15},
    "self-improve": {"CE": 30, "MS": 15},
    
    # 价值观/对齐相关 -> VS++
    "价值观": {"VS": 15},
    "对齐": {"VS": 15},
    "安全": {"VS": 10},
    "safety": {"VS": 10},
    
    # 工具/API相关 -> MS+
    "工具": {"MS": 8},
    "tool": {"MS": 8},
    "api": {"MS": 5},
    "browser": {"MS": 5},
    
    # 工作流/编排相关 -> MS+
    "工作流": {"MS": 12},
    "workflow": {"MS": 12},
    "编排": {"MS": 10},
    "orchestrat": {"MS": 10},
    "agent": {"MS": 8},
    
    # 持久化/存储相关 -> ES+
    "存储": {"ES": 10},
    "storage": {"ES": 10},
    "database": {"ES": 8},
    "persist": {"ES": 8},
    
    # 轨迹/日志相关 -> CE+
    "轨迹": {"CE": 10},
    "trajectory": {"CE": 10},
    "日志": {"CE": 5},
    "log": {"CE": 5},
    
    # 反馈相关 -> VS+, CE+
    "反馈": {"VS": 8, "CE": 5},
    "feedback": {"VS": 8, "CE": 5},
}


# ============================================================
# 基础分配置
# ============================================================

BASE_SCORES = {
    "ES": 30,
    "IS": 20,
    "MS": 50,  # 需要模型名称来修正
    "VS": 40,
    "CE": 20,
}


# ============================================================
# 核心函数
# ============================================================

def parse_description(description: str) -> Dict[str, int]:
    """
    解析描述文本，提取Agent特征并估算维度分数
    
    Args:
        description: Agent描述文本
        
    Returns:
        估算的五维度分数字典
    """
    text = description.lower()
    
    # 初始化基础分
    scores = BASE_SCORES.copy()
    
    # 关键词匹配
    for keyword, adjustments in KEYWORD_RULES.items():
        if keyword in text:
            for dim, increment in adjustments.items():
                scores[dim] = min(100, scores.get(dim, 0) + increment)
    
    # 模型名称检测
    model_keywords = {
        "gpt-4o": 75, "gpt-4": 70, "gpt-3.5": 55,
        "claude-3.5": 78, "claude-3": 72, "claude": 68,
        "qwen": 60, "glm": 62, "llama": 55, "deepseek": 62,
        "local": 40, "ollama": 42,
    }
    
    for model, baseline in model_keywords.items():
        if model in text:
            scores["MS"] = baseline
            break
    
    # 安全检查：限制在有效范围
    for dim in scores:
        scores[dim] = max(0, min(100, scores.get(dim, 0)))
    
    return scores


def estimate_from_system_type(system_type: str) -> Dict[str, int]:
    """
    根据系统类型估算维度分数
    
    Args:
        system_type: 系统类型名称
        
    Returns:
        估算的五维度分数字典
    """
    # 精确匹配
    if system_type in SYSTEM_DEFAULTS:
        return SYSTEM_DEFAULTS[system_type].copy()
    
    # 模糊匹配
    system_lower = system_type.lower()
    for sys_name, scores in SYSTEM_DEFAULTS.items():
        if sys_name in system_lower or system_lower in sys_name:
            return scores.copy()
    
    # 默认返回Agent类型
    return SYSTEM_DEFAULTS["Agent"].copy()


def interactive_collect() -> Tuple[int, int, int, int, int]:
    """
    交互式收集五维度分数
    
    Returns:
        (ES, IS, MS, VS, CE) 元组
    """
    print("\n" + "="*50)
    print("📝 EIE Agent 交互式评估")
    print("="*50)
    
    dimensions = [
        ("ES", "环境适应度", "系统稳定运行、渠道覆盖、容错恢复"),
        ("IS", "感知深度", "记忆能力、知识检索、多模态处理"),
        ("MS", "决策质量", "模型能力、工具使用、工作流编排"),
        ("VS", "对齐强度", "安全机制、价值约束、风险控制"),
        ("CE", "成长速度", "自我改进、经验积累、迭代能力"),
    ]
    
    scores = {}
    
    for dim, name, desc in dimensions:
        while True:
            try:
                print(f"\n【{dim}】{name}")
                print(f"   说明：{desc}")
                value = input(f"   请输入 0-100 的分数（直接回车使用估算值）: ").strip()
                
                if not value:
                    # 使用默认值
                    scores[dim] = BASE_SCORES.get(dim, 50)
                    print(f"   → 使用估算值: {scores[dim]}")
                else:
                    scores[dim] = int(value)
                    if not 0 <= scores[dim] <= 100:
                        print("   ⚠️ 分数必须在 0-100 之间，请重新输入")
                        continue
                
                break
            except ValueError:
                print("   ⚠️ 请输入有效的数字")
    
    print("\n" + "="*50)
    return scores["ES"], scores["IS"], scores["MS"], scores["VS"], scores["CE"]


def batch_evaluate(file_path: str) -> List[Dict]:
    """
    批量评估多个系统
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        评估结果列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            systems = json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ JSON格式错误: {file_path}")
        return []
    
    results = []
    
    for idx, system in enumerate(systems):
        name = system.get("name", f"System-{idx+1}")
        
        try:
            if "description" in system:
                scores = parse_description(system["description"])
            elif "system_type" in system:
                scores = estimate_from_system_type(system["system_type"])
            elif all(k in system for k in ["ES", "IS", "MS", "VS", "CE"]):
                scores = {k: system[k] for k in ["ES", "IS", "MS", "VS", "CE"]}
            else:
                print(f"⚠️ 系统 '{name}' 缺少必要字段，跳过")
                continue
            
            es = int(scores.get("ES", 50))
            is_val = int(scores.get("IS", 50))
            ms = int(scores.get("MS", 50))
            vs = int(scores.get("VS", 50))
            ce = int(scores.get("CE", 50))
            
            meq = calculate_meq(es, is_val, ms, vs, ce)
            vl, stage = check_vl4_vl5_conditions(meq, ms, vs)
            
            results.append({
                "name": name,
                "MEQ": meq,
                "VL": vl,
                "stage": stage,
                "ES": es,
                "IS": is_val,
                "MS": ms,
                "VS": vs,
                "CE": ce,
            })
            
            print(f"✓ {name}: MEQ={meq}, {vl}")
            
        except Exception as e:
            print(f"⚠️ 系统 '{name}' 评估失败: {str(e)}")
    
    return results


def format_batch_results(results: List[Dict]) -> str:
    """
    格式化批量评估结果
    """
    if not results:
        return "没有可显示的结果"
    
    header = "╔══════════════════════════════════════════════════════════════════╗\n"
    header += "║                    📊 Agent 能力对比                                ║\n"
    header += "╠══════════════════════════════════════════════════════════════════╣\n"
    header += "║  系统          │ MEQ │  VL  │  ES │  IS │  MS │  VS │  CE  ║\n"
    header += "╠══════════════════════════════════════════════════════════════════╣"
    
    lines = [header]
    
    for r in results:
        name = r["name"][:12].ljust(12)
        meq = f"{r['MEQ']:.0f}".rjust(4)
        vl = r["VL"].rjust(4)
        es = str(r["ES"]).rjust(3)
        is_val = str(r["IS"]).rjust(3)
        ms = str(r["MS"]).rjust(3)
        vs = str(r["VS"]).rjust(3)
        ce = str(r["CE"]).rjust(3)
        
        line = f"║  {name} │ {meq} │ {vl}  │ {es}  │ {is_val}  │ {ms}  │ {vs}  │ {ce}  ║"
        lines.append(line)
    
    footer = "╚══════════════════════════════════════════════════════════════════╝"
    lines.append(footer)
    
    return "\n".join(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="EIE Agent 进化评估器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python evaluator.py --interactive
  python evaluator.py --es 60 --is 70 --ms 65 --vs 75 --ce 55
  python evaluator.py --system "RAG Agent"
  python evaluator.py --batch systems.json
  
  【v4.1 新增】任务助手模式
  python evaluator.py --with-tasks
  python evaluator.py --es 46 --is 30 --ms 73 --vs 42 --ce 53 --with-tasks
        """
    )
    
    parser.add_argument("--es", type=int, help="环境适应度 (ES) 分数 (0-100)")
    parser.add_argument("--is", dest="is_val", type=int, help="感知深度 (IS) 分数 (0-100)")
    parser.add_argument("--ms", type=int, help="决策质量 (MS) 分数 (0-100)")
    parser.add_argument("--vs", type=int, help="对齐强度 (VS) 分数 (0-100)")
    parser.add_argument("--ce", type=int, help="成长速度 (CE) 分数 (0-100)")
    
    parser.add_argument("--system", type=str, help="系统类型：简单聊天机器人/规则型客服/LLM问答/RAG Agent/多模态Agent/自进化Agent")
    parser.add_argument("--description", "-d", type=str, help="Agent描述文本，系统将自动分析")
    
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式输入模式")
    parser.add_argument("--batch", "-b", type=str, help="批量评估JSON文件")
    
    parser.add_argument("--with-coupling", "-c", action="store_true", help="使用涌现耦合项计算MEQ")
    parser.add_argument("--json", "-j", action="store_true", help="输出JSON格式")
    parser.add_argument("--no-advice", action="store_true", help="不显示进化建议")
    
    # 【v4.1】任务助手参数
    parser.add_argument("--with-tasks", "-t", action="store_true", help="启用任务助手模式，输出任务清单")
    parser.add_argument("--workspace", "-w", default=".", help="工作目录（用于任务助手）")
    
    args = parser.parse_args()
    
    # 批量评估模式
    if args.batch:
        results = batch_evaluate(args.batch)
        if results:
            print("\n" + format_batch_results(results))
        return
    
    # 交互式模式
    if args.interactive:
        es, is_val, ms, vs, ce = interactive_collect()
    else:
        # 确定评估模式
        if all(v is not None for v in [args.es, args.is_val, args.ms, args.vs, args.ce]):
            # 直接指定分数
            es, is_val, ms, vs, ce = args.es, args.is_val, args.ms, args.vs, args.ce
        elif args.system:
            # 按系统类型估算
            scores = estimate_from_system_type(args.system)
            es, is_val, ms, vs, ce = scores["ES"], scores["IS"], scores["MS"], scores["VS"], scores["CE"]
            print(f"\n📊 基于系统类型「{args.system}」自动估算维度分数")
        elif args.description:
            # 解析描述
            scores = parse_description(args.description)
            es, is_val, ms, vs, ce = scores["ES"], scores["IS"], scores["MS"], scores["VS"], scores["CE"]
            print(f"\n📊 基于描述自动估算维度分数")
        else:
            # 尝试使用dimension_estimator
            if dimension_estimator_available:
                print("\n📊 尝试使用智能分析...")
                try:
                    result = estimate_from_description(input("请输入Agent描述: "))
                    if result:
                        es, is_val, ms, vs, ce = result
                        print(f"   → 分析完成")
                    else:
                        print("❌ 无法分析描述，请使用 --interactive 或直接指定维度")
                        return
                except Exception as e:
                    print(f"⚠️ 分析失败: {str(e)}")
                    print("请使用 --interactive 或直接指定维度")
                    return
            else:
                print("❌ 请提供评估参数")
                print("   --interactive    交互式输入")
                print("   --es --is --ms --vs --ce  直接指定分数")
                print("   --system 'RAG Agent'  按系统类型估算")
                print("   --description '你的描述'  解析描述")
                return
    
    # 计算MEQ
    try:
        if args.with_coupling:
            meq = calculate_meq_with_coupling(es, is_val, ms, vs, ce)
            print(f"\n📐 MEQ (含耦合项) = {meq}")
        else:
            meq = calculate_meq(es, is_val, ms, vs, ce)
            print(f"\n📐 MEQ = {meq}")
        
        vl, stage = check_vl4_vl5_conditions(meq, ms, vs)
        percentile = get_percentile(meq)
        
        # 格式化输出
        if args.json:
            output = {
                "MEQ": meq,
                "VL": vl,
                "stage": stage,
                "ES": es,
                "IS": is_val,
                "MS": ms,
                "VS": vs,
                "CE": ce,
                "percentile": percentile,
            }
            if not args.no_advice:
                output["advice"] = get_evolution_suggestion(meq, ms, vs)
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            output = format_result(es, is_val, ms, vs, ce, meq, args.with_coupling)
            print(output)
            
            # 百分位信息
            print(f"\n📊 超越 {percentile}")
            
            # 进化建议
            if not args.no_advice:
                advice = get_evolution_suggestion(meq, ms, vs)
                warnings = get_dimension_warning(es, is_val, ms, vs, ce)
                
                if warnings:
                    print(f"\n⚠️ 维度短板：")
                    for w in warnings:
                        print(f"   • {w}")
                
                if advice:
                    print(f"\n💡 {advice}")
        
        # 【v4.1】任务助手模式
        if args.with_tasks and TASK_ASSISTANT_AVAILABLE:
            print("\n" + "="*60)
            print("🎯 启动 EIE 任务助手...")
            print("="*60)
            assistant = EIETaskAssistant(args.workspace)
            print(assistant.generate_report(es, is_val, ms, vs, ce))
        elif args.with_tasks and not TASK_ASSISTANT_AVAILABLE:
            print("\n⚠️  任务助手不可用，请确保 eie_task_assistant.py 存在")
        
    except Exception as e:
        print(f"\n❌ 计算错误: {str(e)}")
        print("请检查输入的分数是否在有效范围内 (0-100)")
        sys.exit(1)


if __name__ == "__main__":
    main()
