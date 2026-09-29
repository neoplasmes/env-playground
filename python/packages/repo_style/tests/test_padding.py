import ast
import subprocess
import sys

import pytest
from repo_style import missing_padding, pad_source


@pytest.mark.parametrize("statement", ["return value", "raise ValueError()", "break", "continue"])
def test_python_control_statements(statement):
    source = f"def run():\n    while True:\n        value = 1\n        {statement}\n"
    assert missing_padding(source, ".py") == [(3, 4)]
    fixed = pad_source(source, ".py")
    assert "value = 1\n\n        " in fixed
    assert ast.dump(ast.parse(source)) == ast.dump(ast.parse(fixed))
    assert pad_source(fixed, ".py") == fixed


@pytest.mark.parametrize("statement", ["return value;", "break 'outer value;", "continue 'outer;"])
def test_rust_control_statements(statement):
    source = (
        "fn run() {\n    'outer: loop {\n        let value = 1;\n"
        f"        {statement}\n    }}\n}}\n"
    )
    assert missing_padding(source, ".rs") == [(3, 4)]
    fixed = pad_source(source, ".rs")
    assert "let value = 1;\n\n        " in fixed
    assert not missing_padding(fixed, ".rs")
    assert pad_source(fixed, ".rs") == fixed


@pytest.mark.parametrize(
    ("suffix", "source"),
    [
        (".py", "def run():\n    return 1\n"),
        (".py", 'def run():\n    value = "return break continue raise"\n\n    return value\n'),
        (".py", 'def run():\n    value = """text\nreturn raise\n"""\n    # return\n'),
        (".py", "def run():\n    value = 1\n    if value:\n        return value\n"),
        (".rs", "fn run() { return 1; }"),
        (".rs", 'fn run() { let value = r#"return;\n break;"#; }'),
        (".rs", "fn run() { let value = 1; if value > 0 { return value; } }"),
        (".rs", "fn run() { let value = 1; value }"),
        (".rs", "macro_rules! rule { () => { work(); return; } }"),
        (".rs", "fn run() { custom_macro!(work(); return;); }"),
        (".rs", "fn run() { let value = 1; match value { 1 => return, _ => {} } }"),
    ],
)
def test_no_false_positives(suffix, source):
    assert missing_padding(source, suffix) == []


@pytest.mark.parametrize(
    ("suffix", "source", "expected"),
    [
        (".py", "def run():\n    work()\n    # reason\n    return\n", [(2, 4)]),
        (".py", "def run():\n    work(\n        1\n    )\n    return\n", [(4, 5)]),
        (".rs", "fn run() {\n    work();\n    /* reason\n\n    */\n    return;\n}", [(2, 6)]),
        (
            ".rs",
            "fn run() {\n    work();\n    #[allow(unreachable_code)]\n    return;\n}",
            [(2, 4)],
        ),
        (".rs", "fn run() {\n    work(\n        1\n    );\n    return;\n}", [(4, 5)]),
    ],
)
def test_comments_attributes_and_multiline_statements(suffix, source, expected):
    assert missing_padding(source, suffix) == expected
    fixed = pad_source(source, suffix)
    assert not missing_padding(fixed, suffix)
    assert fixed.replace("\n\n", "\n", 1) == source


@pytest.mark.parametrize(
    ("suffix", "source"),
    [(".py", "def run(): work(); return\n"), (".rs", "fn run() { work(); return; }")],
)
def test_same_line_statements_need_language_formatter(suffix, source):
    assert missing_padding(source, suffix) == [(1, 1)]
    assert pad_source(source, suffix) == source


@pytest.mark.parametrize(("suffix", "source"), [(".py", "def run(:"), (".rs", "fn run( {")])
def test_syntax_errors_fail_closed(suffix, source):
    with pytest.raises(SyntaxError):
        missing_padding(source, suffix)


def test_crlf_is_preserved():
    source = "def run():\r\n    work()\r\n    return\r\n"
    assert pad_source(source, ".py") == "def run():\r\n    work()\r\n\r\n    return\r\n"


def test_cli_check_fix_and_generated_directory_exclusion(tmp_path):
    source = tmp_path / "example.py"
    source.write_text("def run():\n    work()\n    return\n")
    generated = tmp_path / "target"
    generated.mkdir()
    (generated / "invalid.rs").write_text("invalid {")
    command = [sys.executable, "-c", "from repo_style import main; raise SystemExit(main())"]
    check = subprocess.run([*command, str(tmp_path)], capture_output=True, text=True)
    assert check.returncode == 1
    assert "example.py:3:1: PAD001" in check.stdout
    fix = subprocess.run([*command, "--fix", str(tmp_path)], capture_output=True, text=True)
    assert fix.returncode == 0, fix.stderr
    assert "work()\n\n" in source.read_text()
    assert subprocess.run([*command, str(tmp_path)], capture_output=True).returncode == 0
