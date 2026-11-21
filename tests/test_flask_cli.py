import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_migrate")
pytest.importorskip("flask_sqlalchemy")

from click.testing import CliRunner
from flask import Flask
from flask_migrate import Migrate
from flask_migrate.cli import db as db_cli
from flask_sqlalchemy import SQLAlchemy

from alembic_status.cli import main as standalone_main
from alembic_status.flask_cli import register_commands


@pytest.fixture
def flask_project(make_scenario):
    def factory(name):
        project = make_scenario(name)
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = project.url
        db = SQLAlchemy(app)
        Migrate(app, db, directory=str(project.root))
        register_commands()
        return app, project

    return factory


def test_flask_db_status_matches_standalone(flask_project):
    app, project = flask_project("two_branches")
    project.upgrade("a1")

    flask_result = app.test_cli_runner().invoke(cli=db_cli, args=["status"])
    standalone_result = CliRunner().invoke(standalone_main, ["-c", str(project.ini), "status"])

    assert flask_result.exit_code == 0, flask_result.output
    assert flask_result.output == standalone_result.output


def test_flask_db_autoupgrade(flask_project):
    app, project = flask_project("two_branches")
    project.upgrade("a1")

    result = app.test_cli_runner().invoke(cli=db_cli, args=["autoupgrade"])

    assert result.exit_code == 0, result.output
    assert project.applied() == {"a2"}


def test_flask_db_status_with_dependencies(flask_project):
    app, project = flask_project("cross_branch_depends")
    project.upgrade("d1")

    result = app.test_cli_runner().invoke(cli=db_cli, args=["status", "--deps"])

    assert result.exit_code == 0, result.output
    assert "└ (delta) d1 migration d1" in result.output
