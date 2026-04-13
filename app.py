"""
app.py — PawPal+ Streamlit UI
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session state bootstrap ───────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None


def get_scheduler() -> Scheduler:
    return st.session_state.scheduler


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners")

# ── Owner setup ───────────────────────────────────────────────────────────────
if st.session_state.owner is None:
    st.subheader("👤 Welcome! Who are you?")
    with st.form("owner_form"):
        owner_name = st.text_input("Your name", placeholder="e.g. Alex")
        submitted = st.form_submit_button("Get Started")
        if submitted and owner_name.strip():
            st.session_state.owner = Owner(owner_name.strip())
            st.session_state.scheduler = Scheduler(st.session_state.owner)
            st.rerun()
    st.stop()

owner: Owner = st.session_state.owner
scheduler: Scheduler = get_scheduler()

st.markdown(f"### Hello, **{owner.name}**! 👋")
st.divider()

# ── Sidebar — Add Pet ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("➕ Add a Pet")
    with st.form("add_pet_form"):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["Dog", "Cat", "Rabbit", "Bird", "Other"])
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
        add_pet_btn = st.form_submit_button("Add Pet")
        if add_pet_btn:
            if not pet_name.strip():
                st.error("Please enter a pet name.")
            elif owner.get_pet(pet_name.strip()):
                st.warning(f"A pet named '{pet_name}' already exists.")
            else:
                owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                st.success(f"Added {pet_name}! 🐾")

    st.divider()
    st.header("📋 Your Pets")
    if owner.pets:
        for pet in owner.pets:
            st.write(f"**{pet.name}** — {pet.species}, age {pet.age}")
    else:
        st.info("No pets yet. Add one above!")

# ── Main layout: two columns ──────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

# ── LEFT: Add Task ────────────────────────────────────────────────────────────
with col_left:
    st.subheader("📝 Schedule a Task")

    if not owner.pets:
        st.info("Add a pet first using the sidebar.")
    else:
        with st.form("add_task_form"):
            pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
            task_desc = st.text_input("Task description", placeholder="e.g. Morning Walk")
            task_time = st.time_input("Time")
            task_freq = st.radio("Frequency", ["once", "daily", "weekly"], horizontal=True)
            task_date = st.date_input("Due date", value=date.today())
            add_task_btn = st.form_submit_button("Add Task")

            if add_task_btn:
                if not task_desc.strip():
                    st.error("Please enter a task description.")
                else:
                    pet = owner.get_pet(pet_choice)
                    time_str = task_time.strftime("%H:%M")
                    new_task = Task(
                        description=task_desc.strip(),
                        time=time_str,
                        frequency=task_freq,
                        pet_name=pet_choice,
                        due_date=task_date,
                    )
                    pet.add_task(new_task)
                    st.success(f"✅ Task '{task_desc}' scheduled for {pet_choice} at {time_str}!")

# ── RIGHT: Today's Schedule ───────────────────────────────────────────────────
with col_right:
    st.subheader("📅 Today's Schedule")

    # Conflict warnings
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            st.warning(warning)

    schedule = scheduler.get_todays_schedule()

    if not schedule:
        st.info("No pending tasks for today! Enjoy the downtime. 😌")
    else:
        for task in schedule:
            task_col, btn_col = st.columns([5, 1])
            with task_col:
                label = f"**{task.time}** — {task.description} _{task.pet_name}_ ({task.frequency})"
                st.markdown(label)
            with btn_col:
                if st.button("✓", key=f"done_{id(task)}", help="Mark complete"):
                    next_task = scheduler.complete_task(task)
                    if next_task:
                        st.success(f"Done! Next '{task.description}' scheduled for {next_task.due_date}.")
                    else:
                        st.success("Task marked complete!")
                    st.rerun()

st.divider()

# ── Full task list with filters ───────────────────────────────────────────────
st.subheader("🗂 All Tasks")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_filter = st.selectbox(
        "Filter by pet",
        ["All"] + [p.name for p in owner.pets],
        key="filter_pet"
    )
with filter_col2:
    status_filter = st.radio(
        "Filter by status",
        ["Pending", "Completed", "All"],
        horizontal=True,
        key="filter_status"
    )

# Build filtered + sorted task list
all_tasks = owner.get_all_tasks()
if pet_filter != "All":
    all_tasks = [t for t in all_tasks if t.pet_name == pet_filter]
if status_filter == "Pending":
    all_tasks = [t for t in all_tasks if not t.completed]
elif status_filter == "Completed":
    all_tasks = [t for t in all_tasks if t.completed]

sorted_tasks = scheduler.sort_by_time(all_tasks)

if sorted_tasks:
    table_data = [
        {
            "Time": t.time,
            "Task": t.description,
            "Pet": t.pet_name,
            "Frequency": t.frequency,
            "Due": str(t.due_date),
            "Done": "✓" if t.completed else "○",
        }
        for t in sorted_tasks
    ]
    st.table(table_data)
else:
    st.info("No tasks match your filters.")
