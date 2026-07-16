import os
import tempfile
import unittest

from src.core.tools.ast_modifier import ast_validate_syntax


class TestASTModifier(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = os.path.join(self.temp_dir.name, "sample.py")
        
        initial_code = """
# This is a sample file
def hello_world():
    print("Hello, world!")
"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(initial_code.strip() + "\n")
            
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ast_validate_syntax_success(self):
        result = ast_validate_syntax.invoke({"file_path": self.file_path})
        self.assertIn("Syntax validation passed", result)

    def test_ast_validate_syntax_failure(self):
        # Write broken python code
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("def broken_func()\n  print('missing colon')\n")
            
        result = ast_validate_syntax.invoke({"file_path": self.file_path})
        self.assertIn("Syntax Error in", result)

if __name__ == "__main__":
    unittest.main()
