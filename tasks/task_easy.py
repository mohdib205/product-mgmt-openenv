"""
Task 1 — Easy
Scenario: Small backlog, relaxed deadline, high team capacity.
Goal: Agent must fill sprint with high priority stories and release.
Passing score: 0.7
"""

from server.product_mgmt_env_environment import ProductMgmtEnvironment
from models import ProductMgmtAction


class EasyTask:
    def __init__(self, seed=42):
        self.env = ProductMgmtEnvironment(task="easy", seed=seed)
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
            "task": "easy",
            "total_reward": round(total_reward, 4),
            "steps": obs.step,
            "completed": obs.completed_count,
            "revenue_unlocked": round(obs.revenue_unlocked, 4),
            "stakeholder_satisfaction": obs.stakeholder_satisfaction,
            "technical_debt": obs.technical_debt,
            "log": self.episode_log,
        }

    def _greedy_action(self, obs) -> ProductMgmtAction:
        # add highest priority story from backlog
        if obs.top_backlog_stories:
            story = min(
                obs.top_backlog_stories,
                key=lambda s: s["priority"]
            )
            used = obs.used_capacity
            if used + story["effort"] <= obs.team_capacity:
                return ProductMgmtAction(decision=0, story_id=story["id"])

        # release if sprint has stories
        if obs.current_sprint_stories:
            return ProductMgmtAction(decision=3, story_id=-1)

        # defer first backlog story
        if obs.top_backlog_stories:
            return ProductMgmtAction(
                decision=1,
                story_id=obs.top_backlog_stories[0]["id"]
            )

        return ProductMgmtAction(decision=3, story_id=-1)