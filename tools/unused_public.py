"""List public names in src/ that could probably be private (start with `_`).

A public top-level name is reported when no *other* file uses it. The result is a
hint only: whether a name belongs to the public API is the owner's decision.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IGNORED = {"main"}  # entry points are public on purpose


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def names_defined_by(node: ast.stmt) -> list[str]:
    """Names a top-level statement creates: functions, classes, variables."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def defined_names(tree: ast.Module) -> list[str]:
    return [name for node in tree.body for name in names_defined_by(node)]


def name_used_by(node: ast.AST) -> str | None:
    """The name a syntax node reads or imports, if it is one that counts as a use."""
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.alias):
        return node.name.split(".")[-1]
    return None


def used_names(tree: ast.Module) -> set[str]:
    """Every name a module reads, calls, imports or accesses as an attribute."""
    uses = (name_used_by(node) for node in ast.walk(tree))
    return {name for name in uses if name is not None}


def candidates(
    tree: ast.Module, used_elsewhere: set[str]
) -> tuple[list[str], list[str]]:
    """Split unused-elsewhere public names into (used only here, used nowhere)."""
    inside = used_names(tree)
    only_here: list[str] = []
    nowhere: list[str] = []
    for name in defined_names(tree):
        if name.startswith("_") or name in IGNORED or name in used_elsewhere:
            continue
        (only_here if name in inside else nowhere).append(name)
    return only_here, nowhere


def main() -> None:
    sources = sorted((ROOT / "src").rglob("*.py"))
    everything = sources + sorted((ROOT / "tests").glob("*.py"))
    trees = {path: parse(path) for path in everything}
    uses = {path: used_names(tree) for path, tree in trees.items()}

    total = 0
    for path in sources:
        elsewhere = set().union(*(u for other, u in uses.items() if other != path))
        only_here, nowhere = candidates(trees[path], elsewhere)
        if only_here or nowhere:
            print(path.relative_to(ROOT))
        if only_here:
            print("  used only in this file (could be _private):", ", ".join(only_here))
        if nowhere:
            print(
                "  used nowhere (dead code, or not wired up yet):", ", ".join(nowhere)
            )
        total += len(only_here) + len(nowhere)
    print(f"\n{total} candidate(s). Decide each one; rename with a leading underscore.")


if __name__ == "__main__":
    main()
