"""
Hard Grader
Scores based on:
  - revenue unlocked         (40%)
  - technical debt control   (25%)
  - stakeholder satisfaction (20%)
  - stories completed        (15%)
Passing score: 0.8
"""

from graders.base_grader import BaseGrader


class HardGrader(BaseGrader):
    def __init__(self):
        super().__init__(passing_score=0.8)

    def score(self, result: dict) -> float:
        completed = result.get("completed", 0)
        revenue = result.get("revenue_unlocked", 0.0)
        satisfaction = result.get("stakeholder_satisfaction", 0.0)
        technical_debt = result.get("technical_debt", 1.0)

        # normalize completed stories (target: at least 4)
        completed_score = min(1.0, completed / 4)

        # normalize revenue (target: at least 2.5)
        revenue_score = min(1.0, revenue / 2.5)

        # lower debt = better score
        debt_score = max(0.0, 1.0 - technical_debt)

        # satisfaction already 0.0–1.0
        satisfaction_score = satisfaction

        final = (
            0.40 * revenue_score +
            0.25 * debt_score +
            0.20 * satisfaction_score +
            0.15 * completed_score
        )
        return round(min(1.0, max(0.0, final)), 4)