# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

`task-tracker` is a Python 3.14 CLI for task management, currently an early scaffold.
`README.md` is the product spec (task fields, status/priority enums, the seven features); the code implements only the task model and storage so far (M1, M2), none of the seven features.
What exists: a placeholder `main()` in `src/task_tracker/__init__.py`, the `Status` / `Priority` `StrEnum`s, the `Task` dataclass in `src/task_tracker/task.py` (with `Task.restore` for rebuilding a stored task), and `load` / `save` in `src/task_tracker/storage.py`.

Labels are reconciled (Q1): users type and see the enum names (`TO_DO`, `IN_PROGRESS`, `DONE`; `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and `Priority.MED` was renamed `MEDIUM` to match `README.md` (M1).

Work is tracked in `docs/implementation-plan.md` (milestones M0 to M9, decisions D1 to D6, spec questions Q1 to Q6) and mirrored by GitHub issues #4 to #13, one per milestone. When a decision or milestone changes, update the plan, the matching issue, and `README.md` together.

## Commands

Package management is `uv`; the Python version is pinned in `.python-version` (3.14.7). `uv sync` and `uv run` include the `dev` dependency group by default.

```bash
uv sync                               # create .venv, install project + dev tools
uv run task-tracker                   # run the CLI (entry point: task_tracker:main)
uv run ruff check .                   # lint (add --fix to autofix)
uv run ruff format .                  # format
uv run pyright                        # type check
uv run pre-commit run --all-files     # every hook: ruff, shellcheck, shfmt, whitespace/yaml
uv run pytest                         # Python tests (see Testing)
./scripts/test_bump_version.sh        # regression suite for bump-version.sh (see below)
uv build                              # wheel + sdist into dist/
```

Ruff and pyright have no config in `pyproject.toml`, so both run on defaults. Ruff 0.16's defaults include `DTZ005`, which flags `datetime.now()`. D6 chose naive local time, so suppress it per line with a comment saying why, not project-wide.

Run the full lint workflow locally with [act](https://github.com/nektos/act) (from `README.md`):

```bash
act push -j build --container-architecture linux/amd64 --env RUN_LOCAL=true --env DEFAULT_BRANCH=main
```

## Testing

Python tests use pytest with pytest-cov (D4) and live in `tests/`. Run them with `uv run pytest`; add `--cov=task_tracker --cov-report=term-missing --cov-fail-under=80` for coverage. Work test-first: watch each test fail for the expected reason before writing the code that passes it.

The bump script has its own tests, `scripts/test_bump_version.sh`, a dependency-free Bash self-check. It builds throwaway Git repos in `mktemp` dirs, seeds them with Conventional Commits, runs `bump-version.sh`, and asserts the bump level and `CHANGELOG.md` contents. It needs `uv` on `PATH`. There is no single-test flag; to run one case, comment out the other calls at the bottom of the file.

## Release automation (spans three files)

Versioning is driven entirely by Conventional Commit messages, so commit message format is load-bearing here, not cosmetic.

- `scripts/bump-version.sh` scans commits since the last Git tag (no tags exist yet, so the whole history). `type!:` or a `BREAKING CHANGE:` footer gives major, `feat` gives minor, `fix` gives patch.
  Any other type (`chore`, `docs`, ...) is ignored, and with nothing to bump the script exits silently with no output. Otherwise it runs `uv version --bump`, prepends a grouped Added/Fixed/Changed entry to `CHANGELOG.md` (created on first bump), and prints the new version.
- The scope pattern is `[a-z0-9_-]+`, so `feat(API):` or `fix(task.sort):` will not be recognized as a feat/fix. It also looks inside squash-merge bullet lines (`* feat: ...`), so one squashed commit can contribute several entries.
- `.github/workflows/version-bump.yml` runs the script only when a PR is merged into `main` from a `release/*` or `hotfix/*` branch. It then commits `pyproject.toml`, `uv.lock`, and `CHANGELOG.md` as `chore(release): vX.Y.Z`, tags it, and pushes both straight to `main`. Don't hand-edit the version or `CHANGELOG.md`.
- `scripts/test_bump_version.sh` is the regression suite for the script. Update it whenever the bump rules change.

## Lint and CI conventions

- `.github/workflows/super-linter.yml` (super-linter v8.7.0) runs on every push and PR and excludes `.serena/` and `.claude/`. Third-party actions are pinned to full commit SHAs with a version comment. Keep that when bumping them.
- `.github/workflows/tests.yml` runs `uv sync --locked` and `uv run pytest` on every push and PR with read-only permissions. A `pytest` run that collects no tests exits with code 5 and fails the job.
- Super-linter runs markdownlint (lines up to 400 characters) and textlint's terminology rule on every Markdown file, and pre-commit does not. Check Markdown locally before pushing, or the PR fails on wording such as `README` without its `.md` or the unhyphenated `Tradeoffs`.
- Super-linter also runs pylint, isort, black, flake8, and mypy on Python files, each with its own pinned version and defaults, separately from ruff and pyright. They first mattered with the `Task` model: `ruff check` passed while pylint scored 8.67 and isort failed. Run them locally at the versions in the CI log before pushing Python.
- `.github/linters/.isort.cfg` marks `task_tracker` as first-party, because isort does not see the `src` layout and would otherwise reject the usual empty line before project imports. Pylint suppressions are inline with the reason beside them, like the ruff `DTZ005` one; do not loosen the rules project-wide.
- `.github/linters/.ruff.toml` sets `line-length = 88`. The super-linter template says 120, which disagrees with local ruff and with the `black` check, so a call between 89 and 120 characters failed one formatter or the other. CI also runs an older ruff (0.15.17) than the lockfile, so check with `uvx ruff==0.15.17 format --config .github/linters/.ruff.toml --check`.
- Pre-commit runs `ruff-check --fix`, `ruff-format` (also on Markdown), `shellcheck`, and `shfmt`. Shell scripts are tab-indented because that is shfmt's default.
- `# ponytail:` comments mark deliberate shortcuts and name their ceiling and upgrade path (see `bump-version.sh`). Read the note before "fixing" one.
