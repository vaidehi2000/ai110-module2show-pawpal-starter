from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90, preferences={"prefers_morning_walks": True})

mochi = Pet(name="Mochi", species="dog", age=3)
biscuit = Pet(name="Biscuit", species="cat", age=7, special_needs=["medication"])

owner.add_pet(mochi)
owner.add_pet(biscuit)

# --- Tasks for Mochi ---
mochi.add_task(Task(title="Morning walk",   category="walk",       duration_minutes=30, priority="high",   preferred_time="morning"))
mochi.add_task(Task(title="Breakfast",      category="feed",       duration_minutes=10, priority="high"))
mochi.add_task(Task(title="Fetch session",  category="enrichment", duration_minutes=20, priority="low",    preferred_time="afternoon"))

# --- Tasks for Biscuit ---
biscuit.add_task(Task(title="Thyroid meds", category="medication", duration_minutes=5,  priority="high",   preferred_time="morning"))
biscuit.add_task(Task(title="Breakfast",    category="feed",       duration_minutes=10, priority="high"))
biscuit.add_task(Task(title="Grooming",     category="grooming",   duration_minutes=25, priority="medium"))

# --- Generate plan ---
scheduler = Scheduler(owner=owner)
plan = scheduler.generate_plan()

# --- Print results ---
print("=" * 50)
print(f"  Today's Schedule for {owner.name}")
print(f"  Time budget: {owner.available_minutes} minutes")
print("=" * 50)

if not plan:
    print("No tasks could be scheduled within the available time.")
else:
    total = 0
    for i, task in enumerate(plan, start=1):
        time_label = f"  [{task.preferred_time}]" if task.preferred_time else ""
        print(f"{i}. [{task.pet_name}] {task.title}{time_label}")
        print(f"   Category: {task.category}  |  Priority: {task.priority}  |  Duration: {task.duration_minutes} min")
        total += task.duration_minutes

    print("-" * 50)
    print(f"  Total time scheduled: {total} min / {owner.available_minutes} min available")

print()
print("--- Scheduler Reasoning ---")
print(scheduler.explain_plan())
