"""Tests for the SHAPE of the code: the packages in brsr_p6/ are layers, and a layer may only use the layers above it.

Why test this?  A rule that is only written in a README gets broken the first time someone is in a hurry.  Here the rule is checked
on every test run by reading the `import` lines of every module, so an upward import (for example `core` importing from `views`)
fails the test with the exact file and line.
"""

import ast
from pathlib import Path

import brsr_p6

PACKAGE_DIR = Path(brsr_p6.__file__).resolve().parent
TESTS_DIR = Path(__file__).resolve().parent

# Top of the list = lowest layer (used by everything).  A package may import from itself and from packages EARLIER in this list.
LAYERS = ["core", "download", "parsing", "extraction", "analysis", "views", "rendering", "workflows", "cli"]


def modules():
    """{dotted name: path} of every module in brsr_p6, for example 'brsr_p6.views.summary_view'."""
    found = {}
    for path in PACKAGE_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        parts = path.relative_to(PACKAGE_DIR.parent).with_suffix("").parts
        found[".".join(parts[:-1] if parts[-1] == "__init__" else parts)] = path
    return found


def imports_of(path):
    """[(dotted module name, line number)] for every brsr_p6 module this file imports."""
    found, known = [], modules()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "brsr_p6":
            found.append((node.module, node.lineno))
            submodules = [f"{node.module}.{a.name}" for a in node.names if f"{node.module}.{a.name}" in known]   # `from brsr_p6.cli import main_cli`
            found += [(name, node.lineno) for name in submodules]
        elif isinstance(node, ast.Import):
            found += [(a.name, node.lineno) for a in node.names if a.name.split(".")[0] == "brsr_p6"]
    return found


def package_of(dotted):
    parts = dotted.split(".")
    return parts[1] if len(parts) > 1 else None


def test_every_module_lives_in_one_of_the_layers():
    """No loose files in brsr_p6/ itself: each module belongs to a package with a job."""
    loose = [name for name in modules() if name.count(".") == 1 and name != "brsr_p6" and name.split(".")[1] not in LAYERS]
    assert not loose, f"modules outside the layers: {loose}"
    assert not [p.name for p in PACKAGE_DIR.glob("*.py") if p.name != "__init__.py"], "put new modules inside a package, not in brsr_p6/"
    assert {p.name for p in PACKAGE_DIR.iterdir() if p.is_dir() and p.name not in ("__pycache__", "templates")} == set(LAYERS)


def test_every_package_says_what_it_is_for():
    for layer in LAYERS:
        init = PACKAGE_DIR / layer / "__init__.py"
        assert init.exists(), f"{layer} has no __init__.py"
        assert ast.get_docstring(ast.parse(init.read_text(encoding="utf-8"))), f"{layer}/__init__.py has no description"


def test_a_package_only_imports_from_packages_above_it():
    problems = []
    for name, path in modules().items():
        own = package_of(name)
        if own not in LAYERS:
            continue
        for imported, line in imports_of(path):
            other = package_of(imported)
            if other in LAYERS and LAYERS.index(other) > LAYERS.index(own):
                problems.append(f"{path.relative_to(PACKAGE_DIR.parent)}:{line} ({own}) imports {imported} ({other}, a higher layer)")
    assert not problems, "\n".join(problems)


def test_there_are_no_circular_imports_between_modules():
    known = modules()
    graph = {name: sorted({imported for imported, _ in imports_of(path) if imported in known and imported != name})
             for name, path in known.items()}
    visiting, done = [], set()

    def visit(name):
        if name in done:
            return
        assert name not in visiting, "circular import: " + " -> ".join(visiting[visiting.index(name):] + [name])
        visiting.append(name)
        for other in graph[name]:
            visit(other)
        visiting.pop()
        done.add(name)

    for name in graph:
        visit(name)


def test_the_test_folders_mirror_the_packages():
    """tests/views tests brsr_p6/views, and so on.  tests/helpers holds shared helpers, not tests."""
    folders = {p.name for p in TESTS_DIR.iterdir() if p.is_dir() and p.name not in ("__pycache__", "helpers")}
    assert folders <= set(LAYERS), f"test folders without a package: {sorted(folders - set(LAYERS))}"
    loose = [p.name for p in TESTS_DIR.glob("test_*.py") if p.name != "test_architecture.py"]
    assert not loose, f"put each test next to the package it tests: {loose}"
