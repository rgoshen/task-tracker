# Summary

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
