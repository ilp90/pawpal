"""
app.py – PawPal+ Streamlit UI
Imports the logic layer from pawpal_system.py and persists all state in
st.session_state so objects survive the page reruns Streamlit triggers on
every user interaction.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, VALID_CATEGORIES, VALID_PRIORITIES, VALID_FREQUENCIES

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes_per_day=120)

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)   # stateless — safe to recreate each run

# ---------------------------------------------------------------------------
# Sidebar – controls and view options
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Controls")
    day_start = st.text_input("Schedule start time (HH:MM)", value="08:00",
                              help="First task will be assigned this start time.")
    pending_only = st.checkbox("Show pending tasks only", value=False)
    st.divider()
    if st.button("Reset everything", type="secondary"):
        st.session_state.owner = Owner(name="", available_minutes_per_day=120)
        st.rerun()

# ---------------------------------------------------------------------------
# Section 1 – Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        name_input = st.text_input("Your name", value=owner.name or "Jordan")
    with col2:
        time_input = st.number_input(
            "Available minutes / day",
            min_value=10, max_value=480,
            value=owner.available_minutes_per_day,
            step=10,
        )
    if st.form_submit_button("Save owner"):
        owner.name = name_input.strip()
        owner.set_available_time(int(time_input))
        st.success(f"Saved: **{owner.name}** — {owner.available_minutes_per_day} min/day")

# ---------------------------------------------------------------------------
# Section 2 – Pets
# ---------------------------------------------------------------------------
st.header("2. Pets")

pets = owner.get_pets()
if pets:
    for pet in pets:
        pending_count = len([t for t in pet.get_tasks() if not t.completed])
        total_count   = len(pet.get_tasks())
        st.markdown(
            f"- **{pet.name}** ({pet.species}"
            + (f", {pet.breed}" if pet.breed else "")
            + f", age {pet.age}) — {pending_count}/{total_count} task(s) pending"
        )
else:
    st.info("No pets yet. Add one below.")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    breed = st.text_input("Breed (optional)")
    if st.form_submit_button("Add pet"):
        owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age), breed=breed.strip()))
        st.success(f"Added **{pet_name}**!")
        st.rerun()

# ---------------------------------------------------------------------------
# Section 3 – Tasks
# ---------------------------------------------------------------------------
st.header("3. Tasks")

pets = owner.get_pets()
if not pets:
    st.warning("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in pets]
    selected_name = st.selectbox("Manage tasks for:", pet_names, key="pet_selector")
    selected_pet: Pet = next(p for p in pets if p.name == selected_name)

    # --- Task list -------------------------------------------------------
    tasks_to_show = (
        scheduler.filter_tasks(pet_name=selected_name, completed=False)
        if pending_only
        else selected_pet.get_tasks()
    )

    if tasks_to_show:
        st.dataframe(
            [
                {
                    "Title": t.title,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Category": t.category,
                    "Recurs": t.frequency if t.frequency != "none" else "—",
                    "Due": str(t.due_date) if t.due_date else "—",
                    "Done": "✓" if t.completed else "",
                }
                for t in tasks_to_show
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        label = "No pending tasks" if pending_only else "No tasks"
        st.info(f"{label} for {selected_pet.name} yet.")

    # --- Add task form ---------------------------------------------------
    with st.expander("Add a task", expanded=True):
        with st.form("task_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                task_title = st.text_input("Task title", value="Morning walk")
            with col2:
                duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            with col3:
                priority = st.selectbox(
                    "Priority",
                    list(VALID_PRIORITIES),
                    index=list(VALID_PRIORITIES).index("high"),
                )
            col4, col5 = st.columns(2)
            with col4:
                category = st.selectbox("Category", list(VALID_CATEGORIES))
            with col5:
                frequency = st.selectbox("Recurrence", list(VALID_FREQUENCIES),
                                         help="Daily/weekly tasks auto-reschedule when completed.")
            if st.form_submit_button("Add task"):
                selected_pet.add_task(
                    Task(
                        title=task_title.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        category=category,
                        frequency=frequency,
                    )
                )
                st.success(f"Added **{task_title}** to {selected_pet.name}!")
                st.rerun()

    # --- Mark complete ---------------------------------------------------
    with st.expander("Mark a task complete"):
        pending = scheduler.filter_tasks(pet_name=selected_name, completed=False)
        if pending:
            task_choice = st.selectbox(
                "Select task to complete",
                [t.title for t in pending],
                key="complete_sel",
            )
            if st.button("Mark complete", key="btn_complete"):
                task_obj = next(t for t in pending if t.title == task_choice)
                scheduler.complete_task(selected_pet, task_obj)
                st.success(f"Marked **{task_choice}** as done!")
                if task_obj.frequency != "none":
                    new_occ = [
                        t for t in selected_pet.get_tasks()
                        if t.title == task_choice and not t.completed
                    ]
                    if new_occ:
                        st.info(
                            f"Next **{task_choice}** ({task_obj.frequency}) "
                            f"queued for {new_occ[-1].due_date}."
                        )
                st.rerun()
        else:
            st.info("No pending tasks to complete.")

# ---------------------------------------------------------------------------
# Section 4 – Generate today's schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Today's Schedule")

if st.button("Generate schedule", type="primary"):
    if not owner.name:
        st.error("Please save owner info (Section 1) first.")
    elif not owner.get_pets():
        st.error("Add at least one pet (Section 2) before scheduling.")
    elif not owner.get_all_tasks():
        st.error("Add at least one task (Section 3) before scheduling.")
    else:
        # Validate day_start format
        import re
        if not re.match(r"^\d{2}:\d{2}$", day_start):
            st.error("Schedule start time must be in HH:MM format (e.g. 08:00).")
        else:
            schedule = scheduler.generate_schedule(day_start=day_start)

            if not schedule:
                st.warning("No tasks fit within your available time budget.")
            else:
                total_min = sum(t.duration_minutes for t in schedule)
                col1, col2, col3 = st.columns(3)
                col1.metric("Tasks scheduled", len(schedule))
                col2.metric("Minutes used", total_min)
                col3.metric("Minutes free", owner.available_minutes_per_day - total_min)

                st.dataframe(
                    [
                        {
                            "#": i,
                            "Start": t.start_time,
                            "Priority": t.priority.upper(),
                            "Task": t.title,
                            "Duration (min)": t.duration_minutes,
                            "Category": t.category,
                            "Recurs": t.frequency if t.frequency != "none" else "—",
                        }
                        for i, t in enumerate(schedule, 1)
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                # --- Conflict detection -----------------------------------
                conflicts = scheduler.detect_conflicts(schedule)
                if conflicts:
                    st.subheader("Scheduling conflicts detected")
                    for warn in conflicts:
                        st.warning(warn)
                else:
                    st.success("No scheduling conflicts — your plan is clean.")

                # --- Plan explanation ------------------------------------
                with st.expander("Plan explanation"):
                    st.code(scheduler.explain_plan(schedule), language=None)
