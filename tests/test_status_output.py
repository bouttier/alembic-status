import pytest

from tests.project import MigrationProject, expected_scenarios, load_expected
from tests.test_core import _status


def _apply_state(project: MigrationProject, name: str, state: str) -> None:
    if state == "partial":
        project.upgrade(load_expected(name)["partial_base"])
    elif state == "up_to_date":
        project.upgrade("heads")


@pytest.mark.parametrize(
    "name, state",
    [
        (name, state)
        for name in expected_scenarios()
        for state in ("initial", "partial", "up_to_date")
    ],
)
def test_full_status_output(make_scenario, name, state):
    project = make_scenario(name)
    _apply_state(project, name, state)

    assert _status(project).text == load_expected(name)[state]
