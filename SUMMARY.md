# Summary

## [2026-10-31 12:07] Commit Summary

**Change Type:** Docs

**Scope:** planning (`TODO.md`)

**Summary:**
Created `TODO.md` with the M1 (Task model) entry: objective, a six-step commit-sized approach, the tests, and risks. No code changed.

**Rationale:**
The plan's "How to work each milestone" requires a `TODO.md` entry before coding starts, and the file did not exist. Two deliberate departures from the plan's M1 checklist order: pytest is added first (every later step is test-first, so a runner must exist), and the CI workflow moves after the model tests, because pytest exits with code 5 when it collects no tests and the first CI run would fail. Both facts were checked against current pytest documentation.
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
`README.md` listed `description` with no default, which left M1's `Task` model underspecified. Chosen with the user on 2026-10-31 from three options. `""` keeps the field a plain `str`, so pyright and display code need no `None` checks, and "no description" has one representation. Rejected: `None` (consistent with `due`, but forces a `str | None` check everywhere it is printed) and leaving the field out of M1 (diverges from the README spec). Whether `add` and `update` expose `--description` stays deferred to M3 and M5, as Q3 did for `start` and `stop`.

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
