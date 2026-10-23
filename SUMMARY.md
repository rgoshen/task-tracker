# Summary

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
