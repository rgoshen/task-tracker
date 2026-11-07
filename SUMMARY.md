# Summary

## [2026-11-07 15:58] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
Rename the unused `prompt` argument of the two `input` replacements that another writer uses to `_prompt`, and say in the comment of the ID-reuse test which case tells "highest + 1" from a count.

**Rationale:**
The CI linters were run on the four M6 commits before the push. Pylint 4.0.6 reported `unused-argument` (W0613) on both replacements and would have failed the `Lint` job. The leading underscore is the form pylint accepts, and `input` is called with the prompt as its only argument, so the name does not matter to the caller.
The comment said a count would number both new tasks 3. That is only true for the gap case: after `delete 3` a count and "highest + 1" agree, which is why the gap case is the one that can fail.
Checked after the change: pylint 10.00, black, isort, flake8, and mypy clean at the CI versions, JSCPD 0 clones, 369 tests pass.

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete, step 6
- Issue: #10

## [2026-11-07 15:56] Commit Summary

**Change Type:** Docs

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
Pin that `add` after a `delete` numbers the new task from the highest remaining ID (D5).
Deleting task 3 and adding a task gives ID 3 again.
Deleting task 2 and adding a task gives ID 4, not 3, so the gap is not reused.
No source code changed.

**Rationale:**
Step 4 of M6 (`TODO.md`: 2026-11-07 Feature: M6 Delete).
The highest-ID case passes with the current code, and so does a count-based rule, so the gap case is the one that tells them apart.
Numbering by count was tried as a temporary mutant: the gap case failed with a duplicate-ID error, and the existing numbering test failed too. The mutant was then reverted.

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete, step 4
- Issue: #10

## [2026-11-07 15:54] Commit Summary

**Change Type:** Fix

**Scope:** CLI (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
After a yes, `delete` reads the task list again and deletes task `ID` only if it still equals the task that was shown.
A task another writer added while the prompt was open is kept.
If the task was renamed, changed, or removed meanwhile, `delete` prints one error line, exits 1, and deletes nothing.

**Rationale:**
Step 3 of M6 (`TODO.md`: 2026-11-07 Feature: M6 Delete).
The prompt waits on a person, so the list read before it can be minutes old, and saving it would drop a task added from another terminal.
`Task` is a dataclass, so `==` compares every field.
The rest of the file is saved as it was read after the answer.
The remaining window between that read and the save is the same as for every other command (#27).

**Bugfix Context (if applicable):**
The first version of `delete` saved the list read before the prompt.
Any task another process added while the prompt was open was lost on a yes.

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete, step 3
- Issue: #10

## [2026-11-07 15:53] Commit Summary

**Change Type:** Feature

**Scope:** CLI (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Refuse a `delete` that names no task or gets no answer.
An unknown ID exits 1 before the prompt is shown.
An answer that cannot be read (end of input, a closed standard stream, or Ctrl-C) exits 1 with one error line saying the task was not deleted, and no traceback.
The list of bad IDs that `update` already tested is now one shared constant, and `delete` uses it too.

**Rationale:**
Step 2 of M6 (`TODO.md`: 2026-11-07 Feature: M6 Delete).
The three exceptions are caught only around the `input` call, because `main` handles just `ValueError` and `OSError`.
A closed standard output has no stream for the prompt, so the prompt is passed on as it is and `input` raises `RuntimeError` itself.
The shared list keeps the duplicated test cases out of the copypaste check (JSCPD, threshold 0).

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete, step 2
- Issue: #10

## [2026-11-07 15:51] Commit Summary

**Change Type:** Feature

**Scope:** CLI (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Add the `delete ID` command. It loads the task list, finds the task, and asks `Delete task ID: name? [y/N]` through `input`.
Only `y` or `yes` (any case, spaces around the answer allowed) deletes the task and saves the rest.
Any other answer keeps the task, prints `Kept task ID: name`, and leaves the file unwritten.
The prompt text goes through `_printable`, so a control character in a name is shown as an escape on one line.

**Rationale:**
Step 1 of M6 (`TODO.md`: 2026-11-07 Feature: M6 Delete). The prompt comes with the command, so no delete happens without a yes. The answer rule and the prompt text were settled on 2026-11-07. The file is read once here; a later step re-reads it after the answer, because the prompt waits on a person and the list can change meanwhile.

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete, step 1
- Issue: #10

## [2026-11-07 15:55] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`, `docs/implementation-plan.md`)

**Summary:**
Settle the open points left in the M6 plan. The four defaults are confirmed: the default answer is no, `yes` is accepted, declining exits 0, and the list is read again after the answer. Ctrl-C and a closed standard output now join the "no way to answer" case instead of being listed as not handled. The prompt stays on standard output.

**Rationale:**
The project owner answered three questions on 2026-11-07.

- Ctrl-C raises `KeyboardInterrupt`, which `main` does not catch, so the prompt would end in a traceback. It shares the handler with `EOFError` and `RuntimeError` and exits 1, not the usual 130: nothing has changed by then, and one code is easier to state.
- A closed standard output (`>&-`) was checked with Python 3.14.7 and raises `RuntimeError: lost sys.stdout`, so the same handler already covers it. The earlier plan called it "not handled" without having checked what it did.
- The prompt goes to standard output through `input(prompt)`. A redirected output hides it, which is accepted. Rejected: standard error, which moves the tests off the `input` argument and adds a second way to write text next to `_say`.

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete
- Issue: #10

## [2026-11-07 15:40] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`, `docs/implementation-plan.md`)

**Summary:**
Plan M6, the `delete` command. `TODO.md` gets the M6 entry with its steps, tests, and trade-offs. The plan's M6 section gets a "Decided (2026-11-07)" block that answers its "Think about" paragraph: what the prompt prints, what a script gets, and what happens when nothing can answer.

**Rationale:**
The prompt exists to catch a reused ID (D5), so it prints the ID and the name, escaped like every other name. The decisions that go beyond the four plan boxes are the ones a review would otherwise find later:

- `input` raises `EOFError` or `RuntimeError` when there is no terminal, and `main` catches neither, so a script would get a traceback. Both become one error line with exit 1. Checked with Python 3.14.7.
- A prompt waits on a person, so a list read before it can be stale when the save comes. The list is read again after the answer, and only a task equal to the one shown is deleted. Rejected: one read (a concurrent `add` would be lost for as long as the person takes) and a lock held across the prompt.
- Four points are taken as defaults and marked as such in both files: the default answer is no, `yes` is accepted, declining exits 0, and the second read.

Ctrl-C at the prompt and a closed standard output while prompting are named as not handled. Issue #10 is not changed in this commit. Its text is copied from the plan, so it needs the same "Decided" block once the project owner agrees.

**References:**

- `TODO.md`: 2026-11-07 Feature: M6 Delete
- Issue: #10

## [2026-11-07 15:15] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Record the three behavior decisions from the PR #29 review in the plan's M5 section (an update never fails because of the clock, a no-change update writes nothing, the ID is plain digits of 1 or more), and bring the M5 steps in `TODO.md` in line with them.

**Rationale:**
The plan, `TODO.md`, `README.md`, and the issue are meant to agree, and the first version of the M5 notes said the opposite of the code in two places: `updated` came straight from the clock, and a no-change update still printed `Updated`. The PR description is corrected in the same round.
The reasons and the rejected alternatives are in the `TODO.md` entry 'Fix: PR #29 review'.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #29 review, step 9
- Issue: #9 (PR #29)

## [2026-11-07 15:14] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
`update` joins the cases that check a corrupt list file (three kinds of bad content) and a directory in place of the list: exit code 1, one error line that names `tasks.json`, and the path left as it was.

**Rationale:**
Review comment 8 on PR #29. `README.md` lists a corrupt or unreadable task file under exit code 1 for `update`, and nothing pinned it for `update` through `main`.
The code already behaved this way, so these tests passed at once, and the check that they bite is a pair of deliberate breaks: `update` treating a corrupt file as an empty list fails three of them, and treating an unreadable file as an empty list fails the directory case.
The other half of the comment, the timeline refusal through `main`, is moot after the fix for comment 1: `update` can no longer produce a timeline error, so there is nothing to pin. The blank name and the rest of the model's refusals keep their tests.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 8|Issue: #9 (PR #29, review comment 8)

**References:**

- Tests added after the behavior, because the behavior was already there and untested. A test that cannot fail proves nothing, so each was shown to fail against a version of `update` that ignores the error.

## [2026-11-07 15:13] Commit Summary

**Change Type:** Docs

**Scope:** tests (`tests/test_task.py`)

**Summary:**
The comment in the test that gives `Task.update` a date as text now says what the test pins. It used to say the model parses text 'as the CLI passes it'.

**Rationale:**
Review comment 5 on PR #29, the part that is agreed. The command line passes the `datetime` that `_due` has already parsed, so the old comment was wrong, and the test with its `type: ignore` looked like it covered a path no caller uses. What it does cover is that `update` applies the constructor's date rule, so text works as it does for `Task(...)`. The test stays and only the comment changes.
Not done, with the reasons in the reply on the thread: the strings from argparse are not converted to `Priority` and `Status` in `_changes`, and its result is not a `TypedDict`. `add` passes the checked strings the same way, `Task` owns the conversion and a test pins it, and `args` attributes are `Any`, so the `TypedDict` would check the keys and little else.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 7|Issue: #9 (PR #29, review comment 5)

**References:**

- A comment change, so no test was written first.

## [2026-11-07 15:12] Commit Summary

**Change Type:** Refactor

**Scope:** cli (`src/task_tracker/cli.py`)

**Summary:**
`add` and `update` now share one list of priority choices (`_PRIORITIES`) and one `--due` definition (`_DUE_OPTION`: the converter, the metavar, and the help text). No behavior change.

**Rationale:**
Review comment 7 on PR #29, the part that is agreed. `update` copied `--priority` and `--due` from `add` word for word, so a change to the accepted format needed two edits. The help output of both commands is the same before and after, and the 329 tests pass unchanged. Two deliberate breaks (the converter dropped from the shared `--due`, `LOW` dropped from the shared choices) each fail tests.
Not done, with the reasons in the reply on the thread: the text of the 'nothing to update' message is not built from the parser, the test keeps its own copy of it, and `_settle_date_completed` is not merged with `_fill_in_defaults`, because after the comment 1 fix they apply different rules.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 6|Issue: #9 (PR #29, review comment 7)

**References:**

- A refactor with the tests as the safety net, so no new test was written first. The shared pieces are a list and a mapping, not a helper function, because a function that takes a parser or a mutually exclusive group would need argparse's private group type in its signature.

## [2026-11-07 15:11] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Every argument of `update` now has help text: the `ID`, `--name`, `--priority`, `--status`, and `--clear-due` (`--due` already had it). A test reads the `update --help` output for each argument.

**Rationale:**
Review comment 6 on PR #29. `task-tracker update -h` listed `--clear-due, -C` with no description, so the one option whose meaning is not obvious was explained only in `README.md`. The omission looked accidental, since `--due` had help text.
Five of the six cases failed first, and all pass now. Two deliberate breaks (the `--clear-due` text removed, the text of `--status` given to `--priority`) each fail a test. The test reads an argument's row with the lines indented under it, because argparse moves the text of a long option such as `--priority {CRITICAL,...}` to the next line.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 5|Issue: #9 (PR #29, review comment 6)

**References:**

- The help for `--priority` and `--name` is short on purpose (`new priority`, `new name`): the choices are already printed in the usage line. `add` has the same gap for its own options and is not changed here, because the comment is about `update`.

## [2026-11-07 15:09] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`, `README.md`)

**Summary:**
The `ID` of `update` is read by a new `_task_id` converter: ASCII digits and 1 or more. `+1`, `0_1`, an ID with spaces around it, non-ASCII digits, `0`, and `-1` now exit 2 with `expected a whole number of 1 or more`, and the tests cover each.

**Rationale:**
Review comment 3 on PR #29. `type=int` accepted forms that `README.md` does not call whole numbers (`+1`, `0_1`, a padded ID, the Arabic-Indic digit one), so `update 0_1 -n x` changed task 1. `0` and `-1` reached the lookup and exited 1, although an ID below 1 can never exist (`Task` refuses it) and is a bad value like `1.5`.
The reviewer's suggestion is used: a small `type=` function that raises `ArgumentTypeError`, the same pattern as `_due`, so the rule has one home. `delete` in M6 can reuse it.
Six new cases failed first because the command accepted them, and the two old cases failed on the changed message. Three deliberate breaks (back to `int`, no ASCII check, no lower bound) each fail a test.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 4|Issue: #9 (PR #29, review comment 3)

**References:**

- The ASCII check is what rejects `0_1`, a padded ID, a sign, and non-ASCII digits (`isdecimal` alone accepts the last). The lower bound is what rejects `0`. `-1` fails `isdecimal` on its own.

## [2026-11-07 15:08] Commit Summary

**Change Type:** Fix

**Scope:** task, cli (`src/task_tracker/task.py`, `src/task_tracker/cli.py`, `tests/`)

**Summary:**
`Task.update` now returns whether it changed anything. When it did not, `update` leaves the file alone and prints `No change to task N: NAME` (exit code 0) in place of `Updated task N: NAME`. `README.md` says so.

**Rationale:**
Review comment 2 on PR #29. `README.md` promised that giving a task the values it already has "changes nothing", but the command saved anyway: a hand-formatted list was rewritten in the standard layout and the line still said `Updated`. A no-change update also opened the lost-write window of #27 for no reason.
The old test could not see this, because it started from a file `save` had written and a rewrite gives the same bytes. It now starts from a file with a four-space indent. It failed first on the output line, and the model tests on `None` where a bool was expected. Three deliberate breaks (always report a change, always save, save only when nothing changed) each fail tests.
Rejected: only changing the sentence in `README.md`, which would keep the rewrite and the misleading line.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 3|Issue: #9 (PR #29, review comment 2)

**References:**

- The model already compared a snapshot before and after to decide whether to move `updated`, but kept the answer to itself. Returning it lets the caller skip the write.

## [2026-11-07 15:06] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`, `tests/test_cli.py`)

**Summary:**
`Task.update` no longer fails when the clock is behind the task's stored times. `updated` becomes the later of the clock and the stored `updated`, and a date completed set by reaching DONE becomes the later of the clock and `stop`. The model test that expected a refusal is replaced by three that expect the update to work, and one command-level test covers rename and DONE.
`README.md` and the `TODO.md` risk notes are corrected.

**Rationale:**
Review comment 1 on PR #29. Naive local time (D6) can move back between two commands, so a task created under one time zone could not be updated under another: every update failed with `updated must not be before created` until the clock caught up. The reviewer's fix is used as it was suggested.
Five tests failed first with the reviewer's messages and with `updated` moving backwards. Three deliberate breaks (`updated` back to the clock, date completed back to the clock, the floor of `updated` taken from `created`) each fail at least one test.
Rejected: keeping the strict rule and only naming the cause in the message, because no option can repair the task and the user must wait for the clock.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 2|Issue: #9 (PR #29, review comment 1)

**References:**

- Step 1 stamped `updated` and the new date completed straight from the clock, then checked the timeline. When the clock was behind `created` or `stop`, the check refused the whole update. Taking the later of the two values keeps the timeline true by construction, so the check can no longer fail for this reason.

## [2026-11-07 15:05] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
The test that moves a DONE task back to TO_DO or IN_PROGRESS now runs with the fixed clock and checks that `updated` is the clock reading.

**Rationale:**
Review comment 4 on PR #29: the test read the real clock through `Task.update`, so it passed only because the wall clock is later than the stored dates, and it did not check `updated` at all. Every other state-changing `update` test already uses `fixed_clock`.
It failed first on the new assertion, with the real time where the fixed clock reading should be, and passes with the fixture.

**Bugfix Context:**
`TODO.md`: 2026-11-07 Fix: PR #29 review, step 1|Issue: #9 (PR #29, review comment 4)

**References:**

- Without the fixture the test depended on the date it was run, which the project's rule for deterministic tests forbids. It never failed, which is why it went unnoticed.

## [2026-11-07 15:04] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Plan the review fixes for PR #29 (M5, `update`): a new `TODO.md` entry, "Fix: PR #29 review", with the order of the commits, the tests, and the trade-offs. No code changes.

**Rationale:**
The eight inline comments were each checked before any change: six were reproduced with the command in a scratch directory (a time zone change that blocks every update, a no-op update that rewrites the file, an ID such as `0_1` that is accepted) and two were confirmed from the source and the tests.
Six are to be fixed. Two are fixed in part and answered with a reason, so their threads stay open for the reviewer.
The plan also corrects a claim from step 1, that no command can make a task with a future `created`, `start`, or `stop`: `add` followed by a time zone change does.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #29 review
- Issue: #9 (PR #29, review comments 1 to 8)

## [2026-11-07 14:44] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`, `CLAUDE.md`, `docs/implementation-plan.md`, `TODO.md`)

**Summary:**
Document the `update` command now that it exists. `README.md` gets the `update` example and bullet, exit codes 1 and 2 for the new cases, and a lost-write note that covers `update`. The "stores the task before it prints" bullet now names `update` too. `CLAUDE.md` says features 3 to 6 exist. The six M5 boxes in the plan are ticked, and `TODO.md` records the one edge case found in step 1.

**Rationale:**
The `README.md` and `CLAUDE.md` text was drafted while the code was written, and held back until the command could be checked against it. Before this commit I ran `update` in a scratch directory and compared each claim:
the output line, exit 2 for an unknown status, an ID that is not a whole number and `--due` with `--clear-due`, exit 1 with the file untouched for no task, no option and a blank name, and date completed set and cleared on the status change.
The edge case is a task whose `start` or `stop` is later than the clock: marking it `DONE` is refused. No command can make such a task, so it is recorded as accepted and not handled.
Issue #9 is not changed here. In M4 the boxes were ticked once CI was green, so that waits for the pull request.

**References:**

- `TODO.md`: 2026-11-07 Feature: M5 Update, step 4
- Issue: #9

## [2026-11-07 14:41] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`update` now refuses two commands with a one-line error and exit code 1: one that names no option, and one whose ID matches no task. Both are checked before the file is written, and in the no-option case before it is read. The file is left byte for byte unchanged, and a missing file is not created.
The module-level pylint suppression for `too-many-lines` is now needed, with the reason beside it.

**Rationale:**
A command that gives no change would otherwise exit 0 and print a success line, which hides a forgotten or mistyped flag, as decided for M5. An unknown ID is refused rather than skipped, so the user sees that nothing changed.
The checks use `ValueError`, which `main` already turns into one error line and exit code 1, so the error path is not duplicated.

**References:**

- `TODO.md`: 2026-11-07 Feature: M5 Update, step 3
- Issue: #9

## [2026-11-07 14:39] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`update ID` changes a stored task's name, priority, status, or due date. It passes only the options that were given to `Task.update`, and `--due` and `--clear-due` are mutually exclusive. Every other task is saved unchanged.
The test helper `_done` now builds on a new `_stored` helper, so the record is written in one place.
Refusing an update with no change and refusing an unknown ID come in the next step.

**Rationale:**
The command only parses options and saves, and the rule stays in `Task.update`, as decided for M5. Options default to `None`, so a missing option is told apart from one given with its default value. `due` is left out of the keyword arguments unless a flag is given, because `None` means "clear the date" to `Task.update`.
The short forms are checked against the long forms byte for byte, so a mistake in a short form cannot pass unnoticed.

**References:**

- `TODO.md`: 2026-11-07 Feature: M5 Update, step 2
- Issue: #9

## [2026-11-07 14:33] Commit Summary

**Change Type:** Feature

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`)

**Summary:**
`Task.update` changes an existing task's name, priority, status, and due date. Its arguments are keyword-only. `None` means "not given" for name, priority, and status, while `due` uses the existing `_UNSET` marker so that `None` can clear the date.
The method reads the clock once, moves `updated` only when a field changes, and sets or clears date completed with the status (Q4). When the result breaks a rule, every field is restored from a snapshot before the error is raised.
Passing `id`, `created`, `updated`, `description`, `start`, or `stop` raises `TypeError`, because the method has no such parameter.

**Rationale:**
The update rule sits beside `_now` and `_validate`, so the command added in a later step stays thin and the model can be tested without argparse. The rejected alternative, the command assigning fields itself, would need the clock and the validation copied or moved out of the model. `TODO.md` records it.
A snapshot with restore is used instead of checking the change first, because the timeline rules already check a whole task. Running them on the changed task and undoing on failure reuses every rule without a second copy.

**References:**

- `TODO.md`: 2026-11-07 Feature: M5 Update, step 1
- Issue: #9

## [2026-11-07 14:26] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`, `docs/implementation-plan.md`, `README.md`)

**Summary:**
Plan M5, the `update` command. `TODO.md` gets the M5 entry with its steps, tests, and trade-offs. The plan's M5 section gets a "Decided (2026-11-07)" block, and Q3 is closed: `update` does not set `start` and `stop`. The `README.md` options table gets `--clear-due` (`-C`), and its columns are re-aligned for the wider cell.

**Rationale:**
The M5 "Think about" paragraph asked four questions, and the project owner answered each in turn: the task owns the update rule (`Task.update`), a due date is cleared with `--clear-due`, `update` with no option is an error, and `start` and `stop` stay out of reach. Recording them before any code means the red tests have nothing left to decide.
Four smaller points were taken as defaults and are marked as such in both files: the `-C` short form, no change to `updated` when a value is the same, `DONE` to `DONE` keeping its date completed, and `description` not being settable.
Rejected alternatives are written next to each decision in `TODO.md` and the plan.
Issue #9 is not changed in this commit. Its text is copied from the plan, so it needs the same "Decided" block and is the next step once the project owner agrees.

**References:**

- `TODO.md`: 2026-11-07 Feature: M5 Update
- Issue: #9

## [2026-11-07 13:53] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
The sort key for the done tasks now raises a `ValueError` for a DONE task without a date completed, where it used an `assert`. `main` turns that into the usual one-line error on standard error and exit code 1. Before, the same task gave a traceback, and under `python -O` it sorted without any error.

**Rationale:**
Review comment 2 on PR #28 showed that the assert is removed by `python -O`, and that the comparison then fails only when a broken record is mixed with a good one. The project owner chose the exception over the assert, because it is the same in every mode and reuses the error path `main` already has.
The new test hands the command a DONE task with no date completed, which `load` refuses to build, so the task is passed in directly. It failed first with a bare `AssertionError` from `main`, and a version of the branch that returns instead of raising fails it. I also ran the command under `python -O` with the asserts confirmed stripped: one error line and exit code 1.
The cost is a branch that real data cannot reach, which the new test covers.

**Bugfix Context:**
Not reachable with stored data today, because `Task` and `load` refuse such a record. The change makes the sort say so by itself in every mode, if that rule is ever broken.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 8
- Issue: #8 (PR #28, review comment 2)

## [2026-11-07 13:44] Commit Summary

**Change Type:** Docs

**Scope:** docs (`SUMMARY.md`)

**Summary:**
Corrected two sentences in the 13:03 entry that the review of PR #28 made false. One said `README.md` needed no edit; it now says that was the first judgment and that the Commands section was updated. The other said issue #8 still had its boxes unticked; it now says the issue was edited after that commit. No code changes.
Issue #8 itself was updated on GitHub: its five extra acceptance items and the three decisions from the plan are now in it, all ticked, so it no longer closes without them.

**Rationale:**
Review comment 6 on PR #28. The project `CLAUDE.md` says to update the plan, the matching issue, and `README.md` together, and step 4 of the M4 entry promised the issue would carry the extra items and the decisions. Only the two original boxes had been ticked, and the `Closes #8` in the pull request would have closed the issue without the rest.
The issue text was built from the plan by script, not typed again, so the two cannot differ; a diff of the old and new body showed only the added items, the new section, and one sentence in the footer.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 7
- Issue: #8 (PR #28, review comment 6)

## [2026-11-07 13:43] Commit Summary

**Change Type:** Docs

**Scope:** docs (`README.md`)

**Summary:**
The Commands section of `README.md` now documents `list --all`. The example block gains `uv run task-tracker list --all`.
A new bullet says what the flag shows (every task, the current ones first in the usual order, then the done ones by date completed and ID), that the lines are unchanged so the date completed is not shown, and the `No tasks in <path>` message.
It also says that plain `list` keeps its own message, including when every task is done.

**Rationale:**
The review of PR #28 pointed out that this section is where a user learns the commands, and it never mentioned the flag. The feature list and the options table already named `--all`, which is why the PR description said no change was needed; that was wrong, because they are a spec and a table, not usage. The description is corrected too.
The earlier `SUMMARY.md` entry for the plan and `CLAUDE.md` has the same wrong sentence; it is corrected in the commit for the review comment about issue #8.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 6
- Issue: #8 (PR #28, PR-level comment)

## [2026-11-07 13:42] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`, `SUMMARY.md`)

**Summary:**
Corrected what the documents said about the done-order `assert` under `python -O`. They said the comparison "fails with a `TypeError`, still loudly". It does only when a broken record is compared with a good one; one such record, or several, sort without an error. The `TODO.md` decision and the earlier `SUMMARY.md` entry now say so. No code changes.

**Rationale:**
Review comment 2 on PR #28 reported this, and it was reproduced first: under `python -O` one done task without a date completed sorted as `[1]`, two as `[1, 2]`, and only a mix with a good record raised.
The assert stays. The guarantee is `Task._validate`, which runs on construction and in `restore`, so a broken record cannot reach the sort; the assert only tells the type checker. The decision was made with the wrong sentence among its pros and cons, so the project owner is asked to confirm it.
Superseded: the review of PR #28 replaced the `assert` with a `ValueError` (see the 13:53 entry).
The other part of the comment, a typed accessor on `Task`, is not done: there is one reader today, and the reasons are in the `TODO.md` entry for this review.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 5
- Issue: #8 (PR #28, review comment 2)

## [2026-11-07 13:41] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
Added a test that the done tasks of `list --all` sort on the full date completed, not on the day. Two tasks are completed on 2026-10-05, the lower ID at 17:00 and the higher at 09:00, and the 09:00 one must come first.

**Rationale:**
Review comment 5 on PR #28. Every done task in the earlier tests was completed at midnight, so a key cut to the day passed the whole suite, and the ID tie-break hid the difference. The new case gives the two keys different answers.
The test passes against the current code, so it was checked with a deliberate break instead of a red run: with the key cut to the day, this test fails and the other 263 still pass, which confirms the gap the comment described.

**Bugfix Context:**
Not a bug in the code: the key was already the full timestamp. The gap was in the tests, which could not tell the two apart.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 4
- Issue: #8 (PR #28, review comment 5)

## [2026-11-07 13:40] Commit Summary

**Change Type:** Refactor

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
The `_done` test helper no longer spells out the eleven stored fields. It starts from `asdict(Task(task_id, name))` and overrides the seven values a done task changes (the four stamps, `due`, `status`, and `date_completed`).

**Rationale:**
Review comment 4 on PR #28 said `_done` was a third copy of the stored record, so a new `Task` field would need a change in three test modules. This removes the copy from the new code: the field list now comes from the dataclass. As a check, a throwaway field added to `Task` leaves the eight list tests passing.
The comment suggested moving `stored()` from `test_task.py` into a shared module. Not done: that call cannot build these records, because `stored()` has `created` on 2026-10-10 at 09:00, after the dates completed here, and `restore` refuses an earlier date completed. Making it work overrides nine of eleven fields, and moving it edits M1 tests outside this diff.
The copies in `test_task.py` and `test_storage.py` remain.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 3
- Issue: #8 (PR #28, review comment 4)

## [2026-11-07 13:39] Commit Summary

**Change Type:** Refactor

**Scope:** cli (`src/task_tracker/cli.py`)

**Summary:**
`_list` builds the empty-list message once, from a word that is `tasks` under `--all` and `current tasks` otherwise. Before, it tested the flag a second time and returned from two near-identical branches. The text printed is the same in every case.

**Rationale:**
Review comment 3 on PR #28. One `if` fewer, and the wording choice now sits next to the comment that explains it. No test was added because no behavior changed: the five tests that pin the two messages are the safety net, and swapping the two words makes all five fail.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 2
- Issue: #8 (PR #28, review comment 3)

## [2026-11-07 13:38] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
The help for `list` in `task-tracker --help` now reads `list the current tasks (all tasks with --all)`. It used to say only `list the current tasks`, which told a reader the command could never show finished work.

**Rationale:**
Review comment 1 on PR #28. The new test reads the top-level help and checks that the `list` line names `--all`; it failed on the old text before the change. It sets a wide terminal, so argparse does not wrap the line being checked.

**Bugfix Context:**
The M4 change added the flag and its own help but left the one-line description that the top-level help prints. That line is the first thing a user reads, so it was out of date as soon as the flag existed.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review, step 1
- Issue: #8 (PR #28, review comment 1)

## [2026-11-07 13:37] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Added the plan for answering the review of PR #28 to `TODO.md`: seven steps, one per comment, the tests each needs, and what is declined and why. No code changes.

**Rationale:**
The project rules ask for the plan before any fix. Each claim in the review was checked first, and one of them showed that a sentence I wrote earlier was wrong: under `python -O` the done-order assert does not always fail loudly. The plan records that, keeps the assert, and asks the project owner to confirm the choice with the corrected facts.
Superseded: the review of PR #28 replaced the `assert` with a `ValueError` (see the 13:53 entry).
Two comments are answered in part with a reason (an accessor on `Task`, and a shared module for the stored record), so their threads stay open for the reviewer.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #28 review
- Issue: #8 (PR #28)

## [2026-11-07 13:22] Commit Summary

**Change Type:** Docs

**Scope:** docs (`SUMMARY.md`)

**Summary:**
Reworded one sentence in the rationale of the previous `SUMMARY.md` entry. It said who wrote the M4 code; it now says only that the sentence removed from `TODO.md` named who would write the code, which is not how M4 was worked. No code changes.

**Rationale:**
The project rules ask for no statements about how the code was generated in the documentation. The previous entry was already pushed, so the wording is corrected in a new commit instead of rewriting history.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 13:21] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Removed the sentence "You write the tests and the code" from the objective of the M4 entry in `TODO.md`. The entry now says only that it fixes the order and the traps. No code changes.

**Rationale:**
The sentence named who would write the code, which is not how M4 was worked, so it was no longer true. The same sentence in the M2 entry is left as it is: it records how that milestone was worked.
Before this commit the unpushed history was also tidied: the one-word wording fix to the first M4 `SUMMARY.md` entry was folded into the commit it belonged to, so the branch has three code commits as the plan describes. The final tree was identical before and after.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 13:03] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `CLAUDE.md`, `SUMMARY.md`)

**Summary:**
Closed out M4 in the docs. The M4 section of the plan gains five Given/When/Then items (done tasks with one date completed, a done task due first, only done tasks, the empty-list wording, a corrupt file), a record of the three decisions, and all seven boxes ticked.
The project `CLAUDE.md` now says that features 3, 4, and 5 exist and that M1 to M4 are built. One earlier `SUMMARY.md` entry said the options table lives in `TODO.md`; it is in `README.md`, and the entry is corrected.

**Rationale:**
The project `CLAUDE.md` says to update the plan, the matching issue, and `README.md` together when a milestone changes. `README.md` was first judged to need no edit, because feature 4 and the options table already name the flag. The review of PR #28 showed that the Commands section did need it, and it was added there.
Each box was ticked only after a passing test covered it. The full suite (262 tests), coverage (97%, with the output-failure branches counted in child processes as before), and the linters CI runs on Python and Markdown were run on this commit's parent, and `list --all` was run by hand in a scratch directory.
Issue #8 was edited on GitHub after this commit: its two boxes were ticked, and the review of PR #28 added the five extra items and the three decisions.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all, step 4
- Issue: #8

## [2026-11-07 12:59] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`list --all` over a missing or empty file now says `No tasks in <path>`, and exits 0. Plain `list` still says `No current tasks in <path>`, including when the file holds only done tasks.
The corrupt-file test also runs `list --all`, and it already passed, because the load error comes before any wording is chosen.

**Rationale:**
`No current tasks` is wrong under `--all`, where done tasks count too. A hint at `--all` in the plain message was rejected, because the spec never asked for it.
The wording is chosen after the lines are built, so the message check stays in one place.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 12:58] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Added `-a` as the short form of `list --all`. The parametrized test runs both forms and checks that each gives the same order.

**Rationale:**
The short form follows the options table in `README.md` and shares the `dest` of the long form, so the two cannot drift apart.
The test is parametrized on the flag rather than repeated, so a new alias needs one entry in the list.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 12:57] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Added `list --all`, whose flag is stored as `include_done`. It lists the current tasks in the M3 order, then the done tasks by date completed, then ID. Plain `list` is unchanged.
The existing plain-list ordering test now builds its file with the same shared helper as the new tests, which keeps the copypaste check (threshold 0) at zero clones.

**Rationale:**
The done half sorts by `(date_completed, id)`, not by the M3 key, as `TODO.md` decides. Most done tasks have no due date, and the ID settles ties the same way it does in M3.
The `assert` tells pyright that a DONE task has a date completed. It adds no branch to cover.
Superseded: the review of PR #28 replaced the `assert` with a `ValueError` (see the 13:53 entry).
The done tests build their tasks with `Task.restore`, because the constructor cannot store a past completion date.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 12:52] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Recorded the four M4 decisions in the `TODO.md` entry, changing "proposed" to "decided" and adding what was rejected.
The done tasks sort by date completed, then ID. The sort key states the "a done task has a date completed" invariant with an `assert` for the type checker.
Superseded: the review of PR #28 replaced the `assert` with a `ValueError` (see the 13:53 entry).
The list line stays as M3 made it. `list --all` over an empty file says `No tasks in <path>`. The flag's value is named `include_done`. No code changes.

**Rationale:**
The project owner went through each proposal and chose the recommended option every time.
The one that got discussion was the order of the done tasks: sorting them by the M3 key (due date, priority, ID) would reuse one key for both halves, but it contradicts `README.md` feature 4 and issue #8.
Most done tasks also have no due date, so they would fall to priority and ID, which say nothing about finished work.
The `assert` was chosen over a `datetime.max` stand-in (dead code that would sort a broken record last) and a `ValueError` (an unreachable branch that needs a forged task to cover). `python -O` strips it, and a broken record would then sort without an error unless it is compared with a good one (corrected in the review of PR #28). It cannot reach the sort, because `Task` checks the date on every load.
Superseded: the review of PR #28 replaced the `assert` with a `ValueError` (see the 13:53 entry).
The plan, `README.md`, and issue #8 are not edited here: no decision changed their text, because the spec's order stands. They are updated in step 4 of the entry, with the ticked boxes.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 12:36] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Added the plan for M4, `list --all`, to `TODO.md`: five steps (the `--all` flag, the `-a` short flag, the empty-list wording, the docs, the local checks), the tests to write, and the risks. No code changes.

**Rationale:**
The project rules ask for the plan before any code, on a branch cut from `develop`. M3 merged as PR #26, so the branch starts from a `develop` that has `add` and `list`.
The entry fixes the traps before the tests are written. The done tasks must be built with `Task.restore`, because the constructor rejects a date completed before `created`. The done half must sort by date completed, then ID, and a test with the later ID completed first would fail an ID order.
The sort key, the list line, the empty-list wording, and the name of the flag's destination are proposed with reasons and left open for the project owner to veto, as in the M2 and M3 entries.

**References:**

- `TODO.md`: 2026-11-07 Feature: M4 List all
- Issue: #8

## [2026-11-07 12:11] Commit Summary

**Change Type:** Refactor

**Scope:** task and storage (`src/task_tracker/task.py`, `src/task_tracker/storage.py`, `tests/test_task.py`, `tests/test_storage.py`)

**Summary:**
`Task.restore` takes one argument, the record, instead of the record spread into keyword arguments. `Task.restore(record)` replaces `Task.restore(**record)`, so no stored key can collide with a parameter of the method, whichever parameters it gains later. The positional-only `cls` from the earlier fix and the paragraph that explained it are gone.
The behavior seen from outside is the same: a key named `cls` or `record` is still reported as an unknown field.

**Rationale:**
Review comment 7 said that the `cls` collision was a symptom of spreading an untrusted dict into `**kwargs`, and that taking the mapping removes the class of bug and the special case. I first planned to answer it with a reason, and one of the reasons was wrong. I wrote that a mapping would reverse an earlier decision;
the commit I had in mind is about the dataclass fields, and the one that made `restore` take `**record` (`db9f244`, from the review of PR #25) did it so that the dataclass is the single list of fields. A mapping keeps that, and its stated cost (no field list in the signature) is the same in both shapes.
With that reason gone, what is left against the change is 20 mechanical edits to call sites, which pytest and the type checker verify, so I made the change. The plan in `TODO.md` is corrected to say so.
The tests were converted first and seen failing (48 failures and 8 setup errors, all `takes 1 positional argument`). The `cls` test now also covers a key named `record`, the parameter's own name. The test that checks that positional fields are refused is renamed to say what it protects: a record is one argument, so the fields cannot be swapped.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 10
- Issue: #7 (PR #26, review comment 7)

## [2026-11-07 12:07] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `README.md`, `TODO.md`)

**Summary:**
Recorded what the second round of review changed. The plan gains two checked Given/When/Then items (the error line and the bidirectional controls; a failed write and a closed standard output) and two "Decided" bullets, and its escaping bullet now lists the bidirectional controls and says the error line is escaped too.
`README.md` says that text-direction controls are escaped and that a closed standard output ends with exit code 0.
The statements that called the `--due` converter a repetition of the naive-time rule ("two places to change") are corrected in `TODO.md` and the plan: it calls `as_naive_datetime` now.

**Rationale:**
The project `CLAUDE.md` says to update the plan and `README.md` together with a decision. Three decisions changed in this round: the `--due` rule lives in one place, the escaped set grew, and a closed output stream is a success. The earlier text for the first would have misled the next reader into thinking the cost was still there.
The `TODO.md` entry for the first review round is kept as the record of what was decided then, with a sentence that says what changed after it, instead of being rewritten.
Issue #7 does not need an edit: its acceptance criteria are the original nine and are all ticked.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 9
- Issue: #7 (PR #26)

## [2026-11-07 12:06] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
The checked plan item for a name that UTF-8 cannot hold now has a test at the command line. The test that covered a blank name is parametrized with a second case: `main(["add", "bad \udcff"])` exits 1, prints one line saying `name must be valid UTF-8 text`, and writes no file. No production code changes.

**Rationale:**
Review comment 8 noticed that the M3 plan ticks "`add` with a name that UTF-8 cannot hold exits 1 and writes nothing", while the only tests for it were in `test_task.py` and `test_storage.py`, which check the model and the file. Nothing proved that the command line turns the model's refusal into the promised result.
The behavior was already right, as the comment said, so the test passes as soon as it is written. It was checked the other way round instead: removing the name check from `Task` makes this case fail first, ahead of the model and storage tests.
The blank-name test was widened instead of copied, so the two cases share one body. Its name now says what both have in common: a name that cannot be kept.

**Bugfix Context:**
Review comment 8 on PR #26. A gap in the tests, not a defect in the program.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 8
- Issue: #7 (PR #26, review comment 8)

## [2026-11-07 12:05] Commit Summary

**Change Type:** Refactor

**Scope:** cli and task (`src/task_tracker/cli.py`, `src/task_tracker/task.py`)

**Summary:**
`--due` is read with the rule `Task` already applies to every date, instead of a second copy of it. `_due` calls `as_naive_datetime` (the helper in `task.py`, no longer private) and only translates its `ValueError` into the `ArgumentTypeError` that gives the message and exit code 2. Behavior is unchanged: the same 249 tests pass.

**Rationale:**
Review comment 6 found that `_due` re-implemented what `_as_naive_datetime` does: parse an ISO 8601 text, reject a UTC offset, drop the microseconds. I had recorded the repetition as a known cost ("two places to change if D6 changes"), and the review showed the cost was avoidable. The helper only needed a public name; its docstring now says why. Rejected:
leaving the copy because the code is only three lines, since a rule repeated in two files drifts the first time D6 changes.
The test for the refactor is the existing set, which pins the behavior from outside: four bad values, a UTC offset, a timed value, and the short flags. Two deliberate breaks show it still has teeth: a rule that accepts offsets is caught by the CLI tests and the model tests, and a `_due` that does not translate the error is caught by the message checks.
The docs that call the repetition a cost (`TODO.md`, the plan) are corrected in the docs commit that closes this round.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 7
- Issue: #7 (PR #26, review comment 6)

## [2026-11-07 12:04] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
The bidirectional formatting characters are escaped on output: the marks U+061C, U+200E and U+200F, the embeddings and overrides U+202A to U+202E, and the isolates U+2066 to U+2069. A name such as `invoice<U+202E>gpj.exe`, which a terminal that applies the Unicode bidirectional algorithm would draw as `invoiceexe.jpg`, now lists as `invoice‮gpj.exe`.
The zero-width joiner and the wide space are still printed as text, so an emoji sequence and a name in another language are unchanged.

**Rationale:**
Review comment 4 pointed out that a name from a shared file could reorder how the rest of its line is displayed, which is the same threat the escaping answers for control characters. The comment listed 11 characters. I enumerated the Unicode data to check the set and added a twelfth, U+061C ARABIC LETTER MARK, the third bidirectional mark beside U+200E and U+200F:
leaving it out would have made the rule cover two of the three marks, for no reason. U+070F, also a format character with a right-to-left class, is not a bidirectional control and is left as text.
The tests were written first. Eleven failed: four names through `list` and seven range edges. The cases next to each range (including U+200D, U+2010, U+061B and U+061D) pass before and after, and keep the rule from growing.
Seven deliberate changes to the new ranges (dropping U+061C, shortening or shifting each of the two ranges, shortening the marks, and widening a range over U+200D) are each caught.
The comment above the pattern now says why each group is escaped. Its claim of "about 20 times faster" was corrected to "an order of magnitude", which is what I measured (16.7 ms to 1.3 ms for 3000 lines).

**Bugfix Context:**
Review comment 4 on PR #26. Root cause: the escaped set was chosen as the Unicode categories `Cc`, `Zl` and `Zp`, and the bidirectional controls are in `Cf`, a category that also holds the joiner that must stay text.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 6
- Issue: #7 (PR #26, review comment 4)

## [2026-11-07 12:03] Commit Summary

**Change Type:** Refactor

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`_printable` finds the characters to escape with one compiled regular expression, `[\x00-\x1f\x7f-\x9f  ]`, instead of calling `unicodedata.category` on every character. The output is the same. Escaping 3000 typical lines went from 16.7 ms to 1.3 ms. The `unicodedata` import, the `_UNSAFE_CATEGORIES` set, and the per-character `map` are gone.

**Rationale:**
Review comment 5 observed that `Cc`, `Zl` and `Zp` are exactly those ranges. I checked it over all 1,114,112 code points before agreeing: 0 mismatches. A scan of the whole line is faster and shorter than a Python call per character, and the code says in one place what is escaped.
Because a refactor has to leave behavior alone, the safety net came first: two parametrized tests pin the first and last character of each escaped range (NUL, unit separator, DEL, the first and last C1 control, and the two separators) and the character next to each range that must stay text (space, `~`, no-break space, hyphenation point, narrow no-break space).
They passed on the old code, then on the new. Four deliberate breaks of a range edge are each caught. A fifth, which escapes the space, passes, and that is expected: `unicode_escape` leaves a printable space as it is, so the change cannot be seen.
The comment above the pattern records the equivalence with the three categories and the measured gain, so the next reader does not have to rediscover them.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 5
- Issue: #7 (PR #26, review comment 5)

## [2026-11-07 12:01] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
The error line is escaped like the rest of the output. A stored record with the key `key<ESC>[2J<newline>second line` used to make `task-tracker list` write the escape sequence to the terminal and a second line to standard error; the error now reads `unknown field(s): key\x1b[2J\nsecond line` on one line.
All text the program writes goes through one function, `_say(line, stream)`, which escapes it for that stream.
One related case is fixed with it: when standard error is closed, `print(file=None)` wrote the error to standard output, into the output another program may be reading. `_say` now writes nothing to a closed stream.

**Rationale:**
The output escaping answered a real threat (`README.md` expects lists to be shared), but only for standard output. `Task.restore` builds `unknown field(s)` from the record's own keys, so the other sink had the same exposure and broke the "one line" promise for errors as well.
The review offered two shapes, and the one chosen is a small `_say(text, stream)` for both streams, not a second call to `_printable` at each print, so a future print cannot forget it. `_printable` now takes the stream, because the encoding to fall back from belongs to the stream it is written to.
Two tests were written first and seen failing: the hostile key (two lines, raw escape) and the closed standard error (the message appeared on standard output). Three deliberate breaks of the code: the closed-stream guard is caught, and an unescaped error in `main` is caught.
An unescaped "cannot write the output" line is not caught, because that message holds only the operating system's error text and has nothing to escape; it uses `_say` anyway so that the program has one way of writing.

**Bugfix Context:**
Review comment 3 on PR #26. Root cause: escaping was applied by one caller of `print` and not by the other.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 4
- Issue: #7 (PR #26, review comment 3)

## [2026-11-07 12:00] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`task-tracker list >&-` and `task-tracker add x >&-`, with descriptor 1 closed, no longer end in an `AttributeError` traceback. They finish with exit code 0 and print nothing, because there is nowhere to print to. For `add` this matters most: the task was saved first and the traceback came after it.

**Rationale:**
When descriptor 1 is closed at start, which happens under cron and some service managers, `sys.stdout` is `None`. `print` treats that as "nowhere to write", but `_printable` read `sys.stdout.encoding` first, and `_show` would have failed on `sys.stdout.flush()` next. The review named the first; the guard at the top of `_show` covers both with one `if sys.stdout is None:
return 0`. The exit code is 0 because the command did its work and a program with no output stream has not failed. Rejected: `getattr(sys.stdout, "encoding", None)` in `_printable` alone, which fixes the first line and leaves the `flush()` failure behind it.
Two tests were written first and seen failing with the traceback, one for each command. They start the real program through `sh` with descriptor 1 closed, and check that standard error is empty, the exit code is 0, and the stored tasks are as expected. Two deliberate breaks of the code are each caught: no guard, and a guard that returns 1.

**Bugfix Context:**
Review comment 2 on PR #26. Root cause: the code assumed `sys.stdout` is always a stream, and Python documents that it can be `None`.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 3
- Issue: #7 (PR #26, review comment 2)

## [2026-11-07 11:58] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
A write failure that is not a broken pipe now ends with exit code 1 and exactly one line on standard error. It used to print `cannot write the output: ...`, then `Exception ignored while flushing sys.stdout`, and exit with 120. A full disk, a file-size limit, or an I/O error behaved the same way.
Both failure branches of `_show` now call one helper, `_discard_stdout`, and the helper closes the extra descriptor it opens, which the first version leaked.

**Rationale:**
A failed write leaves its bytes in the buffer, and Python flushes stdout once more at exit. Only the broken-pipe branch pointed stdout at devnull, so the other branch let that second flush fail and turn the exit code into 120. This breaks the promise in `README.md` of one error line and a plain exit code 1. The fix is the one the review described:
a single helper used by both branches, with the descriptor closed after `dup2`.
The old test for this case replaced `sys.stdout` with a fake object, so there was no buffer for Python to flush again, which is why it never saw the bug.
The new tests run the real command in a child process with standard output on a read-only descriptor, which fails every write with EBADF, and they check the exit code and the error lines for `list` and for `add` (the task stays saved).
The leaked descriptor cannot be seen from outside a process that is about to exit, so two small in-process tests pin the helper itself: later writes go to devnull, and no extra descriptor stays open. A deliberate break that removed the `close` first survived, which is why that test exists.
The fake `sys.stdout` for those tests is installed inside the test body, because pytest's capture puts its own stream back when the body starts; my first version set it in a fixture and redirected the capture file instead.

**Bugfix Context:**
Review comment 1 on PR #26. Root cause: the cleanup for a failed flush existed in one `except` branch and not in the other.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 2
- Issue: #7 (PR #26, review comment 1)

## [2026-11-07 11:55] Commit Summary

**Change Type:** Refactor

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
The helper that runs `task-tracker list` in a child process is now a context manager, `_list_in_a_new_process(folder, stdout)`. It opens the error file, starts the process, yields it, and waits for it when the block ends. This removes the `# pylint: disable=consider-using-with` line, which had no reason beside it. No behavior changes: the same 215 tests pass.

**Rationale:**
Review comment 9 asked for the reason to be written next to the suppression, because the project `CLAUDE.md` requires one for every pylint suppression and forbids loosening the rules. The reason was that the caller closed the process, which is a promise made across two functions. A context manager makes the promise structural:
`Popen` is entered with `with`, so the check has nothing to flag and nothing to suppress. A reason comment would have kept the suppression and the need to remember it.
The caller no longer has to remember `os.close` order and `with child` either; it uses the child inside one block. The refactor was checked against the two pipe tests with deliberate breaks of the code (no `BrokenPipeError` branch, no flush), and both are still caught.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round, step 1
- Issue: #7 (PR #26, review comment 9)

## [2026-11-07 11:54] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Planned the work that answers nine more inline review comments on PR #26: nine steps, each with its commit subject, the tests that pin it, and the risks. Eight comments are fixed and one (#7) is answered with a reason instead of a code change.

**Rationale:**
The project rule is to plan in `TODO.md` before any code changes. Every claim in the review was reproduced first:
exit 120 after a failed write, the `AttributeError` with a closed standard output (and the task saved before it), an escape sequence and a second line on standard error from a hostile key, the bidirectional controls passing through, and the 16.7 ms against 0.9 ms for the per-character lookup.
Two points go beyond what the comments asked for, and both are recorded as risks: U+061C joins the escaped bidirectional controls, and the closed-output fix also covers `flush()`, which would fail on `None` the same way as `.encoding`.

**References:**

- `TODO.md`: 2026-11-07 Fix: PR #26 review, second round
- Issue: #7 (PR #26)

## [2026-11-01 18:22] Commit Summary

**Change Type:** Fix

**Scope:** tests and docs (`tests/test_cli.py`, `SUMMARY.md`, `TODO.md`)

**Summary:**
CI's `Lint` job failed on the push of the review fixes: codespell 2.4.2 in super-linter read the three letters before the backslash in the escaped form of an accented example word as a misspelling of "calf" (`SUMMARY.md`, `TODO.md`, and `tests/test_cli.py`). The ASCII-output test now uses the name `Zoë ☕`, expecting `Zo\xeb \u2615`, and the two docs describe the escape in words.
No behavior changes.

**Rationale:**
The escape is correct output, but the word was split by the backslash, so a spell checker sees a fragment. Changing the example is cheaper and clearer than adding a codespell ignore word for the whole repository, and the test checks the same thing with any non-ASCII letter.
The unescaped `café` in the other tests is not flagged, because the checker reads `é` as part of the word.
My local checks run ruff, black, isort, flake8, pylint, mypy, markdownlint, textlint, Prettier, and the duplicate-code check at the CI versions, but not codespell, which is why this reached CI. It now has been run locally at 2.4.2 over every tracked file and reports nothing.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review
- Issue: #7 (PR #26, CI)

## [2026-11-01 18:19] Commit Summary

**Change Type:** Fix

**Scope:** repository (`.gitignore`)

**Summary:**
`.gitignore` now ignores `/tasks.json` and `.tasks.json.*.tmp`. Running the example in `README.md`, `uv run task-tracker add ...`, from the repository root writes `tasks.json` there, and a save that is killed leaves a `.tasks.json.<random>.tmp` file behind. Neither was ignored, so a later `git add .` would have committed a personal task list.

**Rationale:**
Review comment 11. The `/tasks.json` pattern is anchored to the repository root, so it does not touch any other file of that name, and `git check-ignore` confirms it: `tasks.json` and a temporary file in any directory are ignored, `tests/tasks.json` is not, and the existing `!.vscode/tasks.json` exception still leaves that file un-ignored.
`README.md` says the temporary pattern belongs in `.gitignore` when the list lives in a repository.
This change also covers a gap the review noted in the commit before it, `0e0d554` (`update .gitignore`, which added `CLAUDE.local.md`): that commit has no `SUMMARY.md` entry. That is recorded here so the log is complete: it ignores `CLAUDE.local.md`, a private per-project instructions file that is not meant to be checked in.
The subject of that commit is not reworded because that would need a force-push.

**Bugfix Context:**
Review comment 11 on PR #26. Root cause: M3 is the first milestone that writes a file named `tasks.json` in the directory it is run from, and nothing ignored it.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 9
- Issue: #7 (PR #26, review comments 8 and 11)

## [2026-11-01 18:18] Commit Summary

**Change Type:** Docs

**Scope:** docs (`CLAUDE.md`)

**Summary:**
The project `CLAUDE.md` now matches the code. "An early scaffold" and "a placeholder `main()` in `__init__.py`" became a description of the first slice: `main()` and the `add` and `list` commands live in `cli.py`, features 3 and 5 exist for the project list only, and the other five are named as not built. A line records the exit-code convention.
The command example is `uv run task-tracker list`, with a note that a command is required, because a bare `task-tracker` now exits 2.

**Rationale:**
Review comment 10: the file is read at the start of every session, so a stale "none of the seven features" sends the next session looking for a placeholder that no longer exists. The global Definition of Done asks for documentation to be updated with the change, and `CLAUDE.md` is documentation.
The exit-code line is the one fact a future change to `main` most needs and cannot guess from the code alone.
The five features not built are listed by name so the file stays true until M4 to M9 change it, and the text says which milestones the code covers instead of counting tests or lines, which would go stale on the next commit.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 9
- Issue: #7 (PR #26, review comment 10)

## [2026-11-01 18:17] Commit Summary

**Change Type:** Docs

**Scope:** docs (`SUMMARY.md`)

**Summary:**
Four M3 entries now carry the minute of the commit that contains them: 14:25 became 14:19 (`feat(cli): add the add command`), 14:26 became 14:21 (`add the list command`), 14:27 became 14:22 (`report errors without a traceback`), and 14:28 became 14:24 (`record the M3 decisions`). The fifth, 14:17, was already right. Only the four headings changed.

**Rationale:**
Review comment 9 found that the stamps were written ahead of the commits, by 4 to 6 minutes, and a log of decisions is only a trustworthy record if its times are real. The times come from `git log --date=iso` for the commit that added each entry, so the mapping can be checked.
Not changed: the file is still not strictly newest-first below the M3 block. The `14:30` entry came in with commit `20ad501`, made at 13:46, so the M2 entries around it were stamped later than their commits. They belong to PR #25, which is merged, and restamping them is a separate change to another milestone's record, so they are left as they are.
From here on each entry is stamped with the clock at the time of writing.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 9
- Issue: #7 (PR #26, review comment 9)

## [2026-11-01 18:16] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `README.md`, `TODO.md`)

**Summary:**
Recorded what the review of PR #26 changed. The plan gains five checked Given/When/Then items and four "Decided" bullets (plain-string priority choices, text UTF-8 cannot hold, output printed after the `try` with escapes, and the corrected limit).
The `--due` and exit-code bullets in the plan and in `TODO.md` now say that an offset exits 2 and that a closed pipe exits 1 quietly. `README.md` says the same in the usage section.
The known limit is reworded from "can take the same ID" to "a task is lost" in all three files, with a pointer to the follow-up issue #27.

**Rationale:**
The project `CLAUDE.md` says to change the plan, the matching issue, and `README.md` together when a decision changes, and two decisions changed: the exit code for a UTC-offset `--due` (1 to 2) and the wording of the concurrency limit. Review comment 6 pointed out that "can take the same ID" understates it:
20 simultaneous `add` commands stored 17, 16 and 14 tasks in three runs, so tasks are lost. The review offered a lock or an honest note; a portable lock needs a design of its own (`fcntl` is Unix-only, and an `O_EXCL` lockfile goes stale after a crash), so the note is here and the lock is issue #27 with three options and acceptance criteria.
Issue #7 still shows the old checklist and is ticked once CI is green, as before.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 8
- Issue: #7 (PR #26, review comment 6), #27 (the lock)

## [2026-11-01 18:13] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Every line the commands print now goes through `_printable`. Control characters, the C1 controls, and the line and paragraph separators are shown as escapes, so `add $'a\nb'` lists as one line ending `a\nb` and `$'evil\x1b[31mRED'` lists as `evil\x1b[31mRED` instead of sending the escape sequence to the terminal.
Text that standard output cannot encode is shown as an escape too: with `PYTHONIOENCODING=ascii`, an accented letter prints as its escape (`é` as `\xe9`) and the command exits 0 where `list` used to stop partway with a codec error. The stored name is unchanged.

**Rationale:**
A name is whatever was typed or whatever a shared file carries, and `README.md` expects lists to be shared, so it should not reach the terminal raw (global `CLAUDE.md`: "sanitize all outputs"). The review offered two places for the fix.
Rejecting control characters in `Task` would make a single such name in a shared file turn the whole list unloadable, so the fix is at the output, the one place that has the danger.
Only the categories that break a line or drive the terminal are escaped (`Cc`, `Zl`, `Zp`). `str.isprintable` was rejected as the test because it also flags format characters and non-ASCII spaces, which would damage a zero-width joiner in an emoji sequence or an ideographic space in a name written in another language.
Encoding uses `backslashreplace` against the stream's own encoding, so the same function covers the surrogate-free but unencodable case.
Known limit: a literal backslash is not doubled, so a name that really contains `\n` looks like one that contains a newline.
Eight tests were written first and seen failing, and four deliberate breaks of the code are each caught (no `Zl`, no `Cc`, `replace` in place of `backslashreplace`, and over-escaping with `Zs` and `Cf`). The over-escaping break first survived, so the test for unchanged text was widened to a joiner and a wide space.

**Bugfix Context:**
Review comment 3 on PR #26. Root cause: `_describe` and the `add` message interpolated the name into the line unchanged.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 7
- Issue: #7 (PR #26, review comment 3)

## [2026-11-01 18:11] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
A failure to write the output is no longer reported as a problem with the data. `task-tracker list | head -1` prints one line and nothing on standard error, and exits 1 quietly; it used to print `task-tracker: error: [Errno 32] Broken pipe` plus `Exception ignored while flushing sys.stdout` and exit 120. Any other write failure prints `task-tracker: error:
cannot write the output: <reason>` and exits 1, and for `add` the task is already saved.

**Rationale:**
`add` and `list` printed inside the `try` that exists for load and save, so a closed pipe or a full disk was reported as an `error:` about the data, and `add` reported it after it had stored the task, which invited a retry and a duplicate. The commands now return their lines and `main` hands them to `_show` after the `try`.
`_show` flushes inside its own `try`, because a pipe buffers and a reader that has gone shows up at the flush, and on `BrokenPipeError` it points stdout at devnull, the recipe in the Python `signal` documentation. That recipe exits with 1 as well, so a closed pipe keeps one exit code.
Rejected: treating a closed pipe as success (exit 0), which the `signal` note does not do, and restoring the default `SIGPIPE` action, which the same note advises against because it also kills the program on a broken socket.
Four tests were written first and seen failing, then checked with four deliberate breaks of the code: no devnull redirect, exit 0 on a closed pipe, no `BrokenPipeError` branch, and no flush. The last one first survived, because a long list fails mid-stream and never reaches the flush.
A second test starts the child with a pipe whose reader is already closed, which makes the flush the only place the error can appear, and it now catches that break. A real `list | head -1` over 3000 tasks was also checked by hand.

**Bugfix Context:**
Review comment 2 on PR #26 (output failures and the `add` retry). Root cause: output and data errors shared one `try`, so one `except` could not tell them apart.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 6
- Issue: #7 (PR #26, review comment 2)

## [2026-11-01 18:08] Commit Summary

**Change Type:** Fix

**Scope:** task (`src/task_tracker/task.py`, `tests/test_task.py`, `tests/test_storage.py`)

**Summary:**
`Task` now refuses a name or description that UTF-8 cannot hold, such as a lone surrogate. `task-tracker add $'bad \xff'` prints `task-tracker: error: name must be valid UTF-8 text`, exits 1, and writes nothing. A file that holds such text is a corrupt file: `load` reports `<file>: record N:
name must be valid UTF-8 text`, where `list` used to print the earlier tasks and then stop with a codec error.

**Rationale:**
A byte that is not valid UTF-8 in a command-line argument reaches Python as a lone surrogate (`surrogateescape`), and JSON accepts an escaped one, so such text can come from either side. `save` writes UTF-8, so it could never be stored: the first task with that name was lost at the point of saving, and a file that already held one made every later `add` fail.
Refusing it in `_normalize` closes both ends with one rule, and it keeps the invariant M2 set up: what `save` writes is what `load` accepts, and what `load` rejects `save` refuses.
Rejected: replacing the bad characters with `?` or an escape on input, which would store a different name than the user typed, and handling the codec error in `main`, which would leave a corrupt file loadable.
Seven tests were written first and seen failing. One older test could no longer be built: it saved a task constructed with a lone surrogate and expected a `UnicodeEncodeError`. Its promise, that a refused save leaves the old file and no temporary file, is now one more case of the existing save-refusal test, with the surrogate assigned after construction.

**Bugfix Context:**
Review comment 2 on PR #26 (the part about names that load but cannot be encoded). Root cause: `Task` accepted text that the storage layer could not write.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 5
- Issue: #7 (PR #26, review comment 2)

## [2026-11-01 18:07] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
Every bad `--due` now gives one message and one exit code. `--due 2026-13-45` prints `argument --due/-D: expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS in local time, not '2026-13-45'` and exits 2.
A value with a UTC offset (`2026-11-02T10:00:00Z`) gets the same message and exit 2, where it used to parse and then fail later with exit 1 and a message that did not name the flag. The old text named the parser (`invalid fromisoformat value`).

**Rationale:**
A small named converter, `_due`, replaces `type=datetime.fromisoformat`. It raises `argparse.ArgumentTypeError`, which argparse shows verbatim after the flag name, and rejects a timezone-aware result. The check repeats a one-line rule that `Task` already enforces (D6, naive local time).
That is the price of one rule and one exit code for every bad `--due`; the project owner chose it over keeping exit 1 for offsets,
which reverses the decision recorded in the plan and `TODO.md` and is updated in the docs commit that follows.
Not changed: `fromisoformat` still accepts more than `README.md` promises (`20261102`, week dates, fractional seconds that `Task` truncates). A stricter parser would be a second spec to keep in step with the standard library, and accepting a superset harms no one.
The test was written first and seen failing four ways: no format in the message, `fromisoformat` in the message, and both offsets not raising `SystemExit` at all.

**Bugfix Context:**
Review comment 5 on PR #26 (and the UTC-offset item of comment 7). Root cause: argparse names the converter in its default message, and the offset rule lived only in the model, so it surfaced after parsing with a different exit code.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 4
- Issue: #7 (PR #26, review comments 5 and 7)

## [2026-11-01 18:06] Commit Summary

**Change Type:** Fix

**Scope:** tests (`tests/test_cli.py`)

**Summary:**
Two documented behaviors of the command line now have a test: `--due` keeps a time of day (`2026-11-02T10:30:45` is stored as that moment, not as midnight), and a bare `task-tracker` with no command exits 2 and says a command is required. No production code changes.

**Rationale:**
Review comment 7 found that every `--due` test passed a bare date, so a version that kept only the date part passed the whole suite, and that dropping `required=True` on the subparsers would only show up when someone ran the program.
Both tests pass as soon as they are written, because the behavior already exists, so they were checked the other way round: each was run against a deliberate break of the code. Dropping the time from the parsed `--due` fails the first test, and `required=False` fails the second. The source was restored and the full suite is green again (192 tests).
The third item in the comment, a UTC-offset `--due`, is pinned in the next commit with the converter that changes what it does.

**Bugfix Context:**
Review comment 7 on PR #26. These were gaps in the tests and not defects in the program.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 3
- Issue: #7 (PR #26, review comment 7)

## [2026-11-01 18:05] Commit Summary

**Change Type:** Fix

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
A wrong `--priority` now says what is valid: `argument --priority/-p: invalid choice: 'URGENT' (choose from 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW')`. It used to say `invalid Priority value: 'URGENT'` and list nothing. Case is still significant, so `-p high` is rejected with the same message. The exit code stays 2.

**Rationale:**
argparse runs `type=` before it checks `choices`, so with `type=Priority` a wrong value died in the converter and the `invalid choice` message was unreachable. Dropping `type=` and passing the labels as plain strings is the change the review suggested, and `Task` already normalizes a string through `Priority(...)`, so nothing else moves.
The choices are `priority.value` strings, not the enum members, because argparse prints each choice with `repr` and a member would show as `<Priority.CRITICAL: 'CRITICAL'>`.
Rejected: `type=str.upper`, which would accept `-p high`. The spec says users type the enum names, and the PR already records the case-sensitive rule as a risk.
The test was written first and seen failing on the missing names. It checks the error line and not the whole output, because the usage line printed above it already lists the four names and would have let the old message pass.

**Bugfix Context:**
Review comment 4 on PR #26. Root cause: the order argparse applies `type` and `choices` made the `choices` check dead code.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 2
- Issue: #7 (PR #26, review comment 4)

## [2026-11-01 18:03] Commit Summary

**Change Type:** Fix

**Scope:** storage (`src/task_tracker/storage.py`, `src/task_tracker/task.py`, `tests/test_storage.py`, `tests/test_task.py`, `tests/test_cli.py`)

**Summary:**
A corrupt task file no longer ends in a traceback in two cases that escaped the CLI's single `except`. A record with a `cls` key is now reported as an unknown field, and a file nested too deeply for `json.load` is reported as `<file>: nested too deeply to read`. Both are one-line errors with exit code 1, from `list` and from `add`, and the file is left alone.

**Rationale:**
`_from_record` spreads a stored record into `Task.restore(**record)`, so a key named `cls` collided with the classmethod's own first parameter and raised a `TypeError`. Making `cls` positional-only is the smallest fix at the root: the key lands in `record` and the existing unknown-field check rejects it.
`json.load` raises `RecursionError` on a file nested 200,000 deep, which is not a `ValueError`, so `_read_records` maps it to the `ValueError` that names the file, as M2 does for every other bad file.
Rejected: catching `TypeError` and `RecursionError` in `main`. That would hide programming mistakes behind the same message, and the contract that a bad file is always a `ValueError` would stay broken for any other caller of `load`. A fuzz of every field against 13 JSON values found no other exception type that escapes `Task.restore`.
Seven tests were written first and seen failing with the raw `TypeError` and `RecursionError`: two in `test_storage.py`, one in `test_task.py`, and four end-to-end cases in `test_cli.py` (both commands, both shapes).

**Bugfix Context:**
Review comment 1 on PR #26. Root cause: `Task.restore(cls, **record)` shared a namespace between the classmethod's parameter and the stored field names, and `load` shared an exception contract with `json.load` that has one hole. Reproduced with `[{"cls": 1}]` and `[` repeated 200,000 times through `task-tracker list` and `task-tracker add`.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review, step 1
- Issue: #7 (PR #26, review comment 1)

## [2026-11-01 18:02] Commit Summary

**Change Type:** Docs

**Scope:** docs (`TODO.md`)

**Summary:**
Planned the work that answers the eleven inline review comments on PR #26: eleven steps, each with its commit subject, the tests that will pin it, and the risks. Eight comments are fixed, one (#5) is fixed in part, and two (#6, #8) are answered with a reason instead of a code change.

**Rationale:**
The project rule is to plan in `TODO.md` before any code changes, and the review fixes touch the exit-code decision, the error path, and the output, so they need a recorded plan as much as a feature does. Every claim in the review was reproduced in a scratch directory before it was triaged: the two tracebacks, the broken pipe, the control characters, the two argparse messages, and the untracked `tasks.json`.
Two choices were made with the project owner before writing this: a UTC-offset `--due` now exits 2 in a named converter, and the concurrent-`add` limit gets a follow-up issue instead of a lock in this PR.

**References:**

- `TODO.md`: 2026-11-01 Fix: PR #26 review
- Issue: #7 (PR #26)

## [2026-11-01 14:24] Commit Summary

**Change Type:** Docs

**Scope:** docs (`docs/implementation-plan.md`, `README.md`)

**Summary:**
Ticked the nine M3 boxes in the plan and added five that record what was built beyond them: the highest-ID-plus-one rule, the ID tie-break, the empty-list message, the shape of a list line, and the two failure cases. Added a "Decided (2026-11-01)" list to M3 and closed the half of Q3 that M3 owned. `README.md` gains a short section on `add` and `list` with the exit codes.

**Rationale:**
The project `CLAUDE.md` says to change the plan, the matching issue, and `README.md` together when a decision changes. The usage section only describes behavior I ran in a scratch directory: the three exit codes, the sort order, and the empty-list message.
Issue #7 still shows the old checklist. It is a change on GitHub, so it waits for the project owner along with the push and the pull request.

**References:**

- `TODO.md`: 2026-11-01 Feature: M3 First slice, add and list
- Issue: #7

## [2026-11-01 14:22] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`add` and `list` no longer end in a traceback when something is wrong with the data or the file. A blank name, a corrupt task file, or a path that cannot be read or written prints `task-tracker: error: <message>` on standard error and returns 1. A bad option value still exits 2 inside argparse.

**Rationale:**
One `except (ValueError, OSError)` in `main`. M2 made every corrupt-file failure a `ValueError` that names the file, and `Task` raises `ValueError` for a bad field, so no custom exception class is needed. `OSError` is the case M2 left for the CLI on purpose: a directory where `tasks.json` should be, or a file that cannot be read.
The risk is that a programming mistake that raises `ValueError` is reported as bad input. It still prints its message and exits nonzero, and the fix would be a custom exception, which waits until the two cases need telling apart.
Four tests, written first and seen failing with the raw exception escaping `main`. Five mutations are each caught: `OSError` not caught, `ValueError` not caught, exit 0 on error, the message on standard output, and no program prefix.

**References:**

- `TODO.md`: 2026-11-01 Feature: M3 First slice, add and list
- Issue: #7

## [2026-11-01 14:21] Commit Summary

**Change Type:** Feature

**Scope:** cli (`src/task_tracker/cli.py`, `tests/test_cli.py`)

**Summary:**
`task-tracker list` prints the current tasks (everything but `DONE`) sorted by due date with undated tasks last, then by priority rank from `CRITICAL` down, then by ID. One line per task: ID, status, priority, due date (`-` when there is none), name. With nothing current it prints `No current tasks in <path>`.

**Rationale:**
The sort key is `(due or datetime.max, priority rank, id)`. `datetime.max` stands in for a missing due date, which sorts undated tasks last without a separate flag. A stored date always has whole seconds, so it can never equal `max`. Rejected: a leading `due is None` item, which the tests showed was redundant.
The rank is the enum's definition order, not the string value, which sorts `MEDIUM` after `LOW` (Review Focus 1). The ID settles ties, and a test stores the pair in the opposite order to prove it is the ID and not the file order.
The empty message names the file so a second list started from a subdirectory explains itself (D2). `start` and `stop` are not shown (Q3).
Eight tests, written first and seen failing on `invalid choice: 'list'`. Seven mutations are each caught: rank by the raw string, no ID tie-break, including `DONE` tasks, undated first, a different empty message, reversed order, and no due column. Ruff 0.16 flags `datetime.max` (DTZ901) where CI's 0.15.17 does not, so the line carries a `noqa` with the D6 reason, as `task.py` does for its sentinel.

**References:**

- `TODO.md`: 2026-11-01 Feature: M3 First slice, add and list
- Issue: #7

## [2026-11-01 14:19] Commit Summary

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
