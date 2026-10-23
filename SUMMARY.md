# Summary

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
