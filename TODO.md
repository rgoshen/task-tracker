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
- A new task takes one clock reading for `created`, `updated`, `start`, and `stop` (proved with a controlled clock). `created` and `updated` cannot be given; `start` and `stop` can, within the rules in the entry below.
- Every datetime field that is not `None` is naive, `tzinfo is None` (D6), and a timezone-aware value raises `ValueError`. `None` has no `tzinfo`.
- A name of `""` or `"   "`, or one that is not a string, raises `ValueError`; a padded name is stored stripped.
- `status` and `priority` given as strings become enum members; an unknown label raises `ValueError`.
- A date completed on a task that is not `DONE` raises `ValueError` (Q4). The rest of the `DONE` rules are in the entry below.
- Fields after `id` and `name` are keyword-only.
- Coverage: `uv run pytest --cov=task_tracker --cov-report=term-missing --cov-fail-under=80`.

**Risks & Trade-offs:**

- **Frozen timestamps.** `created: datetime = datetime.now()` raises no error. Checked on 2026-10-31: two instances created 0.2 s apart shared one object. The dataclass guard only rejects unhashable defaults ([dataclasses]), and a `datetime` passes. The "between before and after" test catches it. The code now reads the clock once in `__post_init__`.
- **Empty test run fails CI.** pytest exits with code 5 when it collects no tests ([pytest exit codes]), so the workflow must not merge before step 3 has real tests.
- **ID entry, decided 2026-10-31 (D5).** `id` is a required `int` and a task never assigns its own ID. `add` computes highest + 1 and passes it in (M3), so every M1 test passes an ID such as 1.
- **One "now", decided 2026-10-31 in review of PR #23 (audit finding G13).** A new task shares a single clock reading across its four timestamps through a private sentinel default, so the fields stay typed `datetime`.
- **`DONE` and its date, decided 2026-10-31 by the project owner.** A `DONE` task always has a date completed, defaulting to the moment it was marked done, and a date passed in cannot be in the future. M4's sort no longer has to cope with a `DONE` task that has none (audit finding G9). See the entry below.
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

## [2026-10-31] Feature: system-stamped created and updated, and a consistent timeline

**Objective:**
Apply two decisions from the project owner on 2026-10-31. `created` and `updated` are always the moment the task was created or updated and are never set by the user. A task's `start` is never before its `created`, and its `stop` is never after its date completed. Model only: no CLI and no storage.

**Approach:**
Test-first on `feature/task-model`, in this order, one commit each.

1. `created` and `updated` stop being constructor arguments. The model sets both to the shared clock reading when the task is built. The M2 loader restores stored values through a deliberate `Task.restore()`, which M2 adds; M5's `update` stamps `updated` through the model.
2. `start` before `created` raises `ValueError`. `stop` after the date completed raises `ValueError`. A done task's default `stop` is its date completed, so a past date completed does not collide with a default of "now".
3. Update `README.md`, the plan (M1 and M2), and issues #5 and #6.
4. Amended the same day by the owner: the full timeline, `created <= start <= stop <= date completed`. This adds `stop` not before `start` or `created`, and `start` not after `stop` or the date completed. A new task can then only be done at the moment it is created, so step 2's done-task default for `stop` can never differ from "now" and is removed.
   The default `stop` becomes the later of now and `start`, so a planned future `start` does not collide with it.

**Tests:**

- Passing `created` or `updated` raises `TypeError`.
- A new task has `created`, `updated`, and `start` equal to the one clock reading.
- A `start` before `created` raises `ValueError` naming the field; a later `start` is kept.
- A `stop` after the date completed raises `ValueError`; a `stop` equal to it is accepted; a task that is not done has no limit on `stop`.
- A done task given a past date completed has that date as its default `stop`.

**Risks & Trade-offs:**

- Without a constructor path for `created` and `updated`, the M2 round trip needs `Task.restore()`. That is deliberate, but M2 must now build it, and the plan says so.
- The full timeline makes a past date completed unreachable through the constructor, because `created` is always now. A new task can only be done now. Past dates matter for a task that already existed, so M2's `Task.restore()` and M5's `update` carry the tests for them.
- A planned future `start` needs `stop` to be at least that late, so the default `stop` follows `start`.
- A `start` after `created` is allowed, including a date in the future, because only "not before created" was asked.

## [2026-11-01] Feature: M2 Save and load

**Objective:**
Save a list of tasks to a JSON file and load it back unchanged, so M3 can build `add` and `list` on top. Covers issue #6 and the M2 section of `docs/implementation-plan.md`.
Produces `load(path)` (a list of tasks, empty when the file is missing), `save(tasks, path)` (atomic, creating parent directories), and `Task.restore()`, the one deliberate way to rebuild a task with its stored `created` and `updated`. No CLI yet. You write the tests and the code; this entry fixes the order and the traps.

**Approach:**
Branch `feature/task-storage` (from `develop`). One atomic commit per step, each with its own `SUMMARY.md` entry. New module `src/task_tracker/storage.py` with tests in `tests/test_storage.py`; the `Task.restore` tests go in `tests/test_task.py`. Standard library only, so `uv.lock` does not change.

1. Refactor while green: separate the stamping of `created` and `updated` from the validation in `Task.__post_init__`, so a second entry point can run the same rules. The existing tests are the safety net, so no new test. Commit: `refactor(task): separate stamping from validation`.
2. `Task.restore(...)`, test-first. It takes every field, including `created`, `updated`, `start`, and `stop`, and applies the constructor's rules with two differences: it never fills in a missing value (a stored record is complete), and the timeline is checked against the stored `created`, not the clock. Commit: `feat(task): add Task.restore for stored records`.
3. `load` of a missing file (`[]`, nothing created), then `save` and `load` together for the round trip, creating missing directories. The round trip needs `restore` because task 2 is `DONE` with a past date completed. Commit: `feat(storage): save and load tasks`.
4. `load` strictness: bad JSON, wrong shape, missing or unknown fields, a wrong `id` type, duplicate IDs. Every error names the file and the record. Commit: `feat(storage): reject a corrupt task file`.
5. Atomic `save`. Write the fails-partway test while `save` is still a plain write and watch it fail because the old contents are gone. Then write a temp file in the target's own directory and `os.replace` it over the target, removing the temp file on failure. Once green, break the atomic code on purpose and confirm the test goes red again. Commit: `feat(storage): write the task file atomically`.
6. Docs: tick the M2 boxes in the plan and issue #6, record the extra rules below in both, and add audit findings G2 and G3 to the plan (queued until PR #23 merged). Commit: `docs(plan): record the M2 rules`.
7. Open a PR into `develop`. Done when the tests pass locally and in CI, coverage on changed code is at least 80%, and the CI-version Python linters and the Markdown linters are clean locally.

**Tests:**
The seven Given/When/Then items are in the M2 section of the plan. In addition:

- `Task.restore` keeps the stored `created` and `updated`, accepts a past date completed (created 2026-10-10, completed 2026-10-15), and raises `ValueError` for each broken timeline link with its own message, as the constructor does.
- `Task.restore` raises `ValueError` when `updated` is before `created`, when a `DONE` record has no date completed (the constructor would fill in "now"; a stored record must not), and when a task that is not `DONE` has one.
- `Task.restore` turns ISO 8601 strings into the one datetime form, as the constructor does. The constructor still raises `TypeError` for `created=`.
- The fails-partway test makes the serializer write some output and then raise, and asserts that the old contents are unchanged and no temp file is left in the directory. A failure that raises before any byte is written passes against a plain write too (audit finding G2). A second test makes `os.replace` raise and checks the same two things.
- Corrupt file: `not json`, an empty file, JSON that is an object instead of a list, a list of non-objects, a record with a missing field, a record with an unknown field, an `id` that is a string or `true`, and two records with the same `id`. Each raises `ValueError` naming the file, and the file is unchanged.
- Saving `[]` writes a file that loads as `[]`.

**Risks & Trade-offs:**

- **Rules beyond the plan, proposed 2026-11-01 (veto any).** A stored record must be complete and internally consistent: `updated` not before `created`; a `DONE` record has a date completed; every field present; no unknown fields; `id` an `int` of 1 or more and not a `bool`; no null `created`, `updated`, `start`, or `stop`; unique IDs.
  Unknown fields are rejected, not ignored, because `save` rewrites the whole file (D1), so ignoring them would delete them on the next save.
  Changed on review of PR #25 (2026-11-01): a "not later than now" check on stored stamps was dropped. Naive local time (D6) means a clock set back an hour, a changed time zone, or a fixed clock would make a file that was valid when saved unloadable, and every command that loads first would be locked out of all tasks.
  The constructor still rejects a future date completed, as M1 did; a hand-edited far-future date on a stored task now loads.
- **`restore` shares the validation, decided 2026-11-01.** `__post_init__` is split into stamping and validation (step 1). `restore` builds the object without calling `__init__`, assigns the stored fields, and runs the same validation.
  Rejected: hidden `_created` and `_updated` init parameters, which reopen the back door M1 closed, and a second copy of the rules, which drifts apart when M5 changes one.
- **Conversion lives in `storage.py`, decided 2026-11-01.** Private `_to_record` and `_from_record` functions sit beside `save` and `load`, and the expected field names come from `dataclasses.fields(Task)` so a new field cannot be forgotten. Rejected for now: `Task.to_record()` and `Task.from_record()`, which make the model aware of its storage format. M8 revisits.
- **`restore` is a door.** The constructor stays closed to `created` and `updated` (M1 owner decision), so `restore` must not become a general way to skip validation. It runs the same checks and differs only in where the two stamps come from.
- **One error type.** `json.JSONDecodeError` and `UnicodeDecodeError` are `ValueError` subclasses ([JSONDecodeError]), and `Task` already raises `ValueError` for any bad field. The loader catches `ValueError`, adds the file path and the record position, and raises `ValueError`.
  M3's CLI then catches one type for a corrupt file and for `add ""`. A custom exception class waits until M3 needs to tell the cases apart. An `OSError` (unreadable file, a directory in the way) propagates.
- **Same directory for the temp file.** `os.replace` is atomic on success, but may fail when the source and target are on different filesystems ([os.replace]), so the temp file lives next to the target, not in the system temp directory.
- **Cleanup.** A failed write must remove its temp file. A process killed between creating the temp file and the replace leaves a stray temp file; `load` ignores it, but Git does not: the project list often lives in a repository, and `git add .` would pick up the hidden `.tasks.json.*.tmp` file.
  `README.md` documents the `.gitignore` pattern (review of PR #25, 2026-11-01). Rejected: deleting stale temporary files at the start of `save`, which could remove another process's file in the middle of its save and adds work to every save for a window of milliseconds.
- **No `fsync`.** Without `flush()` and `os.fsync()` before the replace, a power loss can still leave the old or an empty file ([os.fsync]). Accepted for a personal task list; mark it with a `# ponytail:` comment naming this ceiling and the upgrade path.
- **Permissions.** A temp file from `tempfile.mkstemp` is readable and writable only by its owner ([tempfile]), so `save` copies the mode of the file it replaces, and a new file stays owner-only (review of PR #25). An atomic save needs write permission on the directory, where a plain write needs it only on the file; that comes with replacing by rename.
- **Lost updates.** Two processes that load, change, and save at once: the last save wins. No lock, because this is a single-user CLI.
- **Encoding.** Read and write with an explicit `encoding="utf-8"` so the file does not depend on the machine's locale. `json.dump` uses `ensure_ascii=False`, so non-ASCII text stays readable in the file; text that cannot be encoded fails the save and keeps the old file.
- **Review of PR #25, decided 2026-11-01.** All eleven threads were accepted, some in part:
  `restore` takes a record (`restore(**record)`) and reads the field list from the dataclass; a missing or unknown field is a `ValueError` raised by `Task`.
  Null stamps and an `id` below 1 are rejected. `save` runs every record through the same rules as `load` before it creates a directory or a temporary file, so it cannot replace the last good file with one `load` rejects.
  `save` follows a symbolic link, keeps an existing file's mode, writes UTF-8 text and whole-second dates. No upper bound on `id`: integers are unbounded and the JSON parser already raises `ValueError` past 4300 digits.
- **Scope held back.** No version field in the file (D5 kept a bare list), no ID assignment (M3), no sorting (M3 and M4). M8 revisits where the task-to-data conversion lives.

[dataclasses]: https://docs.python.org/3/library/dataclasses.html#mutable-default-values
[pytest exit codes]: https://docs.pytest.org/en/stable/reference/exit-codes.html
[JSONDecodeError]: https://docs.python.org/3/library/json.html#json.JSONDecodeError
[os.replace]: https://docs.python.org/3/library/os.html#os.replace
[os.fsync]: https://docs.python.org/3/library/os.html#os.fsync
[tempfile]: https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp
