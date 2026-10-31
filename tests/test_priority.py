import pytest

from task_tracker.priority import Priority


@pytest.mark.parametrize("name", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
def test_every_priority_name_the_readme_promises_can_be_parsed(name: str):
    assert Priority(name).value == name
