import ast
import json
import logging
from typing import Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

class Jinja2DecouplingVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        self.scope_stack: list[dict[str, str]] = [{}]
        self.path_aliases = {'Path'}
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module == 'pathlib':
            for name in node.names:
                if name.name == 'Path':
                    self.path_aliases.add(name.asname or name.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef):
        self.scope_stack.append({})
        self.generic_visit(node)
        self.scope_stack.pop()

    def _extract_string_val(self, node: ast.AST) -> str | None:
        """Extracts text from static strings AND resolves f-strings."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.JoinedStr):
            res = ""
            for val in node.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    res += val.value
            return res if res else "<dynamic>"
        return None

    def _is_path_call(self, node: ast.Call) -> str | None:
        """Returns the string argument if this is a Path() or pathlib.Path() call."""
        is_path = False
        if isinstance(node.func, ast.Name) and node.func.id in self.path_aliases:
            is_path = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr in self.path_aliases:
            is_path = True
            
        if is_path and len(node.args) >= 1:
            return self._extract_string_val(node.args[0])
        return None

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call):
            path_str = self._is_path_call(node.value)
            if path_str:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.scope_stack[-1][target.id] = path_str
        self.generic_visit(node)

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
                filename = self._extract_string_val(node.args[0])
                if filename and '.md' in filename:
                    mode = 'r'
                    if len(node.args) >= 2:
                        mode_val = self._extract_string_val(node.args[1])
                        if mode_val: mode = mode_val
                    else:
                        for kw in node.keywords:
                            if kw.arg == 'mode':
                                mode_val = self._extract_string_val(kw.value)
                                if mode_val: mode = mode_val
                    if 'w' in mode or 'a' in mode or 'x' in mode:
                        self.violations.append(f"Direct inline writing to markdown file detected: {filename}")
        
        # 2. Check for pathlib bypass: Path('file.md').write_text(...) or .open('w')
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ['write_text', 'open']:
                path_str = None
                
                # Case A: Direct Call e.g. Path('file.md') or pathlib.Path('file.md')
                if isinstance(node.func.value, ast.Call):
                    path_str = self._is_path_call(node.func.value)
                # Case B: Variable reference e.g. file_path.write_text(...)
                elif isinstance(node.func.value, ast.Name):
                    for scope in reversed(self.scope_stack):
                        if node.func.value.id in scope:
                            path_str = scope[node.func.value.id]
                            break
                
                if path_str and ('.md' in path_str or path_str == "<dynamic.md>"):
                    if node.func.attr == 'write_text':
                        self.violations.append(f"Direct Pathlib write_text to markdown file detected: {path_str}")
                    elif node.func.attr == 'open':
                        # Default for Path.open is 'r', so check for write modes
                        mode = 'r'
                        if len(node.args) >= 1:
                            mode_val = self._extract_string_val(node.args[0])
                            if mode_val: mode = mode_val
                        else:
                            for kw in node.keywords:
                                if kw.arg == 'mode':
                                    mode_val = self._extract_string_val(kw.value)
                                    if mode_val: mode = mode_val
                        if 'w' in mode or 'a' in mode or 'x' in mode:
                            self.violations.append(f"Direct Pathlib open() write to markdown file detected: {path_str}")

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
