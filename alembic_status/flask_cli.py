"""Optional Flask-Migrate integration: adds ``status`` and ``autoupgrade`` to ``flask db``.

Requires the ``flask`` extra. Call :func:`register_commands` once, for example in the
application factory or the module that defines the Flask CLI.
"""

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_migrate.cli import db as db_cli

from alembic_status.core import autoupgrade as run_autoupgrade
from alembic_status.core import get_status


@click.command("status")
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "--deps", "--dependencies", "show_dependencies", is_flag=True, help="Show dependencies"
)
@click.argument("branches", nargs=-1)
@with_appcontext
def status_command(directory, show_dependencies, branches):
    """Show all revisions sorted by branches."""
    db = current_app.extensions["sqlalchemy"]
    config = current_app.extensions["migrate"].migrate.get_config(directory)
    report = get_status(
        config,
        db.session.connection(),
        branches=branches,
        show_dependencies=show_dependencies,
        style=click.style,
    )
    click.echo(report.text)


@click.command("autoupgrade")
@click.option(
    "-d",
    "--directory",
    default=None,
    help='Migration script directory (default is "migrations")',
)
@click.option(
    "--sql",
    is_flag=True,
    help="Don't emit SQL to database - dump to standard output instead",
)
@click.option(
    "--tag",
    default=None,
    help='Arbitrary "tag" name - can be used by custom env.py scripts',
)
@click.option(
    "-x", "--x-arg", multiple=True, help="Additional arguments consumed by custom env.py scripts"
)
@with_appcontext
def autoupgrade_command(directory, sql, tag, x_arg):
    """Upgrade all branches to head."""
    db = current_app.extensions["sqlalchemy"]
    config = current_app.extensions["migrate"].migrate.get_config(directory)
    run_autoupgrade(config, db.session.connection(), sql=sql, tag=tag, x_args=x_arg)


def register_commands(group: click.Group | None = None) -> None:
    """Add ``status`` and ``autoupgrade`` to the ``flask db`` group, or to ``group``."""
    target = db_cli if group is None else group
    target.add_command(status_command)
    target.add_command(autoupgrade_command)
