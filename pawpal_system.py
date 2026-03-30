"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Contains all backend classes: Task, Pet, Owner, and Scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity (walk, feeding, medication, etc.)."""

    name: str
    duration_minutes: int
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["pending", "completed"] = "pending"

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass

    def update(
        self,
        name: str | None = None,
        duration_minutes: int | None = None,
        priority: str | None = None,
    ) -> None:
        """Update one or more fields on this task."""
        pass


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
        """Append a new Task to this pet's task list."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return the current list of tasks for this pet."""
        pass


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
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of every Task across all owned pets."""
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Planning brain for PawPal+.
    Takes a list of tasks and produces a daily care schedule.
    """

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted high → medium → low priority."""
        pass

    def sort_by_duration(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted shortest to longest duration."""
        pass

    def filter_by_pet(self, tasks: list[Task], pet: Pet) -> list[Task]:
        """Return only the tasks that belong to the given pet."""
        pass

    def check_conflicts(self, tasks: list[Task]) -> list[str]:
        """
        Detect scheduling problems (e.g. total duration exceeds available time).
        Returns a list of human-readable warning strings.
        """
        pass

    def generate_plan(self, tasks: list[Task]) -> list[Task]:
        """
        Produce an ordered daily plan that fits within available_minutes.
        High-priority tasks are included first; lower-priority tasks fill
        remaining time. Returns the final list of scheduled tasks.
        """
        pass