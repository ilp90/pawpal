# PawPal+ Project Reflection

## 1. System Design

### Core User Actions

The three core actions a PawPal+ user should be able to perform are:

1. **Register their pet** — Enter basic information about their pet (name, species, age, breed) so the system can tailor care recommendations appropriately.
2. **Add and manage care tasks** — Create tasks like walks, feeding, medication, and grooming, each with a duration (in minutes) and a priority level (low / medium / high).
3. **Generate today's daily care plan** — Ask the system to produce an ordered schedule of tasks that fits within the owner's available time, prioritizing the most important tasks first, and explain why each task was included.

**a. Initial design**

The system is built around four classes:

- **Owner** — Holds the owner's name and their available time per day (in minutes). Maintains a list of pets and any scheduling preferences (e.g., no tasks before 8 AM). Responsible for adding pets and surfacing the constraint of available time to the scheduler.
- **Pet** — Holds the pet's name, species, age, breed, and any owner notes. Owns a list of Task objects and is responsible for adding/retrieving them. Using a Python dataclass keeps the data clean and easy to compare.
- **Task** — A dataclass representing a single care action: title, duration, priority, category (walk/feed/med/grooming/enrichment), and completion status. Lightweight by design — it holds data and can mark itself complete.
- **Scheduler** — The "brain" of the system. It takes an Owner and a Pet, collects their tasks, sorts by priority, and greedily fits tasks into the available time window. It also generates a plain-English explanation of the resulting plan.

**Relationships:** An Owner owns one or more Pets; each Pet has zero or more Tasks; the Scheduler uses the Owner (for time constraints) and the Pet (for tasks) to produce a schedule.

```mermaid
classDiagram
    class Owner {
        +str name
        +int available_minutes_per_day
        +list~str~ preferences
        +list~Pet~ pets
        +add_pet(pet: Pet) None
        +get_pets() list
        +set_available_time(minutes: int) None
    }
    class Pet {
        +str name
        +str species
        +int age
        +str breed
        +str notes
        +list~Task~ tasks
        +add_task(task: Task) None
        +get_tasks() list
    }
    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str category
        +bool completed
        +mark_complete() None
    }
    class Scheduler {
        +Owner owner
        +Pet pet
        +list~Task~ tasks
        +generate_schedule() list
        +prioritize_tasks() list
        +explain_plan(schedule: list) str
    }
    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler --> Owner : uses
    Scheduler --> Pet : schedules for
    Scheduler --> Task : orders
```

**b. Design changes**

During the skeleton and implementation phases, two refinements emerged:

- **Pet became a dataclass (from a plain class).** The original sketch had `Pet` as a regular class, but since it primarily holds data with only two helper methods, `@dataclass` reduces boilerplate and makes instances directly comparable with `==` — useful for testing. The `tasks` list is declared as `field(default_factory=list)` to avoid the mutable-default-argument bug. Owner stayed a plain class because it has richer initialisation logic that doesn't fit cleanly into dataclass constraints.

- **Scheduler changed from `(owner, pet)` to `(owner)` only.** The initial UML passed a single `Pet` to `Scheduler`, but the project brief says the scheduler should "retrieve, organise, and manage tasks *across* pets" (plural). Passing just an `Owner` is cleaner: `Scheduler` calls `owner.get_all_tasks()` to collect every task from every pet in one step. This also makes it trivial to add a second pet — the scheduler doesn't need to change at all. A new helper `Owner.get_all_tasks()` was added to centralise that aggregation logic.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints: **priority** (high/medium/low) and the **owner's total available minutes per day**. Priority was chosen as the primary sort key because a pet owner cares more about urgency (medication before enrichment) than about clock time. The daily budget is the hard cap — no task is added once time runs out. A secondary sort by duration (shorter tasks first within the same priority tier) helps fit more tasks into the remaining budget after high-priority items are placed.

**b. Tradeoffs**

The conflict detector only flags tasks that have an explicit `start_time` set. Tasks without a start time are auto-assigned sequential slots by `generate_schedule()` and are therefore guaranteed not to overlap each other — but any manually pre-assigned time is trusted at face value and checked against the rest.

This is a deliberate simplification: checking every possible pair regardless of whether a time was set would produce false positives for tasks that were never actually time-pinned. The tradeoff is that a user who forgets to set `start_time` will not get a conflict warning even if they mentally intend two tasks to overlap — but the app never silently crashes or produces an invalid schedule.

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
