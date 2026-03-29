"""
Medium Grader
Scores based on:
  - stories completed        (30%)
  - revenue unlocked         (30%)
  - technical debt control   (20%)
  - stakeholder satisfaction (20%)
Passing score: 0.75
"""

from graders.base_grader import BaseGrader


class MediumGrader(BaseGrader):
    def __init__(self):
        super().__init__(passing_score=0.75)

    def score(self, result: dict) -> float:
        completed = result.get("completed", 0)
        revenue = result.get("revenue_unlocked", 0.0)
        satisfaction = result.get("stakeholder_satisfaction", 0.0)
        technical_debt = result.get("technical_debt", 1.0)

        # normalize completed stories (target: at least 6)
        completed_score = min(1.0, completed / 6)

        # normalize revenue (target: at least 4.0)
        revenue_score = min(1.0, revenue / 4.0)

        # lower debt = better score
        debt_score = max(0.0, 1.0 - technical_debt)

        # satisfaction already 0.0–1.0
        satisfaction_score = satisfaction

        final = (
            0.3 * completed_score +
            0.3 * revenue_score +
            0.2 * debt_score +
            0.2 * satisfaction_score
        )
        return round(min(1.0, max(0.0, final)), 4)