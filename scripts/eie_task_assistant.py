#!/usr/bin/env python3
"""
EIE 任务助手 v4.1

基于 JTBD 视角（Jobs-to-be-Done）：
- 功能任务：解决系统进化的核心痛点
- 情感任务：给实践者带来心理满足
- 意义任务：实现系统与实践者的价值升华

核心改进：
1. 输出任务清单（而不只是 MEQ）
2. 评估任务完成度（而不只是系统能力）
3. 提供可执行的具体任务（而不只是建议）

使用方式：
    python eie_task_assistant.py --assess
    python eie_task_assistant.py --generate-tasks
    python eie_task_assistant.py --track-progress
"""

import json
import os
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 导入 EIE 计算器
from meq_calculator_eie import calculate_meq_eie, get_vl_level


# ============================================================
# 任务助手核心类
# ============================================================

class EIETaskAssistant:
    """EIE 任务助手 - 帮助用户完成进化任务"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace = workspace_path or os.getcwd()
        self.task_templates = self._load_task_templates()
        self.task_history = self._load_task_history()
    
    def _load_task_templates(self) -> Dict:
        """加载任务模板"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'config', 
            'task_templates.json'
        )
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  任务模板未找到: {template_path}")
            return {}
    
    def _load_task_history(self) -> Dict:
        """加载任务历史"""
        history_path = os.path.join(self.workspace, 'log', 'eie_tasks.json')
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"tasks": [], "completed": [], "created_at": datetime.now().isoformat()}
    
    def _save_task_history(self):
        """保存任务历史"""
        history_path = os.path.join(self.workspace, 'log', 'eie_tasks.json')
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(self.task_history, f, ensure_ascii=False, indent=2)
    
    def assess_system(self, es: int, is_val: int, ms: int, vs: int, ce: int) -> Dict:
        """
        评估系统并生成任务报告
        
        返回包含：
        - MEQ 评估结果
        - 生成的任务清单
        - 任务优先级
        - 预估完成时间
        """
        # 1. EIE 评估
        eie_result = calculate_meq_eie(es, is_val, ms, vs, ce)
        
        # 2. 生成任务
        tasks = self._generate_tasks(eie_result)
        
        # 3. 计算任务完成度
        completion = self._calculate_completion(tasks)
        
        return {
            "eie_result": eie_result,
            "tasks": tasks,
            "completion": completion,
            "assessed_at": datetime.now().isoformat(),
        }
    
    def _generate_tasks(self, eie_result: Dict) -> List[Dict]:
        """基于 EIE 评估结果生成任务"""
        tasks = []
        dim = eie_result["dimensions"]
        chain_efficiency = eie_result["chain_efficiency"]
        
        # 功能任务
        functional_tasks = self.task_templates.get("task_categories", {}).get("functional", {}).get("tasks", [])
        for task_template in functional_tasks:
            if self._should_trigger_task(task_template, dim, chain_efficiency):
                tasks.append(self._create_task_from_template(task_template, "functional"))
        
        # 情感任务（根据用户反馈，这里简化处理）
        emotional_tasks = self.task_templates.get("task_categories", {}).get("emotional", {}).get("tasks", [])
        for task_template in emotional_tasks[:1]:  # 只取第一个
            tasks.append(self._create_task_from_template(task_template, "emotional"))
        
        # 意义任务（根据当前 VL 等级）
        meq = eie_result["meq"]
        vl, _ = get_vl_level(meq)
        if vl in ["VL0", "VL1", "VL2"]:
            meaning_tasks = self.task_templates.get("task_categories", {}).get("meaning", {}).get("tasks", [])
            if meaning_tasks:
                tasks.append(self._create_task_from_template(meaning_tasks[0], "meaning"))
        
        # 按优先级排序
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        tasks.sort(key=lambda x: priority_order.get(x.get("priority", "P2"), 2))
        
        return tasks
    
    def _should_trigger_task(self, task_template: Dict, dim: Dict, chain_efficiency: float) -> bool:
        """判断是否应该触发任务"""
        trigger = task_template.get("trigger", "")
        
        # 解析触发条件（简化处理）
        if "IS < 40" in trigger and dim["IS"] < 40:
            return True
        
        if "CE < 40" in trigger and dim["CE"] < 40:
            return True
        
        if "CE < 50" in trigger and dim["CE"] < 50:
            return True
        
        if "chain_efficiency < 50%" in trigger and chain_efficiency < 50:
            return True
        
        if "无 error 记录" in trigger:
            error_dir = os.path.join(self.workspace, "log", "error")
            if not os.path.exists(error_dir) or not os.listdir(error_dir):
                return True
        
        if "无 evolution 记录" in trigger:
            evolution_dir = os.path.join(self.workspace, "log", "evolution")
            if not os.path.exists(evolution_dir) or len(os.listdir(evolution_dir)) < 3:
                return True
        
        return False
    
    def _create_task_from_template(self, template: Dict, category: str) -> Dict:
        """从模板创建任务"""
        priority_map = {
            "F1": "P0", "F2": "P0", "F4": "P0",
            "F3": "P1", "E1": "P1", "E2": "P1",
            "E3": "P2", "M1": "P2", "M2": "P2", "M3": "P2"
        }
        
        return {
            "id": template.get("id"),
            "name": template.get("name"),
            "category": category,
            "description": template.get("description"),
            "steps": template.get("steps", []),
            "success_criteria": template.get("success_criteria"),
            "estimated_time": template.get("estimated_time"),
            "human_time": template.get("human_time", "0"),
            "collaboration_mode": template.get("collaboration_mode", "Unknown"),
            "difficulty": template.get("difficulty"),
            "priority": priority_map.get(template.get("id"), "P2"),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
    
    def _calculate_completion(self, tasks: List[Dict]) -> Dict:
        """计算任务完成度"""
        if not tasks:
            return {"overall": 0, "by_category": {}}
        
        # 按类别统计
        by_category = {}
        for task in tasks:
            cat = task.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = {"total": 0, "completed": 0}
            by_category[cat]["total"] += 1
            if task.get("status") == "completed":
                by_category[cat]["completed"] += 1
        
        # 计算各类别完成度
        for cat in by_category:
            total = by_category[cat]["total"]
            completed = by_category[cat]["completed"]
            by_category[cat]["percentage"] = round(completed / total * 100, 1) if total > 0 else 0
        
        # 总体完成度
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
        overall = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
        
        return {
            "overall": overall,
            "by_category": by_category,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
        }
    
    def generate_report(self, es: int, is_val: int, ms: int, vs: int, ce: int) -> str:
        """生成完整的任务报告"""
        report = self.assess_system(es, is_val, ms, vs, ce)
        
        eie = report["eie_result"]
        meq = eie["meq"]
        vl, stage = get_vl_level(meq)
        tasks = report["tasks"]
        completion = report["completion"]
        
        output = f"""
╔══════════════════════════════════════════════════════════╗
║       🎯 EIE 任务助手报告（JTBD 视角 v4.1）          ║
╠══════════════════════════════════════════════════════════╣
║                                                            ║
║   【系统评估】                                             ║
║   MEQ = {meq:>5.1f} | {vl} · {stage:<12s}            ║
║   E-I-E 链条效率：{eie['chain_efficiency']:>5.1f}%                     ║
║                                                            ║
║   【任务完成度】                                           ║
║   总体完成度：{completion['overall']:>5.1f}%                      ║"""
        
        for cat, data in completion.get("by_category", {}).items():
            cat_name = {"functional": "功能任务", "emotional": "情感任务", "meaning": "意义任务"}.get(cat, cat)
            output += f"""
║   {cat_name}：{data['percentage']:>5.1f}% ({data['completed']}/{data['total']})            ║"""
        
        output += f"""
║                                                            ║
║   【推荐任务清单】（按优先级排序）                          ║
╠══════════════════════════════════════════════════════════╣"""
        
        for i, task in enumerate(tasks[:5], 1):  # 只显示前 5 个
            priority_emoji = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}.get(task.get("priority"), "⚪")
            cat_name = {"functional": "【功能】", "emotional": "【情感】", "meaning": "【意义】"}.get(task.get("category"), "")
            
            # 人机协作时间显示
            time_display = task.get('estimated_time', 'N/A')
            # 去除 "AI:" 前缀（如果存在）
            if time_display.startswith('AI: '):
                time_display = time_display[4:]
            human_time = task.get('human_time', '0')
            collab_mode = task.get('collaboration_mode', 'Unknown')
            
            mode_emoji = {
                "AI-Only": "🤖",
                "Human-Guided": "👤➡️🤖",
                "Human-AI-Co": "🤝",
                "Human-Only": "👤"
            }.get(collab_mode, "❓")
            
            output += f"""
║                                                            ║
║   {priority_emoji} {i}. {task.get('name')}              ║
║      {cat_name} {mode_emoji} AI:{time_display} | 人类:{human_time} | 难度：{task.get('difficulty')}   ║
║      {task.get('description')[:45]:<45}              ║"""
        
        if len(tasks) > 5:
            output += f"""
║                                                            ║
║      ... 还有 {len(tasks) - 5} 个任务 ...                          ║"""
        
        output += f"""
║                                                            ║
║   💡 下一步行动：                                           ║
║      1. 选择优先级最高的任务开始执行                         ║
║      2. 按照步骤完成任务                                    ║
║      3. 完成后更新任务状态                                  ║
║      4. 重新评估系统能力                                    ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝
"""
        return output


# ============================================================
# CLI 入口
# ============================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EIE 任务助手 v4.1")
    parser.add_argument("--assess", action="store_true", help="评估系统并生成任务报告")
    parser.add_argument("--es", type=int, default=46, help="环境适应度")
    parser.add_argument("--is", dest="is_val", type=int, default=30, help="感知深度")
    parser.add_argument("--ms", type=int, default=73, help="决策质量")
    parser.add_argument("--vs", type=int, default=42, help="对齐强度")
    parser.add_argument("--ce", type=int, default=53, help="成长速度")
    parser.add_argument("--workspace", "-w", default=".", help="工作目录")
    
    args = parser.parse_args()
    
    assistant = EIETaskAssistant(args.workspace)
    
    if args.assess:
        print(assistant.generate_report(args.es, args.is_val, args.ms, args.vs, args.ce))
    else:
        # 默认评估 OpenClaw
        print("🎯 EIE 任务助手 v4.1")
        print("="*60)
        print("\n使用默认参数评估 OpenClaw：")
        print("ES=46, IS=30, MS=73, VS=42, CE=53\n")
        print(assistant.generate_report(46, 30, 73, 42, 53))


if __name__ == "__main__":
    main()
