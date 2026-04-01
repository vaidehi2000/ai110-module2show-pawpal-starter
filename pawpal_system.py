from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import Optional

# Maps priority labels to sortable integers (higher = more important).
# Using a constant avoids silent bugs when sorting by the raw string,
# where alphabetical order ("high" < "low" < "medium") is incorrect.
PRIORITY_ORDER: dict[str, int] = {"low": 1, "medium": 2, "high": 3}

# Maps preferred_time labels to display order (None/unspecified sorts last).
TIME_SLOT_ORDER: dict[str, int] = {"morning": 0, "afternoon": 1, "evening": 2}

# Maximum minutes allowed per pet per named time slot before a conflict is flagged.
SLOT_BUDGET_MINUTES: dict[str, int] = {"morning": 240, "afternoon": 240, "evening": 240}


@dataclass
class Task:
    title: str
    category: str           # walk | feed | medication | grooming | enrichment
    duration_minutes: int
    priority: str           # low | medium | high
    pet_name: str = ""      # which pet this task belongs to
    preferred_time: Optional[str] = None    # e.g. "morning", "evening"
    is_completed: bool = False
    recurrence: Optional[str] = None   # "daily" | "weekly" | None
    due_date: Optional[date] = None    # set automatically on recurring tasks
    start_time: Optional[str] = None   # explicit wall-clock start, e.g. "08:00" (HH:MM)

    @property
    def numeric_priority(self) -> int:
        """Returns a sortable integer so tasks can be ranked high → low."""
        return PRIORITY_ORDER.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as done so the scheduler skips it in future runs."""
        self.is_completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Create a fresh copy of this task scheduled for its next due date.

        Uses ``datetime.timedelta`` so month-boundary and leap-year arithmetic
        is handled correctly by Python's date library rather than manual math.
        The new instance inherits every field unchanged except ``is_completed``
        (reset to False) and ``due_date`` (advanced by the recurrence interval).

        Returns:
            A new Task with ``is_completed=False`` and an updated ``due_date``:
            - ``"daily"``  → current due_date + 1 day
            - ``"weekly"`` → current due_date + 7 days
            None if this task has no recurrence set.

        Example:
            nxt = task.next_occurrence()
            if nxt:
                scheduler.add_task(nxt)
        """
        if not self.recurrence:
            return None

        base = self.due_date if self.due_date else date.today()

        if self.recurrence == "daily":
            next_due = base + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_due = base + timedelta(weeks=1)
        else:
            return None

        # dataclasses.replace() copies every field, then overrides the ones
        # we specify — so the new task inherits title, category, duration,
        # priority, pet_name, preferred_time, and recurrence unchanged.
        return replace(self, is_completed=False, due_date=next_due)

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
            "recurrence": self.recurrence,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "start_time": self.start_time,
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

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks into chronological slot order without mutating the input.

        Uses ``sorted()`` with a lambda key that maps each task's
        ``preferred_time`` string to its integer rank in ``TIME_SLOT_ORDER``
        (morning=0, afternoon=1, evening=2), falling back to 3 so tasks with
        no preferred time are placed at the end.

        Args:
            tasks: Any list of Task objects to sort. The original list is
                not modified — a new sorted list is returned.

        Returns:
            A new list ordered morning → afternoon → evening → unspecified.
        """
        return sorted(tasks, key=lambda t: TIME_SLOT_ORDER.get(t.preferred_time, 3))

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Return a filtered subset of tasks across all pets owned by this owner.

        Both parameters are optional and combinable: pass both to filter by pet
        *and* status simultaneously; pass neither to return all tasks unfiltered.

        Args:
            pet_name: If provided, keep only tasks whose ``pet_name`` matches
                this string exactly. Pass ``None`` to include all pets.
            completed: If ``True``, return only completed tasks. If ``False``,
                return only pending tasks. If ``None`` (default), return tasks
                regardless of completion status.

        Returns:
            A new list of Task objects matching all supplied criteria. The
            original pet task lists are not modified.
        """
        all_tasks = [t for pet in self.owner.pets for t in pet.tasks]

        if pet_name is not None:
            all_tasks = [t for t in all_tasks if t.pet_name == pet_name]

        if completed is not None:
            all_tasks = [t for t in all_tasks if t.is_completed == completed]

        return all_tasks

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task done and auto-schedule its next occurrence if it recurs.

        Combines two operations atomically: marking the task complete and, for
        recurring tasks, calling ``task.next_occurrence()`` to create the follow-
        up instance and immediately registering it under the same pet via
        ``add_task()``. Non-recurring tasks are simply marked done.

        Args:
            task: The Task to complete. Must already belong to a pet registered
                with this scheduler's owner, as the next occurrence is added via
                ``add_task()`` which looks up the pet by name.

        Returns:
            The newly created follow-up Task if the completed task recurs
            (``"daily"`` or ``"weekly"``), otherwise ``None``.

        Example:
            nxt = scheduler.complete_task(thyroid_meds)
            if nxt:
                print(f"Next dose due: {nxt.due_date}")
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task:
            self.add_task(next_task)
        return next_task

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

        # Re-sort the final plan by time slot so the output reads
        # morning → afternoon → evening → unspecified, while the greedy
        # priority-based budget logic above is left completely intact.
        self.scheduled_plan.sort(
            key=lambda t: TIME_SLOT_ORDER.get(t.preferred_time, 3)
        )

        return self.scheduled_plan

    def detect_conflicts(self) -> list[str]:
        """
        Check the current scheduled_plan for per-pet, per-slot overflows.
        A conflict is when the combined duration of tasks for the same pet
        in the same named time slot exceeds SLOT_BUDGET_MINUTES for that slot.
        Tasks with no preferred_time are never flagged.
        Returns a (possibly empty) list of human-readable warning strings.
        """
        from collections import defaultdict

        # buckets[pet_name][slot] = [task, ...]
        buckets: dict = defaultdict(lambda: defaultdict(list))
        for task in self.scheduled_plan:
            if task.preferred_time:
                buckets[task.pet_name][task.preferred_time].append(task)

        warnings: list[str] = []
        for pet_name, slots in buckets.items():
            for slot, tasks in slots.items():
                total = sum(t.duration_minutes for t in tasks)
                budget = SLOT_BUDGET_MINUTES.get(slot, None)
                if budget is not None and total > budget:
                    titles = ", ".join(f"'{t.title}'" for t in tasks)
                    warnings.append(
                        f"{pet_name} has {total} min of tasks in the {slot} slot "
                        f"(budget: {budget} min). Tasks: {titles}."
                    )
        return warnings

    @staticmethod
    def _to_minutes(time_str: str) -> int:
        """Convert an ``'HH:MM'`` wall-clock string to minutes since midnight.

        Used internally by ``detect_time_conflicts()`` so that two time strings
        can be compared and subtracted as plain integers rather than datetime
        objects, keeping the conflict check arithmetic simple.

        Args:
            time_str: A string in ``'HH:MM'`` 24-hour format, e.g. ``'09:30'``.

        Returns:
            An integer representing minutes elapsed since midnight.
            For example, ``'09:30'`` → 570, ``'14:00'`` → 840.

        Raises:
            ValueError: If ``time_str`` cannot be split on ``':'`` or either
                part is not an integer, with a message showing the bad value
                and the expected format.
        """
        try:
            h, m = time_str.split(":")
            return int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid start_time '{time_str}' — expected 'HH:MM' format (e.g. '09:00')."
            )

    def detect_time_conflicts(self, tasks: Optional[list[Task]] = None) -> list[str]:
        """Detect overlapping time windows across any pair of scheduled tasks.

        A lightweight, non-throwing conflict detector: problems are reported as
        human-readable warning strings rather than exceptions, so the schedule
        can still be displayed even when conflicts are present.

        Only tasks with an explicit ``start_time`` (``'HH:MM'``) are checked;
        slot-only tasks (``preferred_time`` without ``start_time``) are skipped.
        Two tasks conflict when their windows overlap using the condition::

            A.start < B.end  AND  B.start < A.end

        This single expression covers all four overlap shapes: partial overlap,
        full containment, and identical start times.

        Args:
            tasks: The list of Task objects to check for conflicts. Defaults to
                ``self.scheduled_plan`` when ``None``, but any ad-hoc list can
                be passed so the check can run without generating a full plan.

        Returns:
            A list of warning strings (possibly empty). Each string identifies
            the two conflicting tasks, their pets, and their exact time windows.
            Labels the conflict as ``"same pet"`` or ``"different pets"`` so
            the owner knows which animals are affected.
        """
        candidates = [t for t in (tasks if tasks is not None else self.scheduled_plan)
                      if t.start_time]

        from itertools import combinations

        warnings: list[str] = []

        # combinations(candidates, 2) yields every unique (a, b) pair without
        # repetition — clearer intent and avoids the manual index arithmetic of
        # range(i+1, len(...)) that a nested loop would require.
        for a, b in combinations(candidates, 2):
            a_start = self._to_minutes(a.start_time)
            a_end   = a_start + a.duration_minutes
            b_start = self._to_minutes(b.start_time)
            b_end   = b_start + b.duration_minutes

            if a_start < b_end and b_start < a_end:
                scope = "same pet" if a.pet_name == b.pet_name else "different pets"
                warnings.append(
                    f"WARNING ({scope}): '{a.title}' [{a.pet_name}] "
                    f"{a.start_time}–{a_end // 60:02d}:{a_end % 60:02d} "
                    f"overlaps '{b.title}' [{b.pet_name}] "
                    f"{b.start_time}–{b_end // 60:02d}:{b_end % 60:02d}."
                )

        return warnings

    def explain_plan(self) -> str:
        """Return the reasoning log produced by the last generate_plan() call."""
        if not self.explanations:
            return "No plan has been generated yet. Call generate_plan() first."
        header = f"Daily plan for {self.owner.name} ({self.owner.available_minutes} min available):\n"
        return header + "\n".join(self.explanations)
