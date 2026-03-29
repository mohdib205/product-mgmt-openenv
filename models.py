# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Product Management Environment.
An AI agent manages a software product backlog, plans sprints,
and optimizes releases under deadlines and team capacity constraints.
"""

from typing import List
from pydantic import Field
from openenv.core.env_server.types import Action, Observation


class ProductMgmtAction(Action):
    """
    Action for the Product Management environment.

    Decisions:
        0 = ADD_TO_SPRINT  → move a story from backlog into current sprint
        1 = DEFER          → push a story lower in priority
        2 = REMOVE         → remove a story from sprint back to backlog
        3 = RELEASE        → close current sprint and ship completed stories
    """
    decision: int = Field(
        ...,
        description="0=ADD_TO_SPRINT, 1=DEFER, 2=REMOVE, 3=RELEASE"
    )
    story_id: int = Field(
        default=-1,
        description="ID of the story to act on (-1 for RELEASE)"
    )


class ProductMgmtObservation(Observation):
    """
    Observation returned after each step.
    Agent uses this to decide its next action.
    """
    # sprint info
    sprint_number: int = Field(default=1, description="Current sprint number")
    step: int = Field(default=0, description="Current step in episode")
    max_steps: int = Field(default=30, description="Maximum steps per episode")

    # capacity
    team_capacity: int = Field(default=20, description="Total story points available")
    used_capacity: int = Field(default=0, description="Story points already assigned")

    # counts
    backlog_count: int = Field(default=0, description="Stories waiting in backlog")
    sprint_count: int = Field(default=0, description="Stories in current sprint")
    completed_count: int = Field(default=0, description="Total completed stories")

    # pressure metrics
    deadline_pressure: float = Field(default=0.2, description="0.0=relaxed, 1.0=critical")
    technical_debt: float = Field(default=0.1, description="0.0=clean, 1.0=very high")
    stakeholder_satisfaction: float = Field(default=0.8, description="0.0-1.0")
    revenue_unlocked: float = Field(default=0.0, description="Total business value delivered")

    # stories agent can see
    top_backlog_stories: List[dict] = Field(
        default_factory=list,
        description="Top 5 backlog stories with id, title, priority, effort, value, is_bug"
    )
    current_sprint_stories: List[dict] = Field(
        default_factory=list,
        description="Stories currently in sprint"
    )