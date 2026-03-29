"""
Task 3 — Hard
Scenario: Large backlog, critical deadline, low team capacity,
          high technical debt, constant new stories added.
Goal: Triage ruthlessly — maximize business value before deadline.
Passing score: 0.8
"""

from server.product_mgmt_env_environment import ProductMgmtEnvironment
from models import ProductMgmtAction


class HardTask:
    def __init__(self, seed=42):
        self.env = ProductMgmtEnvironment(task="hard", seed=seed)
        self.episode_log = []

    def run(self, agent=None) -> dict:
        obs = self.env.reset()
        self.episode_log = []
        total_reward = 0.0

        while not obs.done:
            if agent:
                action = agent.act(obs)
            else:
                action = self._greedy_action(obs)

            obs = self.env.step(action)
            total_reward += obs.reward or 0.0

            self.episode_log.append({
                "step": obs.step,
                "action": action.decision,
                "story_id": action.story_id,
                "reward": obs.reward,
                "completed": obs.completed_count,
                "revenue": obs.revenue_unlocked,
            })

        return {
            "task": "hard",
            "total_reward": round(total_reward, 4),
            "steps": obs.step,
            "completed": obs.completed_count,
            "revenue_unlocked": round(obs.revenue_unlocked, 4),
            "stakeholder_satisfaction": obs.stakeholder_satisfaction,
            "technical_debt": obs.technical_debt,
            "log": self.episode_log,
        }

    def _greedy_action(self, obs) -> ProductMgmtAction:
        # fix bugs first when debt is high
        if obs.technical_debt >= 0.6:
            bugs = [
                s for s in obs.top_backlog_stories
                if s["is_bug"]
            ]
            if bugs:
                bug = sorted(bugs, key=lambda s: s["effort"])[0]
                if obs.used_capacity + bug["effort"] <= obs.team_capacity:
                    return ProductMgmtAction(decision=0, story_id=bug["id"])

        # pick best ROI story (highest value / lowest effort)
        candidates = [
            s for s in obs.top_backlog_stories
            if obs.used_capacity + s["effort"] <= obs.team_capacity
        ]
        if candidates:
            best = max(
                candidates,
                key=lambda s: s["value"] / max(1, s["effort"])
            )
            return ProductMgmtAction(decision=0, story_id=best["id"])

        # release under deadline pressure or full capacity
        capacity_used = obs.used_capacity / max(1, obs.team_capacity)
        if obs.current_sprint_stories and (
            capacity_used >= 1.0 or
            obs.deadline_pressure >= 0.8
        ):
            return ProductMgmtAction(decision=3, story_id=-1)

        # remove lowest value story to make room
        if obs.current_sprint_stories:
            worst = min(
                obs.current_sprint_stories,
                key=lambda s: s["value"]
            )
            return ProductMgmtAction(decision=2, story_id=worst["id"])

        return ProductMgmtAction(decision=3, story_id=-1)