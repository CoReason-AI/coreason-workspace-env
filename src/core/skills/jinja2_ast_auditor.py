import ast
import json
import logging
from typing import Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

class Jinja2DecouplingVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        
    def visit_Expr(self, node: ast.Expr):
        # If the expression is just a string constant, it's likely a docstring.
        # We skip visiting its children to avoid false positives on Markdown tables in docstrings.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call):
        # 1. Check for standard open('file.md', 'w')
        if isinstance(node.func, ast.Name) and node.func.id == 'open':
            if len(node.args) >= 1:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                    if arg0.value.endswith('.md'):
                        mode = 'r'
                        if len(node.args) >= 2:
                            arg1 = node.args[1]
                            if isinstance(arg1, ast.Constant) and isinstance(arg1.value, str):
                                mode = arg1.value
                        else:
                            for kw in node.keywords:
                                if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
                                    mode = kw.value.value
                        if 'w' in mode or 'a' in mode or 'x' in mode:
                            self.violations.append(f"Direct inline writing to markdown file detected: {arg0.value}")
        
        # 2. Check for pathlib bypass: Path('file.md').write_text(...) or .open('w')
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ['write_text', 'open']:
                # The node.func.value is the Path(...) part. We must check if it's a Call to 'Path'
                path_call = node.func.value
                if isinstance(path_call, ast.Call) and isinstance(path_call.func, ast.Name) and path_call.func.id == 'Path':
                    if len(path_call.args) >= 1:
                        path_arg = path_call.args[0]
                        if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str):
                            if path_arg.value.endswith('.md'):
                                if node.func.attr == 'write_text':
                                    self.violations.append(f"Direct Pathlib write_text to markdown file detected: {path_arg.value}")
                                elif node.func.attr == 'open':
                                    # Default for Path.open is 'r', so check for write modes
                                    mode = 'r'
                                    if len(node.args) >= 1:
                                        mode_arg = node.args[0]
                                        if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
                                            mode = mode_arg.value
                                    if 'w' in mode or 'a' in mode or 'x' in mode:
                                        self.violations.append(f"Direct Pathlib open() write to markdown file detected: {path_arg.value}")

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # Look for markdown structures in f-strings
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if '|---' in value.value or '\n# ' in value.value or value.value.startswith('# '):
                    self.violations.append("Markdown formatting detected inside an f-string.")
        self.generic_visit(node)
        
    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str):
            if '|---' in node.value and '\n' in node.value:
                self.violations.append("Inline markdown table generation detected.")
        self.generic_visit(node)

@tool
def jinja2_ast_auditor(python_code: str) -> str:
    """
    Mathematically parses the Abstract Syntax Tree (AST) of the submitted Python code 
    to detect violations of the Jinja2 Decoupling Pattern.
    Returns a GuardrailViolationEvent if inline markdown generation or direct .md file writing is detected.
    """
    logger.info("Auditing Python payload for Jinja2 Decoupling Pattern compliance...")
    
    try:
        tree = ast.parse(python_code)
    except SyntaxError as e:
        return json.dumps({
            "status": "FAIL", 
            "reason": f"Syntax error in submitted code: {e}"
        })
        
    visitor = Jinja2DecouplingVisitor()
    visitor.visit(tree)
    
    if visitor.violations:
        return json.dumps({
            "status": "FAIL",
            "reason": "GuardrailViolationEvent: Jinja2 Decoupling Pattern broken. Markdown must be generated via a separate Jinja2 template and compiler script.",
            "violations": visitor.violations
        })
        
    return json.dumps({
        "status": "PASS",
        "reason": "Code conforms to the Jinja2 Decoupling Pattern."
    })
