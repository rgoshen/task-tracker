# Summary

## [2026-11-01 14:25] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`task-tracker add NAME [--priority/-p P] [--due/-D DATETIME]` now stores a task in `./tasks.json` and prints `Added task <id>: <name>`. The ID is the highest stored ID plus one.
`main(argv)` moved from `__init__.py` into the new `cli.py` and returns the exit code; `__init__.py` reexports it, so the `task_tracker:main` entry point is unchanged.
`list` and error handling follow in the next commits.

**Rationale:**
argparse subcommands (D3) with `set_defaults(run=...)`, the pattern in the Python documentation, so a new command is one parser plus one function. A bad priority and an unparsable `--due` are left to argparse, which exits 2 as the plan asks; `--due` uses `datetime.fromisoformat` and `Task` does the rest of the normalizing (D6), so the rules are not written twice.
The ID rule lives in `_add` (D5 says the command computes it).
Five tests, written first and seen failing on `main() takes 0 positional arguments`. Mutation checks: `len(tasks) + 1` for the ID, renamed short flags, ignored priority, ignored exit code, and no output are each caught.
One test was too weak. Comparing the long and the short form of the same command passes when both runs drop `--due`, so ignoring `--due` survived until the test also asserted the stored due date. An early mutation run also read a stale `.pyc` (same size, same second), so the runs were repeated with bytecode caching off.

**References:**

- `TODO.md`: 2026-11-01 Feature: M3 First slice, add and list
- Issue: #7

## [2026-11-01 14:17] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Added the M3 entry to `TODO.md`: objective, a five-step approach, the tests beyond the plan's nine, and the decisions the plan left to the implementer. Those are the two exit codes, a single `except` in `main`, how `--due` is parsed, priority rank from the enum's definition order, what `add` and `list` leave out (Q3 and `description`), the shape of a list line, and where the ID and sort rules live.

**Rationale:**
The global rules say the plan is written before any code. The M3 "Think about" list asks seven questions, and this records an answer to each so the tests that follow have something to be wrong against. I did not stop to ask first: every answer is cheap to change in M4 to M8 and none touches stored data.
Pushing and the pull request are left to the project owner, as the entry says.

**References:**

- `TODO.md`: 2026-11-01 Feature: M3 First slice, add and list
- Issue: #7

## [2026-11-01 14:30] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_storage.py`)

**Summary:**
Two tests each carried the same ten-line `os.replace` spy. It is now one fixture, `replacements`, that records every call as (source, destination) and still performs it. No product code changed, and the number of tests is the same (165).

**Rationale:**
The `Lint` job on PR #25 failed after the review fixes were pushed. Only one linter failed: JSCPD, the duplicate-code detector in super-linter, with threshold 0, reported the duplicated spy (`tests/test_storage.py` lines 318 to 327 and 474 to 483). I introduced the copy in the symlink commit by pasting the spy from the earlier temporary-file test.
My local mirror of the CI linters covered ruff, black, isort, flake8, pylint, mypy, markdownlint, textlint, and Prettier, but not JSCPD, so this was invisible until CI ran. `jscpd` 5.0.10 with super-linter's own config is now part of the local checks. Run against the pushed version it reports exactly what CI did (1 clone, 9 duplicated lines, 71 tokens), and against this change it reports 0 clones.
One consequence of sharing the fixture: it patches `os.replace` before the test body runs, so the setup `save` in the symlink test is recorded too. That test clears the list before the call it checks.
Tests: 165 pass before and after; the spy tests were run in both shapes.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, failed `Lint` check after the review fixes

## [2026-11-01 14:20] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Brought the plan, the `TODO.md` entry, and `README.md` in step with the review of PR #25. The plan gains three boxes (a refused save, stored dates not compared with the clock, the saved file's format) and four decisions.
`TODO.md` drops the rule that stored `created` and `updated` are not later than now, and records the new ones. `README.md` documents the hidden `.tasks.json.*.tmp` file that a killed save can leave and the `.gitignore` pattern for it.

**Rationale:**
The project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` together when a decision changes. The earlier docs still listed a rule that the code no longer enforces, which would send the next reader back to the wrong behavior.
Review of PR #25, thread 11: a process killed between creating the temporary file and the replace leaves a hidden file beside the list, which `git add .` would commit when the list lives in a repository.
I took the reviewer's minimum option, documenting the pattern. The other option, deleting stale temporary files at the start of `save`, could remove another process's file in the middle of its save, and adds work to every save for a window of milliseconds.
Issue #6 is regenerated from the plan separately, because it is a change on GitHub.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review thread 11

## [2026-11-01 14:12] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_storage.py`)

**Summary:**
The test that a directory in place of the file is not reported as a corrupt file no longer matches the operating system's error text. It asserts an `OSError` and that the error is not a `ValueError`.

**Rationale:**
Review of PR #25, thread 10. `open()` on a directory raises `IsADirectoryError: ... Is a directory` on macOS and Linux and `PermissionError: ... Permission denied` on Windows, so `match="directory"` failed there although `load` behaved correctly. I confirmed it by simulating the Windows wording: the old assertion failed on the text alone, and the new one passed.
The `ValueError` check is the part of the old test that mattered: `pytest.raises(OSError)` alone would already fail for a `ValueError`, but the explicit assertion states the intent, that a disk problem is not reported as a corrupt file. A targeted mutation check (an `OSError` reported as corrupt, an `OSError` treated as "no file") fails the test, and the file was verified identical afterwards.
No product code changed.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review thread 10

## [2026-11-01 14:05] Commit Summary

**Change Type:** Fix

**Scope:** storage (`src/task_tracker/storage.py`, `tests/test_storage.py`)

**Summary:**
`save` now follows a symbolic link and replaces the file it points to, so a list kept in a synced folder or a dotfiles repository stays linked. It also copies the mode of the file it replaces onto the new one. A file that did not exist is still created readable and writable by its owner only.

**Rationale:**
Review of PR #25, thread 5. `os.replace` on a symlink replaces the link itself: after a save the link was a regular file and the real file kept stale content (reproduced). A 0644 file became 0600 because `tempfile.mkstemp` creates owner-only files, so a list someone shared quietly became private.
The fix resolves the path after validation, so errors still name the path the caller gave, and builds the temporary file beside the real file, because `os.replace` is atomic only within one filesystem and a link can point to another one. The mode comes from `shutil.copymode`; for a file that does not exist yet the copy is skipped.
Not done: the review also notes that an atomic save needs write permission on the directory, where a plain write needs it only on the file. That cost comes with replacing by rename and cannot be removed without giving up atomicity, so it is documented in the plan instead.
Test-first: the symlink test and the mode test failed (the link became a regular file, 0644 became 0600); the owner-only test for a new file already passed and now pins the behavior. The mutation check found two gaps in my first tests, a temporary file built beside the link instead of the real file and directories created beside the link, and two more tests close them.
Mutation check: seven breaks (link not followed, mode not kept, a new file treated as an error, the link replaced, the temporary file or the directories beside the link, the mode copied from the wrong file) each fail a test. The file was verified identical afterwards. The mode tests skip on Windows, which has no owner, group, and other bits.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review thread 5

## [2026-11-01 13:58] Commit Summary

**Change Type:** Fix

**Scope:** storage (`src/task_tracker/storage.py`, `tests/test_storage.py`)

**Summary:**
`save` now writes non-ASCII text as text (`"Café ☕"`, not `"Café ☕"`) and every date in whole seconds (`2026-11-01T09:00:00`), whatever was assigned to a field after the task was built.
Text that cannot be written as UTF-8 (a lone surrogate) now fails the save with `UnicodeEncodeError`, leaves the previous file as it was, and leaves no temporary file.

**Rationale:**
Review of PR #25, threads 4 and 6. The file is meant to be read and edited by a person (D1) and is opened as UTF-8, but `json.dump` defaults to `ensure_ascii=True`, so the encoding never mattered and a name in any other script was unreadable.
The `README.md` promises every date as `YYYY-MM-DDTHH:MM:SS`, but the model drops microseconds only when it builds or restores a task, so `task.due = datetime.now()` (likely in M5's `update`) wrote `…:00.123456`, and `load` then truncated it: the round trip did not hold.
`timespec="seconds"` in the writer closes the file-format half. The in-memory task still holds the microseconds until M5's `update` normalizes what it assigns, which is the known limit already recorded for M5; the loaded copy equals what was saved.
Side effect worth knowing: a command-line argument that is not valid UTF-8 reaches Python as a lone surrogate. Before this change it was written as an escape. Now the write fails (`UnicodeEncodeError` is a `ValueError`, so M3's single catch handles it) and nothing on disk changes. A test pins this.
Test-first: three tests failed (escapes in the file, microseconds in the file, nothing raised for the surrogate), then all 160 passed. Mutation check: five breaks (escapes back on, microseconds kept, minutes only, microseconds padded, no conversion) each fail a test; a sixth was skipped because its pattern matched twice and duplicated the first. The file was verified identical afterwards.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review threads 4 and 6

## [2026-11-01 13:50] Commit Summary

**Change Type:** Fix

**Scope:** storage (`src/task_tracker/storage.py`, `tests/test_storage.py`)

**Summary:**
`save` now refuses a list of tasks that `load` would reject, with the same `ValueError` naming the file and the record (for example `record 3: duplicate id 1`), before it creates a directory or a temporary file. The previous file is left as it was.
`load` and `save` share one helper, `_restore_all`, so both apply the same rules from one place.

**Rationale:**
Review of PR #25, thread 3. `save([Task(1, "a"), Task(1, "b")], path)` succeeded and the next `load` raised, and the same happened after `task.name = "   "` (the dataclass is mutable, and M5's `update` will assign to fields).
Because `save` replaces the previous good file, the user lost their last valid state and had to repair JSON by hand. The atomic replace protects against a crash partway through a write, but not against writing something unreadable.
The check runs each record through the loader's own path (`_from_record`, which is `Task.restore`), so the rules cannot drift apart, and it needs no clock because the stored-date check was removed in the previous commits. A task the constructor accepts always passes.
Alternative rejected: checking only for duplicate IDs in `save` and leaving per-task rules to M5's `update`. That would cover the case in this review, but not the next bug that assigns a bad value; the extra cost is one pass over the records.
Test-first: three tests failed with `DID NOT RAISE`, then all 157 passed. Mutation check: eight breaks (validation skipped, run after the directory is created, duplicates not detected or never remembered, position or filename wrong, `load` bypassing the helper, a record dropped on write) each fail a test, and the file was verified identical afterwards.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review thread 3

## [2026-11-01 13:42] Commit Summary

**Change Type:** Refactor

**Scope:** task, storage (`src/task_tracker/task.py`, `src/task_tracker/storage.py`, tests)

**Summary:**
`Task.restore` now takes the stored record as keyword arguments (`restore(**record)`) and reads the field list from the dataclass, so the 11-parameter copy of it is gone. It raises `ValueError` for a missing field and for an unknown one, and `storage._from_record` defers to it, so `_FIELD_NAMES` is gone too. Behavior is unchanged except that the two errors are now raised by the model.
The remaining pylint suppressions now have their reason beside them.

**Rationale:**
Review of PR #25, threads 8 and 9. Adding a `Task` field needed three edits (the dataclass, the `restore` signature, and `_FIELD_NAMES`); it now needs one. The old shape also let a forgotten parameter surface as `TypeError: unexpected keyword`, which the loader does not catch.
Cost accepted: `restore` no longer documents its fields in its signature, and pyright cannot check a misspelled keyword at a call site. Every caller already passes a dictionary, and the dataclass is the one list.
The two `# pylint: disable=protected-access` lines call `_normalize` and `_validate` from a classmethod of the same class. The reason sits in the comment directly above them, the way `DTZ001` is explained in `task.py`. The `redefined-builtin` and `too-many-arguments` suppressions disappeared with the old signature. One new `disable-next` in a test carries its reason on the line above it.
Test-first: three tests failed with the raw `TypeError`s, then all 143 passed. The first mutation check found a real gap: a record without `description` would have been filled in with a default and no test noticed, because the test only dropped `stop` and `due`. A test now drops each of the eleven fields in turn.
Mutation check: eight breaks (each check dropped, an unknown field ignored, a field never assigned, `_normalize` or `_validate` skipped, one dataclass field ignored, a default filled in for a missing field) each fail a test (154 tests), and the file was verified identical afterwards.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review threads 8 and 9

## [2026-11-01 13:35] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
`Task.restore` no longer compares `created`, `updated`, or `date_completed` with the clock. A stored task is checked for order only: `updated` not before `created`, and the timeline `created <= start <= stop <= date completed`. A new task is still held to the clock for its date completed: one in the future raises `ValueError` at construction, as in M1.

**Rationale:**
Review of PR #25, thread 2, a design call confirmed by the project owner. Times are naive local time (D6). A task saved at 01:30 on the night daylight saving ends could not be loaded when the clock read 01:01: `load` raised `created must not be in the future`.
A changed time zone or a fixed clock does the same for hours, and every command that loads first is then locked out of all tasks, with an error that blames a file that was valid when written.
M1 applied the future check once, at creation, and that is where it stays.
Trade-off accepted: a hand-edited far-future date now loads without complaint. Alternatives rejected: a 24-hour margin (an arbitrary constant that a long clock skew still defeats) and keeping the check (the lockout).
This reverses a rule I added in this pull request and listed as open to veto: `created` and `updated` not later than now. `_validate` no longer takes the clock, and the constructor's check moved into `__post_init__`, where the one clock reading lives.
Three "rejects a future date" restore tests became two "accepts a later stamp" tests. The restore tests no longer pin the clock, because restore no longer reads it.
Test-first: the two new tests failed, then all 142 passed. Mutation check: eight breaks (restore comparing each of `created`, `updated`, and `date_completed` with the clock again, the constructor check dropped or made exclusive, and the three other ordering rules dropped) each fail a test. The file was verified identical afterwards.
Tooling note: my mutation script restored the original within the same second as a same-length mutant, so Python could run a cached `.pyc` of the mutant (it briefly made valid IDs fail). It now clears the cache before every run, and I re-ran all five earlier mutation sets with it: the results are unchanged (38 of 39 caught, the one survivor being the equivalent mutant already reported).

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review thread 2

## [2026-11-01 13:32] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`, `tests/test_storage.py`)

**Summary:**
A `null` in `created`, `updated`, `start`, or `stop` now raises `ValueError: <field> must be a date or ISO 8601 text`, and an `id` below 1 raises `ValueError: id must be 1 or more`. Only `due` and `date_completed` may be empty.

**Rationale:**
Review of PR #25, threads 1 and 7. A hand-edited `tasks.json` with `"created": null` made `load` fail with a raw `TypeError` from a comparison, not the `ValueError` naming the file and record, and M3's CLI catches only `ValueError`. `Task(start=None)` did the same. An `id` of 0 or -5 loaded without complaint, although IDs are "highest existing ID + 1" (D5) and the first is 1.
No upper bound on `id` was added: Python integers are unbounded, `highest + 1` works for any size, and the JSON parser already raises a `ValueError` for an integer over 4300 digits.
My earlier mutation check never dropped the `None` handling, so it could not have found the first gap; the new one drops each field from the allowed-empty list in turn.
Test-first: 16 new tests failed (10 raw `TypeError`s, 6 `DID NOT RAISE`), then all 143 passed. Mutation check: ten breaks (each of the four stamps allowed to be null, `due` and `date_completed` no longer allowed, the ID bound dropped, off-by-one in each direction) each fail a test. The file was verified identical afterwards.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6
- Pull request: #25, review threads 1 and 7

## [2026-11-01 13:48] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `CLAUDE.md`)

**Summary:**
Ticked the seven M2 boxes in the plan and added three that record what was built beyond them: the rules a stored record must meet, the handling of a file that is empty, binary, or not a list, and the failure cases for the atomic save. Added a "Decided" list for M2 and noted that audit findings G2 and G3 are addressed. The project `CLAUDE.md` "Project state" now names `Task.restore` and `storage.py`.

**Rationale:**
The project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` in step. `README.md` needs no change: it already names JSON and the file locations, and M2 changed neither. Issue #6 is regenerated from the plan separately, because it is a change on GitHub.
The plan now says why the fails-partway test writes `[{` into the open file before raising, so the next reader does not "simplify" it into the version that passes against a plain overwrite (G2).

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load, step 6
- Issue: #6

## [2026-11-01 13:31] Commit Summary

**Change Type:** Feature

**Scope:** storage (`src/task_tracker/storage.py`, `tests/test_storage.py`)

**Summary:**
`save` is now atomic. It writes the new content to a temporary file in the same directory as the target and moves it over the target with `os.replace`. A failure at any point leaves the previous file exactly as it was, and the temporary file is removed.

**Rationale:**
A plain overwrite truncates the file first, so a crash or a full disk partway through destroys every task, and `save` rewrites the whole file on every change (D1).
The temporary file sits next to the target because `os.replace` is atomic only within one filesystem and may fail across two. `tempfile.mkstemp` creates it readable and writable only by its owner, so the saved file takes that mode.
Audit finding G2 was a test that passes against a non-atomic save. The cause is a test that makes serialization fail before any byte is written. Here the fake serializer writes `[{` into the open file and then raises.
The test was run against the plain write from the previous commit first: it failed because the old contents had been replaced with `[{`, and a first failed save left a stray `tasks.json`. A second test makes `os.replace` raise, and a third checks that the temporary file is built beside the target.
A `ponytail:` comment marks the one corner cut: no `flush` and `fsync` before the replace, so a power cut right after a save can still leave the old or an empty file. The upgrade path is in the comment.
Test-first: four of five new tests failed against the plain write, then all 127 passed. Mutation check: eight breaks (temporary file in the system temp directory, never removed, `unlink` insisting it exists, `rename` instead of `os.replace`, writing straight to the target, no `mkdir`, no trailing newline, the replace skipped) each fail a test, and the file was verified identical afterwards.
Coverage of `storage.py` is 100%, and `ruff`, `pyright`, and the CI-version Python linters are clean.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load, step 5
- Issue: #6

## [2026-11-01 13:12] Commit Summary

**Change Type:** Feature

**Scope:** storage (`src/task_tracker/storage.py`, `tests/test_storage.py`)

**Summary:**
`load` now rejects a corrupt file with a `ValueError` that names the file and, for a bad task, its position, such as `tasks.json: record 2: name must not be blank`.
It rejects content that is not JSON (an empty file and binary garbage included), JSON that is not a list, a record that is not an object, a missing field, an unknown field, any value `Task.restore` refuses, and two records with the same `id`. The file is never touched.

**Rationale:**
A hand-edited `tasks.json` is the realistic source of bad data, and the next `add` would build its ID from it. Every rule is enforced, not only the one the plan names (`not json`), because each describes an impossible file.
Unknown fields are rejected, not ignored: `save` rewrites the whole file, so ignoring a field would silently delete it on the next save.
One error type: `JSONDecodeError`, `UnicodeDecodeError`, and the `ValueError` from `Task` are all `ValueError`s, so M3's CLI catches one type for a corrupt file and for `add ""`. A custom exception class waits until M3 needs to tell them apart. A failure to read the file (a directory in its place, no permission) stays an `OSError`, because the content is not at fault.
A missing file stays `[]`. A missing directory does too, because `load` never creates anything.
Test-first: 16 new tests failed (the messages had no filename or position, and a non-list or non-object file was not caught), then all 122 passed.
Mutation check: ten breaks each fail a test (each rule dropped, the position starting at 0, the filename left out, an `OSError` reported as corrupt or as "no file"). One mutant survived and is equivalent: ignoring unknown fields at the final call changes nothing, because the earlier check already raises. The file was verified identical afterwards.
Coverage of `storage.py` is 100%, and `ruff`, `pyright`, and the CI-version Python linters are clean.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load, step 4
- Issue: #6

## [2026-11-01 12:58] Commit Summary

**Change Type:** Feature

**Scope:** storage (`src/task_tracker/storage.py`, `tests/test_storage.py`)

**Summary:**
Added `load(path)` and `save(tasks, path)`. `save` writes a JSON list of plain records and creates the directories above the file. `load` rebuilds each task with `Task.restore`, and a file that does not exist is an empty list: nothing is created, not even the directory.
The file holds one object per task with all eleven fields. Dates are ISO 8601 text (D6), the enums are their labels, and a missing value is `null`.

**Rationale:**
This is the round trip M3 builds on. The conversion between a task and plain data is two private functions in `storage.py`, as decided in `TODO.md`. The field names come from `dataclasses.fields(Task)`, so a new field cannot be forgotten.
`save` is a plain write for now. The next commits make `load` strict (step 4) and `save` atomic (step 5), each test-first. The plain version is deliberate: the fails-partway test must be seen failing against it before the atomic version exists, or it proves nothing (audit finding G2).
`load` opens the file and catches `FileNotFoundError` instead of checking `exists()` first, so there is no gap between the check and the open.
The round-trip test builds its second task (`DONE`, completed 2026-10-15) with `Task.restore`, because the constructor cannot build a task done in the past.
Test-first: collection failed (no module), then all 105 tests passed. Mutation check: six breaks (no `mkdir`, `mkdir` without `parents`, no trailing newline, a missing file no longer giving `[]`, dates not converted, a field dropped) each fail a test, and the file was verified identical afterwards. Coverage of `storage.py` is 100%, and `ruff`, `pyright`, and the CI-version Python linters are clean.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load, step 3
- Issue: #6

## [2026-11-01 12:41] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
Added `Task.restore(...)`, the one way to rebuild a task that already existed. It keeps the stored `created` and `updated`, runs the same rules as the constructor, and fills nothing in.
The model also gained rules that a stored record needs and the constructor now shares: `updated` is not before `created`, neither is later than now, a `DONE` task has a date completed, `id` is an `int` and not a `bool`, and `description` is a string.
`restore` rejects a `DONE` record without a date completed; the constructor still fills in "now".

**Rationale:**
M1 closed the constructor to `created` and `updated`, so the M2 loader needs a deliberate door. `restore` builds the object without calling `__init__`, assigns the stored fields, then runs `_normalize` and `_validate`, the same two steps the constructor uses. That keeps one rule set.
Alternatives rejected: hidden `_created` and `_updated` init parameters (a back door for a false history), and a second copy of the rules inside `restore` (they drift apart when M5 changes one).
The `id` and `description` checks close two gaps from M1 that a hand-edited `tasks.json` could reach: `"id": "1"` or `"id": true` would load and then break `highest + 1`, and `"description": null` would load as `None`. They raise `ValueError`, like the other fields, so the loader catches one type.
Because the checks sit in the shared step, `Task(id="1", ...)` now fails too; that is intended (D5: `id` is a required `int`).
Test-first: 35 new tests failed (28 because `restore` did not exist, 7 `DID NOT RAISE`), then all 98 passed.
Mutation check: 14 breaks each fail a test (each new rule dropped, `restore` skipping `_normalize` or `_validate`, stored stamps replaced by the clock, a boundary made exclusive), and the file was verified identical to the green version afterwards.
Coverage of `task.py` is 100%. `ruff`, `pyright`, and the CI-version Python linters are clean.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load, step 2
- Issue: #6

## [2026-11-01 12:24] Commit Summary

**Change Type:** Refactor

**Scope:** task (`src/task_tracker/task.py`)

**Summary:**
Split `Task.__post_init__` into four steps: stamp `created` and `updated`, `_normalize`, `_fill_in_defaults`, and `_validate`. Behavior is unchanged.

**Rationale:**
`Task.restore` (next commit) must run the same rules as the constructor, but with stored `created` and `updated` instead of the clock. Before this change the rules were interleaved with the defaults: `_settle_date_completed` both filled in a missing date and checked it. Now filling in is separate from checking, so `restore` can skip the defaults (a stored record is complete) and still run every check.
Proof of no change: the 63 existing tests pass unmodified, and `ruff`, `pyright`, and the CI-version Python linters (pylint, isort, black, flake8, mypy) are clean.

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load, step 1
- Issue: #6

## [2026-11-01 12:20] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Added the plan for M2 save and load: seven commits in order, the tests beyond the plan's seven boxes, and the risks. It records two decisions made today. `Task.restore` shares one validation with the constructor, and the task-to-data conversion lives in `storage.py`.

**Rationale:**
The project rules ask for a `TODO.md` entry before any code.
The entry adds rules for a stored record that the plan does not state: `updated` not before `created`, neither later than now, a `DONE` record has a date completed, every field present and none unknown, `id` an `int` and not a `bool`, and unique IDs. Unknown fields are rejected because `save` rewrites the whole file, so ignoring them would delete them on the next save.
Alternatives rejected: hidden `_created` and `_updated` init parameters (a back door for a false history), a second copy of the rules inside `restore` (they drift apart), and `to_record` and `from_record` methods on `Task` (the model would know its storage format).

**References:**

- `TODO.md`: 2026-11-01 Feature: M2 Save and load
- Issue: #6

## [2026-10-31 14:51] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`)

**Summary:**
Recorded the full timeline where the spec lives. `README.md` now gives `start` and `stop` their complete limits. The plan replaces the two-rule boxes with one that lists every broken link, one that states a new task can only be done when it is created, and a corrected done-task box. M2's `restore` box now also covers a stored timeline out of order and the first place a past date completed can be tested.

**Rationale:**
The project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` in step. Issues #5 and #6 are regenerated from the plan after this commit.
One plan box said a date completed in the past "is kept", which stopped being true for a new task once the timeline became enforced, so it is corrected here rather than left to contradict the code.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline, step 4
- Issues: #5, #6
- Pull request: #23

## [2026-10-31 14:50] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
A task's timeline is now fully enforced: `created <= start <= stop <= date completed`, where the last link applies when the task has a date completed. Each broken link raises a `ValueError` with its own message. The default `stop` is the later of now and `start`.

**Rationale:**
Decision from the project owner on 2026-10-31, and the owner's remark that these rules should have been a given. The earlier "exactly the two stated rules" option left `stop` before `start` and a date completed before `created` possible, which are impossible histories. The model now checks every link, including the one that follows from the others.
That way a date completed before `created` gets its own clear message and not a confusing complaint about `start`.
Consequence the owner was told about: `created` is always the moment of creation, so a new task can only be done at that moment. A past date completed is rejected at construction. It belongs to a task that already existed, so those cases move to `Task.restore()` in M2 and `update` in M5.
The done-task default for `stop` added earlier the same day could then never differ from "now", so it was removed as dead code. The default is now the later of now and `start`, which keeps a planned future `start` valid.
Test-first: five tests failed (four `DID NOT RAISE`, one default), then all 63 passed. Four earlier tests could no longer be built through the constructor and were rewritten as rejections or removed, and the "this very moment" test now uses the controlled clock, because a real clock could cross a second boundary between two reads and make it flaky.
Mutation check: eleven breaks fail a test, covering each of the five links being dropped, the default ignoring a future start, and each of the five boundaries being made exclusive. The file was verified identical to the green version afterwards.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline, step 4
- Issues: #5, #6
- Pull request: #23

## [2026-10-31 14:48] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Amended the timeline entry in `TODO.md` for the owner's follow-up of 2026-10-31: the full timeline, `created <= start <= stop <= date completed`.

**Rationale:**
The project rules require the plan before any code. The owner chose "exactly your two rules" earlier and now asks for the full timeline, which was the other option offered. The entry records the cost that option carried: a new task can only be done at the moment it is created.
So a past date completed is unreachable through the constructor, and its tests move to `Task.restore()` in M2 and `update` in M5.
It also removes a default added earlier the same day. A done task's `stop` defaulting to its date completed can no longer differ from "now", so it would be dead code. The default becomes the later of now and `start`, so a planned future `start` does not collide with it.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline, step 4
- Issues: #5, #6
- Pull request: #23

## [2026-10-31 14:42] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Recorded the owner's timestamp decisions of 2026-10-31 where the spec lives. `README.md` says `created` and `updated` are set by the tool and never given by the user, that `start` is never before `created`, and that `stop` is never after the date completed. The plan replaces the old shared-reading box with four, updates the defaults line, and gives M2 a new first box for `Task.restore()`.

**Rationale:**
The project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` in step. Issues #5 and #6 are updated from the plan after this commit.
The M2 box matters most. Because the constructor no longer accepts `created` or `updated`, the M2 round trip cannot pass without a deliberate restore path, so the plan now says so before M2 starts, instead of leaving its implementer to find a wall.
The shared-reading box now explains why a controlled clock is needed: whole-second timestamps make two real clock reads agree almost always, so a real-clock test cannot tell one reading from two.
The two rules not enforced are written down in the plan so they are a recorded choice and not an omission: `stop` before `start`, and a date completed before `created`.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline, step 3
- Issues: #5, #6
- Pull request: #23

## [2026-10-31 14:41] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
A task's `start` can no longer be before its `created`, and its `stop` can no longer be after its date completed. Both raise `ValueError` naming the field. A done task's default `stop` is its date completed.

**Rationale:**
Decision from the project owner on 2026-10-31: start is never before created, and stop is never after the done date. Only those two rules were enforced, as chosen from two options. `stop` before `start` and a date completed before `created` stay allowed, and are recorded as such in `TODO.md`.
The default for `stop` matters: with a default of "now", a done task given a past date completed would have a `stop` after that date and be rejected by the new rule. So a done task stops when it was done. For a task that is not done, `stop` still defaults to now and has no upper limit.
Both boundaries are inclusive: a `start` equal to `created` and a `stop` equal to the date completed are accepted, which is also what the defaults produce.
Test-first: three tests failed (two `DID NOT RAISE`, and a default `stop` of now), then all 59 passed. Three guards pass before and after on purpose: a later `start`, a `stop` equal to the date completed, and an open task's unlimited `stop`.
Mutation check: six breaks each fail a test, including both off-by-one comparisons and a limit wrongly applied to open tasks, and the file was verified identical to the green version afterwards.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline, step 2
- Issues: #5
- Pull request: #23

## [2026-10-31 14:40] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
`created` and `updated` are no longer constructor arguments. The model stamps both with the one clock reading it takes when the task is built. A small private `_now()` function supplies that reading, so tests can control the clock.

**Rationale:**
Decision from the project owner on 2026-10-31, chosen from three options: `created` and `updated` are the moment of creation or update and are never set by the user. Because the constructor no longer accepts them, a caller cannot pass a false history.
The M2 loader will restore stored values through a deliberate `Task.restore()`, which the plan now assigns to M2. M5's `update` stamps `updated` through the model.
Test-first: the new test for passing `created` or `updated` failed with `DID NOT RAISE TypeError`, then all 53 tests passed.
A mutation check found a hole that I introduced earlier. The survivor "updated read from a second clock call" passed every test. Since the normalization commit truncates timestamps to whole seconds, two consecutive clock reads almost always land in the same second, so the loop-based "shared reading" tests could only fail at a second boundary. They had been weak since then.
Fixed with a seam, not by repeating more: `_now()` is a named production function, and the tests replace it with a clock that hands out a new second on every call. The two loop tests became deterministic, and one asserts that the next reading is still unused, so the task took exactly one. All six clock and argument mutants now fail a test.
This partly answers the reviewer's request to control the clock in the tests, which I had declined on 2026-10-31. A named seam avoids the objection I gave, that patching `datetime` ties the tests to the import style.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline, step 1
- Issues: #5
- Pull request: #23

## [2026-10-31 14:34] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Added the `TODO.md` entry for the project owner's decisions of 2026-10-31 on timestamps: the model stamps `created` and `updated`, `start` is never before `created`, and `stop` is never after the date completed.

**Rationale:**
The project rules require the plan before any code. Two choices were put to the owner with pros and cons.
First, how to keep `created` and `updated` out of the user's hands: the model stamps them, with a deliberate `Task.restore()` for storage, over a convention that the CLI never exposes them, or an automatic bump on every change.
Second, how strict the timeline should be: exactly the two stated rules, over also requiring `stop` not before `start`.
The entry records what the choice costs: the M2 round trip needs `Task.restore()`, and `stop` before `start` and a date completed before `created` stay allowed.

**References:**

- `TODO.md`: 2026-10-31 Feature: system-stamped created and updated, and a consistent timeline
- Issues: #5, #6
- Pull request: #23

## [2026-10-31 14:25] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Recorded the project owner's decisions of 2026-10-31 where the spec lives.
`README.md` now says a done task defaults its date completed to the moment it was marked done and cannot be given a future date, and that every datetime is stored and shown as `YYYY-MM-DDTHH:MM:SS`.
The plan amends Q4 and D6 to match, replaces the open `DONE` box with three ticked ones, and `TODO.md` no longer lists the question as open.

**Rationale:**
The project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` in step, and issue #5 is regenerated from the plan after this commit.
The amendments are marked with their date and source so the original 2026-10-23 decisions stay readable beside them. Q4 and D6 are amended in place and not given new numbers, because they are the same questions with a fuller answer.
The M2 loader and the M3 `list` command are told which call to use for the canonical form, `isoformat()`, so neither invents a second format.

**References:**

- `TODO.md`: 2026-10-31 Feature: DONE date and one date form, step 3
- Issues: #5 (regenerated from the plan after this commit)
- Pull request: #23

## [2026-10-31 14:24] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
A `DONE` task now always has a date completed. If none is given it defaults to the same clock reading as the task's other timestamps. A date completed that is passed in, as an object or as text, cannot be later than that reading: it raises `ValueError`.

**Rationale:**
Decision from the project owner on 2026-10-31, answering the open half of the review thread on `task.py` line 21 and audit finding G9: if a task is marked done it gets the date it was marked done, a date passed in is allowed but cannot be in the future.
Test-first: four tests failed (`None is not None`, and `DID NOT RAISE` for a future object and for two future strings), then all 53 passed. Three guards pass before and after on purpose, since they protect allowed paths: a past date is kept, a task that is not `DONE` still has none, and a date completed of this very moment is accepted.
That last guard exists because of a subtlety: `datetime.now()` carries microseconds, so comparing it with the truncated reading would wrongly reject "now". The date is normalized to whole seconds before the comparison.
Mutation check: a `DONE` task with no default, a future date accepted, `>=` instead of `>`, an open task allowed a date, and a second clock read for the default each fail a test, and the file was restored byte-for-byte.
Two existing tests used 2026-11-02 as a completed date. With today at 2026-10-31 that is in the future, which the new rule rightly rejects, so they now use a fixed past date.
Known trade-off, recorded in `TODO.md`: the model cannot tell "marked done now" from "loaded from a file", so a hand-edited `DONE` record with no date would receive the load time.

**References:**

- `TODO.md`: 2026-10-31 Feature: DONE date and one date form, step 2
- Issues: #5
- Pull request: #23 (review thread on `task.py` line 21)

## [2026-10-31 14:23] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
Every datetime field now ends up in one form however it is passed in. An ISO 8601 string, a `date`, or a `datetime` becomes a naive local `datetime` with whole seconds, so `isoformat()` always reads `YYYY-MM-DDTHH:MM:SS`. A bare date means midnight (Q6). An invalid string, a value with a UTC offset, or a value of another type raises `ValueError` that names the field.

**Rationale:**
Decision from the project owner on 2026-10-31: all dates are formatted the same whatever way the user passes them in. The model is the one place the CLI and the M2 loader both go through, so one normalizer covers both, as the enum coercion does for labels.
Whole seconds is my reading of "the same": `created` carried microseconds while a typed date did not, and a save at second precision would then make the M2 round trip lose them. The reading is flagged in `TODO.md` for correction.
Test-first: 13 new tests failed for the expected reasons (raw strings stored as text, a `date` not equal to a datetime, microseconds present, four bad inputs not rejected), then all 46 tests passed. The existing before/after clock test now truncates its lower bound to whole seconds, since the stored value is truncated the same way.
Mutation check: keeping microseconds, not parsing strings, reading a bare date as noon, accepting a UTC offset, and leaving the field name out of the error each fail a test, and the file was restored byte-for-byte.
The aware-datetime check moved into the normalizer, so a string such as `2026-11-02T09:00:00+00:00` is rejected after parsing. That also covers audit finding G6 at the model level. The `dataclasses.fields` loop it replaced is gone, because strings must be handled before a field can be recognized as a datetime.
The field types stay `datetime`; strings and dates are accepted at the boundary, as labels are for the enums.

**References:**

- `TODO.md`: 2026-10-31 Feature: DONE date and one date form, step 1
- Issues: #5
- Pull request: #23

## [2026-10-31 14:21] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Added the `TODO.md` entry for the decisions the project owner gave on 2026-10-31: a `DONE` task gets a date completed by default, a date completed cannot be in the future, and all datetimes share one form.

**Rationale:**
The project rules require the plan before any code. The decisions answer the open half of the review thread on `task.py` line 21 of PR #23, and audit finding G9.
One interpretation is mine and is flagged in the entry for correction: "formatted the same" is read as one canonical form, whole seconds in ISO 8601, with a bare date meaning midnight (Q6). Whole seconds, because `created` carries microseconds while a typed date does not, and a save at second precision would then break the M2 round trip.
The entry records a trade-off the owner may want to revisit: the model cannot tell "marked done now" from "loaded from a file", so a hand-edited `DONE` record with no date would get the load time.

**References:**

- `TODO.md`: 2026-10-31 Feature: DONE date and one date form
- Issues: #5
- Pull request: #23

## [2026-10-31 14:13] Commit Summary

**Change Type:** Fix

**Scope:** lint (`.github/linters/.ruff.toml`, `CLAUDE.md`)

**Summary:**
Fixed the `Lint` failure on the review-fix push to PR #23: super-linter's `PYTHON_RUFF_FORMAT` reported that `tests/test_task.py` would be reformatted. Added a repository-level ruff config with `line-length = 88`.

**Rationale:**
Reproduced before changing anything, with CI's own ruff 0.15.17 and super-linter's template config: it wants a wrapped `parametrize` decorator joined onto one line. The same file passes `black`, local ruff, and the pre-commit hook, because the template sets `line-length = 120` while those three use 88.
So the template contradicts itself, and any call between 89 and 120 characters passes one formatter and fails the other.
Fixed at the cause, as with the isort config: super-linter reads `.github/linters/.ruff.toml` before its default, and the new file keeps the template's cache directory and `E203` ignore and changes only the width. Rejected: setting 120 project-wide, which would make `black` fail instead, and joining the decorator onto one line, which would break the local pre-commit hook.
After the change, ruff 0.15.17 format and check pass on all six Python files, black and local ruff 0.16.6 still pass, and the full set of Python checks is green.
My earlier verification missed this because it ran the lockfile's ruff with the default width, not CI's version with CI's config. The script now runs both CI-version ruff checks.

**Bugfix Context:**
Root cause: super-linter's default ruff width (120) differs from the width used by the other formatters here (88), and the earlier local check did not use CI's config.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23

## [2026-10-31 14:08] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Recorded the review-driven `Task` behavior in the plan's M1 section and in `TODO.md`: six new ticked boxes, a non-UTC time zone in the timestamp test, the answers to two "Think about" questions, and the open spec question about `DONE`.

**Rationale:**
The project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` in step. The five code commits before this one changed what `Task` accepts, so the plan's description of M1 would otherwise be out of date, and issue #5 is regenerated from it.
The "Think about" answers now say what was decided and why, in the same place the question was asked, instead of leaving a question that the code already answers.
Two things stay open on purpose and are written down so they are not lost: whether `DONE` requires a date completed (Q4 is silent, audit finding G9), and that `update` in M5 must re-validate because assigning an attribute skips `__post_init__`.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5 (regenerated from the plan after this commit)
- Pull request: #23

## [2026-10-31 14:07] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
A new `Task` now reads the clock once and shares that reading across `created`, `updated`, `start`, and `stop`, and the default-timestamp test runs under a non-UTC `TZ`.

**Rationale:**
Two review comments on PR #23. With four separate `datetime.now()` calls, `created != updated` on 568 of 2000 new tasks in my run (the reviewer saw 614). Anything that reads `updated > created` as "was modified" would misclassify an untouched task, and the audit had left this open as finding G13.
Mechanism chosen with the user on 2026-10-31 from four options: a private sentinel default that `__post_init__` replaces with one shared reading. The fields stay typed `datetime`, so pyright needs no `None` checks in the M2 loader and the M3 `add`, and `Task(id=1, name="x")` keeps working. The cost is an unusual-looking default, which carries a comment.
Rejected: `None` defaults (the fields would become `datetime | None`), a `Task.new()` factory (two construction paths), and keeping the skew.
The sentinel is compared with `is`, so a caller who passes an equal date keeps it.
Second comment: a default read from UTC but stored naive passed both timestamp tests on a UTC machine such as the CI runner, so the "local" half of D6 was not pinned. The test now sets `TZ=Asia/Kolkata`, which has no daylight saving and differs from UTC all year, so that mutant fails everywhere.
Test-first: both shared-clock tests failed, showing `created` and `updated` one microsecond apart, then all 33 tests passed.
Mutation check on the final `task.py`: eight breaks (naive-UTC default, separate clock reads, aware datetimes allowed, Q4 unenforced, positional fields, unstripped name, no enum coercion, null name) each fail at least one test, and the file was restored byte-for-byte.
Not done: patching the clock inside the tests. The bracket pattern is the plan's own, patching would tie the tests to the module's import style, and the real gap was the missing non-UTC zone.

**Bugfix Context:**
Root cause: each timestamp field had its own `default_factory`, so every default was a separate clock read, and the tests could not tell a local default from a UTC one.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23 (review threads on `task.py` line 18 and `test_task.py` line 38)

## [2026-10-31 14:06] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
Every `Task` field after `id` and `name` is now keyword-only, using a `KW_ONLY` marker. `Task(1, "Buy milk")` still works.

**Rationale:**
Review comment on PR #23. All 11 fields could be passed positionally and six share the `datetime` type, so `Task(1, "n", "d", later, earlier)` stored `created=later, updated=earlier` and no type checker could object (reproduced). The M2 loader and the M3 `add` command are about to construct tasks in volume, so the class of bug is closed before they exist.
Test-first: the positional-arguments test failed with `DID NOT RAISE TypeError`, then all 31 tests passed. A second test, that `id` and `name` still work positionally, passes before and after on purpose: it guards the shorthand the reviewer's suggestion kept.
`id` and `name` stay positional-or-keyword because the reviewer's suggestion placed the marker after them, and they are the two required, differently typed fields. The marker is `dataclasses.KW_ONLY`, so no new dependency and no change to the generated field order.

**Bugfix Context:**
Root cause: a dataclass accepts every field positionally by default, and type checking cannot tell two `datetime` arguments apart.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23 (review thread on `task.py` line 15)

## [2026-10-31 14:05] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
`Task` now enforces two invariants that were only documented: no datetime field may be timezone-aware (D6), and only a `DONE` task may have a date completed (the half of Q4 that the spec states).

**Rationale:**
Two review comments on PR #23. D6 says naive local time, but `Task(due=<aware>)` was accepted, and sorting one aware task against a naive one raised `TypeError: can't compare offset-naive and offset-aware datetimes` (reproduced). The check loops over `dataclasses.fields`, so a field added later is covered without remembering to list it.
Q4 says a task that is not `DONE` always has no date completed, but `Task(status=TO_DO, date_completed=<now>)` was accepted and would land in the wrong section of `list` and `list --all`. A loader reading a hand-edited file now gets a `ValueError` for it.
Test-first: eight new tests failed with `DID NOT RAISE ValueError`, then all 29 passed. One more test, that a `DONE` task keeps its date, passes before and after on purpose: it guards the allowed path against the new rule.
Deliberately not decided here: whether `DONE` requires a date completed. Q4 is silent, and `Task(status=DONE)` still has none. The review thread stays open for that spec question, and the audit's finding G9 (M4's sort must cope with it) is unchanged.

**Bugfix Context:**
Root cause: both rules lived only in the plan and `README.md`, and the model validated nothing but the name.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23 (review threads on `task.py` lines 20 and 21)

## [2026-10-31 14:04] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
`Task` now normalizes and validates its inputs at construction: a non-string name raises `ValueError`, the name is stored stripped, and `status` and `priority` are coerced to `Status` and `Priority` members, so an unknown label raises `ValueError`.

**Rationale:**
Three review comments on PR #23, reproduced before changing anything.
`Task(id=1, name=None)` raised `AttributeError`, so a hand-edited `tasks.json` with a null name would surface a traceback and a caller catching `ValueError` would miss it.
`Task(id=1, name="  Buy milk  ").name` kept its padding, so the delete prompt, any name filter and duplicate detection would see different text than the user meant.
`Task(1, "x", priority="HIGH")` stored a plain `str`, so `t.priority is Priority.HIGH` was `False`. Because both are `StrEnum`s, an equality assertion in the M2 round-trip test would have passed anyway.
Test-first: five new tests failed for the expected reasons (`AttributeError`, the padded name, `'DONE' is not Status.DONE`, two `DID NOT RAISE`), then all 20 tests passed.
`ValueError` for a non-string name is a decision, not an oversight. Ruff's `TRY004` prefers `TypeError`, but the loader should catch one exception type for any bad field, which a bad enum label already raises. The suppression sits on that line with the reason beside it.
Storing the stripped name in the model, not only at the command line, puts the rule in one place for the loader and for `add`.

**Bugfix Context:**
Root cause: `__post_init__` validated the name only after calling `.strip()` on it, and trusted the annotations for the enum fields, although the annotations are not checked at runtime.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23 (review threads on `task.py` lines 22 and 28)

## [2026-10-31 14:03] Commit Summary

**Change Type:** Fix

**Scope:** test (`tests/test_priority.py`)

**Summary:**
The priority test now asserts the member name as well as the value: `Priority[name].name == name` and `Priority(name) is Priority[name]`.

**Rationale:**
Review comment on PR #23. The old test checked only `Priority(name).value == name`, so an enum written as `MED = "MEDIUM"` passed while `Priority.MEDIUM` did not exist. Q1 says users type and see the enum names, and M3 will parse them with `Priority[name]`, so that break would have shipped with the test green.
Red step for a test-only change: the new test fails against exactly that mutant with `KeyError: 'MEDIUM'` (3 other cases pass), and passes against the real enum. The mutated file was restored byte-for-byte.

**Bugfix Context:**
Root cause: the assertion covered the lookup by value but not the lookup by name, which are different enum operations.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23 (review thread on `tests/test_priority.py`)

## [2026-10-31 13:26] Commit Summary

**Change Type:** Fix

**Scope:** lint (`.github/linters/.isort.cfg`, `src/task_tracker/task.py`, `tests/`, `CLAUDE.md`)

**Summary:**
Fixed the `Lint` failure on PR #23. Super-linter's `PYTHON_ISORT` rejected the two test files, and `PYTHON_PYLINT` scored the code 8.67 for a missing docstring in each test module and function, and for `Task` having 11 instance attributes against a limit of 7. The new `Tests` workflow itself passed on GitHub.

**Rationale:**
Both checks passed on earlier pull requests only because there was almost no Python. Local verification covered ruff, pyright, and the Markdown linters, but not the five Python linters super-linter runs separately (pylint, isort, black, flake8, mypy).
Reproduced before fixing: pylint 4.0.6 and isort 8.0.1 with the super-linter v8.7.0 default configs gave the same score, the same eight messages, and the same two files as the CI log. After the fix all five linters pass at CI's versions, and pylint scores 10.00.
isort: it does not see the `src` layout, so it treats `task_tracker` as a third-party package and rejects the usual empty line before project imports.
Fixed at the cause with `known_first_party` in a repository-level config, `.github/linters/.isort.cfg`, which super-linter reads before its default.
A controlled check confirmed it: the repository config exits 0 on the unchanged files, the default config still fails them. Rejected: deleting the empty lines to suit the default, which would recur in every later milestone.
pylint: inline suppressions with the reason beside them, matching how `DTZ005` was handled.
The test modules get a docstring and one file-level `missing-function-docstring` disable, since the test names already state the intent.
`Task` gets a class-level `too-many-instance-attributes` disable, because `README.md` defines the 11 fields.
Rejected: a docstring on every test that repeats its name, and raising pylint limits project-wide, which would also loosen future classes.

**Bugfix Context:**
Root cause: the verification routine omitted super-linter's Python linters. The project `CLAUDE.md` now lists them, and the saved lint-recipe memory covers them too.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #23

## [2026-10-31 13:03] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`)

**Summary:**
Ticked the eight M1 boxes and updated the plan to match what was built: the rename test wording, the CI template, and the outcomes of two "Think about" questions.

**Rationale:**
The rename bullet now describes the test that exists, which parses each name `README.md` promises, because a test that a removed name stays removed fails only on a redesign. The CI bullet now says to follow `super-linter.yml` and not `version-bump.yml`, which closes audit finding G11: the bump job needs `contents: write`, a test job should have `contents: read` only.
The timestamp and empty-name questions keep their text and gain the current answer. The empty-name note records a known limit for M5: `__post_init__` covers construction, but assigning `task.name = ""` later skips it.
Ticked after the full verification run: tests, coverage gate at 96.77%, ruff, pyright, all pre-commit hooks, and both Markdown linters. The Tests workflow itself is still unproven on GitHub, so issue #5 stays open and unticked until this pull request's CI result is in.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5 (boxes ticked after CI passes)
- Pull request: pending

## [2026-10-31 13:01] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`)

**Summary:**
Added the Tests badge next to the Lint badge (M1 step 5). It points at the `Tests` workflow on `main` and links to the workflow page.

**Rationale:**
The Lint badge only reports linting, so without this one nothing on the page says the tests pass.
Checked before adding it: the Lint badge returns HTTP 200 and reads "Lint - passing", while the Tests badge returns HTTP 404 today, because `tests.yml` exists only on this branch and GitHub serves a workflow badge only once the file is on the default branch.
Consequence, accepted: the badge shows as a broken image when `README.md` is viewed on `develop`. After `develop` is promoted to `main` it should read "no status" until the first run on `main`, then "passing". `main` itself is unaffected until then, because its `README.md` does not contain the badge yet.
Rejected: pointing the badge at `develop`, which would show a real status sooner but would not mirror the Lint badge or describe the branch users install from.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model, step 5
- Issues: #5
- Pull request: pending

## [2026-10-31 13:00] Commit Summary

**Change Type:** Feature

**Scope:** ci (`.github/workflows/tests.yml`, `CLAUDE.md`)

**Summary:**
Added the `Tests` workflow (M1 step 4). On every push and pull request it checks out the code, installs uv with caching, runs `uv sync --locked`, then `uv run pytest`. The project `CLAUDE.md` documents the workflow and the Markdown linting gap that failed PR #20.

**Rationale:**
Added after the model tests exist, because pytest exits with code 5 when it collects no tests and a workflow merged earlier would fail on its first run.
The audit (G11) warned that copying `version-bump.yml` would also copy its `contents: write`. This workflow follows `super-linter.yml` instead: top-level `permissions: {}`, job-level `contents: read` only, and `persist-credentials: false`. Both pinned action SHAs are the ones already used in the other workflows.
The step order and `--locked` follow the uv GitHub Actions guide, and `enable-cache` follows your CI rule to cache dependencies.
Configuration is the one case where test-first does not apply, so it was validated with the tools super-linter runs. zizmor 1.31.1 (offline), actionlint, and Prettier report nothing, and yamllint reports only the line-length warning that `version-bump.yml` also has. Running the two `run` commands locally passed: the lockfile satisfies `--locked` and all 15 tests pass.
Not verified: the first real run on GitHub, including uv downloading the Python version pinned in `.python-version` and the cache behavior. That is what this pull request's CI will show.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model, step 4
- Issues: #5
- Pull request: pending

## [2026-10-31 12:59] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`, `CLAUDE.md`)

**Summary:**
Added the `Task` dataclass (M1 step 3): required `id` and `name`, `description` defaulting to `""`, four timestamps defaulting to the current local time, `due` and `date_completed` defaulting to `None`, `status` `TO_DO`, `priority` `LOW`. A blank or whitespace-only name raises `ValueError`.
Fields follow the `README.md` "Task object" order. The project `CLAUDE.md` now describes the code and the test setup as they are.

**Rationale:**
Written in three red-green cycles, each test watched failing for the expected reason first: module missing, attribute missing, and `DID NOT RAISE`. The full suite then passed: 15 tests, 100% coverage on `task.py`, ruff and pyright clean.
Mutation check, done by breaking a backed-up copy of `task.py` and restoring it byte-for-byte: a default frozen at import, a timezone-aware default, a wrong default priority, removed validation, and a name check without `strip()` each fail at least one test.
The name check lives in `__post_init__`, so every way of constructing a task hits it. Updating an existing task's name later (M5) will need the same rule, because assigning an attribute skips `__post_init__`.
Open question from the plan, defaulted: each timestamp has its own `default_factory`, so `created` and `updated` on one new task can differ by microseconds. This is the simplest option and no current test depends on equality; sharing one "now" would need a classmethod or a custom `__post_init__`.
Ruff 0.16.6 enables `DTZ005` by default, which flags the test's `datetime.now()` calls. D6 chose naive local time, so the two lines carry `# noqa: DTZ005` with the reason beside them. No project-wide ignore was added.
The required `id` has no dedicated test: a test that fails only when someone gives it a default would be a change detector. Every test passes an `id`, which keeps the decision exercised.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model, step 3
- Issues: #5
- Pull request: pending

## [2026-10-31 12:55] Commit Summary

**Change Type:** Refactor

**Scope:** priority (`src/task_tracker/priority.py`, `tests/test_priority.py`, `CLAUDE.md`)

**Summary:**
Renamed `Priority.MED` to `Priority.MEDIUM` (value `"MEDIUM"`), added the first test file, and removed the now-false "until M1 lands the rename" sentence from the project `CLAUDE.md`.

**Rationale:**
Q1: users type and see the enum names, and `README.md` says `MEDIUM`. The stored value is the enum value, so the rename had to land before any task file exists.
Test-first: the new test failed with `ValueError: 'MEDIUM' is not a valid Priority` for exactly the `MEDIUM` case and passed for the other three; after the rename the whole suite, ruff, and pyright are clean.
Deliberate departure from the plan's wording "a test that `Priority.MEDIUM` exists and `Priority.MED` does not": asserting that a removed symbol stays removed only fails on a redesign, never on a bug.
The test instead parses each of the four names `README.md` promises users can type, with the expected values taken from the `README.md` literal list. That is the behavior the `--priority` option and the JSON loader will depend on.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model, step 2
- Issues: #5
- Pull request: pending

## [2026-10-31 12:54] Commit Summary

**Change Type:** Feature

**Scope:** deps (`pyproject.toml`, `uv.lock`)

**Summary:**
Added `pytest` and `pytest-cov` to the `dev` dependency group (M1 step 1). The lockfile gained 147 lines and lost none.

**Rationale:**
Decision D4 chose pytest with pytest-cov: `tmp_path`, `monkeypatch`, and `capsys` cover what this CLI needs, and `--cov-fail-under` gates coverage with one flag. Done first so every later M1 step can start with a failing test.
`uv add --dev` writes to `[dependency-groups]`, which `pyproject.toml` already used (checked against the uv documentation). The lock was taken after the `main` sync, so the earlier `virtualenv` bump is untouched.
Also confirmed on this machine that `uv run pytest` exits with code 5 when it collects no tests, which is why the CI workflow waits until the model tests exist.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model, step 1
- Issues: #5
- Pull request: pending

## [2026-10-31 12:45] Commit Summary

**Change Type:** Fix

**Scope:** deps (`uv.lock`)

**Summary:**
Merged `main` into `develop`. The only change that comes across is Dependabot PR #18, which bumps `virtualenv` from 21.7.13 to 21.14.13 in `uv.lock`.

**Rationale:**
Dependabot targets the default branch, so its pull request merged into `main` and left `develop` three commits behind (the bump, its merge, and the earlier promotion merge). M1 step 1, `uv add --dev pytest pytest-cov`, rewrites `uv.lock` on a branch cut from `develop`. Syncing first means that change starts from the current lockfile and cannot conflict with the bump when `develop` is promoted to `main`.
Chosen with the user on 2026-10-31 over deferring the sync to promotion time. The merge was made without committing so this entry could go in the same commit, as the project rules require.
Not addressed here: the repository has no `dependabot.yml`, so the divergence will recur on the next security bump. Redirecting Dependabot to `develop` was not part of this change and has not been checked against the Dependabot documentation.

**Bugfix Context:**
The bump is a dependency security update. Developing against the older `virtualenv` would leave `develop` behind the fix that `main` already has.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model (step 1 touches `uv.lock`)
- Issues: none
- Pull request: pending

## [2026-10-31 12:33] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`)

**Summary:**
Reordered the M1 checklist to match `TODO.md`: pytest first, then the `MEDIUM` rename with a failing test, then the model tests, then the CI workflow and the Tests badge. Added the reason for the CI placement and a link to the pytest exit-code documentation.

**Rationale:**
Finding G12 of the Opus spec-gap audit: the plan and `TODO.md` disagreed on M1 step order, and the project `CLAUDE.md` says to keep the plan, the matching issue, and `README.md` in step.
The order is not cosmetic. pytest exits with code 5 when it collects no tests, so a CI workflow merged before any test exists fails its first run. The rename now carries its own failing test so it follows the same red, green cycle as the model.
The documentation URL returned HTTP 200 when checked earlier in this session.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5 (synced in the next step of this branch)
- Pull request: pending

## [2026-10-31 12:32] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Reworded the M1 naive-datetime test to cover only datetime fields that are not `None`, and added a "Think about" question on whether a new task shares one timestamp across `created`, `updated`, `start`, and `stop`. Mirrored both in `TODO.md`.

**Rationale:**
Findings G4 (naive-datetime part) and G13 of the Opus spec-gap audit.
The old wording said every datetime field is naive, but `due` and date completed default to `None` and `None.tzinfo` raises, so the test could not be written as stated.
The timestamp question is left open as a question, not decided: it is a design choice the implementer owns, and either answer passes the existing "between before and after" test.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5 (synced in a later step of this branch)
- Pull request: pending

## [2026-10-31 12:31] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Decided that a task's `id` is a required `int`. Added the decision to D5 in the plan, reworded the first M1 test to start from ID 1, replaced the open ID question in M1's "Think about" and in `TODO.md` with the decision.

**Rationale:**
Finding G1 of the Opus spec-gap audit: `README.md` marks the ID required, but the first M1 test built a task from only its name, so the open ID question had to be answered one way before that test could be written.
Chosen with the user on 2026-10-31. A required `int` leaves no `None` state, so no save has to guard against a task without an ID, and it matches the reasoning used to default `description` to the empty string.
Rejected: an optional `id` set when the task is added. It makes the first test work as written, but contradicts "required" and needs an extra M2 test that rejects an unsaved ID.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5 (synced in a later step of this branch)
- Pull request: pending

## [2026-10-31 12:30] Commit Summary

**Change Type:** Fix

**Scope:** docs (`SUMMARY.md`, `TODO.md`)

**Summary:**
Fixed the four linting errors that failed the `Lint` workflow on PR #20: two `SUMMARY.md` lines over 400 characters (MD013), one bare `README` in `SUMMARY.md`, and `Tradeoffs` in the `TODO.md` heading.

**Rationale:**
Edited the content instead of excluding files, matching the 2026-10-23 decision.
The `TODO.md` heading now reads "Risks & Trade-offs". This is a deliberate change from the global template wording, because textlint's terminology rule rejects the unhyphenated form.

**Bugfix Context:**
Root cause: pre-commit runs ruff and the shell linters but not markdownlint or textlint, so the push went out unchecked. This is the same gap recorded on 2026-10-23.
Reproduced the exact four findings locally with markdownlint-cli 0.49.0 and textlint 15.7.1, installed in the session scratchpad outside the repository, and confirmed all five Markdown files pass after the fix.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5
- Pull request: #20

## [2026-10-31 12:07] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Created `TODO.md` with the M1 (Task model) entry: objective, a six-step commit-sized approach, the tests, and risks. No code changed.

**Rationale:**
The plan's "How to work each milestone" requires a `TODO.md` entry before coding starts, and the file did not exist.
Two deliberate departures from the plan's M1 checklist order: pytest is added first (every later step is test-first, so a runner must exist), and the CI workflow moves after the model tests, because pytest exits with code 5 when it collects no tests and the first CI run would fail.
Both facts were checked against current pytest documentation.
The entry also records a trap verified by running it: `created: datetime = datetime.now()` raises no error and shares one frozen timestamp across instances, because the dataclass guard only rejects unhashable defaults. The ID-entry question from the plan's "Think about" is left open for the user to decide before the model is written.
Both cited documentation URLs returned HTTP 200 and the dataclasses anchor exists.

**References:**

- `TODO.md`: 2026-10-31 Feature: M1 Task model
- Issues: #5 (M1)
- Pull request: pending

## [2026-10-31 12:06] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`)

**Summary:**
Recorded that a task's `description` defaults to the empty string. `README.md` now reads "task description (string, default empty)", the plan's Global Constraints list it with the other defaults, and the first M1 test also asserts it.

**Rationale:**
`README.md` listed `description` with no default, which left M1's `Task` model underspecified.
Chosen with the user on 2026-10-31 from three options. `""` keeps the field a plain `str`, so pyright and display code need no `None` checks, and "no description" has one representation.
Rejected: `None` (consistent with `due`, but forces a `str | None` check everywhere it is printed) and leaving the field out of M1 (diverges from the `README.md` spec).
Whether `add` and `update` expose `--description` stays deferred to M3 and M5, as Q3 did for `start` and `stop`.

**References:**

- `TODO.md`: none yet (the M1 entry follows in the next commit)
- Issues: #5 needs the same one-line test change (pending, see Pull request)
- Pull request: pending

## [2026-10-31 12:04] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`)

**Summary:**
Ticked the M0 box "Tag `v0.1.0` on `main` and push the tag" in the plan.

**Rationale:**
The tag was pushed on 2026-10-23 but the box stayed unticked, so the plan contradicted M0's own "Done when" line. Checked before ticking: `git ls-remote --tags origin` lists `refs/tags/v0.1.0` at `9e974fb`. Issue #4 already shows 15 of 15 boxes ticked and is closed, so nothing else mirrors this line.

**References:**

- `TODO.md`: none (a one-character fix to a status box)
- Issues: #4 (closed, already ticked)
- Pull request: pending

## [2026-10-23 13:46] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`)

**Summary:**
Added four status badges under the title of `README.md`: Lint (the `super-linter.yml` workflow on `main`), License (MIT), Latest tag, and Python (read from `pyproject.toml`). Added two follow-up boxes to the plan: a Tests badge in M1, and a check in M9 that the tag badge shows `v0.2.0`.

**Rationale:**
Each badge URL was fetched and its displayed text read before it was chosen.
The first badge is named Lint because no workflow runs pytest yet, so a generic build badge would claim more than CI checks. The Tests badge waits for the pytest workflow in M1.
The Python badge reads `requires-python` from `pyproject.toml` on `main`, so it cannot drift from the real floor the way a hardcoded badge would.
Rejected: GitHub Releases (no releases exist, only tags), PyPI version and coverage (nothing published, no tests yet), OpenSSF Scorecard (invalid repository path), Version Bump workflow (no status on `main`), and the Ruff, uv, and pre-commit badges as decorative.

**References:**

- `TODO.md`: none (no entry was written before this change)
- Issues: #5 and #13 updated to mirror the plan, ahead of this change merging
- Pull request: pending

## [2026-10-23 13:22] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `README.md`)

**Summary:**
Follow-up to the commit that recorded the M0 decisions. Removed wording in the plan that still described the decisions as pending, ticked the two M0 boxes that are complete, and added the test runner to the developer requirements in `README.md`.

**Rationale:**
The previous pass searched for the new text it had added, not for old text that had become false, so three statements still said the decisions were owed: the plan introduction, the "Decisions to make before M1" heading, and the "answer in `README.md` during M0" heading.
The M0 boxes for creating `develop` and for the decisions are now ticked in the plan to match issue #4.
The decision about pytest (D4) was missing from `README.md`, so it now lists pytest with pytest-cov.
This is a new commit, not an amend, because the pull request is already open and an amend would need a force push.

**References:**

- `TODO.md`: none (no entry was written before this change)
- Issue: #4 (M0). Not complete: the `v0.1.0` tag is still outstanding
- Pull request: #14

## [2026-10-23 13:10] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `docs/implementation-plan.md`, `CLAUDE.md`)

**Summary:**
Recorded every M0 decision where it is consumed. `README.md` now types the Task object (datetime fields, nullable `due`, ID rule), lists the enum names, gains an Options table with short and long forms, and names the commands in features 3 to 7.
The plan marks D1 to D6 and Q1 to Q6 as decided and updates the M1 to M7 checklists to match.
Project `CLAUDE.md` replaces the label-mismatch note and says the plan, the matching issue, and `README.md` change together.

**Rationale:**
The plan was written with recommendations; the decisions replace them so the milestones stop describing options.
Each decision pins a test where behavior could silently drift: the `MEDIUM` rename, a naive datetime check, a null `due` round trip, undated tasks sorting last, a mandatory delete confirmation, short-form parity, and a `-d` versus `-D` slip that must create nothing.
GitHub issues #4 to #13 were edited in place to mirror the plan, so the plan stays the source and the issues are copies.
Two choices differ from the recommendation given at the time: plain `start` and `stop` fields (Q3) and `-d` for `--dir`.
Alternatives not taken: recording D1 to D6 as ADRs, and splitting this into one commit per file, which would leave the plan, `README.md`, and `CLAUDE.md` disagreeing between commits.

**References:**

- `TODO.md`: none (no entry was written before this change)
- Issues: #4 to #13 (M0 to M9), updated on GitHub, not part of this commit
- Pending code change: rename `Priority.MED` to `MEDIUM` in `src/task_tracker/priority.py`, the first box in M1 (#5)

## [2026-10-23 12:18] Commit Summary

**Change Type:** Fix

**Scope:** docs (`CLAUDE.md`, `docs/implementation-plan.md`)

**Summary:**
Resolved the markdownlint and textlint failures that broke the `Lint` workflow on `703cfbb`. Wrapped the 471-character bullet in `CLAUDE.md`, and corrected terminology in both files (capitalization, hyphenation, `README` written as the `README.md` filename).

**Rationale:**
The fix edits the content instead of excluding the files from super-linter, so the documents keep being linted. `textlint --fix` was not used: it would rewrite the `README.md` filename to "readme" and the "To-do" status label to "todo", and `CLAUDE.md` says to reconcile that label deliberately.

**Bugfix Context:**
Root cause: `703cfbb` added the first Markdown files other than `README.md`. Super-linter's default configuration then reported MD013 (line over 400 characters) and 27 `terminology` errors.
Neither pre-commit nor ruff runs those linters, so nothing caught it before the push. Verified locally with the same linter versions CI uses (markdownlint-cli 0.49.0, textlint 15.7.1, prettier 3.8.4): all exit 0.

**References:**

- `TODO.md`: none (no entry was written before this fix)
- Failing run: GitHub Actions `Lint` 40007580901 (`develop`) and 40007472521 (`main`)
