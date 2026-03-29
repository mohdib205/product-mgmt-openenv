# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Product Management Environment Implementation.

An AI agent manages a software product backlog, plans sprints,
and optimizes releases under deadlines and team capacity constraints.

Tasks:
    easy   - Small backlog, relaxed deadline, high capacity
    medium - Larger backlog, moderate pressure, reduced capacity
    hard   - Large backlog, critical deadline, low capacity, high debt
"""

import random
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import ProductMgmtAction, ProductMgmtObservation
except ImportError:
    from models import ProductMgmtAction, ProductMgmtObservation


# ── Story helper ──────────────────────────────────────────────────────────────

class Story:
    def __init__(self, id, title, priority, effort, value, is_bug=False):
        self.id = id
        self.title = title
        self.priority = priority      # 1=highest, 5=lowest
        self.effort = effort          # story points: 1,2,3,5,8
        self.value = value            # business value: 0.0–1.0
        self.is_bug = is_bug
        self.is_done = False

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "effort": self.effort,
            "value": round(self.value, 2),
            "is_bug": self.is_bug,
            "is_done": self.is_done,
        }


# ── Environment ───────────────────────────────────────────────────────────────

class ProductMgmtEnvironment(Environment):
    """
    Product Management Environment.

    The agent manages a product backlog across multiple sprints.
    It must prioritize stories, manage team capacity, fix bugs,
    and release value before the deadline.

    Reward signal:
        +0.4  adding high priority story
        +0.3  fixing a bug
        +0.2  high business value story added
        +0.5  successful release with high value
        -0.2  overfilling capacity
        -0.3  ignoring bugs under pressure
        -0.4  removing high value story
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    # story titles pool
    STORY_TITLES = [
        "User login flow", "Dashboard redesign", "Fix checkout bug",
        "Add search feature", "Payment gateway", "Fix crash on iOS",
        "Email notifications", "Dark mode support", "API rate limiting",
        "Performance optimization", "Fix data export", "Onboarding flow",
        "Fix billing bug", "Mobile responsiveness", "Security patch",
        "User feedback form", "Analytics dashboard", "New reporting feature",
        "Fix null pointer error", "Improve load time",
    ]

    def __init__(self, task: str = "easy", seed: int = 42):
        self.task = task
        self.seed = seed
        self._rng = random.Random(seed)
        self._state = State(episode_id=str(uuid4()), step_count=0)

        # episode variables
        self._step = 0
        self._sprint_number = 1
        self._backlog: list[Story] = []
        self._sprint: list[Story] = []
        self._completed: list[Story] = []
        self._revenue = 0.0
        self._deadline_pressure = 0.2
        self._technical_debt = 0.1
        self._satisfaction = 0.8
        self._done = False
        self._next_id = 1

    # ── config helpers ────────────────────────────────────────────────────────

    @property
    def _max_steps(self) -> int:
        return 30

    @property
    def _team_capacity(self) -> int:
        return {"easy": 20, "medium": 15, "hard": 10}.get(self.task, 20)

    @property
    def _starting_pressure(self) -> float:
        return {"easy": 0.2, "medium": 0.5, "hard": 0.8}.get(self.task, 0.2)

    @property
    def _backlog_size(self) -> int:
        return {"easy": 8, "medium": 10, "hard": 12}.get(self.task, 8)

    # ── story generation ──────────────────────────────────────────────────────

    def _make_story(self, bug_chance: float = 0.25) -> Story:
        story = Story(
            id=self._next_id,
            title=self._rng.choice(self.STORY_TITLES),
            priority=self._rng.randint(1, 5),
            effort=self._rng.choice([1, 2, 3, 5, 8]),
            value=round(self._rng.uniform(0.1, 1.0), 2),
            is_bug=self._rng.random() < bug_chance,
        )
        self._next_id += 1
        return story

    def _generate_backlog(self) -> list:
        bug_chance = {"easy": 0.2, "medium": 0.3, "hard": 0.4}.get(self.task, 0.2)
        return [self._make_story(bug_chance) for _ in range(self._backlog_size)]

    # ── reward ────────────────────────────────────────────────────────────────

    def _compute_reward(self, action: ProductMgmtAction, story=None) -> float:
        reward = 0.0

        if action.decision == 0 and story:       # ADD TO SPRINT
            if story.priority <= 2:
                reward += 0.4
            if story.is_bug:
                reward += 0.3
            if story.value >= 0.7:
                reward += 0.2
            if self._deadline_pressure >= 0.7:
                reward += 0.1
            if sum(s.effort for s in self._sprint) > self._team_capacity:
                reward -= 0.2
            high_pri = any(s.priority == 1 for s in self._backlog)
            if story.priority >= 4 and high_pri:
                reward -= 0.3

        elif action.decision == 1 and story:     # DEFER
            if story.priority >= 4 and story.value < 0.4:
                reward += 0.2
            if story.is_bug and self._deadline_pressure >= 0.7:
                reward -= 0.3
            if story.priority == 1:
                reward -= 0.2

        elif action.decision == 2 and story:     # REMOVE
            if story.value < 0.3:
                reward += 0.1
            if story.value >= 0.7:
                reward -= 0.4

        elif action.decision == 3:               # RELEASE
            completed_value = sum(s.value for s in self._sprint)
            if completed_value >= 0.6:
                reward += 0.5
            if self._deadline_pressure < 0.4:
                reward += 0.2
            if self._technical_debt >= 0.7:
                reward -= 0.3
            if self._step < 3:
                reward -= 0.2

        # global signals
        if self._technical_debt >= 0.8:
            reward -= 0.2
        if self._satisfaction < 0.3:
            reward -= 0.3
        if self._satisfaction >= 0.7:
            reward += 0.1

        return round(max(-1.0, min(1.0, reward)), 4)

    # ── dynamics ──────────────────────────────────────────────────────────────

    def _update_dynamics(self):
        # deadline pressure grows each step
        self._deadline_pressure = round(
            min(1.0, self._deadline_pressure + 0.02), 3
        )
        # technical debt grows with unfixed bugs
        unfixed_bugs = sum(1 for s in self._backlog if s.is_bug)
        self._technical_debt = round(
            min(1.0, self._technical_debt + unfixed_bugs * 0.01), 3
        )
        # satisfaction based on completed value
        if self._completed:
            avg_value = sum(s.value for s in self._completed) / len(self._completed)
            self._satisfaction = round(min(1.0, avg_value + 0.1), 3)

    # ── observation builder ───────────────────────────────────────────────────

    def _build_observation(self, reward: float = 0.0, done: bool = False) -> ProductMgmtObservation:
        used = sum(s.effort for s in self._sprint)
        top_backlog = sorted(self._backlog, key=lambda s: s.priority)[:5]
        return ProductMgmtObservation(
            # sprint info
            sprint_number=self._sprint_number,
            step=self._step,
            max_steps=self._max_steps,
            # capacity
            team_capacity=self._team_capacity,
            used_capacity=used,
            # counts
            backlog_count=len(self._backlog),
            sprint_count=len(self._sprint),
            completed_count=len(self._completed),
            # pressure
            deadline_pressure=self._deadline_pressure,
            technical_debt=self._technical_debt,
            stakeholder_satisfaction=self._satisfaction,
            revenue_unlocked=round(self._revenue, 4),
            # stories
            top_backlog_stories=[s.to_dict() for s in top_backlog],
            current_sprint_stories=[s.to_dict() for s in self._sprint],
            # openenv required
            done=done,
            reward=reward,
        )

    # ── OpenEnv API ───────────────────────────────────────────────────────────

    def reset(self) -> ProductMgmtObservation:
        """Reset environment and start a new episode."""
        self._rng = random.Random(self.seed)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._step = 0
        self._sprint_number = 1
        self._next_id = 1
        self._backlog = self._generate_backlog()
        self._sprint = []
        self._completed = []
        self._revenue = 0.0
        self._deadline_pressure = self._starting_pressure
        self._technical_debt = 0.1
        self._satisfaction = 0.8
        self._done = False

        return self._build_observation(reward=0.0, done=False)

    def step(self, action: ProductMgmtAction) -> ProductMgmtObservation:
        """Execute one step — apply action, update dynamics, return observation."""
        self._state.step_count += 1
        self._step += 1

        # find story
        story = None
        if action.story_id != -1:
            story = next(
                (s for s in self._backlog + self._sprint if s.id == action.story_id),
                None
            )

        # apply action
        if action.decision == 0 and story and story in self._backlog:
            # ADD TO SPRINT
            used = sum(s.effort for s in self._sprint)
            if used + story.effort <= self._team_capacity:
                self._sprint.append(story)
                self._backlog.remove(story)

        elif action.decision == 1 and story and story in self._backlog:
            # DEFER — lower priority
            story.priority = min(5, story.priority + 1)

        elif action.decision == 2 and story and story in self._sprint:
            # REMOVE from sprint back to backlog
            self._sprint.remove(story)
            self._backlog.append(story)

        elif action.decision == 3:
            # RELEASE — complete sprint
            for s in self._sprint:
                s.is_done = True
                self._completed.append(s)
                self._revenue += s.value
            self._sprint = []
            self._sprint_number += 1

            # add new incoming stories after release
            bug_chance = {"easy": 0.2, "medium": 0.3, "hard": 0.4}.get(self.task, 0.2)
            for _ in range(self._rng.randint(1, 3)):
                self._backlog.append(self._make_story(bug_chance))

        # compute reward
        reward = self._compute_reward(action, story)

        # update environment dynamics
        self._update_dynamics()

        # check if episode is done
        done = self._step >= self._max_steps
        self._done = done

        return self._build_observation(reward=reward, done=done)

    @property
    def state(self) -> State:
        """Return current episode state (read-only snapshot)."""
        return self._state