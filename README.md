# Py Task Tracker

## Requirements

- Type: CLI

- Task Status (enum)
  - To-do
  - In Progress
  - Done
- Priority (enum)
  - Critical
  - High
  - Medium
  - Low
- Manage tasks
  - Create tasks
  - Read tasks
  - Update tasks
  - Delete tasks

- Task object
  - id (auto gen) (required)
  - task name (string) (required)
  - task description (string)
  - created date (default current)
  - updated date (default current)
  - due date (default current)
  - date completed (default null)
  - status (string enum default To-do)
  - priority (string enum default Low)
  - start time (default current)
  - stop time (default current)

## Features

1. user sees list of current tasks (status: To-do and In Progress) sorted asc by due date then desc priority  using flags
2. user can see a list of all tasks (status: all) show current first sorted by due date (asc) then priority (desc) then completed tasks sorted completed date (asc) using flags
3. user should be able to create a new task using flag
4. user should be able update a created task using flag
5. user should be able to delete a created task using flag
