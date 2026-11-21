import subprocess
import sys

import pytest
from sqlalchemy import create_engine

from alembic_status import autoupgrade, get_status
from tests.project import (
    MigrationProject,
    RevisionSpec,
    expected_scenarios,
    load_expected,
    load_specs,
)

SCENARIO_NAMES = expected_scenarios()


def _bases(specs: list[RevisionSpec]) -> list[str]:
    return [revision for revision, down, _, _ in specs if down is None]


def _heads(specs: list[RevisionSpec]) -> set[str]:
    referenced = {down for _, down, _, _ in specs if isinstance(down, str)}
    referenced |= {parent for _, down, _, _ in specs if isinstance(down, tuple) for parent in down}
    return {revision for revision, _, _, _ in specs} - referenced


def _status(project: MigrationProject, **kwargs):
    engine = create_engine(project.url)
    try:
        with engine.connect() as connection:
            return get_status(project.config(), connection, **kwargs)
    finally:
        engine.dispose()


def _autoupgrade(project: MigrationProject) -> list[str]:
    engine = create_engine(project.url)
    try:
        with engine.connect() as connection:
            return autoupgrade(project.config(), connection)
    finally:
        engine.dispose()


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_status_nothing_applied(make_scenario, name):
    specs = load_specs(name)
    report = _status(make_scenario(name))

    assert not report.outdated
    assert "✓" not in report.text
    assert "×" not in report.text
    for revision, *_ in specs:
        assert f"{revision} migration {revision}" in report.text


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_status_outdated_after_partial_upgrade(make_scenario, name):
    project = make_scenario(name)
    base = load_expected(name)["partial_base"]
    project.upgrade(base)

    report = _status(project)

    assert report.outdated
    assert "×" in report.text
    applied_lines = [line for line in report.text.splitlines() if "[x]" in line]
    assert len(applied_lines) == 1
    assert f" {base} migration" in applied_lines[0]


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_status_up_to_date_after_full_upgrade(make_scenario, name):
    specs = load_specs(name)
    project = make_scenario(name)
    project.upgrade("heads")

    report = _status(project)

    assert not report.outdated
    assert "×" not in report.text
    assert report.text.count("✓") == len(_bases(specs))
    # A revision only used as a depends_on target is not stored, alembic covers it implicitly.
    assert project.applied() <= _heads(specs)


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_autoupgrade_is_noop_when_up_to_date(make_scenario, name):
    project = make_scenario(name)
    project.upgrade("heads")
    before = project.applied()

    assert _autoupgrade(project) == []
    assert project.applied() == before


@pytest.mark.parametrize(
    "name, expected_targets, expected_applied",
    [
        ("linear", ["l3"], {"l3"}),
        ("two_branches", ["a2"], {"a2"}),
        ("fork", ["c3a", "c3b"], {"c3a", "c3b"}),
        ("fork_and_merge", ["c4"], {"c4"}),
        ("cross_branch_depends", ["d2"], {"d2"}),
        ("branch_from_middle", ["m2"], {"m2"}),
        ("three_branches", ["p2"], {"p2"}),
    ],
)
def test_autoupgrade_moves_started_branch_to_head(
    make_scenario, name, expected_targets, expected_applied
):
    project = make_scenario(name)
    project.upgrade(load_expected(name)["partial_base"])

    targets = _autoupgrade(project)

    assert targets == expected_targets
    assert project.applied() == expected_applied
    assert not _status(project).outdated


def test_autoupgrade_only_upgrades_outdated_branches(make_scenario):
    project = make_scenario("two_branches")
    project.upgrade("a2")
    project.upgrade("b1")

    assert _autoupgrade(project) == ["b2"]
    assert project.applied() == {"a2", "b2"}


def test_autoupgrade_completes_partially_applied_fork(make_scenario):
    project = make_scenario("fork")
    project.upgrade("c3a")
    assert _status(project).outdated

    assert _autoupgrade(project) == ["c3b"]
    assert project.applied() == {"c3a", "c3b"}
    assert not _status(project).outdated


def test_status_filters_branches(make_scenario):
    project = make_scenario("two_branches")

    text = _status(project, branches=("beta",)).text

    assert "[beta]" in text
    assert "[alpha]" not in text


def test_status_show_dependencies(make_scenario):
    project = make_scenario("cross_branch_depends")
    project.upgrade("d1")

    assert "(delta) d1 migration d1" not in _status(project).text
    assert "└ (delta) d1 migration d1" in _status(project, show_dependencies=True).text


def test_empty_project(make_scenario):
    project = make_scenario("empty")

    report = _status(project)

    assert report.text == ""
    assert not report.outdated
    assert _autoupgrade(project) == []


def test_status_is_deterministic(make_scenario):
    project = make_scenario("fork_and_merge")
    first = _status(project, show_dependencies=True).text

    assert all(_status(project, show_dependencies=True).text == first for _ in range(5))


@pytest.mark.parametrize(
    "name, message",
    [
        ("unlabeled_base", "no branch label"),
        ("merged_branches", "belongs to several branches"),
        ("branch_loop", "depend on each other in a loop"),
    ],
)
def test_unsupported_graphs_are_rejected(make_scenario, name, message):
    project = make_scenario(name)

    with pytest.raises(ValueError, match=message):
        _status(project)
    with pytest.raises(ValueError, match=message):
        _autoupgrade(project)


def test_core_does_not_import_flask():
    code = (
        "import sys, alembic_status, alembic_status.core, alembic_status.cli; "
        "assert not [m for m in sys.modules if m == 'flask' or m.startswith('flask_')]"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
