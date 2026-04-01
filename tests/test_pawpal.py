"""
tests/test_pawpal.py – Unit tests for PawPal+ core logic
Run:  python -m pytest
"""

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
