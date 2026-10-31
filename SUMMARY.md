# Summary

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
