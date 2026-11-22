"""Standalone ``alembic-status`` command, usable without Flask."""

import click
from alembic.config import Config

from alembic_status.core import autoupgrade as run_autoupgrade
from alembic_status.core import get_status


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
    report = get_status(
        config,
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
    run_autoupgrade(config, sql=sql, tag=tag, x_args=x_arg)


if __name__ == "__main__":
    main()
