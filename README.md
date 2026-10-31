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
  - start time (datetime, default current; never before the created date)
  - stop time (datetime, default current, or the date completed for a done task; never after the date completed)
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

| Long         | Short |
| ------------ | ----- |
| `--dir PATH` | `-d`  |
| `--global`   | `-g`  |
| `--priority` | `-p`  |
| `--due`      | `-D`  |
| `--status`   | `-s`  |
| `--name`     | `-n`  |
| `--all`      | `-a`  |

## App requirements

- Python version: >=3.14
- Storage format: JSON
- Project task list: `tasks.json` in the current directory, or in the directory named by `--dir`
- Global task list: `tasks.json` in `~/.task-tracker/`
- Dates and times: naive local time, stored as ISO 8601 strings

### Developer requirements

- ruff version: >=0.16.6
- pyright version: >=1.1.411
- Test runner: pytest with pytest-cov (added in M1)

## Commands

### Running GitHub Actions locally

> NOTE: Must have [act](https://github.com/nektos/act) installed already

```bash
act push -j build \
  --container-architecture linux/amd64 \
  --env RUN_LOCAL=true \
  --env DEFAULT_BRANCH=main
```
