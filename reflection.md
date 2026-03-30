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

I used **Claude Code** (not GitHub Copilot) throughout this project as my primary AI collaborator. Claude was involved in three distinct phases:

1. **Design brainstorming** — I described the app's goals in plain language and asked Claude to help me think through which classes were actually necessary. Rather than starting with code, we started with responsibilities: what does each object *own* and what does it *know how to do*?

2. **Implementation scaffolding** — Once the UML was settled, I used Claude to generate the initial class skeletons. This let me focus on verifying the structure was correct before writing any logic.

3. **Debugging and refactoring** — When the Streamlit UI and the scheduler weren't connecting cleanly, I pasted the relevant functions into a new chat and asked targeted questions like: *"Why does `generate_plan` return an empty list when tasks exist?"* Scoped questions got faster, more accurate answers than broad ones.

The most effective prompt pattern was: **give context first, then ask one specific question.** Vague prompts like "fix my scheduler" produced generic answers. Prompts like "here is my `generate_plan` method — it sorts by priority but ignores duration as a tiebreaker, can you show me how to add that?" produced exactly what I needed.

**b. Judgment and verification**

When I asked Claude to generate the initial `Scheduler` class, it returned a `generate_plan` method that sorted tasks purely by priority string (`"high"`, `"medium"`, `"low"`) using Python's default alphabetical sort. Alphabetically, `"high" > "low" > "medium"` — which would have scheduled `medium` tasks before `low` ones correctly, but only by accident. If a new priority like `"critical"` were ever added, the sort would silently break.

I rejected this approach and replaced it with an explicit priority map:

```python
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
tasks.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 99))
```

This makes the ordering intentional and self-documenting. I verified it by writing a quick manual test with three tasks in reversed priority order and confirming the output sequence was correct before moving on.

Using **separate Claude chat sessions for different phases** (design → implementation → debugging) helped me stay organized because each session had a focused context. A single long conversation tends to drift — early assumptions get buried and Claude starts optimizing for the current message rather than the overall design. Starting a fresh session for each phase forced me to re-state the key constraints explicitly, which also helped me catch inconsistencies in my own thinking.

**Summary — being the "lead architect" with AI:**

The clearest lesson from this project is that AI is a fast, capable *implementer* but a poor *decision-maker* about what to build. Claude could generate a working scheduler in seconds, but it could not know that I wanted the exclusion reasoning surfaced to the user, or that I cared more about predictability than optimality. Every structural decision — what classes exist, what they return, what the UI exposes — had to come from me. The moment I handed over an architectural decision without thinking it through first, I got code that worked but did not fit the system. Staying in the "lead architect" role meant treating every AI output as a draft to be reviewed, not a solution to be accepted.

---

## 4. Testing and Verification

**a. What you tested**

- **Task scheduling within time limit** — verified that `generate_plan` only includes tasks whose cumulative duration fits within the available time window.
- **Priority ordering** — confirmed that `high` priority tasks are always scheduled before `medium` and `low`, regardless of insertion order.
- **Duration tiebreaking** — verified that within the same priority tier, shorter tasks are scheduled first.
- **Exclusion reporting** — checked that tasks left out of the plan appear in `ScheduleResult.excluded` with a human-readable reason string.
- **Empty task list** — confirmed the scheduler returns an empty plan gracefully rather than throwing an error.

These tests mattered because the scheduler's correctness is the core promise of the app. A bug in priority ordering or time accounting would produce a plan the user cannot trust, which defeats the entire purpose.

**b. Confidence**

I am confident the scheduler handles the common cases correctly. The priority map and greedy sort are simple enough to reason about by inspection, and the manual tests I ran covered the main paths.

Edge cases I would test next with more time:
- **Exact fit** — a task whose duration equals the remaining time exactly (off-by-one risk).
- **All tasks same priority** — ensure duration tiebreaking is stable.
- **Zero available time** — should return an empty plan, not an error.
- **Duplicate task names** — the UI uses task name as a display key; duplicates could cause confusion.
- **Very large task lists** — confirm the O(n log n) sort stays fast enough for real-world use.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the `ScheduleResult` dataclass decision. The original design returned only a list of scheduled tasks, which meant all the reasoning behind the plan was silently discarded. Introducing `ScheduleResult` to carry both `scheduled` and `excluded` (with reasons) made the UI genuinely informative — the owner can see not just what is planned, but *why* something was left out. That single design change elevated the app from a task filter into an actual planning tool.

**b. What you would improve**

If I had another iteration, I would add **persistent storage**. Right now all data lives in Streamlit's session state and is lost on page refresh. Even a simple JSON file or SQLite database would make the app genuinely usable day-to-day. I would also introduce a `time_of_day` constraint that actually blocks scheduling — currently it is a sort hint, not a hard boundary, which means a "morning" task could still appear at any point in the plan.

**c. Key takeaway**

The most important thing I learned is that **AI tools amplify your design skills, they do not replace them.** When I had a clear mental model of what I wanted — concrete class names, specific return types, explicit constraints — Claude produced excellent code quickly. When I was fuzzy on the design, Claude produced plausible-looking code that quietly violated the system's intent. The quality of the AI's output was almost entirely determined by the quality of the thinking I brought to the conversation before typing a single prompt.

---

## 📸 Demo

<a href="/course_images/ai110/Screenshot 2026-03-30 012722.png" target="_blank"><img src='/course_images/ai110/Screenshot 2026-03-30 012722.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

<a href="/course_images/ai110/Screenshot 2026-03-30 012736.png" target="_blank"><img src='/course_images/ai110/Screenshot 2026-03-30 012736.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

<a href="/course_images/ai110/Screenshot 2026-03-30 012741.png" target="_blank"><img src='/course_images/ai110/Screenshot 2026-03-30 012741.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>
