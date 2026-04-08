---
title: Product Mgmt OpenEnv
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_file: server/app.py
---
# Product Management OpenEnv

An AI agent environment where the agent manages a software product backlog,
plans sprints, and optimizes releases under deadlines and team capacity constraints.

Built on the [OpenEnv](https://huggingface.co/openenv) framework by Meta + Hugging Face.

---

## Environment Description

The agent acts as a Product Manager. Each episode simulates one product cycle
across 30 steps. The agent must:

- Prioritize stories from a backlog
- Fill sprints within team capacity
- Fix bugs before technical debt grows
- Release value before the deadline
- Keep stakeholder satisfaction high

---

## Action Space

| Decision | Value | Description |
|---|---|---|
| ADD_TO_SPRINT | 0 | Move a story from backlog into current sprint |
| DEFER | 1 | Push a story lower in priority |
| REMOVE | 2 | Remove a story from sprint back to backlog |
| RELEASE | 3 | Close current sprint and ship completed stories |

Each action also takes a `story_id` (int) to identify which story to act on.
Use `story_id=-1` for RELEASE.

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| sprint_number | int | Current sprint number |
| step | int | Current step in episode |
| max_steps | int | Maximum steps per episode (30) |
| team_capacity | int | Total story points available |
| used_capacity | int | Story points already assigned |
| backlog_count | int | Stories waiting in backlog |
| sprint_count | int | Stories in current sprint |
| completed_count | int | Total completed stories |
| deadline_pressure | float | 0.0=relaxed, 1.0=critical |
| technical_debt | float | 0.0=clean, 1.0=very high |
| stakeholder_satisfaction | float | 0.0–1.0 |
| revenue_unlocked | float | Total business value delivered |
| top_backlog_stories | list[dict] | Top 5 backlog stories |
| current_sprint_stories | list[dict] | Stories currently in sprint |

---

## Reward Function

| Event | Reward |
|---|---|
| Adding high priority story (priority 1-2) | +0.4 |
| Adding a bug fix | +0.3 |
| Adding high value story (value >= 0.7) | +0.2 |
| Acting under deadline pressure | +0.1 |
| Successful release with high value | +0.5 |
| Good stakeholder satisfaction | +0.1 |
| Overfilling sprint capacity | -0.2 |
| Ignoring bugs under deadline | -0.3 |
| Deferring high priority story | -0.2 |
| Removing high value story | -0.4 |
| High technical debt | -0.2 |
| Low stakeholder satisfaction | -0.3 |

Reward is clamped between -1.0 and 1.0.

---

## Tasks

| Task | Scenario | Passing Score |
|---|---|---|
| easy | Small backlog, relaxed deadline, high capacity | 0.7 |
| medium | Larger backlog, moderate pressure, bugs mixed in | 0.75 |
| hard | Large backlog, critical deadline, low capacity | 0.8 |

---

## Baseline Scores (Greedy Agent, seed=42)

| Task | Score | Passed |
|---|---|---|
| Easy | 0.9274 | ✓ YES |
| Medium | 0.8592 | ✓ YES |
| Hard | 0.6932 | ✗ NO |
| Average | 0.8266 | — |

---

## Setup Instructions

### Requirements
- Python 3.10+
- Git
- Docker (for deployment)
- Hugging Face account

### Installation
```bash
# clone the OpenEnv repo
git clone https://github.com/meta-pytorch/OpenEnv.git
cd OpenEnv/product_mgmt_env

# create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# install dependencies
pip install openenv-core
pip install -r server/requirements.txt
```

### Run Baseline
```bash
python baseline/run_baseline.py
```

### Run Server Locally
```bash
cd server
uvicorn app:app --reload --port 8000
```

### Run with Docker
```bash
docker build -t product-mgmt-env -f server/Dockerfile .
docker run -p 8000:8000 product-mgmt-env
```

### Connect Agent
```python
from product_mgmt_env import ProductMgmtEnv, ProductMgmtAction

with ProductMgmtEnv(base_url="http://localhost:8000") as env:
    obs = env.reset()

    while not obs.done:
        action = ProductMgmtAction(decision=0, story_id=1)
        result = env.step(action)
        obs = result.observation
        print(f"Reward: {result.reward}")
```

---

## Project Structure
```
product_mgmt_env/
├── server/
│   ├── app.py                          # FastAPI server
│   ├── product_mgmt_env_environment.py # Environment logic
│   ├── requirements.txt
│   └── Dockerfile
├── tasks/
│   ├── task_easy.py                    # Easy task
│   ├── task_medium.py                  # Medium task
│   └── task_hard.py                    # Hard task
├── graders/
│   ├── base_grader.py                  # Base grader
│   ├── easy_grader.py                  # Easy grader
│   ├── medium_grader.py                # Medium grader
│   └── hard_grader.py                  # Hard grader
├── baseline/
│   └── run_baseline.py                 # Baseline inference script
├── models.py                           # Typed Action + Observation
├── client.py                           # Agent client
├── openenv.yaml                        # OpenEnv spec
└── README.md
```

---

## License

BSD — see LICENSE file in the root directory.