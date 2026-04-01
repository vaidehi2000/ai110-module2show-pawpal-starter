import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import Pet, Task, Owner, Scheduler


def test_mark_complete_changes_status():
    """mark_complete() should flip is_completed from False to True."""
    task = Task(title="Morning walk", category="walk", duration_minutes=30, priority="high")

    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog", age=3)

    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Breakfast", category="feed", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should order tasks morning → afternoon → evening → None."""
    owner = Owner(name="Alex", available_minutes=300)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    evening_task   = Task(title="Evening walk",   category="walk",  duration_minutes=30, priority="low",    preferred_time="evening")
    morning_task   = Task(title="Morning feed",   category="feed",  duration_minutes=10, priority="high",   preferred_time="morning")
    afternoon_task = Task(title="Afternoon meds", category="medication", duration_minutes=5, priority="medium", preferred_time="afternoon")
    no_slot_task   = Task(title="Anytime groom",  category="grooming",   duration_minutes=20, priority="low")

    tasks = [evening_task, morning_task, afternoon_task, no_slot_task]
    sorted_tasks = scheduler.sort_by_time(tasks)

    slots = [t.preferred_time for t in sorted_tasks]
    assert slots == ["morning", "afternoon", "evening", None]


def test_sort_by_time_does_not_mutate_input():
    """sort_by_time() must return a new list and leave the original unchanged."""
    owner = Owner(name="Alex", available_minutes=300)
    scheduler = Scheduler(owner)

    tasks = [
        Task(title="Evening walk", category="walk", duration_minutes=30, priority="low", preferred_time="evening"),
        Task(title="Morning feed", category="feed", duration_minutes=10, priority="high", preferred_time="morning"),
    ]
    original_order = [t.title for t in tasks]
    scheduler.sort_by_time(tasks)

    assert [t.title for t in tasks] == original_order


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_day_occurrence():
    """Completing a daily task should add a new task due the following day."""
    owner = Owner(name="Alex", available_minutes=300)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    today = date.today()
    meds = Task(
        title="Thyroid meds",
        category="medication",
        duration_minutes=5,
        priority="high",
        pet_name="Mochi",
        recurrence="daily",
        due_date=today,
    )
    pet.add_task(meds)

    next_task = scheduler.complete_task(meds)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.is_completed is False
    assert next_task.title == meds.title


def test_complete_nonrecurring_task_returns_none():
    """Completing a task with no recurrence should return None (no follow-up)."""
    owner = Owner(name="Alex", available_minutes=300)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    walk = Task(title="One-off walk", category="walk", duration_minutes=30, priority="medium", pet_name="Mochi")
    pet.add_task(walk)

    result = scheduler.complete_task(walk)

    assert result is None
    assert walk.is_completed is True


def test_next_occurrence_crosses_month_boundary():
    """next_occurrence() on Jan 31 should produce Feb 1, not crash."""
    task = Task(
        title="Daily feed",
        category="feed",
        duration_minutes=10,
        priority="high",
        recurrence="daily",
        due_date=date(2025, 1, 31),
    )
    nxt = task.next_occurrence()

    assert nxt is not None
    assert nxt.due_date == date(2025, 2, 1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_time_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap should produce a conflict warning."""
    owner = Owner(name="Alex", available_minutes=300)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    task_a = Task(title="Walk",  category="walk",     duration_minutes=60, priority="high",   pet_name="Mochi", start_time="08:00")
    task_b = Task(title="Feed",  category="feed",     duration_minutes=30, priority="medium", pet_name="Mochi", start_time="08:30")
    scheduler.scheduled_plan = [task_a, task_b]

    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


def test_detect_time_conflicts_ignores_back_to_back_tasks():
    """Tasks that are adjacent (not overlapping) should NOT be flagged."""
    owner = Owner(name="Alex", available_minutes=300)
    pet = Pet(name="Mochi", species="dog", age=3)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    task_a = Task(title="Walk", category="walk", duration_minutes=30, priority="high",   pet_name="Mochi", start_time="08:00")
    task_b = Task(title="Feed", category="feed", duration_minutes=30, priority="medium", pet_name="Mochi", start_time="08:30")
    scheduler.scheduled_plan = [task_a, task_b]

    warnings = scheduler.detect_time_conflicts()

    assert warnings == []


def test_detect_conflicts_slot_budget_is_per_pet():
    """Slot budget overflow for one pet should not flag a different pet's tasks."""
    owner = Owner(name="Alex", available_minutes=1000)
    mochi = Pet(name="Mochi", species="dog", age=3)
    rex   = Pet(name="Rex",   species="dog", age=5)
    owner.add_pet(mochi)
    owner.add_pet(rex)
    scheduler = Scheduler(owner)

    # Each pet has 200 min in the morning — under the 240-min budget individually.
    scheduler.scheduled_plan = [
        Task(title="Mochi task 1", category="walk", duration_minutes=120, priority="high",   pet_name="Mochi", preferred_time="morning"),
        Task(title="Mochi task 2", category="feed", duration_minutes=80,  priority="medium", pet_name="Mochi", preferred_time="morning"),
        Task(title="Rex task 1",   category="walk", duration_minutes=120, priority="high",   pet_name="Rex",   preferred_time="morning"),
        Task(title="Rex task 2",   category="feed", duration_minutes=80,  priority="medium", pet_name="Rex",   preferred_time="morning"),
    ]

    warnings = scheduler.detect_conflicts()

    assert warnings == []
