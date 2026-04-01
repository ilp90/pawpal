"""
app.py – PawPal+ Streamlit UI
Imports the logic layer from pawpal_system.py and persists all state in
st.session_state so objects survive the page reruns Streamlit triggers on
every user interaction.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, VALID_CATEGORIES, VALID_PRIORITIES

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session-state initialisation
#
# Streamlit reruns this entire script on every click/input.
# st.session_state is a persistent "vault": values stored here survive reruns
# for the lifetime of the browser session.
# We check "if key not in st.session_state" so we only create the Owner once,
# not on every rerun.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes_per_day=120)

owner: Owner = st.session_state.owner  # convenient local alias

# ---------------------------------------------------------------------------
# Sidebar – reset
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("App controls")
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
        task_count = len(pet.get_tasks())
        st.markdown(
            f"- **{pet.name}** ({pet.species}"
            + (f", {pet.breed}" if pet.breed else "")
            + f", age {pet.age}) — {task_count} task(s)"
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

pets = owner.get_pets()  # re-fetch after possible add
if not pets:
    st.warning("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in pets]
    selected_name = st.selectbox("Manage tasks for:", pet_names, key="pet_selector")
    selected_pet: Pet = next(p for p in pets if p.name == selected_name)

    # Show existing tasks for the selected pet
    existing = selected_pet.get_tasks()
    if existing:
        st.table(
            [
                {
                    "Title": t.title,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Category": t.category,
                    "Done": "✓" if t.completed else "",
                }
                for t in existing
            ]
        )
    else:
        st.info(f"No tasks for {selected_pet.name} yet.")

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
        category = st.selectbox("Category", list(VALID_CATEGORIES))
        if st.form_submit_button("Add task"):
            selected_pet.add_task(
                Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category,
                )
            )
            st.success(f"Added **{task_title}** to {selected_pet.name}!")
            st.rerun()

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
        scheduler = Scheduler(owner)
        schedule = scheduler.generate_schedule()

        if not schedule:
            st.warning("No tasks fit within your available time budget.")
        else:
            total_min = sum(t.duration_minutes for t in schedule)
            st.success(
                f"{len(schedule)} task(s) scheduled — "
                f"{total_min} of {owner.available_minutes_per_day} minutes used."
            )
            st.table(
                [
                    {
                        "#": i,
                        "Priority": t.priority.upper(),
                        "Task": t.title,
                        "Duration (min)": t.duration_minutes,
                        "Category": t.category,
                    }
                    for i, t in enumerate(schedule, 1)
                ]
            )
            with st.expander("Plan explanation"):
                st.code(scheduler.explain_plan(schedule), language=None)
