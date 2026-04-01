"""
PawPal+ – Logic layer
All backend classes live here. The Streamlit UI (app.py) imports from this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

# Priority rank: lower number = higher urgency (used by standard scheduler)
_PRIORITY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

# Weighted scheduler constants (Challenge 1)
_PRIORITY_WEIGHT: dict[str, float] = {"high": 10.0, "medium": 5.0, "low": 1.0}
_URGENCY_BONUS: dict[str, float] = {
    "overdue":    5.0,   # due_date <= today
    "tomorrow":   3.0,   # due in 1 day
    "soon":       1.5,   # due in 2–3 days
    "upcoming":   0.5,   # due in 4–7 days
}

# Default first-task start time
_DAY_START = "08:00"
_DAY_END   = "22:00"

VALID_PRIORITIES  = ("low", "medium", "high")
VALID_CATEGORIES  = ("walk", "feed", "medication", "grooming", "enrichment", "other")
VALID_FREQUENCIES = ("none", "daily", "weekly")

# Emoji display helpers (Challenges 3 & 4)
PRIORITY_EMOJI: dict[str, str] = {"high": "🔴", "medium": "🟡", "low": "🟢"}
CATEGORY_EMOJI: dict[str, str] = {
    "walk":       "🦮",
    "feed":       "🍽️",
    "medication": "💊",
    "grooming":   "✂️",
    "enrichment": "🎾",
    "other":      "📋",
}


# ---------------------------------------------------------------------------
# Task – a single pet-care action
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity with duration, priority, recurrence, and schedule time."""

    title: str
    duration_minutes: int
    priority: str = "medium"      # "low" | "medium" | "high"
    category: str = "other"       # see VALID_CATEGORIES
    completed: bool = False
    start_time: str = ""          # "HH:MM" assigned by Scheduler, or set manually
    frequency: str = "none"       # "none" | "daily" | "weekly"
    due_date: Optional[date] = None  # next due date; used by recurring tasks

    def mark_complete(self) -> Optional["Task"]:
        """Mark complete; return the next Task occurrence if recurring, else None."""
        self.completed = True
        if self.frequency == "daily":
            next_due = (self.due_date or date.today()) + timedelta(days=1)
            return Task(title=self.title, duration_minutes=self.duration_minutes,
                        priority=self.priority, category=self.category,
                        frequency=self.frequency, due_date=next_due)
        if self.frequency == "weekly":
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
            return Task(title=self.title, duration_minutes=self.duration_minutes,
                        priority=self.priority, category=self.category,
                        frequency=self.frequency, due_date=next_due)
        return None

    # -- Serialisation (Challenge 2) ------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary suitable for JSON encoding."""
        return {
            "title":            self.title,
            "duration_minutes": self.duration_minutes,
            "priority":         self.priority,
            "category":         self.category,
            "completed":        self.completed,
            "start_time":       self.start_time,
            "frequency":        self.frequency,
            "due_date":         self.due_date.isoformat() if self.due_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a serialised dictionary."""
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=data.get("priority", "medium"),
            category=data.get("category", "other"),
            completed=data.get("completed", False),
            start_time=data.get("start_time", ""),
            frequency=data.get("frequency", "none"),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
        )


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

    # -- Serialisation (Challenge 2) ------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary suitable for JSON encoding."""
        return {
            "name":    self.name,
            "species": self.species,
            "age":     self.age,
            "breed":   self.breed,
            "notes":   self.notes,
            "tasks":   [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Reconstruct a Pet (and its tasks) from a serialised dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age=data.get("age", 0),
            breed=data.get("breed", ""),
            notes=data.get("notes", ""),
        )
        for td in data.get("tasks", []):
            pet.add_task(Task.from_dict(td))
        return pet


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

    # -- Serialisation (Challenge 2) ------------------------------------

    def to_dict(self) -> dict:
        """Serialise the owner and all pets/tasks to a plain dictionary."""
        return {
            "name":                     self.name,
            "available_minutes_per_day": self.available_minutes_per_day,
            "preferences":              self.preferences,
            "pets":                     [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Reconstruct an Owner (with all pets and tasks) from a serialised dictionary."""
        owner = cls(
            name=data.get("name", ""),
            available_minutes_per_day=data.get("available_minutes_per_day", 120),
            preferences=data.get("preferences", []),
        )
        for pd in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pd))
        return owner

    def save_to_json(self, path: str = "data.json") -> None:
        """Persist the full owner graph to a JSON file at *path*."""
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load and reconstruct an Owner from a JSON file. Raises FileNotFoundError if absent."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Scheduler – the planning engine
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds and analyses a prioritised, time-annotated daily care plan."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # -- Core scheduling -------------------------------------------------

    def prioritize_tasks(self) -> list[Task]:
        """Return incomplete tasks sorted by priority (high→medium→low) then duration."""
        incomplete = [t for t in self.owner.get_all_tasks() if not t.completed]
        return sorted(
            incomplete,
            key=lambda t: (_PRIORITY_RANK.get(t.priority, 1), t.duration_minutes),
        )

    def generate_schedule(self, day_start: str = _DAY_START) -> list[Task]:
        """
        Greedily select tasks in priority order within the owner's time budget.
        Assigns sequential start times to each selected task beginning at day_start.
        """
        budget = self.owner.available_minutes_per_day
        cursor = datetime.strptime(day_start, "%H:%M")
        scheduled: list[Task] = []
        for task in self.prioritize_tasks():
            if task.duration_minutes <= budget:
                task.start_time = cursor.strftime("%H:%M")
                scheduled.append(task)
                budget -= task.duration_minutes
                cursor += timedelta(minutes=task.duration_minutes)
        return scheduled

    def explain_plan(self, schedule: list[Task]) -> str:
        """Return a plain-English summary of the schedule and any skipped tasks."""
        if not schedule:
            return "No tasks could fit within the available time."

        total_used = sum(t.duration_minutes for t in schedule)
        available = self.owner.available_minutes_per_day
        lines = [
            f"Today's plan for {self.owner.name}",
            f"Time used: {total_used} / {available} min\n",
        ]
        for i, task in enumerate(schedule, 1):
            time_str = f" @ {task.start_time}" if task.start_time else ""
            lines.append(
                f"  {i}. [{task.priority.upper():6}] {task.title}"
                f"  –  {task.duration_minutes} min  ({task.category}){time_str}"
            )

        all_incomplete = [t for t in self.owner.get_all_tasks() if not t.completed]
        skipped = [t for t in all_incomplete if t not in schedule]
        if skipped:
            lines.append(f"\n  Skipped (time constraint): {', '.join(t.title for t in skipped)}")

        return "\n".join(lines)

    # -- Sorting ---------------------------------------------------------

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by start_time (HH:MM ascending). Tasks without a time go last."""
        def _key(t: Task) -> tuple:
            if t.start_time:
                try:
                    return (0, datetime.strptime(t.start_time, "%H:%M"))
                except ValueError:
                    pass
            return (1, datetime.min)
        return sorted(tasks, key=_key)

    # -- Filtering -------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """
        Filter tasks across all pets by pet name and/or completion status.
        Pass None to skip a filter criterion.
        """
        result: list[Task] = []
        for pet in self.owner.get_pets():
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.get_tasks():
                if completed is not None and task.completed != completed:
                    continue
                result.append(task)
        return result

    # -- Conflict detection ----------------------------------------------

    def detect_conflicts(self, schedule: list[Task]) -> list[str]:
        """
        Check for overlapping time windows among scheduled tasks that have an
        explicit start_time set. Returns human-readable warning strings.

        Tradeoff: only tasks with a start_time are checked; tasks without one
        are assumed to be sequentially safe and are silently skipped.
        """
        timed: list[tuple[Task, datetime]] = []
        for t in schedule:
            if t.start_time:
                try:
                    timed.append((t, datetime.strptime(t.start_time, "%H:%M")))
                except ValueError:
                    pass

        warnings: list[str] = []
        for i, (a, start_a) in enumerate(timed):
            end_a = start_a + timedelta(minutes=a.duration_minutes)
            for b, start_b in timed[i + 1:]:
                end_b = start_b + timedelta(minutes=b.duration_minutes)
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"Conflict: '{a.title}' "
                        f"({a.start_time}–{end_a.strftime('%H:%M')}) "
                        f"overlaps '{b.title}' "
                        f"({b.start_time}–{end_b.strftime('%H:%M')})"
                    )
        return warnings

    # -- Recurring task completion ---------------------------------------

    def complete_task(self, pet: Pet, task: Task) -> None:
        """
        Mark a task complete. If recurring, automatically add the next occurrence
        to the same pet so it appears in tomorrow's schedule.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            pet.add_task(next_task)

    # -- Challenge 1: Weighted urgency scheduling ------------------------

    def _task_score(self, task: Task) -> float:
        """
        Compute a composite urgency score combining priority weight and due-date
        proximity. Higher score = schedule sooner.

        Score = priority_weight + urgency_bonus
          priority_weight: high=10, medium=5, low=1
          urgency_bonus:   overdue=5, tomorrow=3, within 3 days=1.5, within 7=0.5
        """
        score = _PRIORITY_WEIGHT.get(task.priority, 5.0)
        if task.due_date:
            days = (task.due_date - date.today()).days
            if days <= 0:
                score += _URGENCY_BONUS["overdue"]
            elif days == 1:
                score += _URGENCY_BONUS["tomorrow"]
            elif days <= 3:
                score += _URGENCY_BONUS["soon"]
            elif days <= 7:
                score += _URGENCY_BONUS["upcoming"]
        return score

    def generate_weighted_schedule(self, day_start: str = _DAY_START) -> list[Task]:
        """
        Enhanced greedy scheduler using a composite urgency score (priority weight
        + due-date proximity) instead of simple priority rank.

        An overdue medium-priority task scores the same as a non-urgent high-priority
        task (both = 10), allowing urgency to break ties when two tasks share a priority
        tier — tasks at risk of being missed are surfaced earlier in the plan.
        """
        incomplete = [t for t in self.owner.get_all_tasks() if not t.completed]
        ranked = sorted(incomplete, key=lambda t: (-self._task_score(t), t.duration_minutes))

        budget = self.owner.available_minutes_per_day
        cursor = datetime.strptime(day_start, "%H:%M")
        scheduled: list[Task] = []
        for task in ranked:
            if task.duration_minutes <= budget:
                task.start_time = cursor.strftime("%H:%M")
                scheduled.append(task)
                budget -= task.duration_minutes
                cursor += timedelta(minutes=task.duration_minutes)
        return scheduled

    def next_available_slot(
        self,
        task: Task,
        schedule: list[Task],
        day_start: str = _DAY_START,
        day_end: str = _DAY_END,
    ) -> Optional[str]:
        """
        Find the earliest HH:MM gap in *schedule* where *task* could be inserted
        without conflicting with any already-scheduled tasks.

        Only tasks with an explicit start_time in *schedule* are treated as occupied
        slots. Tasks without a start_time are ignored (assumed untimed/flexible).
        Returns None if the task cannot fit anywhere before day_end.
        """
        end_of_day = datetime.strptime(day_end, "%H:%M")
        cursor = datetime.strptime(day_start, "%H:%M")

        # Collect and sort occupied windows from the schedule
        occupied: list[tuple[datetime, datetime]] = []
        for t in schedule:
            if t.start_time:
                try:
                    s = datetime.strptime(t.start_time, "%H:%M")
                    occupied.append((s, s + timedelta(minutes=t.duration_minutes)))
                except ValueError:
                    pass
        occupied.sort()

        for slot_start, slot_end in occupied:
            gap = int((slot_start - cursor).total_seconds() // 60)
            if gap >= task.duration_minutes:
                return cursor.strftime("%H:%M")
            cursor = max(cursor, slot_end)

        # Check remaining time after the last scheduled task
        remaining = int((end_of_day - cursor).total_seconds() // 60)
        if remaining >= task.duration_minutes:
            return cursor.strftime("%H:%M")

        return None
