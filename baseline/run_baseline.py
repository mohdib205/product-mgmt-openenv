"""
Baseline Inference Script
Runs all 3 tasks with a greedy agent and prints reproducible scores.

Usage:
    cd C:\\Users\\MSI\\Desktop\\OpenEnv\\product_mgmt_env
    python baseline\\run_baseline.py
"""

import sys
import os
import json

# add parent folder to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.task_easy import EasyTask
from tasks.task_medium import MediumTask
from tasks.task_hard import HardTask
from graders.easy_grader import EasyGrader
from graders.medium_grader import MediumGrader
from graders.hard_grader import HardGrader

SEED = 42


def run_all():
    print("=" * 55)
    print("  Product Management OpenEnv — Baseline Evaluation")
    print("=" * 55)

    results = {}

    # ── Task 1: Easy ──────────────────────────────────────────
    print("\n[1/3] Running Easy Task...")
    easy_task = EasyTask(seed=SEED)
    easy_result = easy_task.run()
    easy_grade = EasyGrader().grade(easy_result)
    results["easy"] = easy_grade

    print(f"      Completed Stories : {easy_result['completed']}")
    print(f"      Revenue Unlocked  : {easy_result['revenue_unlocked']}")
    print(f"      Satisfaction      : {easy_result['stakeholder_satisfaction']}")
    print(f"      Technical Debt    : {easy_result['technical_debt']}")
    print(f"      Score             : {easy_grade['score']} / 1.0")
    print(f"      Passed            : {'✓ YES' if easy_grade['passed'] else '✗ NO'}")

    # ── Task 2: Medium ────────────────────────────────────────
    print("\n[2/3] Running Medium Task...")
    medium_task = MediumTask(seed=SEED)
    medium_result = medium_task.run()
    medium_grade = MediumGrader().grade(medium_result)
    results["medium"] = medium_grade

    print(f"      Completed Stories : {medium_result['completed']}")
    print(f"      Revenue Unlocked  : {medium_result['revenue_unlocked']}")
    print(f"      Satisfaction      : {medium_result['stakeholder_satisfaction']}")
    print(f"      Technical Debt    : {medium_result['technical_debt']}")
    print(f"      Score             : {medium_grade['score']} / 1.0")
    print(f"      Passed            : {'✓ YES' if medium_grade['passed'] else '✗ NO'}")

    # ── Task 3: Hard ──────────────────────────────────────────
    print("\n[3/3] Running Hard Task...")
    hard_task = HardTask(seed=SEED)
    hard_result = hard_task.run()
    hard_grade = HardGrader().grade(hard_result)
    results["hard"] = hard_grade

    print(f"      Completed Stories : {hard_result['completed']}")
    print(f"      Revenue Unlocked  : {hard_result['revenue_unlocked']}")
    print(f"      Satisfaction      : {hard_result['stakeholder_satisfaction']}")
    print(f"      Technical Debt    : {hard_result['technical_debt']}")
    print(f"      Score             : {hard_grade['score']} / 1.0")
    print(f"      Passed            : {'✓ YES' if hard_grade['passed'] else '✗ NO'}")

    # ── Summary ───────────────────────────────────────────────
    avg_score = round(
        sum(r["score"] for r in results.values()) / len(results), 4
    )

    print("\n" + "=" * 55)
    print("  FINAL SUMMARY")
    print("=" * 55)
    print(f"  Easy   : {results['easy']['score']} / 1.0")
    print(f"  Medium : {results['medium']['score']} / 1.0")
    print(f"  Hard   : {results['hard']['score']} / 1.0")
    print(f"  Average: {avg_score} / 1.0")
    print("=" * 55)

    # save results to json
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "baseline_results.json"
    )
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: baseline/baseline_results.json")


if __name__ == "__main__":
    run_all()