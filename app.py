import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — created once, survives every rerun
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=90)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)

owner: Owner         = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# ===========================================================================
# 1. Owner setup
# ===========================================================================
st.header("1. Owner Setup")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        input_name = st.text_input("Your name", value=owner.name or "Jordan")
    with col2:
        input_minutes = st.number_input(
            "Time available today (minutes)", min_value=10, max_value=480, value=owner.available_minutes
        )
    submitted = st.form_submit_button("Save owner info")
    if submitted:
        owner.name = input_name
        owner.available_minutes = input_minutes
        st.success(f"Saved: {owner.name}, {owner.available_minutes} min available.")

# ===========================================================================
# 2. Add a pet
# ===========================================================================
st.header("2. Add a Pet")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    special_needs_input = st.text_input(
        "Special needs (comma-separated, or leave blank)", placeholder="e.g. diabetic, senior"
    )
    add_pet = st.form_submit_button("Add pet")
    if add_pet:
        special_needs = [s.strip() for s in special_needs_input.split(",") if s.strip()]
        new_pet = Pet(name=pet_name, species=species, age=age, special_needs=special_needs)
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.get_profile()}")

if owner.pets:
    st.markdown("**Current pets:**")
    for pet in owner.pets:
        st.markdown(f"- {pet.get_profile()}")
else:
    st.info("No pets added yet.")

# ===========================================================================
# 3. Add a task
# ===========================================================================
st.header("3. Add a Task")

if not owner.pets:
    st.warning("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
            category   = st.selectbox("Category", ["walk", "feed", "medication", "grooming", "enrichment"])
            target_pet = st.selectbox("For which pet?", [p.name for p in owner.pets])
        with col2:
            duration      = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority      = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            preferred_time = st.selectbox("Preferred time (optional)", ["(none)", "morning", "afternoon", "evening"])
            recurrence_input = st.selectbox("Recurrence", ["(none)", "daily", "weekly"])

        add_task = st.form_submit_button("Add task")
        if add_task:
            new_task = Task(
                title=task_title,
                category=category,
                duration_minutes=int(duration),
                priority=priority,
                pet_name=target_pet,
                preferred_time=None if preferred_time == "(none)" else preferred_time,
                recurrence=None if recurrence_input == "(none)" else recurrence_input,
            )
            scheduler.add_task(new_task)
            st.success(f"Added '{task_title}' ({priority} priority, {duration} min) for {target_pet}.")

    # Show tasks with filter controls
    all_tasks_flat = [t for pet in owner.pets for t in pet.tasks]
    if all_tasks_flat:
        st.markdown("**Current tasks:**")
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            filter_pet = st.selectbox(
                "Filter by pet", ["All"] + [p.name for p in owner.pets], key="filter_pet"
            )
        with fcol2:
            filter_status = st.selectbox(
                "Filter by status", ["All", "Pending", "Completed"], key="filter_status"
            )

        filtered = all_tasks_flat
        if filter_pet != "All":
            filtered = [t for t in filtered if t.pet_name == filter_pet]
        if filter_status == "Pending":
            filtered = [t for t in filtered if not t.is_completed]
        elif filter_status == "Completed":
            filtered = [t for t in filtered if t.is_completed]

        if filtered:
            st.table([t.to_dict() for t in filtered])
        else:
            st.info("No tasks match the current filters.")

# ===========================================================================
# 4. Generate schedule
# ===========================================================================
st.header("4. Today's Schedule")

if st.button("Generate schedule", type="primary"):
    if not owner.name:
        st.error("Please save owner info first.")
    elif not owner.pets:
        st.error("Add at least one pet first.")
    else:
        plan = scheduler.generate_plan()
        if not plan:
            st.warning("No tasks could be scheduled — check that tasks have been added and the time budget is large enough.")
        else:
            total = sum(t.duration_minutes for t in plan)
            st.success(f"Scheduled {len(plan)} task(s) using {total} of {owner.available_minutes} minutes.")

            for i, task in enumerate(plan, start=1):
                time_label = f" · {task.preferred_time}" if task.preferred_time else ""
                recurrence_badge = f" · repeats {task.recurrence}" if task.recurrence else ""
                st.markdown(f"**{i}. [{task.pet_name}] {task.title}**{time_label}{recurrence_badge}")
                st.caption(f"Category: {task.category} · Priority: {task.priority} · Duration: {task.duration_minutes} min")

            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.divider()
                st.warning("**Scheduling conflicts detected:**")
                for msg in conflicts:
                    st.markdown(f"- {msg}")

            st.divider()
            with st.expander("Scheduler reasoning"):
                st.text(scheduler.explain_plan())
