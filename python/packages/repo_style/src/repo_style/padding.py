"""Require padding before control-flow statements, using language syntax trees."""

import argparse
import ast
import os
import sys
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path

import tree_sitter_rust
from tree_sitter import Language, Node, Parser

SKIP_DIRECTORIES = {".git", ".venv", ".cache", "__pycache__", "target", "node_modules"}
PYTHON_CONTROL = (ast.Return, ast.Raise, ast.Break, ast.Continue)
RUST_CONTROL = {"return_expression", "break_expression", "continue_expression"}


def python_pairs(source: str) -> Iterator[tuple[int, int]]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        for _, field in ast.iter_fields(node):
            if not isinstance(field, list):
                continue
            for previous, current in pairwise(field):
                if isinstance(previous, ast.stmt) and isinstance(current, PYTHON_CONTROL):
                    assert previous.end_lineno is not None
                    yield previous.end_lineno, current.lineno


def rust_pairs(source: str) -> tuple[list[tuple[int, int]], set[int]]:
    tree = Parser(Language(tree_sitter_rust.language())).parse(source.encode("utf-8"))
    if tree.root_node.has_error:
        raise SyntaxError("Rust parser rejected this file; padding was not checked")
    pairs: list[tuple[int, int]] = []
    comment_lines: set[int] = set()
    pending: list[Node] = [tree.root_node]
    while pending:
        node = pending.pop()
        if node.type in {"block_comment", "line_comment"}:
            comment_lines.update(range(node.start_point.row + 1, node.end_point.row + 2))

            continue
        if node.type in {"token_tree", "macro_definition"}:
            continue
        if node.type == "block":
            statements = [
                child
                for child in node.named_children
                if child.type not in {"line_comment", "block_comment", "attribute_item"}
            ]
            for previous, current in pairwise(statements):
                expression = current
                if current.type == "expression_statement" and current.named_children:
                    expression = current.named_children[0]
                if expression.type in RUST_CONTROL:
                    pairs.append((previous.end_point.row + 1, current.start_point.row + 1))
        pending.extend(node.named_children)

    return pairs, comment_lines


def missing_padding(source: str, suffix: str) -> list[tuple[int, int]]:
    """Return (previous end line, control statement line), both one-based."""
    if suffix in {".py", ".pyi"}:
        pairs, comment_lines = list(python_pairs(source)), set()
    elif suffix == ".rs":
        pairs, comment_lines = rust_pairs(source)
    else:
        raise ValueError(f"Unsupported source extension: {suffix}")
    lines = source.splitlines()

    return sorted(
        (previous, current)
        for previous, current in pairs
        if not any(
            not lines[line - 1].strip() and line not in comment_lines
            for line in range(previous + 1, current)
        )
    )


def pad_source(source: str, suffix: str) -> str:
    lines = source.splitlines(keepends=True)
    newline = "\r\n" if "\r\n" in source else "\n"
    insertion_points = {
        previous for previous, current in missing_padding(source, suffix) if previous < current
    }
    for index in sorted(insertion_points, reverse=True):
        lines.insert(index, newline)

    return "".join(lines)


def source_files(paths: list[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_symlink():
            continue
        candidates = [path]
        if path.is_dir():
            candidates = []
            for directory, children, files in os.walk(path, followlinks=False):
                children[:] = sorted(child for child in children if child not in SKIP_DIRECTORIES)
                candidates.extend(Path(directory) / name for name in sorted(files))
        for candidate in candidates:
            if candidate.suffix not in {".py", ".pyi", ".rs"} or candidate.is_symlink():
                continue
            canonical = candidate.resolve()
            if canonical not in seen:
                seen.add(canonical)
                yield candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="Insert missing blank lines")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    try:
        for path in source_files(args.paths):
            try:
                source = path.read_bytes().decode("utf-8")
                if args.fix:
                    fixed = pad_source(source, path.suffix)
                    if fixed != source:
                        path.write_bytes(fixed.encode("utf-8"))
                    source = fixed
                for previous, current in missing_padding(source, path.suffix):
                    message = "Expected a blank line before this control-flow statement"
                    if previous == current:
                        message += "; run the language formatter to split this line first"
                    print(f"{path}:{current}:1: PAD001 {message}")
                    failed = True
            except (SyntaxError, UnicodeError) as error:
                print(f"{path}: PAD000 {error}", file=sys.stderr)
                failed = True
    except OSError as error:
        print(error, file=sys.stderr)

        return 1

    return int(failed)
