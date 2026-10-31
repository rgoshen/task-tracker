"""Tests for the Priority enum."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import pytest

from task_tracker.priority import Priority


@pytest.mark.parametrize("name", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
def test_every_priority_name_the_readme_promises_can_be_parsed(name: str):
    member = Priority[name]

    assert member.name == name
    assert Priority(name) is member
