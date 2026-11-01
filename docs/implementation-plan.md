# Task Tracker Implementation Plan

> **You implement this plan.** It pins what to build, the tests that prove each piece, and the decisions behind them (all made on 2026-10-23). It holds no implementation code: every test is a Given/When/Then with exact values for you to turn into a pytest test. Check boxes off as you go.

**Goal:** Ship the seven `README.md` features as an installable `task-tracker` CLI.

**Architecture:** Grow it in vertical slices. `add` and `list` work end-to-end first (M3), then one command per milestone. Splitting into domain, storage, and CLI layers waits until M8, when working code shows where the seams are.

**Tech stack:** Python 3.14 standard library at runtime ([argparse], [dataclasses], [enum], [datetime], [JSON], [pathlib], [os.replace]). Dev: pytest, pytest-cov, ruff, pyright, uv.

**Spec:** `README.md`, sections Requirements and Features.

## Global Constraints

- Python: `.python-version` pins 3.14.7 for development; the floor is `>=3.14` in both `README.md` and `pyproject.toml` (decided 2026-10-23: a patch-level floor would block installs on older 3.14 releases for no code reason).
- Runtime dependencies stay empty (`dependencies = []`).
- `Status`: `TO_DO`, `IN_PROGRESS`, `DONE`. `Priority` by rank, highest first: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- Defaults (`README.md`, after Q1 to Q3): status `TO_DO`, priority `LOW`, description `""`, due `None`, date completed `None` (a `DONE` task defaults to the current time); created and updated are stamped by the model and cannot be given; start defaults to created and stop to the current time, or to start if that is later. All datetimes are naive local time (D6).
- Timeline: `created <= start <= stop <= date completed`, with equality allowed at every link.
- "Current" tasks are `TO_DO` plus `IN_PROGRESS`.
- The project-level list in the current directory is the default; `--dir PATH` selects another directory and `--global` selects the home list. The two flags are mutually exclusive.
- Every option has a long and a short form: `--dir`/`-d`, `--global`/`-g`, `--priority`/`-p`, `--due`/`-D`, `--status`/`-s`, `--name`/`-n`, `--all`/`-a`. `-d` and `-D` differ by one Shift, so a slip must fail safe (M7). A letter claimed twice in one parser raises `ArgumentError` when the parser is built.
- Commits use Conventional Commits with lowercase scopes. `scripts/bump-version.sh` only recognizes scopes matching `[a-z0-9_-]+`, so `feat(CLI):` produces no version bump.
- From your global CLAUDE.md: tests first, at least 80% coverage on changed code, GitFlow branches, a `TODO.md` entry before each milestone, a `SUMMARY.md` entry before each commit.

## Decisions (all made on 2026-10-23)

### D1. Storage format

- **JSON** ([JSON]). Pro: integers and `null` survive as-is; one call each way. Con: the whole file is rewritten on every change; dates and enums still need converting.
- **CSV** ([csv]). Pro: opens in a spreadsheet; the flat task fields fit. Con: every value loads back as a string, so IDs, `None`, dates, and enums all need converting.
- **SQLite** ([SQLite3]). Pro: built-in atomic writes and auto-increment IDs. Con: not human-readable; priority rank needs a SQL `CASE`; the most to learn up front.

**Decision (2026-10-23): JSON**, the fewest conversions for a flat list. The examples below assume JSON.

### D2. Where the lists live

- **Current directory only** (project list at `./tasks.json`). Pro: simple, no searching. Con: running from a subdirectory starts a second list.
- **Walk up to the nearest `.git`**. Pro: one list per repository from anywhere inside it. Con: more code, and you need an answer for "not in a repository".

The global list lives under the home directory, for example `~/.task-tracker/tasks.json`.

**Decision (2026-10-23): the current directory by default, or the directory named by `--dir PATH` (`-d`).** Walking up to `.git` was rejected: it assumes a code project, and a task list can live anywhere. Running from a subdirectory still starts a second list, so M3 considers having `list` name the file it read. `--dir` and `--global` are mutually exclusive.

### D3. CLI shape

- **argparse subcommands with flags** (`task-tracker add "Buy milk" --priority HIGH`). Pro: each action gets its own options and `--help`; [argparse] supports it directly. Con: reads less like the `README.md` "using a flag" wording.
- **Flags only** (`task-tracker --add "Buy milk"`). Pro: literal match to `README.md`. Con: options that apply to one action only, plus mutual-exclusion rules to maintain.
- **click or typer**. Pro: less boilerplate. Con: adds the first runtime dependency.

**Decision (2026-10-23): argparse subcommands.** The milestones below assume them. `README.md` features 3 to 7 name the commands (`list`, `list --all`, `add`, `update`, `delete`); `--global` stays a flag. Every option has a long and a short form (see Global Constraints).

### D4. Test runner

- **pytest + pytest-cov**. Pro: [tmp_path], [monkeypatch], and [capsys] cover exactly what this CLI needs (temp files, cwd and `HOME`, printed output); [pytest-cov] gates coverage with one flag. Con: two dev dependencies.
- **unittest + coverage**. Pro: stdlib runner. Con: more boilerplate; temp dirs, cwd, and env patching by hand.

**Decision (2026-10-23): pytest + pytest-cov.**

### D5. Task IDs

- **Highest existing ID + 1**. Pro: short and typeable (`update 3`). Con: deleting the highest task frees its ID for reuse.
- **Counter stored in the file**. Pro: IDs never reused. Con: the file becomes a wrapper object instead of a bare list.
- **UUID**. Pro: globally unique. Con: painful to type.

**Decision (2026-10-23): highest + 1, with a confirmation prompt on delete (Q5).** Deleting the highest task frees its ID, so a stale `delete 3` could hit a different task; the prompt shows the task name to catch that. M6 pins both behaviors.

**Decision (2026-10-31, from the spec-gap audit): a task's `id` is a required `int`.** `README.md` marks the ID required, so a `Task` never exists without one. The `add` command computes highest + 1 from the other tasks and passes it in; a task never assigns its own ID. Rejected: an optional `id` set when the task is added, which leaves a `None` state that every save would have to guard against.

### D6. Dates and times

- **Naive local time, stored as ISO 8601 strings** ([datetime] `isoformat` / `fromisoformat`). Pro: readable, matches what the user types. Con: ambiguous across DST changes and travel.
- **Timezone-aware UTC**. Pro: unambiguous everywhere. Con: every display needs a conversion to local time.

**Decision (2026-10-23): naive local** for a single-user local CLI. A bare `--due 2026-11-02` parses to midnight with `datetime.fromisoformat`.

**Amended 2026-10-31 (project owner): one form for every datetime, however it is passed in.** `Task` turns an ISO 8601 string, a `date`, or a `datetime` into a naive local `datetime` with whole seconds, so `isoformat()` always reads `YYYY-MM-DDTHH:MM:SS`. M2 saves and M3 prints with that same call.
Whole seconds because `created` carries microseconds while a typed date does not, and a save at second precision would otherwise lose them in the M2 round trip.

## Spec questions (answered in `README.md`)

- Q1. **Decided:** users type and see the enum names (`TO_DO`, `IN_PROGRESS`, `DONE`; `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). `Priority.MED` is renamed `MEDIUM` so the word matches `README.md`. Do it before any task file exists: the stored value is the enum value.
- Q2. **Decided:** `due` is optional and defaults to `None`. Tasks without a due date sort after tasks with one, then by priority. (Defaulting to now made every new task overdue and ranked undated tasks ahead of future deadlines.)
- Q3. **Decided:** `start` and `stop` are plain datetime fields that default to the current time, with no tracking logic. Still open: can `add` and `update` set them, and does `list` show them (decide in M3 and M5)?
- Q4. **Decided:** yes. Moving a task out of `DONE` sets date completed to `None`, so `status != DONE` always means date completed is `None`. **Amended 2026-10-31 (project owner):** the converse holds too. A `DONE` task always has a date completed, defaulting to the moment it was marked done, and a date passed in cannot be in the future.
- Q5. **Decided:** yes. `delete` shows the task's name and asks before deleting (see D5). A `--yes` flag for scripts is deferred.
- Q6. **Decided:** a date and time. `due`, `created`, `updated`, and `date completed` are all datetimes; a bare date such as `2026-11-02` parses to midnight.

## Review Focus

The five failure modes most likely to bite a user, each pinned by a test in the milestone named.

1. **Priority order.** `StrEnum` members are `str` and sort alphabetically (`CRITICAL < HIGH < LOW < MEDIUM`), so sorting on the raw value misplaces `MEDIUM` and `LOW` in either direction. Expect rank order. Pinned in M3.
2. **Interrupted save.** Opening the task file for writing truncates it; a crash mid-write loses every task. Expect the old file intact. Pinned in M2.
3. **First run.** No list file and no `~/.task-tracker/` yet. Expect an empty list, and the first save creates what's missing. Pinned in M2 and M7.
4. **Bad input.** Unknown ID, invalid priority or status, malformed date, empty name, corrupt file. Expect a one-line error, a nonzero exit, the file unchanged, and no traceback. Pinned in M3, M5, M6.
5. **Silent round-trip loss.** `Priority.HIGH == "HIGH"` is `True`, so `==` assertions pass even when loading returns plain strings. Expect real enum members and `None` back. Pinned in M2.

## How to work each milestone

1. Branch from `develop`: `feature/<milestone>`.
2. Add the milestone's `TODO.md` entry.
3. Red: write the listed tests; `uv run pytest` fails for the reason you expect.
4. Green: the least code that passes.
5. Refactor while green: `uv run ruff check . && uv run ruff format . && uv run pyright`.
6. Prepend `SUMMARY.md`, commit (for example `feat(cli): add list command`), open a PR into `develop`.

Coverage: `uv run pytest --cov=task_tracker --cov-report=term-missing --cov-fail-under=80`.

## Milestones

### M0. Groundwork (no code)

- [x] Create `develop` from `main` and push it. The version-bump workflow only runs when `release/*` or `hotfix/*` merges into `main`, so features land in `develop` first.
- [x] Tag `v0.1.0` on `main` and push the tag. With no tags, the first release scans all history and `7c90c7f fix: pin to specific shaw to fix linting error` lands in the first CHANGELOG.
- [x] Decide D1 to D6, answer Q1 to Q6, and update `README.md`, including the Python floor. Decided on 2026-10-23: D1 to D6, Q1 to Q6, and the Python floor.

**Done when:** `develop` and `v0.1.0` exist on origin and `README.md` reflects the answers.

### M1. Task model

Branch `feature/task-model`. Covers `README.md` "Task object".

- [x] `uv add --dev pytest pytest-cov` ([uv dependencies]). First, so every later step can start with a failing test.
- [x] Rename `Priority.MED` to `Priority.MEDIUM` in `src/task_tracker/priority.py` (Q1). Red first: a test that parses each name `README.md` promises (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with `Priority(name)`; it fails only for `MEDIUM`. A test that `MED` no longer exists would fail only on a redesign, never on a bug. The stored value is the enum value, so do this before any task file exists.
- [x] Given ID 1 and the name "Buy milk", when a task is created, then status is `Status.TO_DO`, priority is `Priority.LOW`, description is `""`, due is `None`, and date completed is `None`.
- [x] Given the time captured just before and just after creating a task, with the process time zone set to a non-UTC zone such as `Asia/Kolkata`, then its created timestamp falls between the two. Repeat for `updated`, `start`, and `stop`; `due` is excluded because it defaults to `None` (Q2). A UTC default passes on a UTC machine such as the CI runner; the non-UTC zone pins "local" (D6).
- [x] Given a task is created, then every datetime field that is not `None` is naive (`tzinfo is None`) (D6). `due` and date completed default to `None`, which has no `tzinfo`.
- [x] Given the name `""` or `"   "`, when a task is created, then `ValueError` is raised.
- [x] Given a name that is not a string, such as the `null` a hand-edited `tasks.json` can hold, then `ValueError` is raised, not `AttributeError`. Given `"  Buy milk  "`, then the stored name is `"Buy milk"`.
- [x] Given `status="DONE"` and `priority="HIGH"` as plain strings, then the stored values are `Status.DONE` and `Priority.HIGH`, checked with `is`. Given an unknown label, then `ValueError` is raised. Equality alone would pass for plain strings, because the enums are `StrEnum`s.
- [x] Given a timezone-aware value for any datetime field, then `ValueError` is raised, because sorting an aware and a naive task raises `TypeError` (D6).
- [x] Given a status other than `DONE` and a date completed, then `ValueError` is raised (Q4).
- [x] Given `Task(status=DONE)` with no date completed, then it equals `created` and so do `start` and `stop`. Given one in the future as an object or as text, then `ValueError` is raised. Given the clock's own reading with microseconds added, then it is accepted: microseconds are dropped before the comparison.
- [x] Given the same day as `"2026-11-02"`, `"2026-11-02T00:00:00"`, `"2026-11-02 00:00:00"`, a `date`, or a `datetime` with microseconds, then `due` equals midnight and `isoformat()` reads `2026-11-02T00:00:00`. Default timestamps have no microseconds.
- [x] Given an invalid string, a string with a UTC offset, or a value of another type for a datetime field, then `ValueError` is raised and names the field.
- [x] Given positional arguments after `id` and `name`, then `TypeError` is raised, so swapped `datetime` arguments cannot type-check and run. `Task(1, "Buy milk")` still works.
- [x] Given a clock that hands out a new second on every reading (the tests replace the model's `_now`), when a task is created, then `created`, `updated`, `start`, and `stop` all equal the first reading and the next reading is unused. Whole-second timestamps make two real clock reads agree almost always, so only a controlled clock can tell one reading from two.
- [x] Given `created=` or `updated=` as an argument, then `TypeError` is raised: the model stamps both, so a caller cannot pass a false history (owner decision, 2026-10-31). Given `stop=` explicitly, then it is kept and the others still share one reading.
- [x] Given the timeline `created <= start <= stop <= date completed`, then every broken link raises `ValueError` with its own message: a `start` before `created`; a `stop` before `start` (which includes before `created`); a `start` after the date completed; a `stop` after it; and a date completed before `created`. Every link accepts equality.
- [x] Given a later `start`, including a future one, then it is kept, and the default `stop` is that `start`, not "now", which would be earlier.
- [x] Given a new task, then it can only be done at the moment it is created: `created` is always now, so a past date completed is a broken link. A past completion belongs to a task that already existed, and is tested through `Task.restore()` in M2 and `update` in M5. An open task's `stop` has no upper limit.
- [x] Add a CI workflow that runs `uv run pytest` on push and pull request, once the tests above exist: pytest exits with code 5 when it collects no tests ([pytest exit codes]), so an earlier workflow fails its first run.
      Follow `super-linter.yml`, not `version-bump.yml`: top-level `permissions: {}`, job-level `contents: read` only (the bump job needs `contents: write`), `persist-credentials: false`, and SHA-pinned `actions/checkout` and `astral-sh/setup-uv`.
- [x] Add a Tests badge for that workflow to `README.md`, next to the Lint badge, so "passing" means the tests passed.

**Think about:**

- In a dataclass, when does `created: datetime = datetime.now()` run? What does `default_factory` change? ([dataclasses])
- Why does `Task` read the clock once in `__post_init__` and not give each timestamp its own `default_factory`? Decided 2026-10-31 in review of PR #23: separate reads differed on about a quarter of new tasks, so a private sentinel default is replaced by one shared reading, and the fields stay typed `datetime` without `None` checks.
- Where does the name check live so every path that builds a task hits it? In `__post_init__`, which also strips the name and requires a string. Assigning `task.name = ""` later skips it, so M5's `update` must re-validate, for example by building a new task with `dataclasses.replace` or through a validating setter.
- The ID is a required `int` (D5, decided 2026-10-31), so every M1 test passes one in. The next ID is computed by `add` in M3, never by the task.

**Done when:** the tests pass locally and in CI.

### M2. Save and load

Branch `feature/task-storage`.

Produces, for later milestones: load (path to list of tasks, empty when the file is missing) and save (list of tasks to path, atomic, creating parent directories).

- [x] Add `Task.restore(...)`. The constructor no longer accepts `created` or `updated` (M1, owner decision 2026-10-31), so the loader rebuilds a task through `restore`, which takes them and still enforces the other rules. Given a saved task, when loaded, then `created` and `updated` equal the stored values, not the load time.
- [x] Given a stored timeline out of order, then a clear error is raised. Given a task created on 2026-10-10 and completed on 2026-10-15, then it loads with both dates kept: this is where a past date completed is tested.
- [x] Given no file at `tmp_path / "tasks.json"`, when loading, then the result is `[]` and no file is created.
- [x] Given task 1 "Buy milk" (`HIGH`, due 2026-11-01 09:00) and task 2 "File taxes" (`DONE`, no due date, completed 2026-10-15 17:30), when saved then loaded, then both equal the originals, `loaded[0].priority is Priority.HIGH`, `loaded[1].status is Status.DONE`, `loaded[0]`'s date completed `is None`, and `loaded[1].due is None`.
- [x] Given an existing file and a save that fails partway (make serialization raise with `monkeypatch`), then the file's previous contents are unchanged.
- [x] Given a file containing `not json`, when loading, then a clear error is raised and the file is unchanged.
- [x] Given `tmp_path / "nested" / "dir" / "tasks.json"` whose directories don't exist, when saving, then the directories are created.
- [x] Given a stored record that cannot be real, then a `ValueError` names the file and the record's position, such as `tasks.json: record 2: name must not be blank`, and the file is unchanged.
      That covers: a record that is not an object, a missing or an unknown field, an `id` that is not an `int` (text, `true`), a `description` that is not text, a value `Task.restore` refuses, `updated` before `created`, a null `created`, `updated`, `start`, or `stop`, an `id` below 1, a `DONE` task without a date completed, and two records with the same `id`.
      Unknown fields are rejected, not ignored, because `save` rewrites the whole file and would delete them.
- [x] Given an empty file, binary content, or JSON that is not a list, then a `ValueError` names the file. Given a directory where the file should be, then the `OSError` is not reported as a corrupt file. Given no file, or a directory that does not exist, then `load` returns `[]` and creates nothing.
- [x] Given a save that fails partway, then a first-time save leaves no file, a failed `os.replace` leaves the old file and no temporary file, and the temporary file is created in the same directory as the target.
      The failure must come after bytes are written (audit finding G2): the test makes `json.dump` write `[{` into the open file and then raise, and was seen failing against a plain overwrite first.

- [x] Given tasks that `load` would reject (a duplicate `id`, or a name blanked after construction), then `save` raises a `ValueError` naming the file and the record before it creates a directory or a temporary file, and the previous file is unchanged.
- [x] Given stamps or a date completed later than the clock (daylight saving ends, the time zone changes), then `Task.restore` accepts them: only the ordering rules apply to a stored task. The constructor still rejects a future date completed.
- [x] Given a saved file, then non-ASCII text is written as text, every date as `YYYY-MM-DDTHH:MM:SS`, a symbolic link is followed, and an existing file's mode is kept. A new file is readable and writable by its owner only.

**Think about:**

- Write a temp file, then [os.replace] it over the real one. Where must the temp file live? (The docs say the replace may fail across filesystems.)
- What happens to the temp file when the write fails?
- One place that converts a task to and from plain data, or inline in save and load? Either is fine for now; M8 revisits it.

**Decided (2026-11-01):**

- `Task.restore` shares one validation with the constructor: `__post_init__` is split into stamping, `_normalize`, `_fill_in_defaults`, and `_validate`, and `restore` builds the object without `__init__`, then runs `_normalize` and `_validate`.
  It takes the record as keyword arguments and reads the field list from the dataclass (review of PR #25), so a missing or unknown field is a `ValueError` raised by `Task`. Rejected: hidden `_created` and `_updated` init parameters and a second copy of the rules.
- The temporary file lives next to the target, because `os.replace` is atomic only within one filesystem, and a `finally` removes it after a failure. If the target is a symbolic link, the temporary file lives next to the real file.
- The task-to-data conversion is two private functions in `storage.py`, with the field names taken from `dataclasses.fields(Task)`. M8 revisits.
- One error type: every corrupt-file failure is a `ValueError` (`JSONDecodeError` and `UnicodeDecodeError` are subclasses), so M3's CLI catches one type. No custom exception class until M3 needs to tell the cases apart.
- Known limit: no `fsync` before the replace (a `ponytail:` comment in `storage.py` names the upgrade).
- Stored dates are not compared with the clock (review of PR #25). Naive local time means a clock set back an hour, a changed time zone, or a fixed clock would make a file that was valid when saved unloadable and lock every command out of all tasks.
  Only the constructor holds a new task to the clock. A hand-edited far-future date on a stored task now loads.
- `save` runs every record through the rules `load` applies, before it creates anything (review of PR #25), so it cannot replace the last good file with one `load` rejects.
- A save killed between creating the temporary file and the replace leaves a hidden `.tasks.json.*.tmp` file. `README.md` documents the `.gitignore` pattern. Rejected: deleting stale temporary files at the start of `save`, which could remove another process's file mid-save.
- An atomic save needs write permission on the directory, where a plain write needs it only on the file. That comes with replacing by rename.
- Audit findings addressed: G2 (a test that passes against a non-atomic save) and G3 (corrupt file handling).

### M3. First slice: add and list

Branch `feature/add-and-list`. Covers features 3 and 5, project-level list only, in `./tasks.json` of the current directory (D2); `--dir` arrives in M7.

Suggested seam: `main(argv: list[str] | None = None) -> int`, so tests call `main(["add", "Buy milk"])` directly, with `monkeypatch.chdir(tmp_path)` and `capsys`.

- [ ] Given an empty project directory, when `add "Buy milk"`, then exit code is 0, the project file holds one task with ID 1 named "Buy milk" with no due date, and the output names ID 1.
- [ ] Given A (due 2026-11-02, `LOW`), B (due 2026-11-01, `LOW`), C (due 2026-11-01, `CRITICAL`), D (`DONE`), and E (due 2026-11-03, `IN_PROGRESS`), when `list`, then the order is C, B, A, E and D is absent.
- [ ] Given four tasks all due 2026-11-01 with priorities `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, when `list`, then the order is `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- [ ] Given a task with no due date (`MEDIUM`) and a task due 2026-11-01 (`LOW`), when `list`, then the dated task comes first (Q2). Given two tasks with no due date, `LOW` added first and `HIGH` second, then `HIGH` comes first.
- [ ] Given `add "Pay rent" --priority URGENT`, then argparse exits with code 2 and no file is written.
- [ ] Given `add "Pay rent" --due 2026-13-45`, then exit code is 2 with an error line and no traceback.
- [ ] Given `add ""`, then the exit code is nonzero, an error line is printed, and no file is written.
- [ ] Given a corrupt project file, when `list`, then a one-line error is printed, the exit code is nonzero, and there is no traceback.
- [ ] Given `add "Pay rent" -p HIGH -D 2026-11-02`, then the stored task equals the one from `add "Pay rent" --priority HIGH --due 2026-11-02`.

**Think about:**

- argparse errors raise `SystemExit` with code 2 ([argparse]). How does a pytest test assert that?
- Two tasks with the same due date and priority: which comes first, and does a test pin it?
- What does `list` print when nothing is current? Which fields fit on one line? Does it show `start` and `stop` (Q3), and what does it print for a missing due date? Should the empty-list message name the file it read (D2), so a second list started from a subdirectory explains itself?
- The generated `task-tracker` script calls `main()`. How does the return value become the process exit code? ([entry points])
- Where does "highest ID + 1" get computed?

**Done when:** `uv run task-tracker add "Buy milk"` then `uv run task-tracker list` works in a scratch directory.

### M4. List all

Branch `feature/list-all`. Covers feature 4.

- [ ] Given A, B, C, E from M3 plus done tasks D (completed 2026-10-10) and F (completed 2026-10-05), when `list --all`, then the order is C, B, A, E, F, D.
- [ ] Given the same tasks, when `list -a`, then the output equals `list --all`.

**Think about:** can the first half reuse the M3 ordering instead of repeating it?

### M5. Update

Branch `feature/update-task`. Covers feature 6.

- [ ] Given task 1 "Buy milk" (`LOW`, created and updated 2026-10-01 09:00), when `update 1 --name "Buy oat milk" --priority HIGH`, then the name and priority change, updated is later than 2026-10-01 09:00, created is unchanged, and the other tasks are untouched.
- [ ] Given task 1 is `TO_DO`, when `update 1 --status DONE`, then date completed is set to the current time.
- [ ] Given task 1 is `DONE`, when `update 1 --status TO_DO`, then date completed is `None` (Q4).
- [ ] Given no task 99, when `update 99 --name x`, then the exit code is 1, stderr names 99, and the file is unchanged.
- [ ] Given `update 1` with no fields, then the behavior you choose (error or no-op) is pinned.
- [ ] Given `update 1 -n "Buy oat milk" -p HIGH`, then the result equals `update 1 --name "Buy oat milk" --priority HIGH`.

**Think about:** who sets updated, the command or the task? What stops `update` from changing the ID or the created date? `due` is nullable (Q2): how does a user clear a due date? Can `update` set `start` and `stop` (Q3)? Pin whichever you choose.

### M6. Delete

Branch `feature/delete-task`. Covers feature 7.

- [ ] Given tasks 1, 2, 3, when `delete 2`, then tasks 1 and 3 remain with their IDs unchanged.
- [ ] Given no task 99, when `delete 99`, then the exit code is 1, stderr names 99, and the file is unchanged.
- [ ] Given tasks 1, 2, 3, when `delete 3` then `add "New"`, then the new task's ID is 3 (D5: highest + 1 reuses the freed ID).
- [ ] Given `delete 2` and the answer "n" (patch `input` with `monkeypatch`), then nothing is deleted. Given the answer "y", then task 2 is deleted. In both cases the prompt includes task 2's name (Q5).

**Think about:** the prompt exists to catch a reused ID, so what must it print? Scripts cannot answer a prompt; a `--yes` flag is deferred until you need one.

### M7. Global list

Branch `feature/global-list`. Covers feature 2.

Produces: one place that turns the global flag, `--dir`, the cwd, and the home directory into a file path.

- [ ] Given `HOME` set to `tmp_path / "home"` and cwd `tmp_path / "project"`, when `--global add "Renew passport"`, then the task is in the global file under `tmp_path / "home"` and no project file exists.
- [ ] Given one project task and one global task, then `list` shows only the project task and `--global list` shows only the global one.
- [ ] Given no `.task-tracker/` under the fake home, then the first global add creates it.
- [ ] Given `--dir tmp_path / "groceries"`, when `add "Milk"`, then the task is in `tmp_path / "groceries" / "tasks.json"` and no `tasks.json` exists in the cwd (D2). `-d` behaves the same.
- [ ] Given `--dir` and `--global` together, or `-d` and `-g`, then argparse exits with code 2, an error line is printed, and no file is written.
- [ ] Given `--dir` naming a directory that does not exist, when `list`, then the empty-list message is printed and the directory is not created.
- [ ] Given `add "Milk" -d 2026-11-02` (a slip for `-D`), then no file or directory named `2026-11-02` is created.

**Think about:**

- Top-level (`task-tracker --global add`) or per-subcommand (`task-tracker add --global`)? The [argparse] docs warn that a parent option and a subparser option with the same `dest` share one attribute. The same question applies to `--dir`.
- In a test of argparse (Python 3.14.7), `add Milk -d 2026-11-02` was rejected as an unrecognized argument when `--dir` belonged to the top-level parser, but silently set `dir='2026-11-02'` when it belonged to the `add` subcommand. Which placement fails safe?
- How do you make `--dir` and `--global` mutually exclusive in argparse? Check the argparse docs for groups.
- A typo'd `--dir` creates a new directory on the first `add`, because M2 creates missing parents. Is that acceptable, or should `add` require the directory to exist?
- Why does setting `HOME` isolate this test? Follow [Path.home] to [os.path.expanduser].

### M8. Refactor

Branch `feature/refactor-layers`. No behavior change: every test stays green, and tests change only their imports.

**Think about:**

- Which code decides what happens (ordering, defaults, completion rules), which does I/O (files, paths), and which talks to the user (argparse, printing)? Your global CLAUDE.md wants these as domain, infrastructure, and CLI layers.
- Could you swap JSON for SQLite by touching only the storage code? If not, what leaks?
- Does `main()` fit on one screen?
- Should CI enforce `--cov-fail-under=80`?

### M9. Install and first release

Branch `release/0.2.0` from `develop`. Covers feature 1.

- [ ] Install from the local checkout with `uv tool install` ([uv tools]), then run `task-tracker list` from an unrelated directory.
- [ ] Add a `README.md` Usage section with one example per command.
- [ ] Open a PR from `release/0.2.0` into `main`. On merge, the version-bump workflow should compute a minor bump from the feat commits since `v0.1.0`, commit `chore(release): v0.2.0`, and tag `v0.2.0`.
- [ ] After that merge, the Latest tag badge in `README.md` shows `v0.2.0`.
- [ ] Merge `main` back into `develop`. The bot commits only to `main`, so otherwise `develop` keeps the old version and has no `CHANGELOG.md`.

**Think about:** how does `uv tool install` pick up a local project instead of a PyPI package? Where does it put the executable, and is that directory on your `PATH`?

[argparse]: https://docs.python.org/3/library/argparse.html
[dataclasses]: https://docs.python.org/3/library/dataclasses.html
[enum]: https://docs.python.org/3/howto/enum.html
[datetime]: https://docs.python.org/3/library/datetime.html
[json]: https://docs.python.org/3/library/json.html
[csv]: https://docs.python.org/3/library/csv.html
[sqlite3]: https://docs.python.org/3/library/sqlite3.html
[pathlib]: https://docs.python.org/3/library/pathlib.html
[Path.home]: https://docs.python.org/3/library/pathlib.html#pathlib.Path.home
[os.path.expanduser]: https://docs.python.org/3/library/os.path.html#os.path.expanduser
[os.replace]: https://docs.python.org/3/library/os.html#os.replace
[tmp_path]: https://docs.pytest.org/en/stable/how-to/tmp_path.html
[monkeypatch]: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
[capsys]: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html
[pytest-cov]: https://pytest-cov.readthedocs.io/en/latest/config.html
[pytest exit codes]: https://docs.pytest.org/en/stable/reference/exit-codes.html
[uv dependencies]: https://docs.astral.sh/uv/concepts/projects/dependencies/
[uv tools]: https://docs.astral.sh/uv/guides/tools/
[entry points]: https://packaging.python.org/en/latest/specifications/entry-points/
