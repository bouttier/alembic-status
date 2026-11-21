"""Standalone ``alembic-status`` command, usable without Flask."""

from collections.abc import Iterator
from contextlib import contextmanager

import click
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from alembic_status.core import autoupgrade as run_autoupgrade
from alembic_status.core import get_status


@contextmanager
def _connect(config: Config) -> Iterator[Connection]:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise click.UsageError("No database URL: set sqlalchemy.url in the config or pass --url.")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()


@click.group(invoke_without_command=True)
@click.option(
    "-c",
    "--config",
    "config_file",
    default="alembic.ini",
    show_default=True,
    type=click.Path(dir_okay=False, exists=True),
    help="Alembic configuration file.",
)
@click.option(
    "-d",
    "--directory",
    default=None,
    help="Migration script directory (default: script_location of the config file).",
)
@click.option(
    "--url",
    default=None,
    help="Database URL (default: sqlalchemy.url of the config file).",
)
@click.pass_context
def main(ctx: click.Context, config_file: str, directory: str | None, url: str | None) -> None:
    """Show and upgrade alembic branches. Without a sub-command, shows the status."""
    config = Config(config_file)
    if directory:
        config.set_main_option("script_location", directory)
    if url:
        config.set_main_option("sqlalchemy.url", url)
    ctx.obj = config
    if ctx.invoked_subcommand is None:
        ctx.invoke(status, show_dependencies=False, branches=())


@main.command()
@click.option(
    "--deps", "--dependencies", "show_dependencies", is_flag=True, help="Show dependencies"
)
@click.argument("branches", nargs=-1)
@click.pass_obj
def status(config: Config, show_dependencies: bool, branches: tuple[str, ...]) -> None:
    """Show all revisions sorted by branches."""
    with _connect(config) as connection:
        report = get_status(
            config,
            connection,
            branches=branches,
            show_dependencies=show_dependencies,
            style=click.style,
        )
    click.echo(report.text)


@main.command()
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
@click.pass_obj
def autoupgrade(config: Config, sql: bool, tag: str | None, x_arg: tuple[str, ...]) -> None:
    """Upgrade all branches to head."""
    with _connect(config) as connection:
        run_autoupgrade(config, connection, sql=sql, tag=tag, x_args=x_arg)


if __name__ == "__main__":
    main()
