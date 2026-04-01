"""
PawPal+ – Logic layer
All backend classes live here. The Streamlit UI (app.py) imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Task – a single pet-care action (dataclass keeps it clean and comparable)
# ---------------------------------------------------------------------------

VALID_PRIORITIES = ("low", "medium", "high")
VALID_CATEGORIES = ("walk", "feed", "medication", "grooming", "enrichment", "other")


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"          # "low" | "medium" | "high"
    category: str = "other"           # see VALID_CATEGORIES
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Pet – represents a single animal
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str                      # e.g. "dog", "cat", "rabbit"
    age: int = 0
    breed: str = ""
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        pass  # TODO: implement

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Owner – the human using PawPal+
# ---------------------------------------------------------------------------

class Owner:
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
        pass  # TODO: implement

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        pass  # TODO: implement

    def set_available_time(self, minutes: int) -> None:
        """Update how many minutes per day the owner has available."""
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Scheduler – the planning engine
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet

    def prioritize_tasks(self) -> list[Task]:
        """Return tasks sorted by priority (high → medium → low), then duration."""
        pass  # TODO: implement

    def generate_schedule(self) -> list[Task]:
        """
        Greedily select tasks in priority order until the owner's available
        time is exhausted. Returns the ordered list of scheduled tasks.
        """
        pass  # TODO: implement

    def explain_plan(self, schedule: list[Task]) -> str:
        """
        Return a plain-English explanation of why each task was included
        and the total time used vs. available.
        """
        pass  # TODO: implement
