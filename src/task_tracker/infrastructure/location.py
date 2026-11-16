"""Which list file a command works on: project, global, or a chosen directory."""

from pathlib import Path

# D2: the project list is `tasks.json` in the current directory; the global list is
# the same file name inside `.task-tracker` in the home directory.
_LIST_FILE = "tasks.json"
_GLOBAL_DIR = ".task-tracker"


class HomeDirectoryError(ValueError):
    """The home directory is needed and cannot be found or used.

    The message gives the reason only. What the user can do instead depends on how
    the program was started, so the caller adds that.
    """


def _expanded(path: Path) -> Path:
    """Return `path` with a leading `~` replaced by the home directory it names.

    A shell expands `~` in `--dir ~/x` but not in `--dir=~/x`, which would make a
    directory literally named `~`, so the program expands it. `--global` is the
    path `~/.task-tracker/tasks.json`, so it goes through here too.
    """
    try:
        expanded = path.expanduser()
    except RuntimeError:
        # A caller handles ValueError and does not catch RuntimeError, on purpose: a
        # bug elsewhere must stay visible. `expanduser` raises it when there is no
        # home directory to find:
        # HOME unset and no password-file entry (a container started with an
        # arbitrary user ID), or `~name` for a user who does not exist.
        problem = "no home directory found"
    else:
        # A relative HOME would put the "global" list under whichever directory the
        # command runs in. A `path` without `~` comes back unchanged and may be relative.
        if expanded == path or expanded.is_absolute():
            return expanded
        problem = "the home directory is not an absolute path"
    raise HomeDirectoryError(f"cannot expand {str(path)!r}: {problem}")


def list_path(*, use_global: bool, directory: Path | None) -> Path:
    """Return the list file a command works on.

    That is the global list for `use_global`, `directory/tasks.json` for a chosen
    directory, and the list in the current directory for neither. Both together
    raise `ValueError`: one of them would have to be ignored, and the caller would
    work on a list it did not choose.
    """
    if use_global and directory is not None:
        raise ValueError("the global list and a directory cannot be chosen together")
    if use_global:
        return _expanded(Path("~") / _GLOBAL_DIR / _LIST_FILE)
    if directory is not None:
        # `absolute()` joins a relative path to the cwd and leaves an absolute one
        # alone without reading the cwd, which `Path.cwd() / directory` would do.
        return _expanded(directory).absolute() / _LIST_FILE
    return Path.cwd() / _LIST_FILE
