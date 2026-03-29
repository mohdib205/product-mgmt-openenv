"""
Easy Grader
Scores based on:
  - stories completed        (40%)
  - revenue unlocked         (40%)
  - stakeholder satisfaction (20%)
Passing score: 0.7
"""

from graders.base_grader import BaseGrader


class EasyGrader(BaseGrader):
    def __init__(self):
        super().__init__(passing_score=0.7)

    def score(self, result: dict) -> float:
        completed = result.get("completed", 0)
        revenue = result.get("revenue_unlocked", 0.0)
        satisfaction = result.get("stakeholder_satisfaction", 0.0)

        # normalize completed stories (target: at least 5)
        completed_score = min(1.0, completed / 5)

        # normalize revenue (target: at least 3.0)
        revenue_score = min(1.0, revenue / 3.0)

        # satisfaction already 0.0–1.0
        satisfaction_score = satisfaction

        final = (
            0.4 * completed_score +
            0.4 * revenue_score +
            0.2 * satisfaction_score
        )
        return round(min(1.0, max(0.0, final)), 4)