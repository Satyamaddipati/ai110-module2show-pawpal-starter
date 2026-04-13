"""
tests/test_pawpal.py — Automated test suite for PawPal+
Run with: python -m pytest
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def today():
    return date.today()

@pytest.fixture
def owner():
    return Owner("Test Owner")

@pytest.fixture
def pet_with_tasks(today):
    pet = Pet("Rex", "Dog", 2)
    pet.add_task(Task("Walk", "08:00", "daily", "Rex", today))
    pet.add_task(Task("Feed", "17:00", "daily", "Rex", today))
    pet.add_task(Task("Medication", "12:00", "weekly", "Rex", today))
    return pet

@pytest.fixture
def scheduler(owner, pet_with_tasks):
    owner.add_pet(pet_with_tasks)
    return Scheduler(owner)


# ── Task Completion ────────────────────────────────────────────────────────────

class TestTaskCompletion:
    def test_mark_complete_changes_status(self, today):
        """Calling mark_complete() should flip completed to True."""
        task = Task("Walk", "08:00", "once", "Rex", today)
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_once_task_returns_no_followup(self, today):
        """A 'once' task should not generate a follow-up."""
        task = Task("Vet", "10:00", "once", "Rex", today)
        result = task.mark_complete()
        assert result is None

    def test_daily_task_returns_tomorrow(self, today):
        """A daily task should generate a follow-up due tomorrow."""
        task = Task("Walk", "08:00", "daily", "Rex", today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False

    def test_weekly_task_returns_next_week(self, today):
        """A weekly task should generate a follow-up due in 7 days."""
        task = Task("Grooming", "11:00", "weekly", "Rex", today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)


# ── Task Addition ──────────────────────────────────────────────────────────────

class TestTaskAddition:
    def test_adding_task_increases_count(self, today):
        """Pet should have one more task after add_task()."""
        pet = Pet("Luna", "Cat", 3)
        initial_count = len(pet.tasks)
        pet.add_task(Task("Feed", "07:00", "daily", "Luna", today))
        assert len(pet.tasks) == initial_count + 1

    def test_get_pending_tasks_excludes_completed(self, today):
        """get_pending_tasks() should exclude completed tasks."""
        pet = Pet("Luna", "Cat", 3)
        t1 = Task("Feed", "07:00", "daily", "Luna", today)
        t2 = Task("Play", "15:00", "once", "Luna", today)
        pet.add_task(t1)
        pet.add_task(t2)
        t1.mark_complete()
        pending = pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].description == "Play"


# ── Sorting Correctness ────────────────────────────────────────────────────────

class TestSorting:
    def test_sort_by_time_is_chronological(self, scheduler):
        """sort_by_time() must return tasks in HH:MM ascending order."""
        sorted_tasks = scheduler.sort_by_time()
        times = [t.time for t in sorted_tasks]
        assert times == sorted(times)

    def test_sort_handles_empty_list(self, scheduler):
        """sort_by_time() on an empty list should return an empty list."""
        assert scheduler.sort_by_time([]) == []

    def test_sort_does_not_mutate_source(self, owner, today):
        """sort_by_time() should return a new list, not modify in place."""
        pet = Pet("Mochi", "Cat", 1)
        pet.add_task(Task("B task", "18:00", "once", "Mochi", today))
        pet.add_task(Task("A task", "06:00", "once", "Mochi", today))
        owner.add_pet(pet)
        sched = Scheduler(owner)
        original_order = [t.description for t in pet.tasks]
        sched.sort_by_time()
        assert [t.description for t in pet.tasks] == original_order


# ── Recurrence Logic ──────────────────────────────────────────────────────────

class TestRecurrence:
    def test_complete_daily_adds_next_to_pet(self, owner, today):
        """Completing a daily task via Scheduler should add a tomorrow task to the pet."""
        pet = Pet("Buddy", "Dog", 2)
        task = Task("Walk", "08:00", "daily", "Buddy", today)
        pet.add_task(task)
        owner.add_pet(pet)
        sched = Scheduler(owner)

        initial_count = len(pet.tasks)
        sched.complete_task(task)

        assert len(pet.tasks) == initial_count + 1
        new_task = pet.tasks[-1]
        assert new_task.due_date == today + timedelta(days=1)
        assert new_task.completed is False

    def test_complete_once_does_not_add_followup(self, owner, today):
        """Completing a 'once' task should not add any new tasks."""
        pet = Pet("Buddy", "Dog", 2)
        task = Task("Vet", "10:00", "once", "Buddy", today)
        pet.add_task(task)
        owner.add_pet(pet)
        sched = Scheduler(owner)

        sched.complete_task(task)
        assert len(pet.tasks) == 1  # unchanged


# ── Conflict Detection ────────────────────────────────────────────────────────

class TestConflictDetection:
    def test_no_conflicts_when_times_differ(self, scheduler):
        """No warnings for tasks at different times."""
        warnings = scheduler.detect_conflicts()
        assert warnings == []

    def test_detects_same_time_conflict(self, owner, today):
        """Two tasks at the same time on same date should produce a warning."""
        pet = Pet("Buddy", "Dog", 2)
        pet.add_task(Task("Walk", "09:00", "once", "Buddy", today))
        pet.add_task(Task("Vet", "09:00", "once", "Buddy", today))
        owner.add_pet(pet)
        sched = Scheduler(owner)

        warnings = sched.detect_conflicts()
        assert len(warnings) == 1
        assert "09:00" in warnings[0]

    def test_conflict_across_pets(self, owner, today):
        """Conflicts are detected across different pets too."""
        pet1 = Pet("Buddy", "Dog", 2)
        pet2 = Pet("Luna", "Cat", 3)
        pet1.add_task(Task("Walk", "10:00", "once", "Buddy", today))
        pet2.add_task(Task("Feed", "10:00", "once", "Luna", today))
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        sched = Scheduler(owner)

        warnings = sched.detect_conflicts()
        assert len(warnings) == 1

    def test_no_conflict_different_dates(self, owner, today):
        """Same time on different dates should NOT be flagged."""
        pet = Pet("Buddy", "Dog", 2)
        pet.add_task(Task("Walk", "09:00", "once", "Buddy", today))
        pet.add_task(Task("Walk", "09:00", "once", "Buddy", today + timedelta(days=1)))
        owner.add_pet(pet)
        sched = Scheduler(owner)

        warnings = sched.detect_conflicts()
        assert warnings == []


# ── Filtering ─────────────────────────────────────────────────────────────────

class TestFiltering:
    def test_filter_by_pet_returns_only_that_pet(self, owner, today):
        """filter_by_pet() should only return tasks for the named pet."""
        p1 = Pet("Buddy", "Dog", 2)
        p2 = Pet("Luna", "Cat", 3)
        p1.add_task(Task("Walk", "08:00", "daily", "Buddy", today))
        p2.add_task(Task("Feed", "07:00", "daily", "Luna", today))
        owner.add_pet(p1)
        owner.add_pet(p2)
        sched = Scheduler(owner)

        results = sched.filter_by_pet("Buddy")
        assert all(t.pet_name == "Buddy" for t in results)
        assert len(results) == 1

    def test_filter_by_status_pending(self, scheduler):
        """filter_by_status(completed=False) should return only incomplete tasks."""
        all_tasks = scheduler.owner.get_all_tasks()
        all_tasks[0].mark_complete()
        pending = scheduler.filter_by_status(completed=False)
        assert all(not t.completed for t in pending)

    def test_pet_with_no_tasks(self, owner):
        """A pet with no tasks should produce an empty filter result."""
        empty_pet = Pet("Ghost", "Cat", 1)
        owner.add_pet(empty_pet)
        sched = Scheduler(owner)
        assert sched.filter_by_pet("Ghost") == []
