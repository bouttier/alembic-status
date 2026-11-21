"""Helpers for the alembic projects used by the tests, with real SQLite databases.

Scenarios live in ``tests/scenarios/<name>/`` as complete alembic projects (``alembic.ini``,
``env.py``, ``versions/``). They can be used by hand, e.g. ``cd tests/scenarios/fork`` then
``alembic history``; tests copy them to a temporary directory before touching the database.
"""

import importlib.util
import shutil
import tomllib
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

SCENARIOS_DIR = Path(__file__).parent / "scenarios"

# (revision, down_revision, branch_labels, depends_on)
RevisionSpec = tuple


def load_specs(name: str) -> list[RevisionSpec]:
    """Read the revisions of scenario ``name``, sorted by file name."""
    specs = []
    for path in sorted((SCENARIOS_DIR / name / "versions").glob("*.py")):
        spec = importlib.util.spec_from_file_location(f"_scenario_{name}_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        specs.append(
            (module.revision, module.down_revision, module.branch_labels, module.depends_on)
        )
    return specs


def expected_scenarios() -> list[str]:
    """Scenarios that come with an expected.toml file."""
    return sorted(p.parent.name for p in SCENARIOS_DIR.glob("*/expected.toml"))


def load_expected(name: str) -> dict[str, str]:
    """Read ``expected.toml``: ``partial_base`` plus the ``output`` of each state
    (``initial``, ``partial``, ``up_to_date``)."""
    data = tomllib.loads((SCENARIOS_DIR / name / "expected.toml").read_text())
    return {
        "partial_base": data["partial_base"],
        # The newline before the closing ''' belongs to the file layout, not to the output.
        **{
            state: data[state]["output"].removesuffix("\n")
            for state in ("initial", "partial", "up_to_date")
        },
    }


class MigrationProject:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.versions = root / "versions"
        self.url = f"sqlite:///{root / 'app.db'}"
        self.ini = root / "alembic.ini"

    @classmethod
    def from_scenario(cls, name: str, dest: Path) -> "MigrationProject":
        """Copy scenario ``name`` to ``dest``; ``%(here)s`` in its alembic.ini points there."""
        ignore = shutil.ignore_patterns("*.db", "__pycache__")
        shutil.copytree(SCENARIOS_DIR / name, dest, ignore=ignore)
        return cls(dest)

    def config(self) -> Config:
        return Config(str(self.ini))

    def upgrade(self, revision: str) -> None:
        command.upgrade(self.config(), revision)

    def applied(self) -> set[str]:
        engine = sa.create_engine(self.url)
        try:
            with engine.connect() as connection:
                if not sa.inspect(connection).has_table("alembic_version"):
                    return set()
                rows = connection.execute(sa.text("SELECT version_num FROM alembic_version"))
                return {row[0] for row in rows}
        finally:
            engine.dispose()
