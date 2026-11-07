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
  `restore` takes a record and reads the field list from the dataclass; a missing or unknown field is a `ValueError` raised by `Task`. It first took keyword arguments (`restore(**record)`); the second review of PR #26 made it one mapping argument (`restore(record)`), so a stored key cannot collide with a parameter.
  Null stamps and an `id` below 1 are rejected. `save` runs every record through the same rules as `load` before it creates a directory or a temporary file, so it cannot replace the last good file with one `load` rejects.
  `save` follows a symbolic link, keeps an existing file's mode, writes UTF-8 text and whole-second dates. No upper bound on `id`: integers are unbounded and the JSON parser already raises `ValueError` past 4300 digits.
- **Scope held back.** No version field in the file (D5 kept a bare list), no ID assignment (M3), no sorting (M3 and M4). M8 revisits where the task-to-data conversion lives.

## [2026-11-01] Feature: M3 First slice, add and list

**Objective:**
Make `uv run task-tracker add "Buy milk"` and `uv run task-tracker list` work end-to-end against `./tasks.json` in the current directory, so the first real command exists before the other five. Covers issue #7 and the M3 section of `docs/implementation-plan.md`. Features 3 and 5 of `README.md`, project-level list only: `--dir` and `--global` arrive in M7.

**Approach:**
Branch `feature/add-and-list` (from `develop`). Test-first, one atomic commit per step, each with its own `SUMMARY.md` entry. New module `src/task_tracker/cli.py` with tests in `tests/test_cli.py`. `main(argv)` moves out of `__init__.py`, which reexports it so the `task_tracker:main` entry point is unchanged. Standard library only, so `uv.lock` does not change.

1. `add`: parse with argparse subcommands, take the next ID from the stored tasks, save, and print the new ID. Commit: `feat(cli): add the add command`.
2. `list`: current tasks only, sorted by due date (undated last), then priority rank, then ID. Commit: `feat(cli): add the list command`.
3. Bad input and failures: a one-line error and a nonzero exit instead of a traceback. Commit: `feat(cli): report errors without a traceback`.
4. Docs: tick the M3 boxes in the plan and issue #7 and record the decisions below in both. Commit: `docs(plan): record the M3 decisions`.
5. Done when the tests pass locally, coverage on changed code is at least 80%, the CI-version linters are clean locally, and the two commands work in a scratch directory. Pushing and opening the PR into `develop` wait for the project owner.

**Tests:**
The nine Given/When/Then items are in the M3 section of the plan. In addition:

- `add` takes ID highest + 1, not the count: with stored IDs 1 and 5 the new task is 6 (D5).
- Two current tasks with the same due date and priority list the lower ID first, even when the file holds them in the other order.
- `list` with nothing current prints a message that names the file it read (D2) and exits 0.
- A directory where `tasks.json` should be gives a one-line error and a nonzero exit, not a traceback (the `OSError` that M2 left for the CLI).
- A corrupt file leaves `add` without a new task and the file unchanged.

**Risks & Trade-offs:**

- **Exit codes, decided 2026-11-01.** 2 for a bad option value, which argparse reports itself (an unknown priority, an unparsable `--due`). 1 for everything else that goes wrong at runtime: a blank name, a corrupt file, an unreadable file. Both print one error line on standard error and never a traceback. The plan only requires nonzero for the second group.
  A reader that closes the pipe early also ends with 1, quietly, and a failed write of the output prints `cannot write the output` and returns 1 (PR #26 review).
- **One `except` in `main`, decided 2026-11-01.** It catches `ValueError` (from `Task` and `load`) and `OSError` and prints `task-tracker: error: <message>`. M2 already made every corrupt-file failure a `ValueError` naming the file, so no custom exception class is needed yet.
- **`--due` is read by `_due`, a converter around `datetime.fromisoformat`.** A malformed value exits 2 as the plan says. A value with a UTC offset also exits 2: it parses, but D6 stores local time only. Changed 2026-11-01 in the review of PR #26; it first exited 1 from `Task`, with a message that did not name the flag.
  The converter first repeated the naive-time rule that `Task` enforces. In the second review round it started to call `as_naive_datetime`, the helper `Task` uses, so the rule (D6) lives in one place and the converter only translates the error.
- **Priority rank comes from the enum's definition order** (`CRITICAL` first), not from the string value, which sorts `MEDIUM` after `LOW` (Review Focus 1). A test pins the order, so reordering the enum fails loudly.
- **Q3 and `description`, decided 2026-11-01.** `add` does not set `start`, `stop`, or `description`, and `list` does not show `start` or `stop`: they stay plain fields with their defaults until a milestone needs them. Cheap to add later; each would need a short flag the options table does not assign yet.
- **List line.** One line per task: ID, status, priority, due date (`-` when there is none), name. No header, no color. Every datetime prints through `isoformat()`, the form M2 stores.
- **Where the rules live.** "Highest ID + 1" and the sort key are private functions in `cli.py`. M4 reuses the sort key for the first half of `list --all`. M8 revisits the module layout.
- **Known limit.** Two processes running `add` at once can both read the same list, so the second save replaces the first: a task is lost, and both took the same ID. No lock, as in M2; tracked in #27.

## [2026-11-01] Fix: PR #26 review

**Objective:**
Answer the eleven inline comments on PR #26 (M3, `add` and `list`). Each claim was reproduced in a scratch directory before it was triaged. Eight are fixed, #5 is fixed in part, and #6 and #8 are answered with a reason.

**Approach:**
Same branch, `feature/add-and-list`. Test-first, one atomic commit per comment, each with its own `SUMMARY.md` entry. The tests are written and seen failing before the code that passes them.

1. #1, a corrupt file can still end in a traceback: `Task.restore` takes `cls` positionally only, so a record with a `cls` key is an unknown field. `RecursionError` from a deeply nested file becomes the `ValueError` that names the file. Commit: `fix(storage): turn every corrupt-file shape into a ValueError`.
2. #4, the priority error lists the valid values: drop `type=Priority`, keep `choices` as plain strings, and let `Task` normalize. Commit: `fix(cli): list the valid priorities in the error`.
3. #7, three untested behaviors: a timed `--due`, a bare `task-tracker`, and a UTC-offset `--due`. The first two pass at once, so they are mutation-checked. Commit: `test(cli): pin a timed due date and the missing command`.
4. #5, one converter for `--due` that names the flag and the format, and sends an offset to exit 2. Commit: `fix(cli): report every bad due date as one exit 2 error`.
5. #2 (names `save` cannot write): `Task` rejects text that UTF-8 cannot hold, in the name and the description. Commit: `fix(task): reject text that UTF-8 cannot hold`.
6. #2 (output failures): the commands return their lines and `main` prints them outside the `try`. A closed pipe exits quietly; any other write failure has its own message. Commit: `fix(cli): keep output failures out of the data-error path`.
7. #3, control characters in a name: escape them, and anything standard output cannot encode, as the line is printed. Commit: `fix(cli): escape control characters and unencodable text on output`.
8. #6 wording, the M3 decisions, and `README.md`: `docs(plan): record the PR #26 review changes`.
9. #9, #10, #11: restamp the M3 `SUMMARY.md` entries with their commit times, update the project `CLAUDE.md`, and ignore `tasks.json` and its temp files.
10. Done when the tests pass locally, coverage is at least 80%, the CI-version linters are clean, and every reply is posted. Pushing waits until the last commit; threads that were fixed are resolved after the push.

**Tests:**

- A record with a `cls` key, and a file nested 200,000 deep, each give the one-line error from `list` and `add` and leave the file alone.
- A wrong `--priority` names all four valid values on the error line. A bad `--due` names the flag and the format and exits 2, for a malformed date and for a UTC offset.
- A real pipeline closed early (`list | head -1` over 3,000 tasks) writes nothing to standard error. A write that fails reports "cannot write the output" and leaves the stored task in place.
- A name with a lone surrogate is rejected by `Task` and by `load`, naming the record. A name with a newline or an escape sequence prints on one line as escapes. A task named with an accented letter and a symbol prints both as escapes (`\xeb`, `\u2615`) when standard output is ASCII.

**Risks & Trade-offs:**

- **Offset `--due` now exits 2, decided 2026-11-01.** The converter first repeated the one-line naive-time rule that `Task` enforces (D6), at the cost of two places to change. The second review round removed that cost: it calls `as_naive_datetime` now, and the gain is one rule and one exit code for every bad `--due`.
- **A superset of ISO 8601 is still accepted** (`20261102`, week dates, fractional seconds that are truncated). Rejected: a stricter parser, which would be a second spec to keep in step with `fromisoformat`.
- **Control characters are escaped on output, not rejected by `Task`.** One such name in a shared file would otherwise make the whole list unloadable. A literal backslash followed by `n` prints the same as an escaped newline.
- **Surrogates are rejected by `Task`**, so a file that holds one is now a corrupt file naming its record, where `list` used to abort partway.
- **Concurrent `add` can lose a task, not only an ID.** The wording is corrected in this plan, `README.md`, and the PR. The lock is deferred to its own issue: `fcntl` is Unix-only and an `O_EXCL` lockfile goes stale after a crash.
- **#8, the subject of `0e0d554`, is not reworded.** That needs a force-push, which this work never does, and the merge commit keeps the subject in history. The missing `SUMMARY.md` entry is recorded in the `.gitignore` commit.

## [2026-11-07] Fix: PR #26 review, second round

**Objective:**
Answer nine more inline comments on PR #26, from a second code review, run after the first round was pushed. Each claim was reproduced before it was triaged: the exit code 120, the traceback with a closed standard output, the escape sequence in an error line, the bidirectional controls, and the 16.7 ms against 0.9 ms.
All nine are fixed. #7 (`Task.restore` taking a mapping) was first planned as an answer with a reason, but the main reason I gave for it was wrong (see step 10 and the last risk), so it is fixed as well.

**Approach:**
Same branch, `feature/add-and-list`. Test-first, one atomic commit per comment, each with its own `SUMMARY.md` entry.

1. `#9` (test helper): the child-process helper becomes a context manager, which removes the pylint suppression that had no reason. Commit: `test(cli): start child processes through one context manager`.
2. `#1`: one `_discard_stdout` helper, used by the broken-pipe and the other write-failure branches, so the exit-time flush cannot fail again (exit 120). Commit: `fix(cli): discard standard output after any failed write`.
3. `#2`: a closed standard output (`sys.stdout is None`) exits 0 without a traceback. Commit: `fix(cli): say nothing when standard output is closed`.
4. `#3`: the error line goes through the same escaping as the output, in one `_say` used for both streams. Commit: `fix(cli): escape the error line like the output`.
5. `#5`: one compiled regular expression replaces the per-character category lookup, with the same behavior. Commit: `refactor(cli): escape with one regular expression`.
6. `#4`: the bidirectional controls are escaped too. Commit: `fix(cli): escape bidirectional controls`.
7. `#6`: `--due` calls the model's date rule instead of repeating it. Commit: `refactor(cli): read --due with the model's date rule`.
8. `#8`: an unencodable name is tested through `main`. Commit: `test(cli): pin the unencodable name at the command line`.
9. Docs: the plan, `README.md`, and this entry record the changes. Commit: `docs(plan): record the second round of PR #26 review changes`.
10. `#7`: `Task.restore` takes one mapping, not keyword arguments, so no stored key can collide with a parameter and the positional-only `/` is not needed. Commit: `refactor(task): restore takes one record`.

**Tests:**

- A child whose standard output is a read-only descriptor gets one stderr line and exit 1 from `list` and `add`, and the task stays saved. A child started with descriptor 1 closed exits 0 with an empty stderr.
- A stored record with a key that holds an escape character and a newline gives a one-line error with no raw escape character.
- A name with U+202E, U+2066, U+200E, or U+061C prints as escapes, and U+200D and U+3000 still print as text.
- `main(["add", "bad \udcff"])` exits 1 with `UTF-8` in the one-line error, and writes nothing.

**Risks & Trade-offs:**

- **Coverage of the failure branches is measured in child processes**, so pytest-cov does not count them. The in-process figure for `cli.py` drops; the tests still fail when the branch breaks, which the deliberate breaks show.
- **`as_naive_datetime` becomes public.** It was private to `task.py`. The gain is that the naive-time rule of D6 lives in one place; the docs that called the repetition a cost are corrected.
- **U+061C is escaped although the comment did not list it.** It is the third Unicode bidirectional mark, next to U+200E and U+200F, and leaving it would make the rule incoherent. U+200D and U+3000 stay text.
- **#7 was first not going to change, and does.** I planned to answer it with a reason, and the main reason was that a mapping argument would reverse an earlier decision. That was a mistake in my reading of the history:
  the commit that made `restore` take `**record` (`db9f244`, from the review of PR #25) did it so that the dataclass is the one list of fields, and a mapping keeps that exactly. What remains against the change is churn, 20 call sites in the tests, which is mechanical and checked by the type checker;
  for it, the whole class of key-against-parameter collisions goes away and so does the `/` special case.

## [2026-11-07] Feature: M4 List all

**Objective:**
Make `uv run task-tracker list --all` (short `-a`) show every task: the current ones first in the M3 order, then the completed ones by date completed, oldest first. Covers issue #8 and the M4 section of `docs/implementation-plan.md`. Feature 4 of `README.md`, project-level list only: `--dir` and `--global` arrive in M7.
This entry fixes the order and the traps.

**Approach:**
Branch `feature/list-all` (from `develop`, after M3 merged as PR #26). Test-first, one atomic commit per step, each with its own `SUMMARY.md` entry. The change stays in `src/task_tracker/cli.py` and `tests/test_cli.py`. Standard library only, so `uv.lock` does not change. `_current_order` stays as it is, and the M3 tests are its safety net.

1. `--all` on the `list` subparser (`action="store_true"`, `dest="include_done"`). Red: `list --all` exits 2 because argparse does not know the flag. Green: the current tasks in `_current_order`, then the done tasks by date completed, then ID. Commit: `feat(cli): add list --all`.
2. `-a`, the short form from the options table. Red: `list -a` exits 2. Commit: `feat(cli): add the -a short flag for list --all`.
3. The empty case: `list --all` over a missing or empty file says `No tasks in <path>`, and plain `list` keeps `No current tasks in <path>`. Commit: `feat(cli): say no tasks when list --all finds none`.
4. Docs: tick the M4 boxes in the plan and issue #8, record the decisions below in both, and update the project state in `CLAUDE.md` (features 3, 4, and 5 exist). Commit: `docs(plan): record the M4 decisions`.
5. Done when the tests pass locally, coverage on changed code is at least 80%, the CI-version linters and the Markdown linters are clean locally, and `list --all` works in a scratch directory. Pushing and opening the PR into `develop` wait for the project owner.

**Tests:**
The two Given/When/Then items are in the M4 section of the plan. In addition:

- Build the done tasks with `Task.restore` and a full record, not the constructor. The constructor stamps `created` with the clock and rejects a date completed before it, so a task completed on 2026-10-10 cannot be built that way (the same trap as M2 step 3). The record must also keep `created <= start <= stop <= date_completed`, so all four sit before 2026-10-05.
- The done half orders by date completed, not by ID. With A to E at IDs 1 to 5 and F at ID 6, F (completed first) must come before D (ID 4); an ID order would give D, F and fail.
- Two done tasks with the same date completed list the lower ID first, even when the file holds them the other way round (the M3 tie rule).
- A done task with the earliest due date still comes after every current task.
- `list -a` and `list --all` print the same output, and both equal the expected order.
- Plain `list` still leaves the done tasks out. A file with only done tasks lists them under `--all`, and plain `list` still says `No current tasks in <path>`.
- A corrupt list file gives the same one-line error and exit 1 under `--all`; add `["list", "--all"]` to the existing parametrized case.

**Risks & Trade-offs:**

- **Sort key of the done half, decided 2026-11-07.** `(date_completed, id)`: the same "ID settles ties" rule as M3, so the order never depends on how the file was written. The half is only the `DONE` tasks, so none of them lacks a date completed.
  Rejected: sorting the done half by the M3 key (due date, priority, ID). It would give one key for both halves, but it contradicts `README.md` feature 4 and issue #8, most done tasks have no due date and would fall to priority (meaningless for finished work) and ID (creation order), and nothing would read `date_completed`.
- **Typing of that key, decided 2026-11-07.** `Task` guarantees that a `DONE` task has a date completed (the constructor fills it in, `restore` and `load` reject a record without one), but the field's type is `datetime | None`, so pyright rejects the bare comparison. An `assert task.date_completed is not None` states the invariant for the type checker and adds no branch to cover.
  Rejected: the `datetime.max` stand-in from `_current_order`, which is dead code here and would quietly sort a broken record last, and a `ValueError`, which is an unreachable branch that needs a forged task to cover.
  Under `python -O` the assert is gone, and a broken record would then sort without an error. One or several done tasks without the date sort by ID, and only a mix with a good record raises `TypeError`. This entry first said "still loudly"; the review of PR #28 showed that is wrong, and the correction is in the entry for that review.
  A broken record cannot reach the sort: `Task._validate` runs on construction and in `restore`, so on every `load`. The assert only tells the type checker.
- **The list line stays as M3 made it, decided 2026-11-07.** It shows the due date, not the date completed, so a reader cannot see why F precedes D. Rejected for now: a completed column under `--all` (two line formats depending on a flag) and in every list (it changes a format that tests pin, and plain `list` would carry a column that is always empty). Cheap to add later.
- **Empty wording, decided 2026-11-07.** `No current tasks in <path>` is wrong under `--all`, where done tasks count, so `--all` says `No tasks in <path>` and plain `list` keeps its message. Rejected: one message for both, which would mislead under `--all`, and a hint at `--all` in plain `list`, which is behavior the spec never asked for.
- **No header or divider between the halves** (M3: no header, one line per task). The status column tells them apart. A divider would break "one line per task" for anyone who parses the output.
- **Flag name in the code, decided 2026-11-07.** argparse derives `dest` from the first long option string ([argparse dest]), so `--all` would become `args.all`. The flag gets `dest="include_done"`, which says what it does where `_list` branches on it and does not read like the built-in `all()`. The cost is one keyword argument, and a name that differs from the flag text.
- **Clock changes.** Date completed is naive local time (D6), so a clock set back could reorder tasks completed in the repeated hour. Accepted, as in M2.
- **Scope held back.** No filtering beyond `--all`, no `--dir` or `--global` (M7), and no change to the layout of `cli.py` (M8).

## [2026-11-07] Fix: PR #28 review

**Objective:**
Answer the six inline comments and the one PR-level comment on PR #28 (M4, `list --all`). Each claim was checked first: the stale top-level help, the behavior of the assert under `python -O`, the `stored()` call that would build a done record, and the gap in the done-order tests.
Five are fixed (#1, #3, #5, #6, and the PR-level `README.md` comment). Two are fixed in part and answered with a reason for the rest (#2 and #4), so those two threads stay open for the reviewer.

**Approach:**
Same branch, `feature/list-all`. Test-first where behavior changes, one atomic commit per comment, each with its own `SUMMARY.md` entry. Pushing waits until the last commit; fixed threads are resolved after the push.

1. #1, the top-level help: red test that `task-tracker --help` names `--all`; green: the help text for `list`. Commit: `fix(cli): name --all in the help for list`.
2. #3, one message built once: a `scope` word picks `tasks` or `current tasks`. The output is the same, so the existing empty-list tests are the safety net, and a swapped wording must fail them. Commit: `refactor(cli): build the empty-list message once`.
3. #4, the third copy of the record: `_done` takes its fields from `asdict(Task(...))` and overrides only what a done task changes. Commit: `test(cli): take the done record's fields from Task`.
4. #5, the full timestamp: two done tasks completed on one day, the lower ID later in the day. Passing at once, so it is mutation-checked: cutting the key to the day must fail it. Commit: `test(cli): pin that the done half sorts on the full timestamp`.
5. #2, the claim about `python -O`, corrected in this file, in `SUMMARY.md`, and in the PR description. Commit: `docs(plan): correct what python -O does to the done-order assert`.
6. PR-level comment, `README.md`: the Commands section documents `list --all`, `-a`, the empty message, and the done half's order. Commit: `docs(readme): document list --all`.
7. #6, issue #8 and stale statements: issue #8 gains the five extra items and the three decisions (a change on GitHub), and the two statements in the 13:03 `SUMMARY.md` entry that the review made false are corrected. Commit: `docs(summary): correct two statements the review made stale`.

**Tests:**

- Top-level `--help` names `--all` next to `list`.
- Two done tasks completed on the same day, the lower ID at 17:00 and the higher at 09:00, list the 09:00 one first. A mutant that cuts the key to `.date()` fails it.
- The empty-list wording for `list` and `list --all` is covered by the existing tests; a mutant that swaps the two words fails them.

**Risks & Trade-offs:**

- **The `python -O` claim was wrong, found 2026-11-07.** I wrote that without the assert the comparison "fails with a `TypeError`, still loudly". Run under `python -O`, one DONE task with no date completed sorts without error, two sort by ID, and only a mix with a good one raises.
  The decision to use the assert was made with that sentence among its pros and cons, so the owner is asked to confirm it with the corrected facts.
  It stands for now: the guarantee is `Task._validate`, which runs on construction and in `restore`, so on every `load`, and a broken record cannot reach `_done_order`. The assert only tells the type checker.
- **No accessor or narrower type on `Task` for `date_completed`, declined in part of #2.** There is one consumer. `update` writes the field and `delete` does not read it. A typed accessor changes the M1 model for one caller and is decided against on 2026-11-07; M8 revisits the layout. Rejected for now, not forever: a second reader of the field is the point to reopen it.
- **`stored()` is not moved into a shared module, declined in part of #4.** The call the comment suggests cannot build these records: `stored()` has `created` on 2026-10-10 at 09:00, after the dates completed here, and `restore` refuses a date completed before `created`. Making it work overrides nine of eleven fields. Moving it also edits the M1 tests, outside this diff.
  What is fixed is the new code's copy: `_done` takes the field list from the dataclass. The older copies in `test_task.py` and `test_storage.py` remain.
- **Scope held back.** No change to `Task`, no change to the older tests, no new `tests/` helper module.

[argparse dest]: https://docs.python.org/3/library/argparse.html#dest
[dataclasses]: https://docs.python.org/3/library/dataclasses.html#mutable-default-values
[pytest exit codes]: https://docs.pytest.org/en/stable/reference/exit-codes.html
[JSONDecodeError]: https://docs.python.org/3/library/json.html#json.JSONDecodeError
[os.replace]: https://docs.python.org/3/library/os.html#os.replace
[os.fsync]: https://docs.python.org/3/library/os.html#os.fsync
[tempfile]: https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp
