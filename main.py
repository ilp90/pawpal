"""
main.py – CLI demo for PawPal+

Demonstrates: scheduling, sort_by_time, filter_tasks, recurring tasks,
and conflict detection.

Run:  python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

SEP = "=" * 56


def section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


def main() -> None:
    # ── Setup ────────────────────────────────────────────────
    jordan = Owner(name="Jordan", available_minutes_per_day=90)

    mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    luna  = Pet(name="Luna",  species="cat", age=5)

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # Tasks added intentionally out of priority/time order to show sorting
    mochi.add_task(Task("Fetch session",  duration_minutes=25, priority="low",    category="enrichment"))
    mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   category="walk"))
    mochi.add_task(Task("Breakfast feed", duration_minutes=10, priority="high",   category="feed",
                        frequency="daily", due_date=date.today()))
    mochi.add_task(Task("Flea treatment", duration_minutes=5,  priority="medium", category="medication"))

    luna.add_task(Task("Morning feed",   duration_minutes=10, priority="high",   category="feed",
                       frequency="daily", due_date=date.today()))
    luna.add_task(Task("Brush coat",     duration_minutes=15, priority="medium", category="grooming"))
    luna.add_task(Task("Laser toy play", duration_minutes=20, priority="low",    category="enrichment"))

    scheduler = Scheduler(owner=jordan)

    # ── 1. Generate schedule (with auto start-times) ─────────
    section("1. Today's Schedule")
    schedule = scheduler.generate_schedule(day_start="08:00")
    print(scheduler.explain_plan(schedule))

    # ── 2. Sort tasks by assigned start_time ─────────────────
    section("2. Schedule sorted by start_time")
    for t in scheduler.sort_by_time(schedule):
        print(f"  {t.start_time}  [{t.priority.upper():6}]  {t.title}  ({t.duration_minutes} min)")

    # ── 3. Filter – only pending tasks for Mochi ─────────────
    section("3. Pending tasks for Mochi only")
    mochi_pending = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    for t in mochi_pending:
        print(f"  - {t.title}  [{t.priority}]")

    # ── 4. Filter – all completed tasks (none yet) ───────────
    section("4. Completed tasks (before marking anything done)")
    done = scheduler.filter_tasks(completed=True)
    print(f"  {len(done)} completed task(s)" if done else "  None yet.")

    # ── 5. Recurring task demo ────────────────────────────────
    section("5. Recurring task: complete 'Breakfast feed' (daily)")
    breakfast = next(t for t in mochi.get_tasks() if t.title == "Breakfast feed")
    print(f"  Before: completed={breakfast.completed}, due={breakfast.due_date}")
    scheduler.complete_task(mochi, breakfast)
    print(f"  After:  completed={breakfast.completed}")

    # The next occurrence was automatically added to Mochi
    new_tasks = [t for t in mochi.get_tasks() if t.title == "Breakfast feed" and not t.completed]
    if new_tasks:
        print(f"  New occurrence added: due {new_tasks[0].due_date}  (tomorrow)")

    # ── 6. Conflict detection ─────────────────────────────────
    section("6. Conflict detection – two overlapping vet slots")
    vet_check   = Task("Vet check",           duration_minutes=60, priority="high",
                       category="other",      start_time="10:00")
    grooming    = Task("Grooming appointment", duration_minutes=45, priority="medium",
                       category="grooming",   start_time="10:30")   # starts before vet check ends

    warnings = scheduler.detect_conflicts([vet_check, grooming])
    if warnings:
        for w in warnings:
            print(f"  ⚠  {w}")
    else:
        print("  No conflicts detected.")

    # Verify non-overlapping tasks produce no warnings
    morning_feed = Task("Morning feed",  duration_minutes=10, start_time="08:00")
    afternoon_walk = Task("Afternoon walk", duration_minutes=30, start_time="16:00")
    no_warnings = scheduler.detect_conflicts([morning_feed, afternoon_walk])
    print(f"\n  Non-overlapping tasks → {len(no_warnings)} warning(s)  ✓")


if __name__ == "__main__":
    main()
