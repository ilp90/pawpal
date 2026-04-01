"""
PawPal+ – Logic layer
All backend classes live here. The Streamlit UI (app.py) imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Priority rank used for sorting: lower number = higher urgency
_PRIORITY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

VALID_PRIORITIES = ("low", "medium", "high")
VALID_CATEGORIES = ("walk", "feed", "medication", "grooming", "enrichment", "other")


# ---------------------------------------------------------------------------
# Task – a single pet-care action (dataclass keeps it clean and comparable)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity with a duration, priority, and completion state."""

    title: str
    duration_minutes: int
    priority: str = "medium"   # "low" | "medium" | "high"
    category: str = "other"    # see VALID_CATEGORIES
    completed: bool = False

    def mark_complete(self) -> None:
        """Set the task's completed flag to True."""
        self.completed = True


# ---------------------------------------------------------------------------
# Pet – represents a single animal
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet with basic profile information and an associated list of care tasks."""

    name: str
    species: str               # e.g. "dog", "cat", "rabbit"
    age: int = 0
    breed: str = ""
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks for this pet."""
        return list(self.tasks)


# ---------------------------------------------------------------------------
# Owner – the human using PawPal+
# ---------------------------------------------------------------------------

class Owner:
    """The pet owner, who has a daily time budget and one or more pets."""

    def __init__(
        self,
        name: str,
        available_minutes_per_day: int = 120,
        preferences: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences: list[str] = preferences if preferences is not None else []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return list(self.pets)

    def set_available_time(self, minutes: int) -> None:
        """Update how many minutes per day the owner has available for pet care."""
        self.available_minutes_per_day = minutes

    def get_all_tasks(self) -> list[Task]:
        """Collect and return every task across all of this owner's pets."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks


# ---------------------------------------------------------------------------
# Scheduler – the planning engine
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves tasks from all of an owner's pets and builds a prioritised daily plan."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def prioritize_tasks(self) -> list[Task]:
        """Return incomplete tasks sorted by priority (high→medium→low), then duration."""
        incomplete = [t for t in self.owner.get_all_tasks() if not t.completed]
        return sorted(incomplete, key=lambda t: (_PRIORITY_RANK.get(t.priority, 1), t.duration_minutes))

    def generate_schedule(self) -> list[Task]:
        """Greedily select tasks in priority order until the owner's time budget is used up."""
        budget = self.owner.available_minutes_per_day
        scheduled: list[Task] = []
        for task in self.prioritize_tasks():
            if task.duration_minutes <= budget:
                scheduled.append(task)
                budget -= task.duration_minutes
        return scheduled

    def explain_plan(self, schedule: list[Task]) -> str:
        """Return a plain-English summary of the schedule and why tasks were included or skipped."""
        if not schedule:
            return "No tasks could fit within the available time."

        total_used = sum(t.duration_minutes for t in schedule)
        available = self.owner.available_minutes_per_day
        lines = [
            f"Today's plan for {self.owner.name}",
            f"Time used: {total_used} / {available} min\n",
        ]
        for i, task in enumerate(schedule, 1):
            lines.append(
                f"  {i}. [{task.priority.upper():6}] {task.title}"
                f"  –  {task.duration_minutes} min  ({task.category})"
            )

        all_incomplete = [t for t in self.owner.get_all_tasks() if not t.completed]
        skipped = [t for t in all_incomplete if t not in schedule]
        if skipped:
            names = ", ".join(t.title for t in skipped)
            lines.append(f"\n  Skipped (time constraint): {names}")

        return "\n".join(lines)
