"""
Task 2 — Medium
Scenario: Larger backlog, moderate deadline pressure,
          reduced team capacity, bugs mixed in.
Goal: Agent must balance bug fixes with feature delivery.
Passing score: 0.75
"""

from server.product_mgmt_env_environment import ProductMgmtEnvironment
from models import ProductMgmtAction


class MediumTask:
    def __init__(self, seed=42):
        self.env = ProductMgmtEnvironment(task="medium", seed=seed)
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
            "task": "medium",
            "total_reward": round(total_reward, 4),
            "steps": obs.step,
            "completed": obs.completed_count,
            "revenue_unlocked": round(obs.revenue_unlocked, 4),
            "stakeholder_satisfaction": obs.stakeholder_satisfaction,
            "technical_debt": obs.technical_debt,
            "log": self.episode_log,
        }

    def _greedy_action(self, obs) -> ProductMgmtAction:
        # fix bugs first under deadline pressure
        if obs.deadline_pressure >= 0.5:
            bugs = [
                s for s in obs.top_backlog_stories
                if s["is_bug"]
            ]
            if bugs:
                bug = min(bugs, key=lambda s: s["effort"])
                if obs.used_capacity + bug["effort"] <= obs.team_capacity:
                    return ProductMgmtAction(decision=0, story_id=bug["id"])

        # add high value stories
        high_value = [
            s for s in obs.top_backlog_stories
            if s["value"] >= 0.6
        ]
        if high_value:
            story = min(high_value, key=lambda s: s["effort"])
            if obs.used_capacity + story["effort"] <= obs.team_capacity:
                return ProductMgmtAction(decision=0, story_id=story["id"])

        # release if sprint reasonably full
        capacity_used = obs.used_capacity / max(1, obs.team_capacity)
        if obs.current_sprint_stories and capacity_used >= 0.7:
            return ProductMgmtAction(decision=3, story_id=-1)

        # defer low priority low value stories
        low = [
            s for s in obs.top_backlog_stories
            if s["priority"] >= 4 and s["value"] < 0.4
        ]
        if low:
            return ProductMgmtAction(decision=1, story_id=low[0]["id"])

        # release if nothing else to do
        if obs.current_sprint_stories:
            return ProductMgmtAction(decision=3, story_id=-1)

        return ProductMgmtAction(decision=1, story_id=-1)