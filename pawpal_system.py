"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Contains all backend classes: Task, Pet, Owner, and Scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Priority order used for sorting (lower index = higher priority)
_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# ScheduleResult  (added after design review)
# ---------------------------------------------------------------------------

@dataclass
class ScheduleResult:
    """
    Returned by Scheduler.generate_plan().
    Separates scheduled tasks from excluded ones and carries human-readable
    reasons for exclusions — fulfilling the README requirement to explain the plan.
    """

    scheduled: list["Task"] = field(default_factory=list)
    excluded: list[tuple["Task", str]] = field(default_factory=list)  # (task, reason)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity (walk, feeding, medication, etc.)."""

    name: str
    duration_minutes: int
    pet_name: str = ""          # links task back to its pet for flat-list filtering
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["pending", "completed"] = "pending"

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.status = "completed"

    def update(
        self,
        name: str | None = None,
        duration_minutes: int | None = None,
        priority: str | None = None,
    ) -> None:
        """Update one or more fields on this task."""
        if name is not None:
            self.name = name
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if priority is not None:
            self.priority = priority  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet owned by an Owner. Holds a list of Tasks."""

    name: str
    species: str
    health_notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a new Task to this pet's task list and stamp pet_name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return the current list of tasks for this pet."""
        return list(self.tasks)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """The person using the app. Owns one or more pets."""

    def __init__(self, name: str, contact_info: str = "") -> None:
        self.name = name
        self.contact_info = contact_info
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's collection."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of every Task across all owned pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Planning brain for PawPal+.
    Retrieves tasks via Owner.get_all_tasks(), then organises them into a
    daily schedule that fits within the owner's available time.
    """

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes

    # ------------------------------------------------------------------
    # Sorting helpers
    # ------------------------------------------------------------------

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted high → medium → low priority."""
        return sorted(tasks, key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))

    def sort_by_duration(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted shortest → longest duration."""
        return sorted(tasks, key=lambda t: t.duration_minutes)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_by_pet(self, tasks: list[Task], pet: Pet) -> list[Task]:
        """Return only the tasks that belong to the given pet."""
        return [t for t in tasks if t.pet_name == pet.name]

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def check_conflicts(self, tasks: list[Task]) -> list[str]:
        """
        Detect scheduling problems.
        Currently checks:
          - Total duration of pending tasks exceeds available_minutes.
        Returns a list of human-readable warning strings (empty = no issues).
        """
        warnings: list[str] = []
        pending = [t for t in tasks if t.status == "pending"]
        total = sum(t.duration_minutes for t in pending)
        if total > self.available_minutes:
            over = total - self.available_minutes
            warnings.append(
                f"Total pending task time ({total} min) exceeds available time "
                f"({self.available_minutes} min) by {over} min."
            )
        return warnings

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_plan(self, tasks: list[Task]) -> ScheduleResult:
        """
        Produce an ordered daily plan that fits within available_minutes.

        Strategy:
          1. Ignore already-completed tasks.
          2. Sort remaining tasks by priority (high first), then by duration
             (shortest first) as a tiebreaker — maximises tasks completed.
          3. Greedily add tasks until available time is exhausted.

        Returns a ScheduleResult with:
          - scheduled: tasks that fit in the plan (in order)
          - excluded:  (task, reason) pairs for tasks that were left out
        """
        result = ScheduleResult()
        time_used = 0

        # Skip completed tasks upfront
        pending = [t for t in tasks if t.status == "pending"]

        # Sort: primary = priority rank, secondary = shortest duration first
        ordered = sorted(
            pending,
            key=lambda t: (_PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )

        for task in ordered:
            if time_used + task.duration_minutes <= self.available_minutes:
                result.scheduled.append(task)
                time_used += task.duration_minutes
            else:
                remaining = self.available_minutes - time_used
                result.excluded.append(
                    (
                        task,
                        f"Not enough time remaining ({remaining} min left, "
                        f"task needs {task.duration_minutes} min).",
                    )
                )

        return result
