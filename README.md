# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond the basic daily plan, `pawpal_system.py` includes several algorithms that make the scheduler more intelligent:

| Feature | Method | Description |
|---|---|---|
| **Priority + time-of-day sort** | `generate_plan` | Sorts pending tasks by priority first, then morning → afternoon → evening, then shortest duration as a tiebreaker — maximises tasks completed in the available window |
| **HH:MM clock sort** | `sort_by_time` | Orders tasks by their `start_time` field using zero-padded string comparison; tasks without a start time sink to the end |
| **Status filtering** | `filter_by_status` | Returns only `pending` or `completed` tasks — used to show "what's left today" vs "what's done" |
| **Recurring task spawning** | `complete_task` / `spawn_next` | When a recurring task is marked complete, a fresh copy is automatically created with its `due_date` advanced using `timedelta` (daily +1 day, weekly +7 days) |
| **Time-overlap detection** | `detect_time_overlaps` | Uses a sort-then-sweep algorithm (O(n log n)) to find pairs of tasks whose scheduled windows overlap, returning human-readable warnings without crashing |
| **Multi-level conflict check** | `check_conflicts` | Combines four independent checks: total time overflow, single task too long to fit, high-priority tasks at risk of exclusion, and time-window overlaps |

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
