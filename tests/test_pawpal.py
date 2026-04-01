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


# ---------------------------------------------------------------------------
# Edge cases – empty / boundary inputs
# ---------------------------------------------------------------------------

def test_schedule_owner_with_no_pets_returns_empty():
    """An owner with no pets should produce an empty schedule."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    assert Scheduler(owner).generate_schedule() == []


def test_schedule_all_tasks_completed_returns_empty():
    """When every task is already completed the schedule should be empty."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, completed=True))
    pet.add_task(Task("Feed", 10, completed=True))
    owner.add_pet(pet)
    assert Scheduler(owner).generate_schedule() == []


def test_schedule_task_exactly_fills_budget():
    """A task whose duration equals the remaining budget exactly should be included."""
    owner = Owner(name="Jordan", available_minutes_per_day=30)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, priority="high"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).generate_schedule()
    assert len(schedule) == 1
    assert schedule[0].title == "Walk"


def test_schedule_task_one_minute_over_budget_is_excluded():
    """A task one minute over the remaining budget must not be scheduled."""
    owner = Owner(name="Jordan", available_minutes_per_day=29)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, priority="high"))
    owner.add_pet(pet)

    assert Scheduler(owner).generate_schedule() == []


def test_schedule_pet_with_no_tasks_does_not_crash():
    """A pet that has no tasks at all should not cause an error."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    owner.add_pet(Pet(name="Mochi", species="dog"))  # no tasks added
    schedule = Scheduler(owner).generate_schedule()
    assert schedule == []


def test_explain_plan_empty_schedule_returns_message():
    """explain_plan() given an empty schedule should return the no-tasks message."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    msg = Scheduler(owner).explain_plan([])
    assert "No tasks" in msg


def test_sort_by_time_empty_list_returns_empty():
    """sort_by_time on an empty list should return an empty list without error."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    assert Scheduler(owner).sort_by_time([]) == []


def test_filter_tasks_unknown_pet_name_returns_empty():
    """filter_tasks for a pet name that does not exist should return []."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30))
    owner.add_pet(pet)
    result = Scheduler(owner).filter_tasks(pet_name="Ghost")
    assert result == []


# ---------------------------------------------------------------------------
# Edge cases – recurring tasks
# ---------------------------------------------------------------------------

def test_mark_complete_daily_no_due_date_uses_today():
    """A daily task with no due_date should base its next occurrence on today."""
    task = Task("Feed", 10, frequency="daily")   # due_date is None
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)


def test_mark_complete_weekly_no_due_date_uses_today():
    """A weekly task with no due_date should base its next occurrence on today."""
    task = Task("Flea treatment", 5, frequency="weekly")  # due_date is None
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_recurring_next_task_inherits_attributes():
    """The next occurrence should copy title, duration, priority, category, frequency."""
    today = date.today()
    task = Task("Morning feed", 10, priority="high", category="feed",
                frequency="daily", due_date=today)
    next_task = task.mark_complete()
    assert next_task.title == "Morning feed"
    assert next_task.duration_minutes == 10
    assert next_task.priority == "high"
    assert next_task.category == "feed"
    assert next_task.frequency == "daily"
    assert next_task.completed is False


# ---------------------------------------------------------------------------
# Edge cases – conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_empty_schedule_returns_empty():
    """detect_conflicts on an empty list should return no warnings."""
    owner = Owner(name="Jordan", available_minutes_per_day=60)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    assert Scheduler(owner).detect_conflicts([]) == []


def test_detect_conflicts_three_way_overlap():
    """Three mutually overlapping tasks should generate three pairwise warnings."""
    owner = Owner(name="Jordan", available_minutes_per_day=180)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    # All three overlap each other: A(10:00-11:00), B(10:15-11:15), C(10:30-11:30)
    a = Task("Vet check",   60, start_time="10:00")
    b = Task("Grooming",    60, start_time="10:15")
    c = Task("Training",    60, start_time="10:30")

    warnings = Scheduler(owner).detect_conflicts([a, b, c])
    assert len(warnings) == 3


def test_detect_conflicts_one_overlap_two_safe():
    """Only the overlapping pair should produce a warning; the safe pair should not."""
    owner = Owner(name="Jordan", available_minutes_per_day=180)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    # A and B overlap; C is safely after both
    a = Task("Walk",    30, start_time="08:00")   # ends 08:30
    b = Task("Feed",    20, start_time="08:15")   # ends 08:35 → overlaps A
    c = Task("Play",    20, start_time="09:00")   # starts well after both

    warnings = Scheduler(owner).detect_conflicts([a, b, c])
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


# ---------------------------------------------------------------------------
# Challenge 1 – Weighted scheduling & next_available_slot
# ---------------------------------------------------------------------------

def test_weighted_schedule_boosts_overdue_medium_above_low():
    """An overdue medium task should be scheduled before a non-urgent low task."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    low_task  = Task("Play session",  20, priority="low")
    overdue   = Task("Overdue meds",  10, priority="medium",
                     frequency="daily", due_date=date.today() - timedelta(days=1))
    pet.add_task(low_task)
    pet.add_task(overdue)
    owner.add_pet(pet)

    schedule = Scheduler(owner).generate_weighted_schedule()
    assert schedule[0].title == "Overdue meds"


def test_weighted_schedule_overdue_medium_equals_nonurgent_high_score():
    """_task_score: overdue medium (5+5=10) must equal non-urgent high (10+0=10)."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    sched = Scheduler(owner)

    high_task  = Task("Vet",  30, priority="high")
    med_overdue = Task("Meds", 10, priority="medium",
                       due_date=date.today() - timedelta(days=2))
    assert sched._task_score(high_task) == sched._task_score(med_overdue)


def test_weighted_schedule_respects_time_budget():
    """Weighted scheduler must not exceed the owner's time budget."""
    owner = Owner(name="Jordan", available_minutes_per_day=40)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, priority="high"))
    pet.add_task(Task("Play", 25, priority="medium"))
    owner.add_pet(pet)

    schedule = Scheduler(owner).generate_weighted_schedule()
    total = sum(t.duration_minutes for t in schedule)
    assert total <= owner.available_minutes_per_day


def test_next_available_slot_empty_schedule_returns_day_start():
    """With no scheduled tasks, the next slot is the day start."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    task = Task("Walk", 30)
    slot = Scheduler(owner).next_available_slot(task, [], day_start="08:00")
    assert slot == "08:00"


def test_next_available_slot_finds_gap_between_tasks():
    """Scheduler should identify a gap between two consecutive scheduled tasks."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    # 08:00–08:30  gap of 90 min  10:00–10:30
    schedule = [
        Task("Walk",    30, start_time="08:00"),
        Task("Groom",   30, start_time="10:00"),
    ]
    slot = Scheduler(owner).next_available_slot(
        Task("Feed", 20), schedule, day_start="08:00"
    )
    assert slot == "08:30"


def test_next_available_slot_no_room_returns_none():
    """Returns None when no gap in the day can fit the task."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    # Two tasks that fill 08:00–10:00 exactly; day_end=10:00 → no room for 30 min
    schedule = [
        Task("Walk", 60, start_time="08:00"),
        Task("Feed", 60, start_time="09:00"),
    ]
    slot = Scheduler(owner).next_available_slot(
        Task("Play", 30), schedule, day_start="08:00", day_end="10:00"
    )
    assert slot is None


def test_next_available_slot_fits_after_last_task():
    """Task fits in remaining time after the last scheduled item."""
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet(name="Mochi", species="dog"))

    schedule = [Task("Walk", 30, start_time="08:00")]  # ends 08:30; day ends 22:00
    slot = Scheduler(owner).next_available_slot(
        Task("Feed", 10), schedule, day_start="08:00"
    )
    assert slot == "08:30"


# ---------------------------------------------------------------------------
# Challenge 2 – JSON serialisation round-trips
# ---------------------------------------------------------------------------

def test_task_roundtrip():
    """to_dict() then from_dict() should reproduce an identical Task."""
    today = date.today()
    task = Task("Walk", 30, priority="high", category="walk",
                frequency="daily", due_date=today, start_time="08:00",
                completed=False)
    assert Task.from_dict(task.to_dict()) == task


def test_task_roundtrip_completed():
    """Completed flag must survive a serialisation round-trip."""
    task = Task("Feed", 10, completed=True)
    assert Task.from_dict(task.to_dict()).completed is True


def test_pet_roundtrip():
    """Pet with tasks should round-trip through to_dict/from_dict."""
    pet = Pet(name="Mochi", species="dog", age=3, breed="Shiba")
    pet.add_task(Task("Walk", 30, priority="high"))
    pet.add_task(Task("Feed", 10, frequency="daily", due_date=date.today()))

    restored = Pet.from_dict(pet.to_dict())
    assert restored.name == pet.name
    assert restored.breed == pet.breed
    assert len(restored.get_tasks()) == 2
    assert restored.get_tasks()[1].frequency == "daily"


def test_owner_save_and_load(tmp_path):
    """save_to_json then load_from_json should reproduce the full object graph."""
    owner = Owner("Jordan", available_minutes_per_day=90)
    pet = Pet("Mochi", "dog", age=3)
    pet.add_task(Task("Walk", 30, priority="high",
                      frequency="daily", due_date=date.today()))
    owner.add_pet(pet)

    path = str(tmp_path / "data.json")
    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded.name == "Jordan"
    assert loaded.available_minutes_per_day == 90
    assert len(loaded.get_pets()) == 1
    assert loaded.get_pets()[0].name == "Mochi"
    loaded_task = loaded.get_pets()[0].get_tasks()[0]
    assert loaded_task.title == "Walk"
    assert loaded_task.due_date == date.today()


def test_owner_load_missing_file_raises():
    """load_from_json should raise FileNotFoundError for a missing path."""
    import pytest
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json("/tmp/pawpal_no_such_file_xyz.json")


def test_owner_roundtrip_preserves_preferences():
    """Owner preferences list must survive a round-trip."""
    owner = Owner("Jordan", preferences=["no tasks before 8am"])
    owner2 = Owner.from_dict(owner.to_dict())
    assert owner2.preferences == ["no tasks before 8am"]
