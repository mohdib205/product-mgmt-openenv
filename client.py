# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Product Management Environment Client.

Used by agents to connect to the environment server
and interact via reset(), step(), and state().
"""

from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from .models import ProductMgmtAction, ProductMgmtObservation


class ProductMgmtEnv(
    EnvClient[ProductMgmtAction, ProductMgmtObservation, State]
):
    """
    Client for the Product Management Environment.

    Connects to the environment server via WebSocket.
    Each client instance gets its own dedicated session.

    Example:
        >>> with ProductMgmtEnv(base_url="http://localhost:8000") as env:
        ...     obs = env.reset()
        ...     print(obs.backlog_count)
        ...
        ...     action = ProductMgmtAction(decision=0, story_id=1)
        ...     result = env.step(action)
        ...     print(result.observation.revenue_unlocked)
        ...     print(result.reward)
    """

    def _step_payload(self, action: ProductMgmtAction) -> Dict:
        """
        Convert ProductMgmtAction to JSON payload for step message.

        Args:
            action: ProductMgmtAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "decision": action.decision,
            "story_id": action.story_id,
        }

    def _parse_result(self, payload: Dict) -> StepResult[ProductMgmtObservation]:
        """
        Parse server response into StepResult[ProductMgmtObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with ProductMgmtObservation
        """
        obs_data = payload.get("observation", {})

        observation = ProductMgmtObservation(
            # sprint info
            sprint_number=obs_data.get("sprint_number", 1),
            step=obs_data.get("step", 0),
            max_steps=obs_data.get("max_steps", 30),
            # capacity
            team_capacity=obs_data.get("team_capacity", 20),
            used_capacity=obs_data.get("used_capacity", 0),
            # counts
            backlog_count=obs_data.get("backlog_count", 0),
            sprint_count=obs_data.get("sprint_count", 0),
            completed_count=obs_data.get("completed_count", 0),
            # pressure
            deadline_pressure=obs_data.get("deadline_pressure", 0.2),
            technical_debt=obs_data.get("technical_debt", 0.1),
            stakeholder_satisfaction=obs_data.get("stakeholder_satisfaction", 0.8),
            revenue_unlocked=obs_data.get("revenue_unlocked", 0.0),
            # stories
            top_backlog_stories=obs_data.get("top_backlog_stories", []),
            current_sprint_stories=obs_data.get("current_sprint_stories", []),
            # openenv required
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )