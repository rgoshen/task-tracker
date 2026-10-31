# TODO

## [2026-10-31] Feature: M1 Task model

**Objective:**
Define the `Task` dataclass for the `README.md` "Task object", and put pytest and a CI workflow behind it so "passing" is checked by a machine from here on. Covers issue #5 and the M1 section of `docs/implementation-plan.md`. No CLI and no storage yet. You write the tests and the code; this entry fixes the order and the traps.

**Approach:**
Branch `feature/task-model` (from `develop`). Each step is one atomic commit with its own `SUMMARY.md` entry. The order differs from the plan's checklist in two places, for the reasons under Risks.

1. `uv add --dev pytest pytest-cov`. Commit: `chore(deps): add pytest and pytest-cov`. First, because every later step is test-first.
2. Rename `Priority.MED` to `Priority.MEDIUM` in `src/task_tracker/priority.py`. Red: a test that `Priority.MEDIUM` exists and `Priority.MED` does not. Green: the rename. Commit: `refactor(priority): rename MED to MEDIUM`. Done before any task file exists, because the stored value is the enum value.
3. `Task` in `src/task_tracker/task.py`, one module per type like `priority.py` and `status.py`. Red: the four tests below, one at a time. Green: the least code. Refactor while green. Commit: `feat(task): add Task model`.
4. CI workflow running `uv run pytest` on push and pull request. Copy the `permissions` shape and the SHA-pinned `actions/checkout` and `astral-sh/setup-uv` from `.github/workflows/version-bump.yml`. Commit: `ci(tests): run pytest on push and pull request`. After step 3, never before.
5. Tests badge in `README.md` next to the Lint badge. Commit: `docs(readme): add tests badge`.
6. Open a PR into `develop`. Done when the tests pass locally and in CI.

**Tests:**
All Given/When/Then with exact values are in the M1 section of the plan. In short:

- Defaults from ID 1 and the name "Buy milk": status `Status.TO_DO`, priority `Priority.LOW`, description `""`, due `None`, date completed `None`.
- `created`, `updated`, `start`, and `stop` each fall between a timestamp taken just before and just after creation, run under a non-UTC time zone so a UTC default fails. `due` is excluded (Q2).
- A new task has `created`, `updated`, `start`, and `stop` equal; a value passed explicitly is kept.
- Every datetime field that is not `None` is naive, `tzinfo is None` (D6), and a timezone-aware value raises `ValueError`. `None` has no `tzinfo`.
- A name of `""` or `"   "`, or one that is not a string, raises `ValueError`; a padded name is stored stripped.
- `status` and `priority` given as strings become enum members; an unknown label raises `ValueError`.
- A date completed on a task that is not `DONE` raises `ValueError` (Q4, first half).
- Fields after `id` and `name` are keyword-only.
- Coverage: `uv run pytest --cov=task_tracker --cov-report=term-missing --cov-fail-under=80`.

**Risks & Trade-offs:**

- **Frozen timestamps.** `created: datetime = datetime.now()` raises no error. Checked on 2026-10-31: two instances created 0.2 s apart shared one object. The dataclass guard only rejects unhashable defaults ([dataclasses]), and a `datetime` passes. The "between before and after" test catches it. The code now reads the clock once in `__post_init__`.
- **Empty test run fails CI.** pytest exits with code 5 when it collects no tests ([pytest exit codes]), so the workflow must not merge before step 3 has real tests.
- **ID entry, decided 2026-10-31 (D5).** `id` is a required `int` and a task never assigns its own ID. `add` computes highest + 1 and passes it in (M3), so every M1 test passes an ID such as 1.
- **One "now", decided 2026-10-31 in review of PR #23 (audit finding G13).** A new task shares a single clock reading across its four timestamps through a private sentinel default, so the fields stay typed `datetime`.
- **Open spec question: does `DONE` require a date completed?** Q4 states only that a task that is not `DONE` has none. `Task(status=DONE)` has none today, and M4's sort must cope with that (audit finding G9).
- **Known limit for M5.** The model validates at construction. Assigning `task.name = ""` later skips the check, so `update` must re-validate.
- **`uv.lock` overlap.** `uv add --dev` rewrites `uv.lock`, and Dependabot PR #18 (base `main`) also changes it. Expect a possible conflict when `develop` is promoted to `main`.
- **Tests badge starts empty.** The Lint badge points at `main`, so the Tests badge will probably show no status until the workflow has run there (unverified). Merge it anyway; check it after the next promotion.
- **Scope held back.** `description` is a plain field with a default. Whether `add` and `update` expose it waits for M3 and M5, as Q3 did for `start` and `stop`.

## [2026-10-31] Feature: DONE date and one date form

**Objective:**
Apply three decisions from the project owner on 2026-10-31. A `DONE` task always has a date completed, defaulting to the moment it is created or marked done. A date completed that is passed in cannot be in the future. Every datetime is held in one form, whatever way it is passed in.
This answers the open half of the review thread on `task.py` line 21 of PR #23 and audit finding G9. Model only: no CLI and no storage.

**Approach:**
Test-first on `feature/task-model`, in this order, one commit each.

1. Normalize every datetime field. An ISO 8601 string, a `date`, or a `datetime` all become a naive `datetime` with whole seconds, so `isoformat()` always reads `YYYY-MM-DDTHH:MM:SS`. A bare date is midnight (Q6).
2. A `DONE` task with no date completed gets the shared clock reading. A date completed later than that reading raises `ValueError`.
3. Update `README.md`, the plan (Q4, D6, M1), and issue #5.

**Tests:**

- Equivalent inputs (`"2026-11-02"`, `"2026-11-02T00:00:00"`, `"2026-11-02 00:00:00"`, a `date`, a `datetime` with microseconds) give the same `due`, and `isoformat()` reads `2026-11-02T00:00:00`.
- Default timestamps carry no microseconds.
- An invalid string, a string with a UTC offset, or a value of another type raises `ValueError` that names the field.
- `Task(status=DONE)` has a date completed equal to `created`; a task that is not `DONE` has none.
- A past date completed is kept, a future one raises `ValueError`, and `datetime.now()` itself is accepted.

**Risks & Trade-offs:**

- Dropping microseconds changes values silently. That is harmless for a task list, and it keeps the M2 round trip exact when dates are saved at whole seconds.
- The model cannot tell "marked done now" from "loaded from a file", so a hand-edited `DONE` record with no date gets the load time. M2's loader must check the raw record if that matters.
- Strings and dates are accepted next to `datetime`, as labels are accepted for the enums. The field types stay `datetime`.
- Only the date completed is checked against the future. A due date may be in the future, and no other field was asked about.

[dataclasses]: https://docs.python.org/3/library/dataclasses.html#mutable-default-values
[pytest exit codes]: https://docs.pytest.org/en/stable/reference/exit-codes.html
