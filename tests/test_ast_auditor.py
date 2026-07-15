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

if __name__ == "__main__":
    unittest.main()
