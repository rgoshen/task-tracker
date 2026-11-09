# Py Task Tracker

[![Lint](https://github.com/rgoshen/task-tracker/actions/workflows/super-linter.yml/badge.svg?branch=main)](https://github.com/rgoshen/task-tracker/actions/workflows/super-linter.yml)
[![Tests](https://github.com/rgoshen/task-tracker/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/rgoshen/task-tracker/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/github/license/rgoshen/task-tracker)](https://github.com/rgoshen/task-tracker/blob/main/LICENSE)
[![Latest tag](https://img.shields.io/github/v/tag/rgoshen/task-tracker)](https://github.com/rgoshen/task-tracker/tags)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/rgoshen/task-tracker/main/pyproject.toml)](https://github.com/rgoshen/task-tracker/blob/main/pyproject.toml)

## Requirements

- Type: CLI

- Task Status (enum)
  - `TO_DO`
  - `IN_PROGRESS`
  - `DONE`
- Priority (enum)
  - `CRITICAL`
  - `HIGH`
  - `MEDIUM`
  - `LOW`
- Manage tasks
  - Create tasks
  - Read tasks
  - Update tasks
  - Delete tasks

- Task object
  - ID (auto gen: highest existing ID + 1) (required)
  - task name (string) (required)
  - task description (string, default empty)
  - created date (datetime, set by the tool when the task is added; never given by the user)
  - updated date (datetime, set by the tool when the task is added and each time it changes; never given by the user)
  - due date (datetime, default null; tasks without one sort last)
  - date completed (datetime, default null; a done task defaults to the moment it was marked done and cannot be given a future date; cleared when a done task is reopened)
  - status (string enum default `TO_DO`)
  - priority (string enum default `LOW`)
  - start time (datetime, default current; never before the created date, never after the stop time or the date completed)
  - stop time (datetime, default current, or the start time if that is later; never before the start time, never after the date completed)
  - every datetime is local time with whole seconds and is stored and shown as `YYYY-MM-DDTHH:MM:SS`, however it is typed (a bare date such as `2026-11-02` means midnight)

## Features

1. install cli app
2. using a flag, create a either project level (default) task listing or a global task listing. The project level listing is `tasks.json` in the current directory unless `--dir PATH` (`-d PATH`) names another directory
3. user sees list of current tasks (status: todo and In Progress) sorted asc by due date (tasks without a due date last) then desc priority using the `list` command
4. user can see a list of all tasks (status: all) show current first sorted by due date (asc, tasks without a due date last) then priority (desc) then completed tasks sorted completed date (asc) using `list --all`
5. user should be able to create a new task using the `add` command
6. user should be able update a created task using the `update` command
7. user should be able to delete a created task using the `delete` command, after a confirmation prompt that shows the task name

## Options

Every option has a long and a short form.

| Long          | Short |
| ------------- | ----- |
| `--dir PATH`  | `-d`  |
| `--global`    | `-g`  |
| `--priority`  | `-p`  |
| `--due`       | `-D`  |
| `--status`    | `-s`  |
| `--name`      | `-n`  |
| `--all`       | `-a`  |
| `--clear-due` | `-C`  |

## App requirements

- Python version: >=3.14
- Storage format: JSON
- Project task list: `tasks.json` in the current directory, or in the directory named by `--dir`
- Global task list: `tasks.json` in `~/.task-tracker/`
- Dates and times: naive local time, stored as ISO 8601 strings
- Interrupted saves: a save writes a temporary file next to the list and renames it over the list. If the process is killed at that moment, a hidden `.tasks.json.*.tmp` file is left behind. It is safe to delete, and `.tasks.json.*.tmp` belongs in `.gitignore` when the list lives in a Git repository

### Developer requirements

- ruff version: >=0.16.6
- pyright version: >=1.1.411
- Test runner: pytest with pytest-cov (added in M1)

## Commands

### Adding, listing, updating and deleting tasks

```bash
uv run task-tracker add "Pay rent" --priority HIGH --due 2026-11-02
uv run task-tracker list
uv run task-tracker list --all
uv run task-tracker update 1 --status DONE
uv run task-tracker delete 1
uv run task-tracker --global add "Renew passport"
uv run task-tracker --dir ~/groceries list
```

- Which list a command works on: with no option, `tasks.json` in the current directory. `--global` (`-g`) selects `tasks.json` in `~/.task-tracker/`, and `--dir PATH` (`-d`) selects `tasks.json` in `PATH`. They cannot be given together.
  `--dir` takes a relative `PATH` from the current directory and expands a leading `~` (a shell does not expand it in `--dir=~/x`). The first `add` creates a missing directory; `list` on one that does not exist prints the empty-list message and creates nothing.
  Both options go before the command: `task-tracker --global add "Milk"`. After the command they are refused, so a slip such as `add "Milk" -d 2026-11-02` (for `-D`) creates nothing.
- `add NAME` stores a task in the chosen list and prints its ID. `--priority` (`-p`) takes `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` and defaults to `LOW`. `--due` (`-D`) takes `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`, in local time: a value with a UTC offset is refused.
- `list` shows the current tasks, one per line: ID, status, priority, due date (`-` when there is none), and name. The earliest due date comes first and tasks without one come last, then the highest priority, then the lowest ID. When nothing is current it says so and names the file it read.
  A name is shown with control characters and text-direction controls as escapes (`\n`, `\x1b`, `\u202e`), so one task is always one line and a shared file cannot change how a line is drawn.
- `list --all` (`-a`) shows every task: the current tasks first, in the order above, then the done tasks by date completed, the earliest first, then the lowest ID. The lines are the same, so the date completed is not shown; it only sets the order.
  When the file holds no tasks it prints `No tasks in <path>`. Plain `list` still prints `No current tasks in <path>` when nothing is current, including when every task is done.
- `update ID` changes one stored task in the chosen list and prints one line, `Updated task ID: NAME`, where `NAME` is the name after the change.
  `--name` (`-n`), `--priority` (`-p`), `--status` (`-s`), and `--due` (`-D`) change those fields, and `--clear-due` (`-C`) removes the due date. `--due` and `--clear-due` cannot be given together. `ID` is a whole number of 1 or more in plain digits: a sign, a space, an underscore, or `0` is a bad value.
  Giving a task the values it already has changes nothing: the file is not written, `updated` does not move, and the line is `No change to task ID: NAME` (exit code 0). Moving a task to `DONE` sets its date completed to now, or to its stop time if the clock is behind it (after a change of time zone, for one). `updated` likewise never moves back.
  Moving a `DONE` task to `TO_DO` or `IN_PROGRESS` clears it, and `DONE` to `DONE` keeps the original. `created`, the ID, `description`, `start`, and `stop` cannot be changed by `update`.
  A change the task rules refuse, or an `update` with no option to change, is refused and the file is left unchanged.
- `delete ID` removes one stored task from the chosen list. It first asks `Delete task 2: Buy milk? [y/N]`, with the ID and the name, because an ID can be reused: deleting the highest-numbered task frees its ID, so the next `add` gets it again, and the name is the check that you mean the right task.
  Answer `y` or `yes` in any case to delete; any other answer, an empty one included, keeps the task. The line is `Deleted task 2: Buy milk` or `Kept task 2: Buy milk`, and a kept task leaves the file unchanged.
  The prompt goes to standard output, so it is not visible when standard output is redirected to a file. A script can answer on standard input (`echo y | task-tracker delete 1`); a `--yes` flag is not built.
  With no answer (standard input empty, at its end, not valid text or closed; standard output or error closed; Ctrl-C), nothing is deleted and the command exits with code 1. On a terminal the error starts on its own line.
  If the task changed or was removed while the prompt was open, nothing is deleted and the command exits with code 1.
- Exit codes: 0 on success, 2 for a bad option value (an unknown priority or status, a `--due` that is not a local date or date and time, an ID that is not a whole number of 1 or more, `--due` given with `--clear-due`, `--dir` given with `--global`, an empty `--dir`, or `--global` or `--dir` after the command).
  1 for anything else that goes wrong (a blank name or one UTF-8 cannot hold, a change the task rules refuse, no task with the given ID, an `update` with no option to change, no answer to a `delete` prompt, a task that changed while `delete` was prompting, a corrupt or unreadable task file, an output that cannot be written,
  a home directory that cannot be found or is not an absolute path, for `--global` or for the `~` of a `--dir`, or a `~name` with no such user).
  An error prints one line on standard error and never a traceback.
- `add`, `update` and `delete` store their change before they print, so an error about the output means the change is stored. A reader that closes the pipe early (`task-tracker list | head -1`) ends the output quietly, with exit code 1. With standard output closed (`task-tracker list >&-`) there is nowhere to print, and `add`, `update` and `list` finish with exit code 0.
  `delete` needs standard output for its prompt, so with it closed `delete` exits with code 1 and deletes nothing.
- Two `add`, `update` or `delete` commands running at the same moment can lose a change: each reads and rewrites the whole list, and there is no lock yet ([#27](https://github.com/rgoshen/task-tracker/issues/27)).

### Running GitHub Actions locally

> NOTE: Must have [act](https://github.com/nektos/act) installed already

```bash
act push -j build \
  --container-architecture linux/amd64 \
  --env RUN_LOCAL=true \
  --env DEFAULT_BRANCH=main
```
