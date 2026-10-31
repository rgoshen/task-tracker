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

- Defaults from only the name "Buy milk": status `Status.TO_DO`, priority `Priority.LOW`, description `""`, due `None`, date completed `None`.
- `created`, `updated`, `start`, and `stop` each fall between a timestamp taken just before and just after creation. `due` is excluded (Q2).
- Every datetime field is naive, `tzinfo is None` (D6).
- A name of `""` or `"   "` raises `ValueError`.
- Coverage: `uv run pytest --cov=task_tracker --cov-report=term-missing --cov-fail-under=80`.

**Risks & Trade-offs:**

- **Frozen timestamps.** `created: datetime = datetime.now()` raises no error. Checked on 2026-10-31: two instances created 0.2 s apart shared one object. The dataclass guard only rejects unhashable defaults ([dataclasses]), and a `datetime` passes. The "between before and after" test is the only thing that catches it; `default_factory` is the fix.
- **Empty test run fails CI.** pytest exits with code 5 when it collects no tests ([pytest exit codes]), so the workflow must not merge before step 3 has real tests.
- **Open design question: how the ID enters a task.** Highest + 1 (D5) needs the other tasks, so a task cannot assign its own ID. Constructor argument or an optional field set on add? The plan's "Think about" asks you to decide; the choice shapes M2 and M3, so make it before step 3 and note it in `SUMMARY.md`.
- **`uv.lock` overlap.** `uv add --dev` rewrites `uv.lock`, and Dependabot PR #18 (base `main`) also changes it. Expect a possible conflict when `develop` is promoted to `main`.
- **Tests badge starts empty.** The Lint badge points at `main`, so the Tests badge will probably show no status until the workflow has run there (unverified). Merge it anyway; check it after the next promotion.
- **Scope held back.** `description` is a plain field with a default. Whether `add` and `update` expose it waits for M3 and M5, as Q3 did for `start` and `stop`.

[dataclasses]: https://docs.python.org/3/library/dataclasses.html#mutable-default-values
[pytest exit codes]: https://docs.pytest.org/en/stable/reference/exit-codes.html
