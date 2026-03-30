"""
main.py
-------
Demo / smoke-test script for PawPal+ logic layer.
Run with:  python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main() -> None:
    today = date.today()

    # ------------------------------------------------------------------ setup
    owner = Owner(name="Alex", contact_info="alex@email.com")

    buddy    = Pet(name="Buddy",    species="Dog")
    whiskers = Pet(name="Whiskers", species="Cat")

    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # Normal tasks
    buddy.add_task(Task(name="Morning walk",     duration_minutes=30, priority="high",
                        time_of_day="morning",   start_time="07:00", due_date=today))
    buddy.add_task(Task(name="Joint supplement", duration_minutes=5,  priority="high",
                        time_of_day="morning",   start_time="07:10", due_date=today))
    whiskers.add_task(Task(name="Breakfast feeding", duration_minutes=10, priority="high",
                           time_of_day="morning",   start_time="07:30", due_date=today))
    whiskers.add_task(Task(name="Litter box clean",  duration_minutes=10, priority="medium",
                           time_of_day="anytime",   start_time="",      due_date=today))

    # --- INTENTIONAL CONFLICTS ---
    # Conflict A: same pet, overlapping windows
    #   "Fetch" starts 14:00, ends 14:20
    #   "Training" starts 14:15, ends 14:45  -> 5-min overlap
    buddy.add_task(Task(name="Fetch / playtime", duration_minutes=20, priority="medium",
                        time_of_day="afternoon", start_time="14:00", due_date=today))
    buddy.add_task(Task(name="Training session", duration_minutes=30, priority="medium",
                        time_of_day="afternoon", start_time="14:15", due_date=today))

    # Conflict B: different pets, overlapping windows
    #   "Evening walk" (Buddy) 18:00-18:30
    #   "Laser pointer" (Whiskers) 18:20-18:35  -> 10-min overlap
    buddy.add_task(Task(name="Evening walk",      duration_minutes=30, priority="medium",
                        time_of_day="evening",   start_time="18:00", due_date=today))
    whiskers.add_task(Task(name="Laser pointer play", duration_minutes=15, priority="low",
                           time_of_day="evening",   start_time="18:20", due_date=today))

    scheduler = Scheduler(available_minutes=90)
    all_tasks  = owner.get_all_tasks()

    # ---------------------------------------- DEMO 1: scheduled task list
    section("All tasks (sorted by start_time)")
    print(f"  {'TIME':6} {'TASK':<24} {'PET':<10} {'DURATION'}")
    print(f"  {'-'*6} {'-'*24} {'-'*10} {'-'*8}")
    for t in scheduler.sort_by_time(all_tasks):
        print(f"  {t.start_time or '--:--':6} {t.name:<24} {t.pet_name:<10} {t.duration_minutes} min")

    # ---------------------------------------- DEMO 2: overlap detection only
    section("Time-overlap detection (new feature)")
    overlaps = scheduler.detect_time_overlaps(all_tasks)
    if overlaps:
        for w in overlaps:
            print(f"  [!] {w}")
    else:
        print("  No overlaps detected.")

    # ---------------------------------------- DEMO 3: full conflict check
    section("Full conflict check (all warnings)")
    all_warnings = scheduler.check_conflicts(all_tasks)
    if all_warnings:
        for w in all_warnings:
            print(f"  [!] {w}")
    else:
        print("  No conflicts.")

    # ---------------------------------------- DEMO 4: schedule runs anyway
    section("generate_plan still works (warnings don't crash the app)")
    plan  = scheduler.generate_plan(all_tasks)
    total = sum(t.duration_minutes for t in plan.scheduled)
    print(f"\n  Scheduled {len(plan.scheduled)} task(s), {total} min used.\n")
    for i, t in enumerate(plan.scheduled, 1):
        print(f"  {i}. {t.start_time or '--:--'} [{t.priority.upper():6}]  "
              f"{t.name} ({t.duration_minutes} min) - {t.pet_name}")
    if plan.excluded:
        print(f"\n  Excluded: {[t.name for t, _ in plan.excluded]}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
