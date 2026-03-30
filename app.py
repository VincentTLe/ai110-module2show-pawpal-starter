import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state initialisation
# Streamlit reruns the entire script on every interaction, so we guard each
# key with "if not in" to avoid resetting objects that already exist.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="")

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("PawPal+")
st.caption("A daily pet care planner")
st.divider()

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner")

with st.form("owner_form"):
    owner_name_input = st.text_input("Your name", value=owner.name or "")
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner and owner_name_input.strip():
    owner.name = owner_name_input.strip()
    st.success(f"Owner saved: {owner.name}")

if owner.name:
    st.write(f"Current owner: **{owner.name}**")

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# Calls owner.add_pet() — the Pet object lives inside the Owner in session_state
# ---------------------------------------------------------------------------
st.subheader("2. Add a Pet")

with st.form("add_pet_form"):
    new_pet_name = st.text_input("Pet name")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
    new_pet_notes = st.text_input("Health notes (optional)")
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    if not new_pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        new_pet = Pet(
            name=new_pet_name.strip(),
            species=new_pet_species,
            health_notes=new_pet_notes.strip(),
        )
        owner.add_pet(new_pet)       # <-- Pet object stored inside Owner
        st.success(f"Added pet: {new_pet.name} ({new_pet.species})")

# Show current pets
if owner.pets:
    st.write("**Your pets:**")
    for p in owner.pets:
        note = f" — {p.health_notes}" if p.health_notes else ""
        st.write(f"- {p.name} ({p.species}){note}")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a task to a pet
# Calls pet.add_task() — the Task object lives inside the chosen Pet
# ---------------------------------------------------------------------------
st.subheader("3. Add a Task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]

    with st.form("add_task_form"):
        selected_pet_name = st.selectbox("Assign task to", pet_names)
        task_name = st.text_input("Task name", value="Morning walk")
        task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        task_priority = st.selectbox("Priority", ["high", "medium", "low"])
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        if not task_name.strip():
            st.warning("Please enter a task name.")
        else:
            target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
            new_task = Task(
                name=task_name.strip(),
                duration_minutes=int(task_duration),
                priority=task_priority,
            )
            target_pet.add_task(new_task)   # <-- Task stored inside Pet; pet_name auto-stamped
            st.success(f"Added '{new_task.name}' to {target_pet.name}")

    # Show all tasks across all pets
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("**All current tasks:**")
        st.table([
            {
                "Pet": t.pet_name,
                "Task": t.name,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Status": t.status,
            }
            for t in all_tasks
        ])
    else:
        st.info("No tasks yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# Calls Scheduler.generate_plan() with owner.get_all_tasks()
# ---------------------------------------------------------------------------
st.subheader("4. Generate Today's Schedule")

available_minutes = st.number_input(
    "Available time today (minutes)", min_value=10, max_value=480, value=60, step=5
)

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add some tasks first.")
    else:
        scheduler = Scheduler(available_minutes=int(available_minutes))
        plan = scheduler.generate_plan(all_tasks)
        warnings = scheduler.check_conflicts(all_tasks)

        if warnings:
            for w in warnings:
                st.warning(w)

        if plan.scheduled:
            total_time = sum(t.duration_minutes for t in plan.scheduled)
            st.success(f"Scheduled {len(plan.scheduled)} task(s) using {total_time} of {available_minutes} min.")
            st.write("**Scheduled tasks (in order):**")
            st.table([
                {
                    "Pet": t.pet_name,
                    "Task": t.name,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                }
                for t in plan.scheduled
            ])
        else:
            st.error("No tasks could fit in the available time.")

        if plan.excluded:
            st.write("**Could not fit:**")
            for task, reason in plan.excluded:
                st.write(f"- **{task.name}** ({task.pet_name}): {reason}")
