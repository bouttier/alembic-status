from collections.abc import Callable
from pathlib import Path

import pytest

from tests.project import MigrationProject


@pytest.fixture
def make_scenario(tmp_path: Path) -> Callable[[str], MigrationProject]:
    def factory(name: str) -> MigrationProject:
        return MigrationProject.from_scenario(name, tmp_path / name)

    return factory
