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

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

Beyond the basic greedy planner, `pawpal_system.py` includes four algorithmic features:

| Feature | Method | How it works |
|---|---|---|
| **Sort by time** | `Scheduler.sort_by_time(tasks)` | Sorts any task list by `start_time` (HH:MM) ascending; untimed tasks go last. |
| **Filter tasks** | `Scheduler.filter_tasks(pet_name, completed)` | Returns tasks matching an optional pet name and/or completion status. Both filters can be combined or omitted. |
| **Recurring tasks** | `Task.mark_complete()` / `Scheduler.complete_task(pet, task)` | A task with `frequency="daily"` or `"weekly"` returns its next occurrence when completed. `complete_task()` automatically appends that occurrence to the pet so it appears in tomorrow's schedule. |
| **Conflict detection** | `Scheduler.detect_conflicts(schedule)` | Compares every pair of tasks that have an explicit `start_time`. Returns a list of human-readable warning strings for any overlapping time windows. Returns `[]` when the schedule is clean. |

`generate_schedule()` assigns sequential start times (default first slot: `08:00`) so the full schedule is always ready for time-based display or conflict checking.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
# or for verbose output:
python -m pytest -v
```

**42 tests** across five areas:

| Area | # tests | What is verified |
|---|---|---|
| Core model | 7 | `Task.mark_complete()`, `Pet.add_task()` / `get_tasks()`, `Owner.get_all_tasks()` |
| Scheduler | 6 | Time budget (exact-fit, one-minute-over), priority ordering, completed-task exclusion, start-time assignment |
| Sort & filter | 6 | Chronological order, untimed-last, filter by pet name / completion status / both, empty-list safety |
| Recurring tasks | 6 | Daily/weekly next-occurrence date, attribute inheritance, `complete_task()` auto-append, non-recurring no-op |
| Conflict detection | 5 | Two-task overlap, no overlap, adjacent (touching) tasks, untimed tasks ignored, three-way pairwise warnings |
| Edge cases | 12 | Empty owner, all tasks completed, unknown pet name, zero-budget, pet with no tasks, `explain_plan` on empty schedule |

**Confidence level: ★★★★☆**
Core scheduling logic and all algorithmic features are fully tested. The Streamlit UI layer has no automated tests and is verified manually.
