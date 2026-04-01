from dataclasses import dataclass, field
from typing import Optional

# Maps priority labels to sortable integers (higher = more important).
# Using a constant avoids silent bugs when sorting by the raw string,
# where alphabetical order ("high" < "low" < "medium") is incorrect.
PRIORITY_ORDER: dict[str, int] = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    title: str
    category: str           # walk | feed | medication | grooming | enrichment
    duration_minutes: int
    priority: str           # low | medium | high
    pet_name: str = ""      # which pet this task belongs to
    preferred_time: Optional[str] = None    # e.g. "morning", "evening"
    is_completed: bool = False

    @property
    def numeric_priority(self) -> int:
        """Returns a sortable integer so tasks can be ranked high → low."""
        return PRIORITY_ORDER.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as done so the scheduler skips it in future runs."""
        self.is_completed = True

    def to_dict(self) -> dict:
        """Serialize all task fields to a plain dict for display or storage."""
        return {
            "title": self.title,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "pet_name": self.pet_name,
            "preferred_time": self.preferred_time,
            "is_completed": self.is_completed,
        }


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet, stamping pet_name if not already set."""
        if not task.pet_name:
            task.pet_name = self.name
        self.tasks.append(task)

    def get_profile(self) -> str:
        """Returns a one-line summary of the pet for display."""
        needs = ", ".join(self.special_needs) if self.special_needs else "none"
        return f"{self.name} ({self.species}, age {self.age}) — special needs: {needs}"

    def requires_medication(self) -> bool:
        """Returns True if any special need implies a medication task."""
        medication_flags = {"diabetic", "epileptic", "thyroid", "medication", "meds"}
        return bool(medication_flags.intersection(self.special_needs))


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: dict = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: dict = preferences or {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner so its tasks are visible to the Scheduler."""
        self.pets.append(pet)

    def get_total_available_time(self) -> int:
        """Return the owner's daily time budget in minutes for the Scheduler to consume."""
        return self.available_minutes


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduled_plan: list[Task] = []
        self.explanations: list[str] = []

    def _collect_tasks(self) -> list[Task]:
        """Gather all incomplete tasks from every pet the owner has."""
        all_tasks = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                if not task.is_completed:
                    all_tasks.append(task)
        return all_tasks

    def add_task(self, task: Task) -> None:
        """Add a task directly to the matching pet by pet_name."""
        for pet in self.owner.pets:
            if pet.name == task.pet_name:
                pet.add_task(task)
                return
        raise ValueError(
            f"No pet named '{task.pet_name}' found. "
            f"Add the pet to the owner first."
        )

    def generate_plan(self) -> list[Task]:
        """
        Build a daily plan using a greedy priority-first strategy:
          1. Collect all incomplete tasks across all pets.
          2. Sort by priority descending, then by duration ascending as a
             tiebreaker (shorter high-priority tasks are scheduled first).
          3. Greedily add tasks until the time budget is exhausted.
          4. Record an explanation for every task (included or skipped).
        """
        self.scheduled_plan = []
        self.explanations = []

        candidates = sorted(
            self._collect_tasks(),
            key=lambda t: (-t.numeric_priority, t.duration_minutes),
        )

        remaining_minutes = self.owner.get_total_available_time()

        for task in candidates:
            if task.duration_minutes <= remaining_minutes:
                self.scheduled_plan.append(task)
                remaining_minutes -= task.duration_minutes
                self.explanations.append(
                    f"INCLUDED  '{task.title}' ({task.pet_name}) — "
                    f"priority: {task.priority}, duration: {task.duration_minutes} min. "
                    f"Time remaining after: {remaining_minutes} min."
                )
            else:
                self.explanations.append(
                    f"SKIPPED   '{task.title}' ({task.pet_name}) — "
                    f"needs {task.duration_minutes} min but only {remaining_minutes} min left."
                )

        return self.scheduled_plan

    def explain_plan(self) -> str:
        """Return the reasoning log produced by the last generate_plan() call."""
        if not self.explanations:
            return "No plan has been generated yet. Call generate_plan() first."
        header = f"Daily plan for {self.owner.name} ({self.owner.available_minutes} min available):\n"
        return header + "\n".join(self.explanations)
