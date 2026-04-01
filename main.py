"""
main.py – CLI demo script for PawPal+

Run:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # --- Owner ---
    jordan = Owner(name="Jordan", available_minutes_per_day=90)

    # --- Pets ---
    mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    luna = Pet(name="Luna", species="cat", age=5, breed="Domestic Shorthair")

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # --- Tasks for Mochi ---
    mochi.add_task(Task("Morning walk",    duration_minutes=30, priority="high",   category="walk"))
    mochi.add_task(Task("Breakfast feed",  duration_minutes=10, priority="high",   category="feed"))
    mochi.add_task(Task("Flea treatment",  duration_minutes=5,  priority="medium", category="medication"))
    mochi.add_task(Task("Fetch session",   duration_minutes=25, priority="low",    category="enrichment"))

    # --- Tasks for Luna ---
    luna.add_task(Task("Morning feed",     duration_minutes=10, priority="high",   category="feed"))
    luna.add_task(Task("Brush coat",       duration_minutes=15, priority="medium", category="grooming"))
    luna.add_task(Task("Laser toy play",   duration_minutes=20, priority="low",    category="enrichment"))

    # --- Schedule ---
    scheduler = Scheduler(owner=jordan)
    schedule = scheduler.generate_schedule()

    # --- Print ---
    print("=" * 52)
    print(scheduler.explain_plan(schedule))
    print("=" * 52)

    # Mark the first task done and re-run to show it is excluded next time
    if schedule:
        schedule[0].mark_complete()
        print(f"\n  ✓ Marked '{schedule[0].title}' as complete.")
        updated = scheduler.generate_schedule()
        print(f"\n  Remaining tasks: {[t.title for t in updated]}")


if __name__ == "__main__":
    main()
