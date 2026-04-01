import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task


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
