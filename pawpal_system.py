"""
PawPal+ System Logic Layer
Defines Owner, Pet, Task, and Scheduler classes for pet care management.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str  # "HH:MM" 24-hour format
    frequency: str  # "once", "daily", "weekly"
    pet_name: str
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return a follow-up task if recurring."""
        self.completed = True
        if self.frequency == "daily":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None

    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.time} — {self.description} ({self.pet_name}, {self.frequency})"


@dataclass
class Pet:
    """Stores pet details and its list of tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return only incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.completed]

    def __repr__(self) -> str:
        return f"{self.name} ({self.species}, age {self.age})"


class Owner:
    """Manages a collection of pets and provides access to all tasks."""

    def __init__(self, name: str) -> None:
        """Initialize an Owner with a name and empty pet list."""
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's roster."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find a pet by name, or return None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def __repr__(self) -> str:
        return f"Owner({self.name}, {len(self.pets)} pets)"


class Scheduler:
    """Organizes and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Initialize the Scheduler with an Owner instance."""
        self.owner = owner

    # ── Sorting ──────────────────────────────────────────────────────────────

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted chronologically by their HH:MM time string."""
        tasks = tasks if tasks is not None else self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    # ── Filtering ─────────────────────────────────────────────────────────────

    def filter_by_status(self, completed: bool = False) -> list[Task]:
        """Return tasks filtered by completion status."""
        return [t for t in self.owner.get_all_tasks() if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks (any status) belonging to a specific pet."""
        return [t for t in self.owner.get_all_tasks()
                if t.pet_name.lower() == pet_name.lower()]

    def get_todays_schedule(self) -> list[Task]:
        """Return today's pending tasks sorted by time."""
        today = date.today()
        pending = [t for t in self.owner.get_all_tasks()
                   if not t.completed and t.due_date <= today]
        return self.sort_by_time(pending)

    # ── Recurring tasks ───────────────────────────────────────────────────────

    def complete_task(self, task: Task) -> Optional[Task]:
        """
        Mark a task complete. If it recurs, add the next occurrence to the pet
        and return it; otherwise return None.
        """
        next_task = task.mark_complete()
        if next_task:
            pet = self.owner.get_pet(task.pet_name)
            if pet:
                pet.add_task(next_task)
        return next_task

    # ── Conflict detection ────────────────────────────────────────────────────

    def detect_conflicts(self) -> list[str]:
        """
        Check for tasks scheduled at the same time on the same due_date.
        Returns a list of human-readable warning strings (empty if no conflicts).
        """
        warnings: list[str] = []
        all_tasks = self.owner.get_all_tasks()
        seen: dict[tuple, list[Task]] = {}

        for task in all_tasks:
            key = (task.due_date, task.time)
            seen.setdefault(key, []).append(task)

        for (due, time), tasks in seen.items():
            if len(tasks) > 1:
                names = ", ".join(t.description for t in tasks)
                warnings.append(
                    f"⚠ Conflict at {time} on {due}: [{names}]"
                )
        return warnings

    # ── Display ───────────────────────────────────────────────────────────────

    def print_schedule(self) -> None:
        """Print today's schedule to the terminal in a readable format."""
        schedule = self.get_todays_schedule()
        conflicts = self.detect_conflicts()

        print(f"\n{'='*50}")
        print(f"  📅 Today's Schedule for {self.owner.name}")
        print(f"{'='*50}")

        if not schedule:
            print("  No pending tasks for today!")
        else:
            for task in schedule:
                print(f"  {task}")

        if conflicts:
            print(f"\n{'─'*50}")
            print("  Conflict Warnings:")
            for w in conflicts:
                print(f"  {w}")

        print(f"{'='*50}\n")
