from click.testing import CliRunner

from alembic_status.cli import main


def test_status_command(make_scenario):
    project = make_scenario("two_branches")
    project.upgrade("a1")

    result = CliRunner().invoke(main, ["-c", str(project.ini), "status"])

    assert result.exit_code == 0, result.output
    assert result.output.startswith("[alpha ×]\n  [x] ┰ a1 migration a1\n")
    assert "run 'autoupgrade' to upgrade them." in result.output


def test_no_subcommand_shows_status(make_scenario):
    project = make_scenario("two_branches")
    project.upgrade("a1")

    bare = CliRunner().invoke(main, ["-c", str(project.ini)])
    explicit = CliRunner().invoke(main, ["-c", str(project.ini), "status"])

    assert bare.exit_code == 0, bare.output
    assert bare.output == explicit.output


def test_status_command_branch_argument_and_deps(make_scenario):
    project = make_scenario("cross_branch_depends")
    project.upgrade("d1")

    result = CliRunner().invoke(main, ["-c", str(project.ini), "status", "--deps", "epsilon"])

    assert result.exit_code == 0, result.output
    assert "[epsilon]" in result.output
    assert "[delta" not in result.output
    assert "└ (delta) d1 migration d1" in result.output


def test_autoupgrade_command(make_scenario):
    project = make_scenario("two_branches")
    project.upgrade("a1")

    result = CliRunner().invoke(main, ["-c", str(project.ini), "autoupgrade"])

    assert result.exit_code == 0, result.output
    assert project.applied() == {"a2"}


def test_url_option_overrides_config(make_scenario, tmp_path):
    project = make_scenario("linear")
    project.upgrade("l1")
    other_url = f"sqlite:///{tmp_path / 'other.db'}"

    result = CliRunner().invoke(main, ["-c", str(project.ini), "--url", other_url, "status"])

    assert result.exit_code == 0, result.output
    assert "[x]" not in result.output
    assert project.applied() == {"l1"}


def test_missing_url_is_a_usage_error(make_scenario):
    project = make_scenario("linear")
    project.ini.write_text(f"[alembic]\nscript_location = {project.root}\n")

    result = CliRunner().invoke(main, ["-c", str(project.ini), "status"])

    assert result.exit_code == 2
    assert "No database URL" in result.output
