# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

`task-tracker` is a Python 3.14 CLI for task management, currently an early scaffold. `README.md` is the product spec (task fields, status/priority enums, the seven features); the code implements almost none of it yet. What exists: a placeholder `main()` in `src/task_tracker/__init__.py` and the `Status` / `Priority` `StrEnum`s.

The README spec and the enums disagree on labels (README: "To-do", "Medium"; code: `TO_DO`, `MED`). Reconcile deliberately rather than assuming either is canonical.

## Commands

Package management is `uv`; the Python version is pinned in `.python-version` (3.14.7). `uv sync` and `uv run` include the `dev` dependency group by default.

```bash
uv sync                               # create .venv, install project + dev tools
uv run task-tracker                   # run the CLI (entry point: task_tracker:main)
uv run ruff check .                   # lint (add --fix to autofix)
uv run ruff format .                  # format
uv run pyright                        # type check
uv run pre-commit run --all-files     # every hook: ruff, shellcheck, shfmt, whitespace/yaml
./scripts/test_bump_version.sh        # the only test suite today (see below)
uv build                              # wheel + sdist into dist/
```

Ruff and pyright have no config in `pyproject.toml`, so both run on defaults.

Run the full lint workflow locally with [act](https://github.com/nektos/act) (from the README):

```bash
act push -j build --container-architecture linux/amd64 --env RUN_LOCAL=true --env DEFAULT_BRANCH=main
```

## Testing

No Python test framework is installed (no pytest in the dev group) and `tests/` is empty. Adding Python tests means adding a runner as a dev dependency first.

The only tests are `scripts/test_bump_version.sh`, a dependency-free bash self-check. It builds throwaway git repos in `mktemp` dirs, seeds them with Conventional Commits, runs `bump-version.sh`, and asserts the bump level and `CHANGELOG.md` contents. It needs `uv` on `PATH`. There is no single-test flag; to run one case, comment out the other calls at the bottom of the file.

## Release automation (spans three files)

Versioning is driven entirely by Conventional Commit messages, so commit message format is load-bearing here, not cosmetic.

- `scripts/bump-version.sh` scans commits since the last git tag (no tags exist yet, so the whole history). `type!:` or a `BREAKING CHANGE:` footer gives major, `feat` gives minor, `fix` gives patch. Any other type (`chore`, `docs`, ...) is ignored, and with nothing to bump the script exits silently with no output. Otherwise it runs `uv version --bump`, prepends a grouped Added/Fixed/Changed entry to `CHANGELOG.md` (created on first bump), and prints the new version.
- The scope regex is `[a-z0-9_-]+`, so `feat(API):` or `fix(task.sort):` will not be recognized as a feat/fix. It also looks inside squash-merge bullet lines (`* feat: ...`), so one squashed commit can contribute several entries.
- `.github/workflows/version-bump.yml` runs the script only when a PR is merged into `main` from a `release/*` or `hotfix/*` branch. It then commits `pyproject.toml`, `uv.lock`, and `CHANGELOG.md` as `chore(release): vX.Y.Z`, tags it, and pushes both straight to `main`. Don't hand-edit the version or `CHANGELOG.md`.
- `scripts/test_bump_version.sh` is the regression suite for the script. Update it whenever the bump rules change.

## Lint and CI conventions

- `.github/workflows/super-linter.yml` (super-linter v8.7.0) runs on every push and PR and excludes `.serena/` and `.claude/`. Third-party actions are pinned to full commit SHAs with a version comment. Keep that when bumping them.
- Pre-commit runs `ruff-check --fix`, `ruff-format` (also on markdown), `shellcheck`, and `shfmt`. Shell scripts are tab-indented because that is shfmt's default.
- `# ponytail:` comments mark deliberate shortcuts and name their ceiling and upgrade path (see `bump-version.sh`). Read the note before "fixing" one.
