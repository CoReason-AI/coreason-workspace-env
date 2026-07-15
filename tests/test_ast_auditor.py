import unittest
import json
from src.core.skills.jinja2_ast_auditor import jinja2_ast_auditor

class TestJinja2ASTAuditor(unittest.TestCase):
    def test_auditor_pass_clean_code(self):
        clean_code = """
import json

def generate_telemetry():
    data = {"accuracy": 0.95}
    with open("results.json", "w") as f:
        json.dump(data, f)
    return data
"""
        # The tool expects a dict or string, let's call it directly
        result = jinja2_ast_auditor.invoke({"python_code": clean_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "PASS")

    def test_auditor_fail_open_md(self):
        bad_code = """
def generate_report():
    with open("output.md", "w") as f:
        f.write("# Hello World\\n")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("output.md" in v for v in parsed["violations"]))

    def test_auditor_fail_fstring_markdown(self):
        bad_code = """
def format_data():
    x = 5
    report = f"# Title\\n|---|---|\\n| {x} | 10 |"
    return report
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Markdown formatting detected inside an f-string" in v for v in parsed["violations"]))

    def test_auditor_fail_inline_table(self):
        bad_code = """
def format_data():
    report = "|---|---|\\n| a | b |"
    return report
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Inline markdown table generation detected" in v for v in parsed["violations"]))

    def test_auditor_pass_docstring_table(self):
        clean_code = '''
def format_data():
    """
    This function formats data.
    |---|---|
    | a | b |
    """
    return "done"
'''
        result = jinja2_ast_auditor.invoke({"python_code": clean_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "PASS")

    def test_auditor_fail_pathlib_write_text(self):
        bad_code = """
from pathlib import Path
def write_report():
    Path("output.md").write_text("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib write_text to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_fail_pathlib_open(self):
        bad_code = """
from pathlib import Path
def write_report():
    with Path("output.md").open("w") as f:
        f.write("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib open() write to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_fail_pathlib_assignment_bypass(self):
        bad_code = """
from pathlib import Path
def write_report():
    file_path = Path("output.md")
    file_path.write_text("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib write_text to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_fail_pathlib_import_alias_bypass(self):
        bad_code = """
import pathlib
def write_report():
    pathlib.Path("output.md").write_text("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib write_text to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_fail_pathlib_open_keyword_bypass(self):
        bad_code = """
from pathlib import Path
def write_report():
    with Path("output.md").open(mode="w") as f:
        f.write("# Hello")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib open() write to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_fail_joinedstr_bypass(self):
        bad_code = """
from pathlib import Path
def write_report():
    date = "2026-07-14"
    Path(f"report_{date}.md").write_text("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib write_text to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_pass_scope_bleed(self):
        code = """
from pathlib import Path
def write_report():
    file_path = Path("output.md")
def other_func():
    file_path = Path("data.json")
    file_path.write_text("{}")
"""
        result = jinja2_ast_auditor.invoke({"python_code": code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "PASS")

    def test_auditor_fail_import_renaming_bypass(self):
        bad_code = """
from pathlib import Path as MDWriter
def write_report():
    MDWriter("output.md").write_text("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib write_text to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_fail_open_joinedstr_bypass(self):
        bad_code = """
def write_report():
    date = "2026-07-14"
    open(f"report_{date}.md", "w").write("# Report Title")
"""
        result = jinja2_ast_auditor.invoke({"python_code": bad_code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "FAIL")
        self.assertTrue(any("Direct inline writing to markdown file detected" in v for v in parsed["violations"]))

    def test_auditor_pass_class_scope_bleed(self):
        code = """
from pathlib import Path
class MyClass:
    file_path = Path("output.md")

def other_func():
    file_path = Path("data.json")
    file_path.write_text("{}")
"""
        result = jinja2_ast_auditor.invoke({"python_code": code})
        parsed = json.loads(result)
        self.assertEqual(parsed["status"], "PASS")

if __name__ == "__main__":
    unittest.main()
