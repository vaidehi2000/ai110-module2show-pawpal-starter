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

## Smarter Scheduling

PawPal+ goes beyond a simple task list with five algorithmic features built into the `Scheduler` class:

### Sort by time slot
`sort_by_time(tasks)` returns tasks ordered **morning → afternoon → evening → unspecified** using Python's `sorted()` with a lambda key. The original list is never mutated, so it is safe to call on any subset of tasks without side effects. The generated daily plan is also automatically re-sorted by slot after the greedy budget pass.

### Filter by pet or status
`filter_tasks(pet_name, completed)` lets you slice the full task list by pet name, completion status, or both. Both parameters are optional — pass neither to return everything, or combine them to get (for example) only Mochi's pending tasks.

### Recurring tasks with auto-scheduling
Tasks can be marked `recurrence="daily"` or `recurrence="weekly"`. When you call `complete_task(task)`, the scheduler marks the task done and automatically creates the next occurrence using `datetime.timedelta` — `+1 day` for daily, `+7 days` for weekly — then registers it under the same pet. No manual re-entry required.

### Slot conflict detection
`detect_conflicts()` checks the scheduled plan for per-pet, per-slot budget overflows. If a pet's combined task duration in a single slot (morning / afternoon / evening) exceeds 4 hours, a warning is returned — without crashing or blocking the rest of the schedule from displaying.

### Exact time-overlap detection
`detect_time_conflicts(tasks)` checks every pair of tasks that have an explicit `start_time` set (in `HH:MM` format) for true window overlap using the condition `A.start < B.end AND B.start < A.end`. This catches all four overlap shapes (partial, full containment, identical start) in a single expression and flags both same-pet and cross-pet conflicts with a human-readable warning string.

---

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
