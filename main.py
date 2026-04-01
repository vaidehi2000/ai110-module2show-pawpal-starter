from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=120, preferences={"prefers_morning_walks": True})

mochi   = Pet(name="Mochi",   species="dog", age=3)
biscuit = Pet(name="Biscuit", species="cat", age=7, special_needs=["medication"])

owner.add_pet(mochi)
owner.add_pet(biscuit)

# --- Tasks added intentionally OUT OF TIME ORDER to exercise sort_by_time() ---

# Mochi: evening first, then no slot, then morning, then afternoon
mochi.add_task(Task(title="Evening walk",   category="walk",       duration_minutes=25, priority="medium", preferred_time="evening"))
mochi.add_task(Task(title="Breakfast",      category="feed",       duration_minutes=10, priority="high"))          # no slot
mochi.add_task(Task(title="Morning walk",   category="walk",       duration_minutes=30, priority="high",   preferred_time="morning"))
mochi.add_task(Task(title="Fetch session",  category="enrichment", duration_minutes=20, priority="low",    preferred_time="afternoon"))

# Biscuit: afternoon first, then morning, then no slot
biscuit.add_task(Task(title="Grooming",     category="grooming",   duration_minutes=25, priority="medium", preferred_time="afternoon"))
biscuit.add_task(Task(title="Thyroid meds", category="medication", duration_minutes=5,  priority="high",   preferred_time="morning",
                      recurrence="daily",  due_date=date.today()))
biscuit.add_task(Task(title="Lunch feed",   category="feed",       duration_minutes=10, priority="high",
                      recurrence="weekly", due_date=date.today()))

# Mark one non-recurring task complete so filter_tasks(completed=...) has something to show
mochi.tasks[1].mark_complete()   # "Breakfast" is done (non-recurring, no next occurrence)

# --- Scheduler ---
scheduler = Scheduler(owner=owner)

# ── Demo 1: sort_by_time ─────────────────────────────────────────────────────
all_tasks = [t for pet in owner.pets for t in pet.tasks]
sorted_tasks = scheduler.sort_by_time(all_tasks)

print("=" * 54)
print("  sort_by_time()  —  all tasks ordered by slot")
print("=" * 54)
for t in sorted_tasks:
    slot = t.preferred_time or "(no slot)"
    print(f"  [{slot:10s}]  {t.pet_name:8s}  {t.title}")

# ── Demo 2: filter_tasks by pet ──────────────────────────────────────────────
print()
print("=" * 54)
print("  filter_tasks(pet_name='Mochi')")
print("=" * 54)
for t in scheduler.filter_tasks(pet_name="Mochi"):
    status = "done" if t.is_completed else "pending"
    print(f"  [{status:7s}]  {t.title}")

# ── Demo 3: filter_tasks by completion status ────────────────────────────────
print()
print("=" * 54)
print("  filter_tasks(completed=False)  —  pending tasks only")
print("=" * 54)
for t in scheduler.filter_tasks(completed=False):
    print(f"  {t.pet_name:8s}  {t.title}")

print()
print("=" * 54)
print("  filter_tasks(completed=True)  —  completed tasks only")
print("=" * 54)
for t in scheduler.filter_tasks(completed=True):
    print(f"  {t.pet_name:8s}  {t.title}")

# ── Demo 4: generate_plan (uses sort_by_time internally) ────────────────────
plan = scheduler.generate_plan()

print()
print("=" * 54)
print(f"  Today's Schedule for {owner.name}")
print(f"  Time budget: {owner.available_minutes} minutes")
print("=" * 54)

if not plan:
    print("  No tasks could be scheduled within the available time.")
else:
    total = 0
    for i, task in enumerate(plan, start=1):
        slot   = f"[{task.preferred_time}]" if task.preferred_time else "[any time]"
        recur  = f"  repeats {task.recurrence}" if task.recurrence else ""
        print(f"{i}. {slot:12s}  [{task.pet_name}] {task.title}{recur}")
        print(f"   {task.category}  |  {task.priority} priority  |  {task.duration_minutes} min")
        total += task.duration_minutes

    print("-" * 54)
    print(f"  Total: {total} min / {owner.available_minutes} min available")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print()
        print("  !! Conflicts detected:")
        for msg in conflicts:
            print(f"  - {msg}")

print()
print("--- Scheduler Reasoning ---")
print(scheduler.explain_plan())

# ── Demo 5: complete_task() with recurring tasks ─────────────────────────────
print()
print("=" * 54)
print("  complete_task()  —  recurring task auto-scheduling")
print("=" * 54)

# Collect the two recurring tasks by name for the demo
thyroid = next(t for t in biscuit.tasks if t.title == "Thyroid meds")
lunch   = next(t for t in biscuit.tasks if t.title == "Lunch feed")

for task in (thyroid, lunch):
    print(f"\n  Completing: '{task.title}' (recurrence={task.recurrence}, due={task.due_date})")
    nxt = scheduler.complete_task(task)
    print(f"  Marked complete:  is_completed={task.is_completed}")
    if nxt:
        print(f"  Next occurrence:  due={nxt.due_date}  (added to {nxt.pet_name}'s task list)")
    else:
        print("  No next occurrence (non-recurring).")

# Confirm Biscuit's updated task list shows both the completed originals
# and the newly generated pending occurrences
print()
print("  Biscuit's full task list after completions:")
for t in biscuit.tasks:
    status = "done   " if t.is_completed else "pending"
    due    = f"  due {t.due_date}" if t.due_date else ""
    recur  = f"  [{t.recurrence}]" if t.recurrence else ""
    print(f"  [{status}]  {t.title}{recur}{due}")

# ── Demo 6: detect_time_conflicts() ──────────────────────────────────────────
print()
print("=" * 54)
print("  detect_time_conflicts()  —  explicit time overlap check")
print("=" * 54)

# Build an ad-hoc list of tasks with start_time set — deliberately
# including conflicts so the warning output is visible in the terminal.
from pawpal_system import Task

conflict_tasks = [
    # Same-pet conflict: both Mochi tasks start at 08:00, window overlaps
    Task(title="Morning walk",  category="walk",      duration_minutes=30,
         priority="high",  pet_name="Mochi",   start_time="08:00"),
    Task(title="Breakfast",     category="feed",      duration_minutes=15,
         priority="high",  pet_name="Mochi",   start_time="08:20"),   # starts inside the walk

    # Cross-pet conflict: Biscuit's meds overlap with Mochi's second walk
    Task(title="Thyroid meds",  category="medication", duration_minutes=10,
         priority="high",  pet_name="Biscuit", start_time="08:25"),   # overlaps both above

    # No conflict: starts after all of the above have finished
    Task(title="Fetch session", category="enrichment", duration_minutes=20,
         priority="low",   pet_name="Mochi",   start_time="09:00"),
]

print("\n  Tasks passed to detect_time_conflicts():")
for t in conflict_tasks:
    end_min = scheduler._to_minutes(t.start_time) + t.duration_minutes
    end_str = f"{end_min // 60:02d}:{end_min % 60:02d}"
    print(f"  [{t.pet_name:8s}]  {t.start_time}–{end_str}  {t.title}")

print()
warnings = scheduler.detect_time_conflicts(tasks=conflict_tasks)
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No time conflicts detected.")
