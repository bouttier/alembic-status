"""Alembic branch status and autoupgrade, without any Flask dependency."""

import argparse
from collections import defaultdict, deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from itertools import chain
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.script.base import Script
from sqlalchemy.engine import Connection

Style = Callable[..., str]

OUTDATED_MESSAGE = "Some branches are outdated, run 'autoupgrade' to upgrade them."


def _no_style(text: str, **_: Any) -> str:
    return text


@dataclass(frozen=True)
class StatusReport:
    text: str
    outdated: bool


def box_drawing(up: bool, down: bool, left: bool, right: bool, bold: bool = True) -> str:
    if not up and not down and not left and not right:
        return "─"
    elif up and not down and not left and not right:
        return "┸"
    elif not up and down and not left and not right:
        return "┰"
    elif up and down and not left and not right:
        return "┃"
    elif up and not down and left and not right:
        return "┛"
    elif up and not down and not left and right:
        return "┗" if bold else "└"
    elif not up and not down:
        return "━"
    elif not up and down and left and not right:
        return "┓"
    elif not up and down and not left and right:
        return "┏"
    elif up and down and not left and right:
        return "┣" if bold else "├"
    elif up and down and left and not right:
        return "┫"
    elif up and not down and left and right:
        return "┻"
    elif not up and down and left and right:
        return "┳"
    elif up and down and left and right:
        return "╋"
    else:
        raise ValueError("Unexpected box drawing symbol")


def set_x_args(config: Config, x_args: Iterable[str]) -> None:
    x_args = list(x_args)
    if x_args:
        config.cmd_opts = argparse.Namespace(x=x_args)


def _branch_label(revision: Script) -> str:
    labels = revision.branch_labels
    if not labels:
        raise ValueError(
            f"Revision {revision.revision} has no branch label. Every branch base needs a "
            "branch_labels entry, see the README."
        )
    if len(labels) > 1:
        found = ", ".join(sorted(labels))
        raise ValueError(
            f"Revision {revision.revision} belongs to several branches ({found}). "
            "Merging branches is not supported, see the README."
        )
    (label,) = labels
    return label


def _parent_ids(revision: Script) -> list[str]:
    parents: list[str] = []
    for value in (revision.down_revision, revision.dependencies):
        if isinstance(value, str):
            parents.append(value)
        elif value:
            parents.extend(value)
    return parents


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    done: set[str] = set()

    def visit(node: str, path: list[str]) -> list[str] | None:
        if node in path:
            return [*path[path.index(node) :], node]
        if node in done:
            return None
        for successor in sorted(graph.get(node, ())):
            cycle = visit(successor, [*path, node])
            if cycle:
                return cycle
        done.add(node)
        return None

    for node in sorted(graph):
        cycle = visit(node, [])
        if cycle:
            return cycle
    return None


def _check_branches(script: ScriptDirectory) -> None:
    """Reject projects whose branches cannot be shown and upgraded independently."""
    depends: dict[str, set[str]] = {}
    for revision in script.walk_revisions():
        label = _branch_label(revision)
        for parent_id in _parent_ids(revision):
            parent_label = _branch_label(script.get_revision(parent_id))
            if parent_label != label:
                depends.setdefault(label, set()).add(parent_label)
    cycle = _find_cycle(depends)
    if cycle:
        raise ValueError(
            "Branches depend on each other in a loop ({}). Loops between branches are not "
            "supported, see the README.".format(" -> ".join(cycle))
        )


class _StatusRenderer:
    def __init__(
        self,
        script: ScriptDirectory,
        bases: dict[str, Script],
        applied: set[Script],
        style: Style,
        show_dependencies: bool,
    ) -> None:
        self.script = script
        self.bases = bases
        self.applied = applied
        self.style = style
        self.show_dependencies = show_dependencies

    def revision_line(
        self,
        lines: list[str],
        prefix: str,
        revision: Script,
        show_branch_label: bool = False,
    ) -> None:
        branch_label = _branch_label(revision)
        branch_base = self.bases[branch_label]
        if branch_base in self.applied:
            fg = "white" if revision in self.applied else "red"
        else:
            fg = None
        branch_display = f"({branch_label}) " if show_branch_label else ""
        lines.append(
            self.style(f"{prefix}{branch_display}{revision.revision} {revision.doc}", fg=fg)
        )
        if self.show_dependencies and revision.dependencies:
            deps = (
                [revision.dependencies]
                if isinstance(revision.dependencies, str)
                else list(revision.dependencies)
            )
            for i, dep in enumerate(deps):
                symbol = box_drawing(
                    up=True, down=i < len(deps) - 1, left=False, right=True, bold=False
                )
                self.revision_line(
                    lines,
                    " " * len(prefix) + symbol + " ",
                    self.script.get_revision(dep),
                    show_branch_label=True,
                )


def get_status(
    config: Config,
    connection: Connection,
    *,
    branches: Iterable[str] = (),
    show_dependencies: bool = False,
    style: Style = _no_style,
) -> StatusReport:
    """Render all revisions grouped by branch, marking the ones applied in the database."""
    script = ScriptDirectory.from_config(config)
    _check_branches(script)
    migration_context = MigrationContext.configure(connection)
    current_heads = migration_context.get_current_heads()
    applied = set(script.iterate_revisions(current_heads, "base"))

    bases: dict[str, Script] = {}
    for base in sorted((script.get_revision(b) for b in script.get_bases()), key=_branch_label):
        bases[_branch_label(base)] = base

    renderer = _StatusRenderer(script, bases, applied, style, show_dependencies)
    branches = tuple(branches)
    blocks: list[str] = []
    outdated = False
    for branch_label, branch_base in bases.items():
        if branches and branch_label not in branches:
            continue
        branch_applied = branch_base in applied
        branch_outdated = False
        lines: list[str] = []
        levels: defaultdict[Script, set[int]] = defaultdict(set)
        seen: set[Script] = set()
        todo: deque[Script] = deque([branch_base])
        while todo:
            rev = todo.pop()

            down_levels = levels[rev]
            if rev.is_merge_point:
                down_ids = rev.down_revision
            elif rev.down_revision:
                down_ids = [rev.down_revision]
            else:
                down_ids = []
            down_revisions = [script.get_revision(r) for r in down_ids]
            next_revisions = [script.get_revision(r) for r in sorted(rev.nextrev)]

            if rev.is_merge_point and (not seen.issuperset(down_revisions) or rev in todo):
                continue
            seen.add(rev)

            next_levels = set()
            for j, nextrev in enumerate(next_revisions):
                if j == 0:
                    next_level = min(down_levels) if down_levels else 0
                else:
                    next_level = max(chain(*(levels[r] for r in todo))) + 1
                levels[nextrev].add(next_level)
                next_levels.add(next_level)
                todo.append(nextrev)

            all_levels = list(chain(down_levels, next_levels))
            min_level = min(all_levels, default=0)
            max_level = max(all_levels, default=0)
            symbol = "".join(
                " "
                if i < min_level
                else box_drawing(
                    up=i in down_levels,
                    down=i in next_levels,
                    left=i > min_level,
                    right=i < max_level,
                )
                for i in range(max_level + 1)
            )

            check = "x" if rev in applied else " "
            if branch_applied and rev not in applied:
                outdated = True
                branch_outdated = True
            renderer.revision_line(lines, f"  [{check}] {symbol} ", rev)

        if branch_applied:
            fg = "white"
            mark = " " + (style("×", fg="red") if branch_outdated else style("✓", fg="green"))
        else:
            fg = None
            mark = ""
        header = style(f"[{branch_label}", bold=True, fg=fg) + mark + style("]", bold=True, fg=fg)
        blocks.append("\n".join([header, *lines]))

    text = "\n".join(blocks)
    if outdated:
        text += "\n" + style(OUTDATED_MESSAGE, fg="red")
    return StatusReport(text=text, outdated=outdated)


def autoupgrade(
    config: Config,
    connection: Connection,
    *,
    sql: bool = False,
    tag: str | None = None,
    x_args: Iterable[str] = (),
) -> list[str]:
    """Upgrade every started branch that has revisions not applied yet.

    A branch is started when its base is applied. A branch can fork, so each of its heads that
    is not applied is upgraded in turn. Returns the upgraded heads in upgrade order.
    """
    set_x_args(config, x_args)
    script = ScriptDirectory.from_config(config)
    _check_branches(script)
    current_heads = MigrationContext.configure(connection).get_current_heads()
    applied = set(script.iterate_revisions(current_heads, "base"))
    targets = _outdated_targets(script, applied)
    for target in targets:
        command.upgrade(config, target, sql=sql, tag=tag)
    return targets


def _outdated_targets(script: ScriptDirectory, applied: set[Script]) -> list[str]:
    bases: dict[str, Script] = {}
    for base_id in script.get_bases():
        base = script.get_revision(base_id)
        bases[_branch_label(base)] = base
    heads: dict[str, list[str]] = defaultdict(list)
    for head_id in script.get_heads():
        heads[_branch_label(script.get_revision(head_id))].append(head_id)
    revisions: dict[str, set[Script]] = defaultdict(set)
    for revision in script.walk_revisions():
        revisions[_branch_label(revision)].add(revision)

    targets = []
    for label in sorted(bases):
        started = bases[label] in applied
        if started and not revisions[label] <= applied:
            targets.extend(
                head_id
                for head_id in sorted(heads[label])
                if script.get_revision(head_id) not in applied
            )
    return targets
