# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The system is designed around three core actions a user needs to perform:

1. **Add a pet to the system.** The user enters basic information about themselves and their pet (such as the pet's name, species, and any relevant health notes). This gives the app the context it needs to personalize care recommendations and store tasks associated with that specific pet.

2. **Add and manage care tasks.** The user can create individual care tasks — such as a morning walk, medication, feeding, or grooming — and assign each task a duration (in minutes) and a priority level. This lets the system understand what needs to happen and how urgently, so it can make sensible scheduling decisions even when time is limited.

3. **Generate and view a daily care plan.** The user requests a daily schedule, and the app produces an ordered plan of tasks based on the available time and each task's priority. The plan is displayed clearly, with an explanation of why tasks were included or excluded, so the owner understands the reasoning and can trust the schedule.

- What classes did you include, and what responsibilities did you assign to each?

I chose four classes, each with a single clear responsibility:

| Class | Responsibility |
|---|---|
| **Task** | Holds all data for a single care item (name, duration, priority, status) and knows how to mark itself complete or update its fields. |
| **Pet** | Represents one animal. Owns a list of Tasks and exposes methods to add a new task or retrieve the current task list. |
| **Owner** | Represents the person using the app. Owns a list of Pets and can add a new pet or collect every task across all pets into one flat list. |
| **Scheduler** | The planning brain. Takes a flat task list and produces a daily schedule by sorting on priority/duration, filtering by pet if needed, and flagging any time conflicts. |

```mermaid
classDiagram
    class ScheduleResult {
        +List~Task~ scheduled
        +List~Tuple~ excluded
    }

    class Task {
        +String name
        +int duration_minutes
        +String pet_name
        +String priority
        +String status
        +mark_complete() void
        +update(name, duration, priority) void
    }

    class Pet {
        +String name
        +String species
        +String health_notes
        +List~Task~ tasks
        +add_task(task: Task) void
        +get_tasks() List~Task~
    }

    class Owner {
        +String name
        +String contact_info
        +List~Pet~ pets
        +add_pet(pet: Pet) void
        +get_all_tasks() List~Task~
    }

    class Scheduler {
        +int available_minutes
        +sort_by_priority(tasks: List~Task~) List~Task~
        +sort_by_duration(tasks: List~Task~) List~Task~
        +filter_by_pet(tasks: List~Task~, pet: Pet) List~Task~
        +check_conflicts(tasks: List~Task~) List~String~
        +generate_plan(tasks: List~Task~) ScheduleResult
    }

    Owner "1" --> "1..*" Pet : owns
    Pet  "1" --> "0..*" Task : has
    Scheduler ..> Task : uses
    Scheduler ..> Owner : uses
    Scheduler ..> ScheduleResult : returns
```

**b. Design changes**

Yes, reviewing the skeleton against the README revealed two gaps that required changes before implementation began:

**Change 1 — Added `pet_name: str` to `Task`**

The original `Task` dataclass had no field linking it back to its pet. `Scheduler.filter_by_pet()` accepts a flat task list and a `Pet` object, but without a `pet_name` on each task there was no way to filter without cross-referencing every `pet.tasks` list. Adding `pet_name` as a field on `Task` makes filtering a simple string comparison and removes the hidden dependency on object identity.

**Change 2 — Added `ScheduleResult` dataclass; changed `generate_plan` return type**

The original `generate_plan` returned `list[Task]` (only the scheduled tasks). The README explicitly says the app should *explain why* it chose the plan. Returning a plain list silently discards all reasoning. A new `ScheduleResult` dataclass was introduced to hold both `scheduled: list[Task]` and `excluded: list[tuple[Task, str]]` (each excluded task paired with a human-readable reason). `generate_plan` now returns a `ScheduleResult` so the UI layer can display the full explanation.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints, in descending order of importance:

1. **Available time** — the hard limit. A task that does not fit in the remaining window is excluded, regardless of priority.
2. **Priority level** — `high` tasks are always attempted before `medium` or `low` tasks. This ensures critical care (medication, feeding) is never pushed out by optional activities.
3. **Duration** — used as a tiebreaker within the same priority group. Shorter tasks are scheduled first, which maximises the number of tasks that fit in the window (classic greedy knapsack heuristic).

`time_of_day` slot (morning / afternoon / evening) is a secondary sort key between priority and duration — it nudges the plan into a natural daily rhythm without overriding the priority constraint.

**b. Tradeoffs**

**Tradeoff: Greedy ordering can exclude a high-priority task in favour of multiple smaller ones**

`generate_plan` sorts by priority first, then by shortest duration within the same priority tier. This means if two tasks share `priority="high"`, the shorter one is scheduled first. In most cases this is the right call — fitting more tasks into the day is generally better for a busy pet owner.

However, the tradeoff shows up in an edge case: imagine a 60-minute window with these two `high` tasks:

| Task | Duration |
|---|---|
| Morning walk | 55 min |
| Joint supplement + Feeding + Litter | 5 + 10 + 10 = 25 min |

The greedy approach schedules the three short tasks first (25 min), leaving only 35 min — not enough for the 55-minute walk. The walk is excluded even though it may be the most important task for the pet's health.

A true optimal solution would require solving the 0/1 knapsack problem (NP-hard), which is overkill for a personal pet care app. The greedy approach was kept because it is fast (O(n log n)), predictable, and correct for the vast majority of realistic task lists. The `check_conflicts` warnings — specifically the "high-priority tasks alone exceed available time" check — alert the owner when this edge case is about to occur, so they can adjust manually.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
