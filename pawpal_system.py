"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Contains all backend classes: Task, Pet, Owner, and Scheduler.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

# Priority order used for sorting (lower index = higher priority)
_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}

# Time-of-day slot order (earlier = lower index)
_TIME_ORDER: dict[str, int] = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}


# ---------------------------------------------------------------------------
# ScheduleResult
# ---------------------------------------------------------------------------

@dataclass
class ScheduleResult:
    """Holds the output of generate_plan(): scheduled tasks and excluded tasks with reasons."""

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
    pet_name: str = ""
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["pending", "completed"] = "pending"

    # --- new fields ---
    recurrence: Literal["none", "daily", "weekly"] = "none"
    time_of_day: Literal["morning", "afternoon", "evening", "anytime"] = "anytime"
    start_time: str = ""        # optional scheduled start in "HH:MM" format, e.g. "07:30"
    due_date: date | None = None  # optional due date; used by recurring task spawning

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.status = "completed"

    def spawn_next(self, today: date) -> Task | None:
        """Copy this task with status reset to pending and due_date advanced by its recurrence interval; return None if non-recurring."""
        if self.recurrence == "none":
            return None

        delta = timedelta(days=1) if self.recurrence == "daily" else timedelta(weeks=1)
        next_due = today + delta

        next_task = copy.copy(self)   # shallow copy — all scalar fields duplicated
        next_task.status = "pending"
        next_task.due_date = next_due
        return next_task

    def update(
        self,
        name: str | None = None,
        duration_minutes: int | None = None,
        priority: str | None = None,
        recurrence: str | None = None,
        time_of_day: str | None = None,
    ) -> None:
        """Update one or more fields on this task."""
        if name is not None:
            self.name = name
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if priority is not None:
            self.priority = priority  # type: ignore[assignment]
        if recurrence is not None:
            self.recurrence = recurrence  # type: ignore[assignment]
        if time_of_day is not None:
            self.time_of_day = time_of_day  # type: ignore[assignment]


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
    """Organises tasks from Owner.get_all_tasks() into a daily plan that fits available time."""

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted high → medium → low priority."""
        return sorted(tasks, key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))

    def sort_by_duration(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted shortest → longest duration."""
        return sorted(tasks, key=lambda t: t.duration_minutes)

    def sort_by_time_of_day(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted morning → afternoon → evening → anytime."""
        return sorted(tasks, key=lambda t: _TIME_ORDER.get(t.time_of_day, 99))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by start_time (HH:MM) ascending; tasks with no start_time sink to the end."""
        return sorted(
            tasks,
            key=lambda t: t.start_time if t.start_time else "99:99",
        )

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_by_pet(self, tasks: list[Task], pet: Pet) -> list[Task]:
        """Return only the tasks that belong to the given pet."""
        return [t for t in tasks if t.pet_name == pet.name]

    def filter_by_status(
        self, tasks: list[Task], status: Literal["pending", "completed"]
    ) -> list[Task]:
        """Return only tasks matching the given status."""
        return [t for t in tasks if t.status == status]

    # ------------------------------------------------------------------
    # Recurring task management
    # ------------------------------------------------------------------

    def complete_task(
        self, task: Task, pet: Pet, today: date | None = None
    ) -> Task | None:
        """Mark task complete and add its next occurrence to pet if it recurs (daily +1 day, weekly +7 days)."""
        task.mark_complete()
        resolved_today = today if today is not None else date.today()
        next_task = task.spawn_next(resolved_today)
        if next_task is not None:
            pet.add_task(next_task)   # registers on pet and stamps pet_name
        return next_task

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    @staticmethod
    def _to_minutes(hhmm: str) -> int:
        """Convert a 'HH:MM' string to total minutes since midnight."""
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    @staticmethod
    def _fmt(minutes: int) -> str:
        """Convert total minutes back to 'HH:MM' for display."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def detect_time_overlaps(self, tasks: list[Task]) -> list[str]:
        """Return a warning string for every pair of pending tasks whose time windows overlap."""
        warnings: list[str] = []

        # Only consider pending tasks that have an explicit start_time set
        timed_tasks = [t for t in tasks if t.status == "pending" and t.start_time]

        # Pre-compute start/end in minutes for each task (avoids re-parsing inside the loop)
        def start_of(t: Task) -> int:
            return self._to_minutes(t.start_time)

        def end_of(t: Task) -> int:
            return self._to_minutes(t.start_time) + t.duration_minutes

        # Sort by start time so we only need to look forward, not at every pair
        timed_tasks.sort(key=start_of)

        # Compare each task against the ones that start after it
        for i, task_a in enumerate(timed_tasks):
            a_start = start_of(task_a)
            a_end   = end_of(task_a)

            for task_b in timed_tasks[i + 1:]:
                b_start = start_of(task_b)
                b_end   = end_of(task_b)

                # Once task_b starts at or after task_a ends, no further overlap is possible
                if b_start >= a_end:
                    break

                # Two windows overlap when one starts before the other ends
                warnings.append(
                    f"TIME OVERLAP: '{task_a.name}' ({task_a.pet_name}, "
                    f"{task_a.start_time}-{self._fmt(a_end)}) "
                    f"overlaps with '{task_b.name}' ({task_b.pet_name}, "
                    f"{task_b.start_time}-{self._fmt(b_end)})."
                )

        return warnings

    def check_conflicts(self, tasks: list[Task]) -> list[str]:
        """Detect and return human-readable warnings for all scheduling problems."""
        warnings: list[str] = []
        pending = [t for t in tasks if t.status == "pending"]
        total = sum(t.duration_minutes for t in pending)

        # 1. Total time overflow
        if total > self.available_minutes:
            over = total - self.available_minutes
            warnings.append(
                f"Total pending task time ({total} min) exceeds available time "
                f"({self.available_minutes} min) by {over} min."
            )

        # 2. Single tasks that can never fit regardless of ordering
        for task in pending:
            if task.duration_minutes > self.available_minutes:
                warnings.append(
                    f"'{task.name}' ({task.duration_minutes} min) is longer than "
                    f"the entire available window ({self.available_minutes} min) "
                    f"and will never be scheduled."
                )

        # 3. High-priority tasks at risk of being excluded
        high_total = sum(
            t.duration_minutes for t in pending if t.priority == "high"
        )
        if high_total > self.available_minutes:
            warnings.append(
                f"High-priority tasks alone require {high_total} min but only "
                f"{self.available_minutes} min are available — some will be dropped."
            )

        # 4. Actual time-window overlaps (uses start_time + duration)
        warnings.extend(self.detect_time_overlaps(tasks))

        return warnings

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_plan(self, tasks: list[Task]) -> ScheduleResult:
        """Sort pending tasks by priority then time-of-day then duration; greedily fill available_minutes."""
        result = ScheduleResult()
        time_used = 0

        pending = [t for t in tasks if t.status == "pending"]

        # Sort: priority first, then time-of-day slot, then shortest duration as tiebreaker
        ordered = sorted(
            pending,
            key=lambda t: (
                _PRIORITY_ORDER.get(t.priority, 99),
                _TIME_ORDER.get(t.time_of_day, 99),
                t.duration_minutes,
            ),
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
