"""
Inference Script — Product Management OpenEnv
=============================================
MANDATORY VARIABLES:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
"""

import os
import sys
import asyncio
import textwrap
from typing import List, Optional

from openai import OpenAI

# add parent path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.product_mgmt_env_environment import ProductMgmtEnvironment
from models import ProductMgmtAction

# ── environment variables ─────────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "product_mgmt_env"
MAX_STEPS = 30
TEMPERATURE = 0.3
MAX_TOKENS = 200
SUCCESS_SCORE_THRESHOLD = 0.7

# ── logging helpers ───────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── system prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
    You are an AI Product Manager. You manage a software product backlog.
    Each turn you must choose ONE action from:
        0 = ADD_TO_SPRINT  (add a story to current sprint)
        1 = DEFER          (lower a story's priority)
        2 = REMOVE         (remove a story from sprint)
        3 = RELEASE        (ship current sprint)

    Rules:
    - Fix bugs early to avoid technical debt
    - Don't overfill team capacity
    - Release when sprint is full or deadline is close
    - Prioritize high value, high priority stories

    Reply with ONLY two integers on one line:
        <decision> <story_id>
    Example: 0 3
    For RELEASE use: 3 -1
""").strip()


# ── user prompt builder ───────────────────────────────────────────────────────

def build_prompt(obs) -> str:
    backlog_str = "\n".join([
        f"  id={s['id']} priority={s['priority']} effort={s['effort']} value={s['value']} bug={s['is_bug']} title={s['title']}"
        for s in obs.top_backlog_stories
    ]) or "  (empty)"

    sprint_str = "\n".join([
        f"  id={s['id']} effort={s['effort']} value={s['value']} title={s['title']}"
        for s in obs.current_sprint_stories
    ]) or "  (empty)"

    return textwrap.dedent(f"""
        Step: {obs.step}/{obs.max_steps}
        Sprint: {obs.sprint_number}
        Team capacity: {obs.used_capacity}/{obs.team_capacity} points used
        Deadline pressure: {obs.deadline_pressure:.2f}
        Technical debt: {obs.technical_debt:.2f}
        Stakeholder satisfaction: {obs.stakeholder_satisfaction:.2f}
        Revenue unlocked: {obs.revenue_unlocked:.2f}

        Backlog (top 5):
{backlog_str}

        Current sprint:
{sprint_str}

        What is your next action? Reply with: <decision> <story_id>
    """).strip()


# ── LLM call ──────────────────────────────────────────────────────────────────

def get_action(client: OpenAI, obs) -> ProductMgmtAction:
    prompt = build_prompt(obs)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()

        # parse response — expect "decision story_id"
        parts = text.split()
        decision = int(parts[0])
        story_id = int(parts[1]) if len(parts) > 1 else -1

        # validate decision range
        if decision not in [0, 1, 2, 3]:
            decision = 2  # default to HOLD

        return ProductMgmtAction(decision=decision, story_id=story_id)

    except Exception as e:
        print(f"[DEBUG] LLM parse error: {e} | response: {text if 'text' in dir() else 'N/A'}", flush=True)
        # fallback greedy action
        if obs.top_backlog_stories:
            story = min(obs.top_backlog_stories, key=lambda s: s["priority"])
            used = obs.used_capacity
            if used + story["effort"] <= obs.team_capacity:
                return ProductMgmtAction(decision=0, story_id=story["id"])
        if obs.current_sprint_stories:
            return ProductMgmtAction(decision=3, story_id=-1)
        return ProductMgmtAction(decision=1, story_id=-1)


# ── run one task ──────────────────────────────────────────────────────────────

def run_task(client: OpenAI, task: str) -> dict:
    from graders.easy_grader import EasyGrader
    from graders.medium_grader import MediumGrader
    from graders.hard_grader import HardGrader

    grader = {
        "easy": EasyGrader(),
        "medium": MediumGrader(),
        "hard": HardGrader(),
    }[task]

    env = ProductMgmtEnvironment(task=task, seed=42)
    obs = env.reset()

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    try:
        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            action = get_action(client, obs)
            action_str = f"decision={action.decision},story_id={action.story_id}"

            obs = env.step(action)

            reward = obs.reward or 0.0
            done = obs.done
            rewards.append(reward)
            steps_taken = step

            log_step(
                step=step,
                action=action_str,
                reward=reward,
                done=done,
                error=None,
            )

            if done:
                break

        # grade the episode
        result = {
            "task": task,
            "completed": obs.completed_count,
            "revenue_unlocked": obs.revenue_unlocked,
            "stakeholder_satisfaction": obs.stakeholder_satisfaction,
            "technical_debt": obs.technical_debt,
            "total_reward": sum(rewards),
        }
        grade = grader.grade(result)
        score = grade["score"]
        success = grade["passed"]

    except Exception as e:
        print(f"[DEBUG] Task error: {e}", flush=True)

    finally:
        log_end(
            success=success,
            steps=steps_taken,
            score=score,
            rewards=rewards,
        )

    return {"task": task, "score": score, "success": success}


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    tasks = ["easy", "medium", "hard"]
    all_results = []

    for task in tasks:
        result = run_task(client, task)
        all_results.append(result)

    # final summary
    avg = sum(r["score"] for r in all_results) / len(all_results)
    print(f"\n[SUMMARY] easy={all_results[0]['score']:.3f} medium={all_results[1]['score']:.3f} hard={all_results[2]['score']:.3f} avg={avg:.3f}", flush=True)


if __name__ == "__main__":
    main()



