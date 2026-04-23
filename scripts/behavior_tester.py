#!/usr/bin/env python3
"""
EIE Agent 行为测试器

不只是静态检测配置，还要动态测试行为

测试类型：
1. 记忆使用测试 - 检查记忆是否真正被使用
2. 框架遵从测试 - 检查是否遵守定义的流程
3. 错误处理测试 - 检查错误是否被记录
4. 进化产出测试 - 检查是否有持续改进
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BehaviorTestResult:
    """行为测试结果"""
    test_name: str
    passed: bool
    score: float  # 0-1
    details: str
    suggestions: List[str] = None
    
    def __post_init__(self):
        self.suggestions = self.suggestions or []


class BehaviorTester:
    """行为测试器"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.memory_dir = self.workspace / "memory"
        self.log_dir = self.workspace / "log"
        self.memory_file = self.workspace / "MEMORY.md"
    
    def test_memory_usage(self, days: int = 7) -> BehaviorTestResult:
        """
        测试记忆使用情况
        
        检查点：
        1. 记忆文件是否存在且有内容
        2. 内容是否在持续更新
        3. 是否有实质性的记录（不只是空文件）
        """
        if not self.memory_dir.exists():
            return BehaviorTestResult(
                test_name="记忆使用",
                passed=False,
                score=0.0,
                details="记忆目录不存在",
                suggestions=["创建 memory/ 目录", "启用记忆系统"]
            )
        
        today = datetime.now()
        active_days = 0
        total_content = 0
        empty_days = 0
        
        for i in range(days):
            date = today - timedelta(days=i)
            filename = date.strftime("%Y-%m-%d.md")
            filepath = self.memory_dir / filename
            
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding='utf-8')
                    lines = len(content.strip().split('\n'))
                    
                    if lines > 5:
                        active_days += 1
                        total_content += lines
                    else:
                        empty_days += 1
                except:
                    empty_days += 1
            else:
                empty_days += 1
        
        usage_rate = active_days / days
        avg_content = total_content / active_days if active_days > 0 else 0
        
        # 评分：使用率 × 内容质量
        content_quality = min(avg_content / 30.0, 1.0)  # 30行为满分
        score = usage_rate * 0.7 + content_quality * 0.3
        
        passed = score >= 0.5
        
        details = f"最近{days}天：活跃{active_days}天，空{empty_days}天，平均{avg_content:.0f}行"
        
        suggestions = []
        if usage_rate < 0.5:
            suggestions.append(f"提高记忆使用率（当前{usage_rate*100:.0f}%）")
        if avg_content < 20:
            suggestions.append("增加记忆内容深度（每条记录应有实质内容）")
        if empty_days > days * 0.5:
            suggestions.append("建立每日记录习惯，避免空记录")
        
        return BehaviorTestResult(
            test_name="记忆使用",
            passed=passed,
            score=score,
            details=details,
            suggestions=suggestions
        )
    
    def test_framework_compliance(self, framework_name: str = "S级框架") -> BehaviorTestResult:
        """
        测试框架遵从度
        
        检查点：
        1. 是否有定义的框架
        2. 是否在实际执行中遵循
        3. 是否有产出记录
        """
        # 检查框架定义是否存在
        framework_markers = []
        
        # 检查 AGENTS.md 或 MEMORY.md 中的框架定义
        if self.memory_file.exists():
            content = self.memory_file.read_text(encoding='utf-8')
            if "S级框架" in content or "S 级框架" in content:
                framework_markers.append("MEMORY.md 定义了 S 级框架")
        
        # 检查 log/evolution/ 是否有进化产出
        evolution_dir = self.log_dir / "evolution"
        evolution_count = 0
        if evolution_dir.exists():
            evolution_count = len(list(evolution_dir.glob("*.md")))
        
        # 检查 memory/ 中是否有框架使用的痕迹
        framework_usage = 0
        if self.memory_dir.exists():
            for md_file in self.memory_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    if "需求卡片" in content or "产出规划" in content or "交付验证" in content:
                        framework_usage += 1
                except:
                    pass
        
        # 计算分数
        has_framework = len(framework_markers) > 0
        has_evolution = evolution_count > 0
        uses_framework = framework_usage > 0
        
        if not has_framework:
            return BehaviorTestResult(
                test_name="框架遵从",
                passed=False,
                score=0.0,
                details="未检测到框架定义",
                suggestions=["定义工作流程框架", "将框架写入 MEMORY.md"]
            )
        
        score = 0.3  # 有框架定义
        if uses_framework:
            score += 0.4
        if has_evolution:
            score += 0.3
        
        passed = score >= 0.7
        
        details = f"框架定义: {'✅' if has_framework else '❌'}, "
        details += f"实际使用: {framework_usage}次, "
        details += f"进化产出: {evolution_count}个"
        
        suggestions = []
        if not uses_framework:
            suggestions.append("在回复中实际使用框架（需求卡片、产出规划、交付验证）")
        if not has_evolution:
            suggestions.append("创建进化产出记录（log/evolution/）")
        
        return BehaviorTestResult(
            test_name="框架遵从",
            passed=passed,
            score=score,
            details=details,
            suggestions=suggestions
        )
    
    def test_error_handling(self, days: int = 30) -> BehaviorTestResult:
        """
        测试错误处理机制
        
        检查点：
        1. 是否有错误记录目录
        2. 是否有错误记录
        3. 错误是否有改进措施
        """
        error_dir = self.log_dir / "error"
        
        if not error_dir.exists():
            return BehaviorTestResult(
                test_name="错误处理",
                passed=False,
                score=0.0,
                details="错误记录目录不存在",
                suggestions=["创建 log/error/ 目录", "建立错误记录机制"]
            )
        
        error_files = list(error_dir.glob("*.md"))
        
        if not error_files:
            return BehaviorTestResult(
                test_name="错误处理",
                passed=False,
                score=0.3,
                details="无错误记录",
                suggestions=["开始记录错误", "建立错误→教训→预防的闭环"]
            )
        
        # 检查错误记录质量
        improved_count = 0
        for ef in error_files:
            try:
                content = ef.read_text(encoding='utf-8').lower()
                if '教训' in content or '预防' in content or 'lesson' in content or 'prevent' in content:
                    improved_count += 1
            except:
                pass
        
        improvement_rate = improved_count / len(error_files) if error_files else 0
        
        score = 0.5 + improvement_rate * 0.5
        passed = improvement_rate >= 0.5
        
        details = f"错误记录: {len(error_files)}个, 含改进措施: {improved_count}个 ({improvement_rate*100:.0f}%)"
        
        suggestions = []
        if improvement_rate < 0.5:
            suggestions.append("每个错误记录必须包含'教训'和'预防措施'")
        
        return BehaviorTestResult(
            test_name="错误处理",
            passed=passed,
            score=score,
            details=details,
            suggestions=suggestions
        )
    
    def test_evolution_output(self, days: int = 30) -> BehaviorTestResult:
        """
        测试进化产出
        
        检查点：
        1. 是否有进化产出目录
        2. 是否有进化记录
        3. 进化是否持续
        """
        evolution_dir = self.log_dir / "evolution"
        
        if not evolution_dir.exists():
            return BehaviorTestResult(
                test_name="进化产出",
                passed=False,
                score=0.0,
                details="进化产出目录不存在",
                suggestions=["创建 log/evolution/ 目录", "每次改进后记录进化产出"]
            )
        
        evolution_files = list(evolution_dir.glob("*.md"))
        
        if not evolution_files:
            return BehaviorTestResult(
                test_name="进化产出",
                passed=False,
                score=0.2,
                details="无进化产出记录",
                suggestions=["每次优化后记录进化产出", "让系统有'记忆'自己如何变好"]
            )
        
        # 检查最近的进化记录
        recent_count = 0
        today = datetime.now()
        
        for ef in evolution_files:
            try:
                mtime = datetime.fromtimestamp(ef.stat().st_mtime)
                if (today - mtime).days <= days:
                    recent_count += 1
            except:
                pass
        
        recency_rate = recent_count / len(evolution_files) if evolution_files else 0
        
        score = 0.4 + recency_rate * 0.6
        passed = recent_count >= 1  # 最近30天至少有1条
        
        details = f"进化记录: {len(evolution_files)}个, 最近{days}天: {recent_count}个"
        
        suggestions = []
        if recent_count == 0:
            suggestions.append(f"最近{days}天无进化记录，系统可能在停滞")
        
        return BehaviorTestResult(
            test_name="进化产出",
            passed=passed,
            score=score,
            details=details,
            suggestions=suggestions
        )
    
    def test_feedback_loop(self) -> BehaviorTestResult:
        """
        测试反馈闭环
        
        检查点：
        1. 错误记录 → 记忆更新 → 行为改变
        2. 这个闭环是否真正工作
        """
        # 检查三个环节
        has_errors = False
        has_memory = False
        has_evolution = False
        
        error_dir = self.log_dir / "error"
        if error_dir.exists():
            has_errors = len(list(error_dir.glob("*.md"))) > 0
        
        if self.memory_dir.exists():
            # 检查最近7天是否有更新
            today = datetime.now()
            for i in range(7):
                date = today - timedelta(days=i)
                filename = date.strftime("%Y-%m-%d.md")
                filepath = self.memory_dir / filename
                if filepath.exists():
                    try:
                        content = filepath.read_text(encoding='utf-8')
                        if len(content.strip()) > 100:
                            has_memory = True
                            break
                    except:
                        pass
        
        evolution_dir = self.log_dir / "evolution"
        if evolution_dir.exists():
            has_evolution = len(list(evolution_dir.glob("*.md"))) > 0
        
        # 闭环评分
        loop_complete = has_errors and has_memory and has_evolution
        
        if loop_complete:
            score = 1.0
        elif has_errors and has_memory:
            score = 0.6  # 有记录和记忆，但没有进化
        elif has_errors or has_memory:
            score = 0.3  # 只有一个环节
        else:
            score = 0.0  # 闭环完全不存在
        
        passed = score >= 0.6
        
        details = f"错误记录: {'✅' if has_errors else '❌'}, "
        details += f"记忆更新: {'✅' if has_memory else '❌'}, "
        details += f"进化产出: {'✅' if has_evolution else '❌'}"
        
        suggestions = []
        if not has_errors:
            suggestions.append("建立错误记录机制")
        if not has_memory:
            suggestions.append("每日更新记忆系统")
        if not has_evolution:
            suggestions.append("记录改进和进化")
        if has_errors and has_memory and not has_evolution:
            suggestions.append("将错误改进转化为进化产出")
        
        return BehaviorTestResult(
            test_name="反馈闭环",
            passed=passed,
            score=score,
            details=details,
            suggestions=suggestions
        )
    
    def run_all_tests(self) -> Dict[str, BehaviorTestResult]:
        """运行所有行为测试"""
        return {
            "记忆使用": self.test_memory_usage(),
            "框架遵从": self.test_framework_compliance(),
            "错误处理": self.test_error_handling(),
            "进化产出": self.test_evolution_output(),
            "反馈闭环": self.test_feedback_loop(),
        }
    
    def generate_report(self) -> str:
        """生成行为测试报告"""
        results = self.run_all_tests()
        
        lines = []
        lines.append("╔══════════════════════════════════════════════════════════╗")
        lines.append("║           🧪 EIE 行为测试报告                              ║")
        lines.append("╠══════════════════════════════════════════════════════════╣")
        
        total_score = 0
        passed_count = 0
        
        for name, result in results.items():
            status = "✅" if result.passed else "❌"
            score_bar = "█" * int(result.score * 10) + "░" * (10 - int(result.score * 10))
            
            lines.append(f"║  {name}: {status} {score_bar} {result.score*100:.0f}%")
            lines.append(f"║    {result.details}")
            
            total_score += result.score
            if result.passed:
                passed_count += 1
        
        avg_score = total_score / len(results)
        pass_rate = passed_count / len(results)
        
        lines.append("╠══════════════════════════════════════════════════════════╣")
        lines.append(f"║  综合得分: {avg_score*100:.0f}% | 通过率: {pass_rate*100:.0f}%")
        lines.append("╠══════════════════════════════════════════════════════════╣")
        lines.append("║  💡 改进建议：")
        
        all_suggestions = []
        for result in results.values():
            all_suggestions.extend(result.suggestions)
        
        for i, s in enumerate(all_suggestions[:5], 1):
            lines.append(f"║    {i}. {s}")
        
        lines.append("╚══════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EIE 行为测试器")
    parser.add_argument("--workspace", "-w", default=".", help="Workspace目录")
    parser.add_argument("--json", "-j", action="store_true", help="输出JSON格式")
    
    args = parser.parse_args()
    
    tester = BehaviorTester(args.workspace)
    
    if args.json:
        results = tester.run_all_tests()
        output = {
            name: {
                "passed": r.passed,
                "score": r.score,
                "details": r.details,
                "suggestions": r.suggestions
            }
            for name, r in results.items()
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(tester.generate_report())
