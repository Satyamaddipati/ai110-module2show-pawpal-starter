"""
main.py — CLI demo for PawPal+
Run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # ── Setup ────────────────────────────────────────────────────────────────
    owner = Owner("Alex")

    buddy = Pet(name="Buddy", species="Dog", age=3)
    whiskers = Pet(name="Whiskers", species="Cat", age=5)

    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    today = date.today()

    # ── Add tasks (intentionally out of chronological order) ─────────────────
    buddy.add_task(Task("Evening Walk", "18:30", "daily", "Buddy", today))
    buddy.add_task(Task("Morning Walk", "07:00", "daily", "Buddy", today))
    buddy.add_task(Task("Flea Medication", "09:00", "weekly", "Buddy", today))
    buddy.add_task(Task("Vet Appointment", "14:00", "once", "Buddy", today))

    whiskers.add_task(Task("Morning Feeding", "07:30", "daily", "Whiskers", today))
    whiskers.add_task(Task("Evening Feeding", "18:30", "daily", "Whiskers", today))  # conflict with Buddy's walk
    whiskers.add_task(Task("Grooming", "11:00", "weekly", "Whiskers", today))

    scheduler = Scheduler(owner)

    # ── Print today's schedule ────────────────────────────────────────────────
    scheduler.print_schedule()

    # ── Demonstrate filtering ─────────────────────────────────────────────────
    print("🐾 Buddy's tasks only:")
    for t in scheduler.sort_by_time(scheduler.filter_by_pet("Buddy")):
        print(f"   {t}")

    # ── Demonstrate task completion + recurrence ──────────────────────────────
    print("\n✅ Completing Buddy's Morning Walk (daily — should auto-schedule tomorrow)...")
    morning_walk = buddy.tasks[1]  # "Morning Walk"
    next_task = scheduler.complete_task(morning_walk)
    if next_task:
        print(f"   Next occurrence created: {next_task}")

    # ── Show updated pending tasks ────────────────────────────────────────────
    print("\n📋 Pending tasks after completion:")
    for t in scheduler.filter_by_status(completed=False):
        print(f"   {t}")


if __name__ == "__main__":
    main()
