"""
Base Grader — all graders inherit from this.
Scores an episode 0.0–1.0.
"""


class BaseGrader:
    def __init__(self, passing_score: float):
        self.passing_score = passing_score

    def score(self, result: dict) -> float:
        raise NotImplementedError("Each grader must implement score()")

    def grade(self, result: dict) -> dict:
        s = self.score(result)
        return {
            "score": round(s, 4),
            "passed": s >= self.passing_score,
            "passing_score": self.passing_score,
            "task": result.get("task"),
            "completed": result.get("completed"),
            "revenue_unlocked": result.get("revenue_unlocked"),
            "stakeholder_satisfaction": result.get("stakeholder_satisfaction"),
            "technical_debt": result.get("technical_debt"),
            "total_reward": result.get("total_reward"),
        }