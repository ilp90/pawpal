"""
tests/test_pawpal.py – Unit tests for PawPal+ core logic
Run:  python -m pytest
"""

from datetime import date, timedelta

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() must flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_is_idempotent():
    """Calling mark_complete() twice should not raise and status stays True."""
    task = Task(title="Feed Mochi", duration_minutes=10)
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """Adding a task to a pet should increase its task count by 1."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(title="Walk", duration_minutes=20))
    assert len(pet.get_tasks()) == 1


def test_add_multiple_tasks():
    """Adding three tasks should result in a count of 3."""
    pet = Pet(name="Luna", species="cat")
    for title in ("Feed", "Brush", "Play"):
        pet.add_task(Task(title=title, duration_minutes=10))
    assert len(pet.get_tasks()) == 3


def test_get_tasks_returns_copy():
    """Mutating the list returned by get_tasks() must not affect the pet's internal list."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=20))
    tasks = pet.get_tasks()
    tasks.clear()
    assert len(pet.get_tasks()) == 1


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_add_pet_increases_count():
    """Adding a pet to an owner should increase the pet count by 1."""
    owner = Owner(name="Jordan")
    assert len(owner.get_pets()) == 0
    owner.add_pet(Pet(name="Mochi", species="dog"))
    assert len(owner.get_pets()) == 1


def test_set_available_time():
    """set_available_time should update available_minutes_per_day."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    owner.set_available_time(90)
    assert owner.available_minutes_per_day == 90


def test_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() should collect tasks from every pet the owner has."""
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task("Walk", 30))
    dog.add_task(Task("Feed dog", 10))
    cat.add_task(Task("Feed cat", 10))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_all_tasks()) == 3


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_schedule_respects_time_budget():
    """Scheduler must not exceed the owner's available_minutes_per_day."""
    owner = Owner(name="Jordan", available_minutes_per_day=40)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk",  30, priority="high"))
    pet.add_task(Task("Play",  25, priority="medium"))  # would exceed budget after walk
    pet.add_task(Task("Brush", 5,  priority="low"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    total = sum(t.duration_minutes for t in schedule)
    assert total <= owner.available_minutes_per_day


def test_schedule_orders_by_priority():
    """High-priority tasks should appear before low-priority ones in the schedule."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Play",  20, priority="low"))
    pet.add_task(Task("Meds",  5,  priority="high"))
    pet.add_task(Task("Walk",  30, priority="medium"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    priorities = [t.priority for t in schedule]
    # All "high" tasks must come before "medium", and "medium" before "low"
    rank = {"high": 0, "medium": 1, "low": 2}
    assert priorities == sorted(priorities, key=lambda p: rank[p])


def test_completed_tasks_excluded_from_schedule():
    """Tasks already marked complete should not appear in the generated schedule."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    done = Task("Walk", 30, priority="high", completed=True)
    pending = Task("Feed", 10, priority="high")
    pet.add_task(done)
    pet.add_task(pending)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    assert done not in schedule
    assert pending in schedule


def test_explain_plan_mentions_owner():
    """explain_plan() output should reference the owner's name."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()
    explanation = scheduler.explain_plan(schedule)
    assert "Jordan" in explanation


def test_generate_schedule_assigns_start_times():
    """generate_schedule() should stamp a start_time on every scheduled task."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, priority="high"))
    pet.add_task(Task("Feed", 10, priority="high"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).generate_schedule(day_start="08:00")
    assert all(t.start_time != "" for t in schedule)


def test_generate_schedule_start_times_are_sequential():
    """Each task's start_time should equal the previous task's end time."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, priority="high"))
    pet.add_task(Task("Feed", 10, priority="high"))
    owner.add_pet(pet)

    from datetime import datetime, timedelta
    schedule = Scheduler(owner).generate_schedule(day_start="08:00")
    for i in range(1, len(schedule)):
        prev = schedule[i - 1]
        prev_end = datetime.strptime(prev.start_time, "%H:%M") + timedelta(minutes=prev.duration_minutes)
        assert schedule[i].start_time == prev_end.strftime("%H:%M")


# ---------------------------------------------------------------------------
# sort_by_time tests
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_ascending():
    """sort_by_time should return tasks in chronological order."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    tasks = [
        Task("Afternoon walk", 30, start_time="14:00"),
        Task("Morning feed",   10, start_time="08:00"),
        Task("Midday meds",     5, start_time="12:00"),
    ]
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(tasks)
    assert [t.start_time for t in sorted_tasks] == ["08:00", "12:00", "14:00"]


def test_sort_by_time_untimed_tasks_go_last():
    """Tasks without a start_time should appear after all timed tasks."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    tasks = [
        Task("No time task",   10),
        Task("Morning feed",   10, start_time="08:00"),
    ]
    sorted_tasks = Scheduler(owner).sort_by_time(tasks)
    assert sorted_tasks[0].start_time == "08:00"
    assert sorted_tasks[1].start_time == ""


# ---------------------------------------------------------------------------
# filter_tasks tests
# ---------------------------------------------------------------------------

def test_filter_by_pet_name():
    """filter_tasks(pet_name=X) should only return tasks belonging to pet X."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task("Walk", 30))
    cat.add_task(Task("Feed", 10))
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler(owner).filter_tasks(pet_name="Mochi")
    assert len(result) == 1
    assert result[0].title == "Walk"


def test_filter_by_completed_status():
    """filter_tasks(completed=False) should exclude completed tasks."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    done = Task("Walk", 30, completed=True)
    pending = Task("Feed", 10)
    pet.add_task(done)
    pet.add_task(pending)
    owner.add_pet(pet)

    result = Scheduler(owner).filter_tasks(completed=False)
    assert pending in result
    assert done not in result


def test_filter_combined():
    """filter_tasks with both pet_name and completed should apply both criteria."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task("Walk", 30, completed=True))
    dog.add_task(Task("Feed", 10))
    cat.add_task(Task("Brush", 15))
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler(owner).filter_tasks(pet_name="Mochi", completed=False)
    assert len(result) == 1
    assert result[0].title == "Feed"


# ---------------------------------------------------------------------------
# Recurring task tests
# ---------------------------------------------------------------------------

def test_mark_complete_nonrecurring_returns_none():
    """A one-off task should return None from mark_complete()."""
    task = Task("Walk", 30, frequency="none")
    assert task.mark_complete() is None


def test_mark_complete_daily_returns_next_task():
    """A daily task should return a new Task due the next day."""
    today = date.today()
    task = Task("Morning feed", 10, frequency="daily", due_date=today)
    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.title == task.title


def test_mark_complete_weekly_returns_next_task():
    """A weekly task should return a new Task due seven days later."""
    today = date.today()
    task = Task("Flea treatment", 5, frequency="weekly", due_date=today)
    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_complete_task_adds_recurrence_to_pet():
    """Scheduler.complete_task() should add the next occurrence to the pet's task list."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    recurring = Task("Morning feed", 10, frequency="daily", due_date=date.today())
    pet.add_task(recurring)
    owner.add_pet(pet)

    before = len(pet.get_tasks())
    Scheduler(owner).complete_task(pet, recurring)
    assert len(pet.get_tasks()) == before + 1  # original + next occurrence


def test_complete_task_no_recurrence_leaves_count_unchanged():
    """complete_task() on a non-recurring task should not add a new task."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    one_off = Task("Vet visit", 60, frequency="none")
    pet.add_task(one_off)
    owner.add_pet(pet)

    before = len(pet.get_tasks())
    Scheduler(owner).complete_task(pet, one_off)
    assert len(pet.get_tasks()) == before


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_overlap():
    """Two tasks whose time windows overlap should produce a warning."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    a = Task("Vet check",   60, start_time="10:00")
    b = Task("Grooming",    45, start_time="10:30")  # starts before vet check ends

    warnings = Scheduler(owner).detect_conflicts([a, b])
    assert len(warnings) == 1
    assert "Vet check" in warnings[0]
    assert "Grooming" in warnings[0]


def test_detect_conflicts_no_overlap():
    """Non-overlapping tasks should produce no warnings."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    a = Task("Morning feed", 10, start_time="08:00")
    b = Task("Evening walk", 30, start_time="17:00")

    warnings = Scheduler(owner).detect_conflicts([a, b])
    assert warnings == []


def test_detect_conflicts_adjacent_tasks_do_not_conflict():
    """Tasks that touch but do not overlap (end == next start) are not conflicts."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    a = Task("Feed",  10, start_time="08:00")   # ends 08:10
    b = Task("Walk",  30, start_time="08:10")   # starts exactly when a ends

    warnings = Scheduler(owner).detect_conflicts([a, b])
    assert warnings == []


def test_detect_conflicts_skips_untimed_tasks():
    """Tasks without a start_time should be silently ignored by detect_conflicts."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    a = Task("Walk",  30, start_time="08:00")
    b = Task("Brush", 15)  # no start_time

    warnings = Scheduler(owner).detect_conflicts([a, b])
    assert warnings == []
