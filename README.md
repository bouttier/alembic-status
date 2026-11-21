# alembic-status

Shows the status of [alembic](https://alembic.sqlalchemy.org/) branches and upgrades outdated
branches, with the `status` and `autoupgrade` sub-commands.

The project works:

- **with alembic alone**, via the `alembic-status` command or the Python API;
- **with Flask-Migrate** (optional), where the sub-commands are added to the `flask db` group.

## Origin

The `status` and `autoupgrade` sub-commands were initially developed for the
[GeoNature](https://github.com/pnx-si/geonature) project. The original code is in
[`utils_flask_sqla/commands.py`](https://github.com/PnX-SI/Utils-Flask-SQLAlchemy/blob/master/src/utils_flask_sqla/commands.py).

## Installation

The project is published on [PyPI](https://pypi.org/project/alembic-status/) and requires Python 3.11 or later.

```bash
# Without Flask (alembic + SQLAlchemy + click)
pip install alembic-status

# With the Flask-Migrate integration
pip install "alembic-status[flask]"
```

To install from the sources (development version):

```bash
pip install /path/to/alembic-status
```

For development, with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --all-groups
uv run pytest
```

## Usage

### Standalone command line

By default, the command reads `alembic.ini` in the current directory and uses its
`script_location` and `sqlalchemy.url`.

```bash
alembic-status                        # same as "status": all branches
alembic-status status --deps main     # only the "main" branch, with dependencies
alembic-status autoupgrade            # upgrades started branches that are outdated
```

Global options:

| Option | Role |
| --- | --- |
| `-c, --config` | alembic configuration file (default: `alembic.ini`) |
| `-d, --directory` | overrides `script_location` |
| `--url` | overrides `sqlalchemy.url` for the connection used by `status` and `autoupgrade` |

`autoupgrade` accepts `--sql`, `--tag` and `-x`, with the same meaning as in alembic.

### `status` sub-command

`status` shows every branch of the project and whether each revision is applied in the
database. `--deps` adds the `depends_on` dependencies, and a branch name restricts the output to
that branch.

#### Example output

Project with three branches: `main` (applied up to `a2`), `billing` (depends on `a2`, not
started) and `reporting` (depends on `a1`, not started). Command: `alembic-status status --deps`

```text
[billing]
  [ ] ┰ b1 migration b1
        └ (main) a2 migration a2
  [ ] ┸ b2 migration b2
[main ×]
  [x] ┰ a1 migration a1
  [x] ┃ a2 migration a2
  [ ] ┸ a3 migration a3
[reporting]
  [ ] ┰ c1 migration c1
  [ ] ┸ c2 migration c2
        └ (main) a1 migration a1
Some branches are outdated, run 'autoupgrade' to upgrade them.
```

After `alembic-status autoupgrade`, the `main` branch is up to date, while `billing` and
`reporting` are untouched because they were never applied:

```text
[billing]
  [ ] ┰ b1 migration b1
  [ ] ┸ b2 migration b2
[main ✓]
  [x] ┰ a1 migration a1
  [x] ┃ a2 migration a2
  [x] ┸ a3 migration a3
[reporting]
  [ ] ┰ c1 migration c1
  [ ] ┸ c2 migration c2
```

Legend:

- `[x]`: revision applied in the database, `[ ]`: not applied.
- `[branch ✓]`: branch started and up to date; `[branch ×]`: branch started but outdated
  (unapplied revisions are shown in red in a terminal); `[branch]`: branch never started.
- `└ (branch) revision`: `depends_on` dependency (only with `--deps`).

### `autoupgrade` sub-command

`autoupgrade` upgrades the outdated branches to their head:

- it only handles branches that are already started, that is branches with at least one applied
  revision; branches never started are left untouched;
- for each started branch, it moves each unapplied head to the head, since a branch can fork;
- it never touches the other branches.

### Python API

```python
from alembic.config import Config
from sqlalchemy import create_engine

from alembic_status import autoupgrade, get_status

config = Config("alembic.ini")
engine = create_engine("postgresql://user:password@localhost/app")

with engine.connect() as connection:
    report = get_status(config, connection, show_dependencies=True)
    print(report.text)
    if report.outdated:
        autoupgrade(config, connection)
```

`get_status` returns a `StatusReport` (`text` and `outdated`). The `style` parameter allows
coloring the output, for example with `click.style`. Without `style`, the output is plain text.

### Flask-Migrate integration

Call `register_commands()` once, after the application and Flask-Migrate have been created
(for example in the application factory or in the module that defines the CLI):

```python
from flask_migrate import Migrate

from alembic_status.flask_cli import register_commands

migrate = Migrate(app, db)
register_commands()
```

The commands then become available:

```bash
flask db status --deps
flask db autoupgrade
```

They accept the same options as the standalone version, with `-d/--directory` for the
migrations directory (default: `migrations`). The connection comes from the Flask-SQLAlchemy
session, and the configuration from Flask-Migrate.

## Limitations

These limitations are checked at startup: an unsupported situation raises an explicit
`ValueError`, instead of displaying a wrong result.

1. **No loops between branches.** A branch cannot depend, directly or indirectly, on a branch
   that depends on it. Rejected example: `x2` depends on `y1`, and `y2` depends on `x1`.
   Message: `Branches depend on each other in a loop (xx -> yy -> xx)`.
   One-way dependencies are supported: several branches can depend on the same branch, or
   start from a revision in the middle of another branch.
2. **No merging of branches.** A merge revision that joins two labeled branches
   (`down_revision = ("p2", "q2")` with `p2` and `q2` in two different branches) is rejected.
   Message: `belongs to several branches`. Forks and merges inside a single branch are
   supported (this is the case of `fork_and_merge` in the tests).
3. **Each branch has a labeled base.** The base of each branch must carry exactly one
   `branch_labels` value, which the other revisions of the branch inherit. A base without a
   label (for example an initial migration without a label) is rejected. All bases must
   therefore be labeled.
4. **Upgrades are not atomic across branches.** `autoupgrade` runs one `command.upgrade` per
   unapplied head. If one fails, the previous ones remain applied.
5. **The database read must be the one used by `env.py`.** `status` and `autoupgrade` read the
   state through the provided connection (`sqlalchemy.url` or `--url`), while `autoupgrade`
   runs the migrations through your `env.py`. Both must point to the same database.

## Tests

```bash
uv run pytest
```

The GitHub Actions workflows (`.github/workflows/`) run the following in CI:

- `ruff check` and `ruff format --check`;
- `pytest` on Python 3.11 to 3.15, with Flask;
- `pytest` without Flask, to verify that the standalone mode works.

The tests use real alembic projects stored in `tests/scenarios/<name>/` (`alembic.ini`,
`env.py`, `versions/`), with a SQLite database. Each test copies a scenario to a temporary
directory before touching the database. Scenarios with an `expected.toml` file list the expected
`status` output for their initial, partially applied and up-to-date states.

The scenarios are:

- `empty`: no revisions;
- `linear`: a single linear branch;
- `two_branches`: two independent branches;
- `fork`: a fork inside a branch;
- `fork_and_merge`: a fork and merge inside a branch;
- `cross_branch_depends`: a branch depends on a revision of another branch;
- `branch_from_middle`: a branch starts from the middle of another branch;
- `three_branches`: three branches, two of which depend on the first;
- `unlabeled_base`, `merged_branches`, `branch_loop`: rejected graphs (unlabeled base, branch
  merge, loop between branches);
- the standalone CLI, and the `flask db` sub-commands (skipped if Flask is not installed).

### Trying a scenario by hand

Each scenario can be run with the alembic command, from its directory:

```bash
cd tests/scenarios/fork
alembic upgrade c1
alembic-status
```

The database is created as `app.db` in the scenario directory (ignored by git).

## Publishing to PyPI

1. Update `version` in `pyproject.toml`, then commit.
2. Create and push a `vX.Y.Z` tag matching the version.
3. The `publish.yml` workflow runs the tests, checks that the tag matches the version, builds
   the project, then publishes it to PyPI.

## License

GPL-3.0-or-later, see [LICENSE](LICENSE). Copyright holders are listed in [NOTICE](NOTICE).
